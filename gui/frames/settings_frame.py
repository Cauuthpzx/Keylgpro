#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa SettingsFrame - Giao diện cài đặt ứng dụng
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable, Dict, Any, Union

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.settings_frame")

class SettingsFrame:
    """Frame giao diện cho chức năng cài đặt ứng dụng."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame cài đặt ứng dụng.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        
        # Biến tkinter (sẽ được cập nhật từ config sau khi tạo widget)
        self.buffer_size_var = tk.IntVar(value=20)
        self.flush_interval_var = tk.DoubleVar(value=5.0)
        self.log_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), ".keylogger"))
        self.encrypt_log_var = tk.BooleanVar(value=False)
        self.delete_after_export_var = tk.BooleanVar(value=False)
        
        # Tạo giao diện
        self.create_widgets()
        
        # Tải cài đặt từ cấu hình
        if self.callback:
            self.callback({"action": "get_settings", "callback": self.update_settings})
    
    def create_widgets(self):
        """Tạo các thành phần giao diện người dùng."""
        # Frame chính
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Tiêu đề
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, text="CÀI ĐẶT ỨNG DỤNG", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame cài đặt chung
        general_frame = ttk.LabelFrame(self.frame, text="Cài đặt chung")
        general_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Kích thước buffer
        buffer_frame = ttk.Frame(general_frame)
        buffer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(buffer_frame, text="Kích thước buffer:").pack(side=tk.LEFT, padx=5)
        buffer_size_spinbox = ttk.Spinbox(
            buffer_frame, from_=1, to=100, textvariable=self.buffer_size_var, width=5
        )
        buffer_size_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(buffer_frame, text="keystroke").pack(side=tk.LEFT)
        
        # Thời gian flush buffer
        flush_frame = ttk.Frame(general_frame)
        flush_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(flush_frame, text="Thời gian flush buffer:").pack(
            side=tk.LEFT, padx=5
        )
        flush_interval_spinbox = ttk.Spinbox(
            flush_frame,
            from_=0.5,
            to=60.0,
            increment=0.5,
            textvariable=self.flush_interval_var,
            width=5,
        )
        flush_interval_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(flush_frame, text="giây").pack(side=tk.LEFT)
        
        # Thư mục lưu log
        log_dir_frame = ttk.Frame(general_frame)
        log_dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(log_dir_frame, text="Thư mục lưu log:").pack(side=tk.LEFT, padx=5)
        log_dir_entry = ttk.Entry(
            log_dir_frame, textvariable=self.log_dir_var, width=40
        )
        log_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_log_dir_btn = ttk.Button(
            log_dir_frame,
            text="Chọn",
            image=UIResources.get_icon_image("search"),
            compound=tk.LEFT,
            command=self.browse_log_dir,
        )
        browse_log_dir_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame cài đặt bảo mật
        security_frame = ttk.LabelFrame(self.frame, text="Bảo mật")
        security_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Mã hóa log
        encrypt_frame = ttk.Frame(security_frame)
        encrypt_frame.pack(fill=tk.X, padx=10, pady=10)
        
        encrypt_check = ttk.Checkbutton(
            encrypt_frame,
            text="Mã hóa file log khi xuất dữ liệu",
            variable=self.encrypt_log_var,
        )
        encrypt_check.pack(side=tk.LEFT, padx=5)
        
        # Xóa log sau khi gửi
        delete_frame = ttk.Frame(security_frame)
        delete_frame.pack(fill=tk.X, padx=10, pady=10)
        
        delete_check = ttk.Checkbutton(
            delete_frame,
            text="Xóa log sau khi xuất dữ liệu",
            variable=self.delete_after_export_var,
        )
        delete_check.pack(side=tk.LEFT, padx=5)
        
        # Frame cài đặt giao diện
        ui_frame = ttk.LabelFrame(self.frame, text="Giao diện")
        ui_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Nút chuyển đổi theme
        theme_frame = ttk.Frame(ui_frame)
        theme_frame.pack(fill=tk.X, padx=10, pady=10)
        
        theme_btn = ttk.Button(
            theme_frame,
            text="Chuyển đổi chủ đề Sáng/Tối",
            image=UIResources.get_icon_image("theme"),
            compound=tk.LEFT,
            command=self.toggle_theme,
        )
        theme_btn.pack(side=tk.LEFT, padx=5)
        
        # Mô tả chủ đề
        self.theme_desc = ttk.Label(
            theme_frame,
            text="Chủ đề hiện tại: Sáng"  # Mặc định ban đầu, sẽ được cập nhật
        )
        self.theme_desc.pack(side=tk.LEFT, padx=15)
        
        # Nút lưu cài đặt
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        
        save_icon = UIResources.get_icon_image("save")
        save_btn = ttk.Button(
            btn_frame,
            text="Lưu cài đặt",
            image=save_icon,
            compound=tk.LEFT,
            command=self.save_settings,
        )
        save_btn.image = save_icon
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        refresh_icon = UIResources.get_icon_image("refresh")
        load_btn = ttk.Button(
            btn_frame,
            text="Khôi phục mặc định",
            image=refresh_icon,
            compound=tk.LEFT,
            command=self.load_default_settings,
        )
        load_btn.image = refresh_icon
        load_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_log_dir(self):
        """Chọn thư mục lưu log."""
        directory = filedialog.askdirectory(initialdir=self.log_dir_var.get())
        if directory:
            self.log_dir_var.set(directory)
    
    def update_settings(self, settings: Dict[str, Any]):
        """Cập nhật giao diện với cài đặt từ cấu hình.
        
        Args:
            settings: Cài đặt ứng dụng
        """
        if "buffer_size" in settings:
            self.buffer_size_var.set(settings["buffer_size"])
        
        if "flush_interval" in settings:
            self.flush_interval_var.set(settings["flush_interval"])
        
        if "log_dir" in settings:
            self.log_dir_var.set(settings["log_dir"])
        
        if "encrypt_log" in settings:
            self.encrypt_log_var.set(settings["encrypt_log"])
        
        if "delete_after_export" in settings:
            self.delete_after_export_var.set(settings["delete_after_export"])
        
        if "theme" in settings:
            theme = settings["theme"]
            self.theme_desc.config(text=f"Chủ đề hiện tại: {'Tối' if theme == 'dark' else 'Sáng'}")
    
    def toggle_theme(self):
        """Chuyển đổi giữa chủ đề sáng và tối."""
        if self.callback:
            self.callback({"action": "toggle_theme"})
            
            # Cập nhật mô tả chủ đề (sẽ được cập nhật sau khi callback)
            if self.theme_desc.cget("text").endswith("Sáng"):
                self.theme_desc.config(text="Chủ đề hiện tại: Tối")
            else:
                self.theme_desc.config(text="Chủ đề hiện tại: Sáng")
    
    def save_settings(self):
        """Lưu cài đặt."""
        settings = {
            "buffer_size": self.buffer_size_var.get(),
            "flush_interval": self.flush_interval_var.get(),
            "log_dir": self.log_dir_var.get(),
            "encrypt_log": self.encrypt_log_var.get(),
            "delete_after_export": self.delete_after_export_var.get(),
        }
        
        if self.callback:
            self.callback({
                "action": "save_settings",
                "settings": settings,
                "callback": self.on_settings_saved
            })
    
    def on_settings_saved(self, success: bool, message: str):
        """Xử lý sau khi lưu cài đặt.
        
        Args:
            success: True nếu lưu thành công, False nếu thất bại
            message: Thông báo kết quả
        """
        if success:
            messagebox.showinfo("Thành công", message)
        else:
            messagebox.showerror("Lỗi", message)
    
    def load_default_settings(self):
        """Khôi phục cài đặt mặc định."""
        if self.callback:
            self.callback({
                "action": "load_default_settings",
                "callback": self.update_settings
            })
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame