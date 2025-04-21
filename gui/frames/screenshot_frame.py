import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import io
import threading
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, Optional, Tuple, List, Callable, Union

from core.screenshot import ScreenshotCapturer, get_display_info
from cryptography.fernet import Fernet


class FullScreenImageViewer(tk.Toplevel):
    """Cửa sổ xem ảnh toàn màn hình"""

    def __init__(self, parent, image_path, encryption_key=None, encrypt=False):
        super().__init__(parent)
        self.parent = parent
        self.image_path = image_path
        self.encryption_key = encryption_key
        self.encrypt = encrypt

        # Cấu hình cửa sổ toàn màn hình
        self.attributes('-fullscreen', True)
        self.configure(background='black')

        # Biến lưu trữ ảnh
        self.photo = None

        # Tạo giao diện
        self._create_widgets()

        # Hiển thị ảnh
        self._load_image()

        # Bắt sự kiện phím
        self.bind("<Escape>", self._close)
        self.bind("<Button-1>", self._close)

    def _create_widgets(self):
        """Tạo các phần tử giao diện"""
        # Label hiển thị ảnh
        self.image_label = ttk.Label(self, background='black')
        self.image_label.pack(expand=True, fill=tk.BOTH)

        # Thêm thông tin hướng dẫn
        self.hint_label = ttk.Label(
            self,
            text="Nhấn ESC hoặc click chuột để đóng",
            background='black',
            foreground='white',
            font=("Arial", 12)
        )
        self.hint_label.place(x=10, y=10)

        # Thêm thông tin về ảnh
        self.info_label = ttk.Label(
            self,
            text="",
            background='black',
            foreground='white',
            font=("Arial", 12)
        )
        self.info_label.place(x=10, y=40)

        # Hiện tooltip trong 3 giây rồi ẩn đi
        self.after(3000, lambda: self.hint_label.place_forget())

    def _load_image(self):
        """Tải và hiển thị ảnh"""
        try:
            # Đọc ảnh dựa vào loại file (mã hóa hoặc không)
            if self.encrypt and str(self.image_path).endswith('.enc'):
                # Xử lý đọc ảnh đã mã hóa - cần giải mã
                if self.encryption_key:
                    with open(self.image_path, "rb") as f:
                        encrypted_data = f.read()
                    fernet = Fernet(self.encryption_key)
                    decrypted_data = fernet.decrypt(encrypted_data)
                    img = Image.open(io.BytesIO(decrypted_data))
                else:
                    self.destroy()
                    return
            else:
                img = Image.open(self.image_path)

            # Kích thước màn hình
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # Kích thước gốc
            orig_width, orig_height = img.size

            # Hiển thị thông tin ảnh
            file_info = Path(self.image_path).stat()
            file_size_kb = file_info.st_size / 1024
            file_time = datetime.fromtimestamp(file_info.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
            self.info_label.config(
                text=f"Ảnh: {Path(self.image_path).name} ({orig_width}x{orig_height}, {file_size_kb:.1f}KB, {file_time})"
            )

            # Tính toán tỉ lệ để giữ nguyên tỉ lệ khung hình
            ratio = min(screen_width / orig_width, screen_height / orig_height)
            new_size = (int(orig_width * ratio), int(orig_height * ratio))

            # Resize ảnh với phương pháp LANCZOS cho chất lượng cao nhất
            img_resized = img.resize(new_size, Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img_resized)

            # Cập nhật ảnh lên label
            self.image_label.config(image=self.photo)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị ảnh toàn màn hình: {str(e)}")
            self.destroy()

    def _close(self, event=None):
        """Đóng cửa sổ xem ảnh"""
        self.destroy()


class ScreenshotFrame(ttk.Frame):
    """Frame quản lý chụp màn hình của Keylogger Pro"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Biến lưu trạng thái
        self.capturer = None
        self.encryption_key = None
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "Keylogger_Pro", "screenshots")
        self.is_active = False
        self.preview_image = None
        self.last_screenshot_path = None
        self.thumbnail_size = (120, 80)  # Kích thước ảnh thu nhỏ
        self.hover_image = None  # Biến lưu trữ ảnh đang hover
        self.thumbnail_frames = []  # Danh sách các frame chứa ảnh thu nhỏ
        self.thumbnail_images = []  # Giữ tham chiếu đến ảnh thu nhỏ
        self.max_thumbnails = 50  # Tăng số lượng ảnh hiển thị
        self._refresh_job = None  # Lưu job ID cho việc tự động làm mới
        self._loading = False  # Trạng thái đang tải ảnh
        self.fullscreen_viewer = None  # Cửa sổ xem ảnh toàn màn hình

        # Tạo giao diện
        self._create_widgets()
        self._init_default_values()

        # Tìm và hiển thị các ảnh đã chụp khi khởi động
        self.after(500, self._load_recent_screenshots)

        # Thiết lập tự động làm mới
        self._setup_auto_refresh()

    def _create_widgets(self):
        """Tạo các phần tử giao diện"""
        # Chia frame chính thành 2 phần: cấu hình và xem trước
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Phần cấu hình
        config_frame = ttk.LabelFrame(main_paned, text="Cấu hình chụp màn hình", padding=10)

        # Phần xem trước
        preview_main_frame = ttk.LabelFrame(main_paned, text="Xem trước", padding=10)

        # Thêm vào paned window với tỷ lệ 40:60
        main_paned.add(config_frame, weight=40)
        main_paned.add(preview_main_frame, weight=60)

        # === Phần cấu hình ===
        # Đường dẫn lưu
        path_frame = ttk.Frame(config_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="Thư mục lưu:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(path_frame, text="Chọn...", command=self._browse_dir).pack(side=tk.RIGHT)

        # Khoảng thời gian
        interval_frame = ttk.Frame(config_frame)
        interval_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interval_frame, text="Chụp mỗi:").pack(side=tk.LEFT)
        self.interval_var = tk.IntVar(value=60)
        ttk.Spinbox(interval_frame, from_=1, to=3600, textvariable=self.interval_var, width=10).pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Label(interval_frame, text="giây").pack(side=tk.LEFT)

        # Vùng chụp
        region_frame = ttk.Frame(config_frame)
        region_frame.pack(fill=tk.X, pady=5)

        ttk.Label(region_frame, text="Vùng chụp:").pack(side=tk.LEFT)
        self.region_var = tk.StringVar(value="Toàn màn hình")
        region_cb = ttk.Combobox(region_frame, textvariable=self.region_var, state="readonly", width=25)
        region_cb.pack(side=tk.LEFT, padx=5)

        # Lấy thông tin màn hình
        screens = get_display_info()
        self.screens = screens
        screen_options = ["Toàn màn hình"]
        for screen in screens:
            screen_options.append(f"Màn hình {screen['id']}")
        region_cb["values"] = screen_options

        ttk.Button(region_frame, text="Tùy chọn...", command=self._select_custom_region).pack(side=tk.RIGHT)

        # Định dạng hình ảnh
        format_frame = ttk.Frame(config_frame)
        format_frame.pack(fill=tk.X, pady=5)

        ttk.Label(format_frame, text="Định dạng:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="PNG")
        format_cb = ttk.Combobox(format_frame, textvariable=self.format_var, state="readonly", width=10)
        format_cb["values"] = ["PNG", "JPEG"]
        format_cb.pack(side=tk.LEFT, padx=5)

        ttk.Label(format_frame, text="Chất lượng:").pack(side=tk.LEFT, padx=(10, 0))
        self.quality_var = tk.IntVar(value=90)
        quality_scale = ttk.Scale(format_frame, from_=10, to=100, variable=self.quality_var, orient=tk.HORIZONTAL)
        quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.quality_label = ttk.Label(format_frame, text="90")
        self.quality_label.pack(side=tk.LEFT, padx=5)

        # Cập nhật nhãn chất lượng khi slider thay đổi
        def update_quality_label(*args):
            self.quality_label.config(text=str(self.quality_var.get()))

        self.quality_var.trace("w", update_quality_label)

        # Tính năng nâng cao
        advanced_frame = ttk.LabelFrame(config_frame, text="Tính năng nâng cao")
        advanced_frame.pack(fill=tk.X, pady=10)

        # Hoạt động theo thay đổi
        self.change_detect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Chỉ chụp khi có thay đổi", variable=self.change_detect_var).pack(
            anchor=tk.W, pady=2)

        sensitivity_frame = ttk.Frame(advanced_frame)
        sensitivity_frame.pack(fill=tk.X, pady=2)

        ttk.Label(sensitivity_frame, text="   Độ nhạy:").pack(side=tk.LEFT)
        self.sensitivity_var = tk.DoubleVar(value=0.1)
        sensitivity_scale = ttk.Scale(sensitivity_frame, from_=0.01, to=0.5, variable=self.sensitivity_var,
                                      orient=tk.HORIZONTAL)
        sensitivity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.sensitivity_label = ttk.Label(sensitivity_frame, text="0.10")
        self.sensitivity_label.pack(side=tk.LEFT, padx=5)

        # Cập nhật nhãn độ nhạy khi slider thay đổi
        def update_sensitivity_label(*args):
            self.sensitivity_label.config(text=f"{self.sensitivity_var.get():.2f}")

        self.sensitivity_var.trace("w", update_sensitivity_label)

        # Mã hóa
        self.encrypt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Mã hóa ảnh chụp", variable=self.encrypt_var).pack(anchor=tk.W, pady=2)

        # Thumbnail
        self.create_thumb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Tạo ảnh thu nhỏ (thumbnail)",
                        variable=self.create_thumb_var).pack(anchor=tk.W, pady=2)

        # Giữ file
        retention_frame = ttk.Frame(advanced_frame)
        retention_frame.pack(fill=tk.X, pady=2)

        ttk.Label(retention_frame, text="   Giữ ảnh:").pack(side=tk.LEFT)
        self.retention_var = tk.IntVar(value=7)
        ttk.Spinbox(retention_frame, from_=1, to=365, textvariable=self.retention_var, width=5).pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Label(retention_frame, text="ngày").pack(side=tk.LEFT)

        # Giới hạn lưu trữ
        storage_frame = ttk.Frame(advanced_frame)
        storage_frame.pack(fill=tk.X, pady=2)

        ttk.Label(storage_frame, text="   Giới hạn:").pack(side=tk.LEFT)
        self.storage_var = tk.IntVar(value=500)
        ttk.Spinbox(storage_frame, from_=50, to=10000, textvariable=self.storage_var, width=5).pack(side=tk.LEFT,
                                                                                                    padx=5)
        ttk.Label(storage_frame, text="MB").pack(side=tk.LEFT)

        # Tải lên từ xa
        self.upload_var = tk.BooleanVar(value=False)
        upload_cb = ttk.Checkbutton(advanced_frame, text="Tải lên máy chủ từ xa", variable=self.upload_var,
                                    command=self._toggle_upload_fields)
        upload_cb.pack(anchor=tk.W, pady=2)

        # Frame cấu hình upload
        self.upload_frame = ttk.Frame(advanced_frame)
        self.upload_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.upload_frame, text="   Endpoint:").pack(side=tk.LEFT)
        self.endpoint_var = tk.StringVar()
        self.endpoint_entry = ttk.Entry(self.upload_frame, textvariable=self.endpoint_var)
        self.endpoint_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        token_frame = ttk.Frame(advanced_frame)

        ttk.Label(token_frame, text="   Token:").pack(side=tk.LEFT)
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var, show="•")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.upload_frame.pack_forget()
        token_frame.pack_forget()

        # Nút điều khiển
        control_frame = ttk.Frame(config_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(control_frame, text="Bắt đầu chụp",
                                       command=self._toggle_capturer, style="success.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(control_frame, text="Tạm dừng",
                                       command=self._toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Thêm nút chụp ngay lập tức
        self.capture_now_button = ttk.Button(control_frame, text="Chụp ngay",
                                             command=self._capture_now)
        self.capture_now_button.pack(side=tk.LEFT, padx=5)

        self.preview_button = ttk.Button(control_frame, text="Xem thư mục",
                                         command=self._open_screenshots_viewer)
        self.preview_button.pack(side=tk.LEFT, padx=5)

        # Thêm nút dọn dẹp thumbnail
        self.clean_button = ttk.Button(control_frame, text="Dọn thumbnail",
                                       command=self._clean_thumbnails)
        self.clean_button.pack(side=tk.LEFT, padx=5)

        # === Phần xem trước ===
        # Tạo frame chia làm 2 phần: ảnh lớn và danh sách ảnh thu nhỏ
        preview_container = ttk.Frame(preview_main_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        # Phần hiển thị ảnh lớn
        self.main_preview_frame = ttk.LabelFrame(preview_container, text="Ảnh hiện tại")
        self.main_preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.preview_label = ttk.Label(self.main_preview_frame, text="Chưa có ảnh chụp")
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Thêm tooltips và binding cho xem ảnh toàn màn hình
        self.preview_label.bind("<Enter>", self._show_preview_tooltip)
        self.preview_label.bind("<Leave>", self._hide_preview_tooltip)
        self.preview_label.bind("<Button-1>", self._show_fullscreen)

        # Frame chứa các thumbnails và nút điều hướng
        thumbnails_control_frame = ttk.Frame(preview_container)
        thumbnails_control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # Thay đổi phần frame chứa thumbnails
        self.thumbnails_frame = ttk.LabelFrame(thumbnails_control_frame, text="Ảnh gần đây")
        self.thumbnails_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Thêm thanh trạng thái hiển thị số lượng ảnh và đang tải
        self.status_frame = ttk.Frame(self.thumbnails_frame)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(self.status_frame, text="0 ảnh", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.loading_label = ttk.Label(self.status_frame, text="", anchor=tk.E)
        self.loading_label.pack(side=tk.RIGHT, padx=5)

        # Tạo canvas và scrollbar - THAY ĐỔI TỪ CUỘN NGANG SANG CUỘN DỌC
        thumbnail_container = ttk.Frame(self.thumbnails_frame)
        thumbnail_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.thumbnails_canvas = tk.Canvas(thumbnail_container, height=300)  # Tăng chiều cao
        self.thumbnails_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Thanh cuộn dọc thay vì ngang
        scrollbar = ttk.Scrollbar(thumbnail_container, orient=tk.VERTICAL,
                                  command=self.thumbnails_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.thumbnails_canvas.configure(yscrollcommand=scrollbar.set)

        # Frame trong canvas để chứa thumbnails
        self.thumbnail_grid = ttk.Frame(self.thumbnails_canvas)
        self.thumbnails_canvas.create_window((0, 0), window=self.thumbnail_grid, anchor="nw")

        # Cấu hình cuộn chuột
        self.thumbnails_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.thumbnail_grid.bind("<Configure>", self._configure_canvas)

        # Khởi tạo UI xem trước
        self._toggle_upload_fields()

        # Tạo tooltip frame cho hover
        self.tooltip_frame = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        self.tooltip_label = ttk.Label(self.tooltip_frame)
        self.tooltip_label.pack(fill=tk.BOTH, expand=True)

        # Tạo frame tooltip cho hướng dẫn
        self.help_tooltip_frame = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        self.help_tooltip_label = ttk.Label(self.help_tooltip_frame,
                                            text="Click để xem ảnh toàn màn hình",
                                            background="#ffffcc",
                                            padding=5)
        self.help_tooltip_label.pack(fill=tk.BOTH, expand=True)

    def _show_preview_tooltip(self, event):
        """Hiển thị tooltip khi hover lên ảnh xem trước"""
        if self.last_screenshot_path:
            x = event.x_root + 15
            y = event.y_root + 10
            self.help_tooltip_frame.place(x=x, y=y)

    def _hide_preview_tooltip(self, event):
        """Ẩn tooltip khi rời khỏi ảnh xem trước"""
        self.help_tooltip_frame.place_forget()

    def _show_fullscreen(self, event):
        """Hiển thị ảnh toàn màn hình khi click vào ảnh xem trước"""
        if self.last_screenshot_path:
            # Đóng cửa sổ toàn màn hình cũ nếu có
            if self.fullscreen_viewer and self.fullscreen_viewer.winfo_exists():
                self.fullscreen_viewer.destroy()

            # Tạo cửa sổ toàn màn hình mới
            self.fullscreen_viewer = FullScreenImageViewer(
                self,
                self.last_screenshot_path,
                self.encryption_key,
                self.encrypt_var.get()
            )

    def _init_default_values(self):
        """Thiết lập giá trị mặc định"""
        # Thiết lập đường dẫn mặc định
        self.path_entry.insert(0, self.screenshot_dir)

        # Tạo thư mục nếu chưa tồn tại
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)

        # Theo dõi sự thay đổi khoảng thời gian
        self.interval_var.trace("w", self._interval_changed)

    def _setup_auto_refresh(self):
        """Thiết lập tự động cập nhật danh sách ảnh"""
        # Lấy khoảng thời gian từ thiết lập
        interval = self.interval_var.get() * 1000  # Chuyển giây sang mili giây
        # Đặt thời gian làm mới bằng với chu kỳ chụp ảnh
        self._schedule_next_refresh(interval)

    def _interval_changed(self, *args):
        """Được gọi khi khoảng thời gian chụp thay đổi"""
        # Hủy bỏ lịch cập nhật hiện tại (nếu có)
        if hasattr(self, '_refresh_job') and self._refresh_job:
            self.after_cancel(self._refresh_job)

        # Thiết lập lại với khoảng thời gian mới
        interval = self.interval_var.get() * 1000  # Chuyển giây sang mili giây
        self._schedule_next_refresh(interval)

    def _schedule_next_refresh(self, interval):
        """Lên lịch cập nhật tiếp theo"""
        # Đảm bảo khoảng thời gian tối thiểu là 1 giây
        interval = max(1000, interval)

        # Lưu job ID để có thể hủy bỏ nếu cần
        self._refresh_job = self.after(interval, self._auto_refresh)

    def _auto_refresh(self):
        """Tự động cập nhật danh sách ảnh"""
        # Tải lại danh sách ảnh
        self._load_recent_screenshots()

        # Lên lịch cập nhật tiếp theo
        interval = self.interval_var.get() * 1000  # Chuyển giây sang mili giây
        self._schedule_next_refresh(interval)

    def _on_mousewheel(self, event):
        """Xử lý sự kiện cuộn chuột - đã chuyển sang cuộn dọc"""
        # Điều chỉnh tốc độ cuộn phù hợp với hệ điều hành
        if sys.platform.startswith('win'):
            self.thumbnails_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif sys.platform.startswith('darwin'):  # macOS
            self.thumbnails_canvas.yview_scroll(int(-1 * event.delta), "units")
        else:  # Linux
            if event.num == 4:  # Cuộn lên
                self.thumbnails_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Cuộn xuống
                self.thumbnails_canvas.yview_scroll(1, "units")

    def _configure_canvas(self, event):
        """Cấu hình kích thước canvas khi frame bên trong thay đổi"""
        self.thumbnails_canvas.configure(scrollregion=self.thumbnails_canvas.bbox("all"))

    def _clean_thumbnails(self):
        """Xóa tất cả ảnh thumbnail trong thư mục"""
        try:
            count = 0
            screenshot_dir = Path(self.path_entry.get())
            if not screenshot_dir.exists():
                messagebox.showinfo("Thông báo", "Thư mục không tồn tại")
                return

            # Tìm tất cả file thumbnail
            for f in screenshot_dir.glob("*_thumb*"):
                if f.is_file():
                    try:
                        f.unlink()  # Xóa file
                        count += 1
                    except Exception as e:
                        print(f"Lỗi xóa file {f}: {e}")

            # Hiển thị kết quả
            if count > 0:
                messagebox.showinfo("Thành công", f"Đã xóa {count} file thumbnail")
                # Tải lại danh sách ảnh
                self._load_recent_screenshots()
            else:
                messagebox.showinfo("Thông báo", "Không tìm thấy file thumbnail nào")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể dọn dẹp thumbnail: {e}")

    def _is_thumbnail(self, filepath):
        """Kiểm tra xem file có phải là thumbnail không"""
        # Kiểm tra tên file
        if "_thumb" in filepath.stem:
            return True

        # Kiểm tra kích thước ảnh (tùy chọn)
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                # Nếu kích thước đúng với thumbnail thì trả về True
                if width == 200 and height in range(100, 150):  # Phạm vi để linh hoạt
                    return True
        except:
            pass

        return False

    def _filter_thumbnails(self, files):
        """Lọc bỏ các file thumbnail khỏi danh sách"""
        return [f for f in files if not self._is_thumbnail(f)]

    def _load_recent_screenshots(self):
        """Tải và hiển thị các ảnh chụp gần đây dưới dạng thumbnails có thể cuộn"""
        if self._loading:
            return

        self._loading = True
        self.loading_label.config(text="Đang tải...")

        try:
            # Xóa tất cả thumbnails hiện tại
            for frame in self.thumbnail_frames:
                frame.destroy()
            self.thumbnail_frames = []
            self.thumbnail_images = []

            # Lấy đường dẫn thư mục
            screenshot_dir = Path(self.path_entry.get())
            if not screenshot_dir.exists():
                self._loading = False
                self.loading_label.config(text="")
                return

            # Lọc các file hình ảnh
            image_extensions = ['.png', '.jpg', '.jpeg']
            if self.encrypt_var.get():
                image_extensions.extend(['.png.enc', '.jpg.enc', '.jpeg.enc'])

            image_files = [f for f in screenshot_dir.iterdir()
                           if f.is_file() and any(f.name.lower().endswith(ext) for ext in image_extensions)]

            # Lọc bỏ thumbnails
            image_files = self._filter_thumbnails(image_files)

            # Sắp xếp theo thời gian sửa đổi (mới nhất trước)
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Lấy nhiều ảnh gần đây hơn
            recent_files = image_files[:self.max_thumbnails]  # Tăng số lượng ảnh hiển thị

            # Cập nhật số lượng ảnh
            self.status_label.config(text=f"{len(recent_files)} ảnh" if recent_files else "Không có ảnh")

            if not recent_files:
                # Nếu không có ảnh, hiển thị thông báo
                message_frame = ttk.Frame(self.thumbnail_grid)
                message_frame.grid(row=0, column=0, padx=5, pady=5)
                ttk.Label(message_frame, text="Chưa có ảnh chụp nào").pack(padx=10, pady=10)
                self.thumbnail_frames.append(message_frame)
                self._loading = False
                self.loading_label.config(text="")
                return

            # Xác định ảnh mới nhất
            latest_image_path = str(recent_files[0])
            # Lưu vào biến để sử dụng
            self.last_screenshot_path = latest_image_path

            # Cập nhật xem trước ảnh mới nhất
            self._update_preview(latest_image_path)

            # Hiển thị thumbnails theo lưới (4 ảnh mỗi hàng)
            items_per_row = 4
            for i, image_path in enumerate(recent_files):
                row = i // items_per_row
                col = i % items_per_row

                # Tạo frame cho thumbnail
                thumb_frame = ttk.Frame(self.thumbnail_grid, width=self.thumbnail_size[0] + 10,
                                        height=self.thumbnail_size[1] + 30, relief=tk.GROOVE, borderwidth=1)
                thumb_frame.grid(row=row, column=col, padx=5, pady=5)
                thumb_frame.grid_propagate(False)  # Giữ kích thước cố định

                # Thêm vào danh sách frame để theo dõi
                self.thumbnail_frames.append(thumb_frame)

                try:
                    # Tạo thumbnail với chất lượng cao hơn
                    if self.encrypt_var.get() and str(image_path).endswith('.enc'):
                        # Xử lý đọc ảnh đã mã hóa - cần giải mã
                        if self.encryption_key:
                            with open(image_path, "rb") as f:
                                encrypted_data = f.read()
                            fernet = Fernet(self.encryption_key)
                            decrypted_data = fernet.decrypt(encrypted_data)
                            img = Image.open(io.BytesIO(decrypted_data))
                        else:
                            # Không có khóa, không thể hiển thị
                            img = Image.new('RGB', self.thumbnail_size, color='gray')
                    else:
                        img = Image.open(image_path)

                    img.thumbnail(self.thumbnail_size, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    # Giữ tham chiếu để tránh bị GC
                    self.thumbnail_images.append(photo)

                    # Tạo label hiển thị ảnh
                    thumb_label = ttk.Label(thumb_frame, image=photo)
                    thumb_label.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

                    # Thêm thời gian chụp
                    mtime = datetime.fromtimestamp(image_path.stat().st_mtime)
                    time_str = mtime.strftime("%H:%M:%S")
                    time_label = ttk.Label(thumb_frame, text=time_str, font=("Arial", 8),
                                           background="#000000", foreground="#FFFFFF")
                    time_label.place(x=0, y=0, relwidth=1)

                    # Thêm viền đặc biệt cho ảnh hiện tại
                    filepath_str = str(image_path)
                    if filepath_str == self.last_screenshot_path:
                        thumb_frame.configure(relief=tk.RAISED, borderwidth=3)
                        # Dùng màu khác để đánh dấu ảnh hiện tại
                        highlight_label = ttk.Label(thumb_frame, text="Hiện tại",
                                                    background="#FF5722", foreground="white",
                                                    font=("Arial", 7, "bold"))
                        highlight_label.place(x=0, y=self.thumbnail_size[1] + 5, relwidth=1, height=15)

                    # Định nghĩa sự kiện click và hover
                    thumb_label.bind("<Button-1>", lambda e, path=filepath_str: self._update_preview(path))
                    thumb_label.bind("<Double-1>", lambda e, path=filepath_str: self._show_fullscreen_thumbnail(path))
                    thumb_label.bind("<Enter>", lambda e, path=filepath_str: self._show_hover_preview(e, path))
                    thumb_label.bind("<Leave>", self._hide_hover_preview)
                    thumb_frame.bind("<Enter>", lambda e, path=filepath_str: self._show_hover_preview(e, path))
                    thumb_frame.bind("<Leave>", self._hide_hover_preview)

                except Exception as e:
                    print(f"[_load_thumbnails] Lỗi tạo thumbnail {image_path}: {e}")
                    ttk.Label(thumb_frame, text="Lỗi ảnh").pack(padx=5, pady=5)

            # Cấu hình lại canvas sau khi thêm tất cả thumbnails
            self.thumbnail_grid.update_idletasks()
            self.thumbnails_canvas.configure(scrollregion=self.thumbnails_canvas.bbox("all"))

            # Cuộn đến ảnh hiện tại (vị trí ở giữa khung)
            self.after(100, self._scroll_to_current_image)

        except Exception as e:
            print(f"[_load_recent_screenshots] Lỗi: {e}")

        finally:
            self._loading = False
            self.loading_label.config(text="")

    def _show_fullscreen_thumbnail(self, image_path):
        """Hiển thị ảnh toàn màn hình khi double-click vào thumbnail"""
        # Đóng cửa sổ toàn màn hình cũ nếu có
        if self.fullscreen_viewer and self.fullscreen_viewer.winfo_exists():
            self.fullscreen_viewer.destroy()

        # Tạo cửa sổ toàn màn hình mới
        self.fullscreen_viewer = FullScreenImageViewer(
            self,
            image_path,
            self.encryption_key,
            self.encrypt_var.get()
        )

    def _scroll_to_current_image(self):
        """Cuộn đến ảnh hiện tại để hiển thị ở đầu danh sách"""
        try:
            # Tìm vị trí của ảnh hiện tại
            current_index = -1
            for i, frame in enumerate(self.thumbnail_frames):
                if frame.cget("relief") == tk.RAISED:  # Ảnh hiện tại có relief=RAISED
                    current_index = i
                    break

            if current_index == -1 and self.thumbnail_frames:
                current_index = 0  # Mặc định là ảnh đầu tiên

            if current_index >= 0 and self.thumbnail_frames:
                items_per_row = 4
                row = current_index // items_per_row

                # Tính vị trí cuộn để ảnh hiện tại hiển thị ở đầu
                bbox = self.thumbnails_canvas.bbox("all")
                if bbox:
                    canvas_height = self.thumbnails_canvas.winfo_height()
                    content_height = bbox[3] - bbox[1]

                    # Ước tính vị trí của hàng hiện tại
                    row_height = content_height / (len(self.thumbnail_frames) // items_per_row + 1)
                    y_position = row * row_height

                    # Tính tỷ lệ cuộn (0-1)
                    if content_height > canvas_height:
                        scroll_pos = y_position / (content_height - canvas_height)
                        scroll_pos = max(0, min(1, scroll_pos))

                        # Cuộn đến vị trí
                        self.thumbnails_canvas.yview_moveto(scroll_pos)

        except Exception as e:
            print(f"[_scroll_to_current_image] Lỗi: {e}")

    def _show_hover_preview(self, event, image_path):
        """Hiển thị ảnh xem trước khi hover chuột trên thumbnail"""
        try:
            # Đọc ảnh gốc
            if self.encrypt_var.get() and str(image_path).endswith('.enc'):
                # Xử lý đọc ảnh đã mã hóa - cần giải mã
                if self.encryption_key:
                    with open(image_path, "rb") as f:
                        encrypted_data = f.read()
                    fernet = Fernet(self.encryption_key)
                    decrypted_data = fernet.decrypt(encrypted_data)
                    img = Image.open(io.BytesIO(decrypted_data))
                else:
                    # Không có khóa, không thể hiển thị
                    img = Image.new('RGB', (400, 300), color='gray')
            else:
                img = Image.open(image_path)

            # Kích thước tối đa cho tooltip
            max_width, max_height = 400, 300

            # Tính toán tỉ lệ để giữ nguyên tỉ lệ khung hình
            img_w, img_h = img.size
            ratio = min(max_width / img_w, max_height / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))

            # Resize ảnh với chất lượng cao
            img_resized = img.resize(new_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)

            # Cập nhật tooltip
            self.tooltip_label.config(image=photo)
            self.hover_image = photo  # Giữ tham chiếu

            # Tính vị trí hiển thị tooltip
            x = event.x_root + 15
            y = event.y_root + 10

            # Hiển thị tooltip
            self.tooltip_frame.place(x=x, y=y)

            # Thêm tooltip hướng dẫn
            self.help_tooltip_label.config(text="Double-click để xem ảnh toàn màn hình")
            self.help_tooltip_frame.place(x=x, y=y + new_size[1] + 10)

        except Exception as e:
            print(f"[_show_hover_preview] Lỗi: {e}")

    def _hide_hover_preview(self, event):
        """Ẩn ảnh xem trước khi chuột rời khỏi thumbnail"""
        self.tooltip_frame.place_forget()
        self.help_tooltip_frame.place_forget()

    def _browse_dir(self):
        """Mở hộp thoại chọn thư mục lưu"""
        dir_path = filedialog.askdirectory(initialdir=self.path_entry.get())
        if dir_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, dir_path)
            # Tải lại danh sách ảnh từ thư mục mới
            self._load_recent_screenshots()

    def _select_custom_region(self):
        """Mở công cụ chọn vùng tùy chỉnh"""
        # Đây là vị trí để mở công cụ chọn vùng
        # Có thể triển khai sau hoặc hiển thị thông báo
        messagebox.showinfo("Tính năng đang phát triển",
                            "Công cụ chọn vùng tùy chỉnh đang được phát triển.\n\n"
                            "Hiện tại bạn có thể chọn toàn màn hình hoặc một màn hình cụ thể.")

    def _toggle_upload_fields(self):
        """Hiển thị/ẩn trường cấu hình upload"""
        if self.upload_var.get():
            self.upload_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.upload_frame.pack_forget()

    def _get_region_from_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """Lấy tọa độ vùng chụp từ lựa chọn"""
        selection = self.region_var.get()

        if selection == "Toàn màn hình":
            return None

        # Xử lý trường hợp "Màn hình X"
        try:
            parts = selection.split()
            if len(parts) == 2 and parts[0] == "Màn hình":
                screen_id = int(parts[1])
                for screen in self.screens:
                    if screen["id"] == screen_id:
                        return screen["bounds"]
        except:
            pass

        # Mặc định là toàn màn hình
        return None

    def _toggle_capturer(self):
        """Bắt đầu/dừng chụp màn hình"""
        if not self.is_active:
            # Bắt đầu chụp
            try:
                # Lấy thông tin cấu hình
                save_dir = self.path_entry.get()
                interval = self.interval_var.get()
                region = self._get_region_from_selection()
                img_format = self.format_var.get()
                quality = self.quality_var.get()
                encrypt = self.encrypt_var.get()

                # Nâng cao
                change_detection = self.change_detect_var.get()
                sensitivity = self.sensitivity_var.get()
                retention_days = self.retention_var.get()
                max_storage = self.storage_var.get()
                create_thumbnails = self.create_thumb_var.get()

                # Upload
                remote_upload = self.upload_var.get()
                remote_endpoint = self.endpoint_var.get() if remote_upload else None
                remote_token = self.token_var.get() if remote_upload else None

                # Mã hóa
                if encrypt and not self.encryption_key:
                    self.encryption_key = Fernet.generate_key()

                # Tạo đối tượng capturer
                self.capturer = ScreenshotCapturer(
                    save_directory=save_dir,
                    interval=interval,
                    region=region,
                    image_format=img_format,
                    quality=quality,
                    encrypt=encrypt,
                    encryption_key=self.encryption_key,
                    retention_days=retention_days,
                    max_storage_mb=max_storage,
                    change_detection=change_detection,
                    change_sensitivity=sensitivity,
                    log_to_stdout=True,
                    remote_upload=remote_upload,
                    remote_endpoint=remote_endpoint,
                    remote_token=remote_token,
                    add_metadata=True,
                    create_thumbnails=create_thumbnails,  # Chuyển tham số này nếu ScreenshotCapturer hỗ trợ
                )

                # Đăng ký callback để cập nhật xem trước
                self.capturer.register_callback(self._screenshot_callback)

                # Bắt đầu
                if self.capturer.start():
                    self.is_active = True
                    self.start_button.config(text="Dừng chụp", style="danger.TButton")
                    self.pause_button.config(state=tk.NORMAL)

                    # Cập nhật lại lịch làm mới với khoảng thời gian mới
                    self._interval_changed()

                    messagebox.showinfo("Chụp màn hình",
                                        f"Đã bắt đầu chụp màn hình mỗi {interval} giây\n"
                                        f"Ảnh sẽ được lưu tại: {save_dir}")
                else:
                    messagebox.showerror("Lỗi", "Không thể bắt đầu chụp màn hình")

            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể bắt đầu chụp màn hình: {str(e)}")

        else:
            # Dừng chụp
            if self.capturer:
                self.capturer.stop()
                self.is_active = False
                self.start_button.config(text="Bắt đầu chụp", style="success.TButton")
                self.pause_button.config(text="Tạm dừng", state=tk.DISABLED)

                messagebox.showinfo("Chụp màn hình", "Đã dừng chụp màn hình")

    def _toggle_pause(self):
        """Tạm dừng/tiếp tục chụp"""
        if self.capturer and self.is_active:
            if self.pause_button.cget("text") == "Tạm dừng":
                # Tạm dừng
                if self.capturer.pause():
                    self.pause_button.config(text="Tiếp tục")

                    # Dừng tự động cập nhật khi tạm dừng chụp
                    if hasattr(self, '_refresh_job') and self._refresh_job:
                        self.after_cancel(self._refresh_job)
            else:
                # Tiếp tục
                if self.capturer.resume():
                    self.pause_button.config(text="Tạm dừng")

                    # Khởi động lại tự động cập nhật
                    self._interval_changed()

    def _capture_now(self):
        """Chụp ngay lập tức một ảnh"""
        try:
            # Nếu đang hoạt động, sử dụng capturer hiện tại
            if self.is_active and self.capturer:
                result = self.capturer.capture_once()
                if result and "filepath" in result:
                    self.last_screenshot_path = result["filepath"]
                    self._update_preview(self.last_screenshot_path)
                    # Tải lại danh sách thumbnails để hiển thị ảnh mới
                    self._load_recent_screenshots()
                    messagebox.showinfo("Thông báo", "Đã chụp một ảnh mới")
                return

            # Nếu không hoạt động, tạo một capturer tạm thời
            save_dir = self.path_entry.get()
            region = self._get_region_from_selection()
            img_format = self.format_var.get()
            quality = self.quality_var.get()
            encrypt = self.encrypt_var.get()
            create_thumbnails = self.create_thumb_var.get()

            # Tạo thư mục nếu chưa tồn tại
            Path(save_dir).mkdir(parents=True, exist_ok=True)

            # Mã hóa
            encryption_key = None
            if encrypt:
                if self.encryption_key:
                    encryption_key = self.encryption_key
                else:
                    self.encryption_key = Fernet.generate_key()
                    encryption_key = self.encryption_key

            temp_capturer = ScreenshotCapturer(
                save_directory=save_dir,
                interval=60,  # Không quan trọng
                region=region,
                image_format=img_format,
                quality=quality,
                encrypt=encrypt,
                encryption_key=encryption_key,
                add_metadata=True,
                create_thumbnails=create_thumbnails,  # Thêm tham số này
            )

            result = temp_capturer.capture_once()
            if result and "filepath" in result:
                self.last_screenshot_path = result["filepath"]
                self._update_preview(self.last_screenshot_path)
                # Tải lại danh sách thumbnails
                self._load_recent_screenshots()
                messagebox.showinfo("Thông báo", "Đã chụp một ảnh mới")

            # Xóa capturer tạm thời
            del temp_capturer

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chụp ảnh: {str(e)}")

    def _screenshot_callback(self, metadata: Dict):
        """Được gọi từ thread background – chỉ schedule cập nhật lên main thread."""
        filepath = metadata.get("filepath")
        if not filepath:
            return

        # Kiểm tra xem file có phải là thumbnail không
        if self._is_thumbnail(Path(filepath)):
            return

        # Lưu đường dẫn ảnh mới nhất
        self.last_screenshot_path = filepath
        # Đưa việc cập nhật preview về main thread
        self.after(0, lambda: self._update_preview(filepath))
        # Cập nhật lại danh sách thumbnails
        self.after(100, self._load_recent_screenshots)

    def _update_preview(self, image_path: Union[str, Path]):
        """Chạy trên main thread, an toàn với Tkinter. Hiển thị ảnh xem trước với chất lượng cao."""
        try:
            # Đặt lại preview_label
            self.preview_label.config(image="", text="Đang tải ảnh...")
            self.preview_label.image = None

            # Bắt buộc cập nhật giao diện
            self.preview_label.update_idletasks()

            # Kiểm tra nếu path là thumbnail, nếu có thì tìm ảnh gốc
            image_path_obj = Path(image_path)
            if self._is_thumbnail(image_path_obj):
                # Tìm file gốc (không có _thumb trong tên)
                original_stem = image_path_obj.stem.replace("_thumb", "")
                parent_dir = image_path_obj.parent

                # Tìm tất cả các file có thể là ảnh gốc
                potential_originals = list(parent_dir.glob(f"{original_stem}.*"))
                if potential_originals:
                    # Lọc bỏ các thumbnail khác
                    potential_originals = [f for f in potential_originals if not self._is_thumbnail(f)]
                    if potential_originals:
                        image_path = str(potential_originals[0])

            # Lấy kích thước container thực tế
            w = self.main_preview_frame.winfo_width()
            h = self.main_preview_frame.winfo_height()

            # Nếu container chưa có kích thước, sử dụng kích thước mặc định
            if w < 50 or h < 50:
                w, h = 400, 300

            # Đọc ảnh dựa vào loại file (mã hóa hoặc không)
            if self.encrypt_var.get() and str(image_path).endswith('.enc'):
                # Xử lý đọc ảnh đã mã hóa - cần giải mã
                if self.encryption_key:
                    with open(image_path, "rb") as f:
                        encrypted_data = f.read()
                    fernet = Fernet(self.encryption_key)
                    decrypted_data = fernet.decrypt(encrypted_data)
                    img = Image.open(io.BytesIO(decrypted_data))
                else:
                    # Không có khóa, không thể hiển thị
                    img = Image.new('RGB', (w, h), color='gray')
                    self.preview_label.config(text="Ảnh được mã hóa\nKhông có khóa giải mã")
                    return
            else:
                img = Image.open(image_path)

            # Kích thước gốc để hiển thị trong tiêu đề
            orig_w, orig_h = img.size

            # Tính toán tỉ lệ để giữ nguyên tỉ lệ khung hình
            # Đảm bảo ảnh vừa với container
            ratio = min(w / orig_w, h / orig_h)
            new_size = (int(orig_w * ratio * 0.95), int(orig_h * ratio * 0.95))  # Giảm 5% để có padding

            # Resize ảnh với phương pháp LANCZOS cho chất lượng cao nhất
            img_resized = img.resize(new_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)

            # Cập nhật ảnh lên label
            self.preview_label.config(image=photo, text="")

            # Giữ tham chiếu để tránh bị GC
            self.preview_label.image = photo

            # Hiển thị thêm thông tin về ảnh
            file_info = Path(image_path).stat()
            file_size_kb = file_info.st_size / 1024
            file_time = datetime.fromtimestamp(file_info.st_mtime).strftime('%d/%m/%Y %H:%M:%S')

            # Cập nhật tiêu đề frame với thông tin về ảnh
            self.main_preview_frame.config(text=f"Ảnh hiện tại ({orig_w}x{orig_h}, {file_size_kb:.1f}KB, {file_time})")

        except Exception as e:
            print(f"[_update_preview] Lỗi: {e}")
            # Nếu lỗi, hiển thị thông báo
            self.preview_label.config(image="", text=f"Không thể hiển thị ảnh\n{str(e)}")
            self.preview_label.image = None

    def _open_screenshots_viewer(self):
        """Mở trình xem ảnh đã chụp"""
        # Đây có thể là một cửa sổ mới hoặc chuyển sang tab khác
        try:
            # Kiểm tra thư mục có ảnh không
            save_dir = self.path_entry.get()
            screenshots_path = Path(save_dir)

            if not screenshots_path.exists() or not any(screenshots_path.iterdir()):
                messagebox.showinfo("Thông báo", "Chưa có ảnh chụp nào trong thư mục")
                return

            # Mở thư mục chứa ảnh
            if os.name == 'nt':  # Windows
                os.startfile(save_dir)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, save_dir])
            else:
                messagebox.showinfo("Thông báo", f"Thư mục ảnh: {save_dir}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục ảnh: {str(e)}")

    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        if self.capturer and self.is_active:
            self.capturer.stop()

        # Hủy bỏ lịch cập nhật định kỳ
        if hasattr(self, '_refresh_job') and self._refresh_job:
            self.after_cancel(self._refresh_job)

        # Đóng bất kỳ cửa sổ xem ảnh toàn màn hình nào đang mở
        if self.fullscreen_viewer and self.fullscreen_viewer.winfo_exists():
            self.fullscreen_viewer.destroy()

    def get_frame(self):
        """Trả về frame để thêm vào notebook"""
        return self