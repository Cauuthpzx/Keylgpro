#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa ManagementFrame - Giao diện quản lý thiết bị
"""

import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable, Dict, List, Any, Union

from gui.resources import UIResources

logger = logging.getLogger("keylogger.gui.management_frame")

class ManagementFrame:
    """Frame giao diện cho chức năng quản lý thiết bị."""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """Khởi tạo frame quản lý thiết bị.
        
        Args:
            parent: Widget cha để chứa frame này
            callback: Hàm callback khi trạng thái thay đổi (tùy chọn)
        """
        self.parent = parent
        self.callback = callback
        self.selected_target_id = None
        
        # Biến tkinter
        self.target_search_var = tk.StringVar()
        
        # Biến dữ liệu
        self.grid_rows = []
        self.grid_current_row = 1  # Hàng tiếp theo để thêm dữ liệu
        
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
            title_frame, text="QUẢN LÝ THIẾT BỊ THEO DÕI", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Tạo frame phía trên
        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Nút làm mới
        refresh_icon = UIResources.get_icon_image("refresh")
        refresh_btn = ttk.Button(
            top_frame,
            text="Làm mới danh sách",
            image=refresh_icon,
            compound=tk.LEFT,
            command=self.refresh_targets,
        )
        refresh_btn.image = refresh_icon
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Thanh tìm kiếm thiết bị
        ttk.Label(top_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        search_icon = UIResources.get_icon_image("search", size=(16, 16))
        target_search_entry = ttk.Entry(
            top_frame, textvariable=self.target_search_var, width=20
        )
        target_search_entry.pack(side=tk.LEFT, padx=5)
        target_search_entry.bind("<KeyRelease>", self.search_targets)
        
        # Tạo frame danh sách thiết bị
        list_frame = ttk.LabelFrame(self.frame, text="Danh sách thiết bị")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Container cho grid
        grid_container = ttk.Frame(list_frame)
        grid_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Định nghĩa các cột
        self.grid_columns = [
            {"name": "id", "text": "ID", "width": 5},
            {"name": "device_name", "text": "Tên thiết bị", "width": 25},
            {"name": "username", "text": "Người dùng", "width": 20},
            {"name": "ip_address", "text": "Địa chỉ IP", "width": 15},
            {"name": "last_seen", "text": "Lần cuối hoạt động", "width": 25}
        ]
        
        # Tạo khung cuộn
        canvas = tk.Canvas(grid_container, borderwidth=0)
        scrollbar_v = ttk.Scrollbar(grid_container, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(grid_container, orient="horizontal", command=canvas.xview)
        self.grid_frame = ttk.Frame(canvas)
        
        # Cấu hình canvas
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Sắp xếp các thành phần
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=self.grid_frame, anchor="nw", tags="grid_frame")
        
        # Thiết lập sự kiện cập nhật kích thước
        self.grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("grid_frame", width=e.width))
        
        # Tạo tiêu đề cột
        for i, col in enumerate(self.grid_columns):
            header = ttk.Label(self.grid_frame, text=col["text"], relief=tk.RIDGE,
                             borderwidth=1, anchor=tk.CENTER, background="#e0e0e0",
                             font=("Arial", 10, "bold"),
                             width=col["width"])
            header.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            self.grid_frame.grid_columnconfigure(i, weight=1)
        
        # Frame hiển thị thông tin chi tiết
        detail_frame = ttk.LabelFrame(self.frame, text="Chi tiết thiết bị")
        detail_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        detail_frame.grid_columnconfigure(0, weight=1)
        
        # Textbox hiển thị chi tiết với thanh cuộn
        self.detail_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=8
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tạo frame cho các nút tương tác
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        
        # Nút tương tác
        view_icon = UIResources.get_icon_image("view")
        view_btn = ttk.Button(
            btn_frame,
            text="Xem dữ liệu",
            image=view_icon,
            compound=tk.LEFT,
            command=self.view_target_data,
        )
        view_btn.image = view_icon
        view_btn.pack(side=tk.LEFT, padx=5)
        
        delete_icon = UIResources.get_icon_image("delete")
        delete_btn = ttk.Button(
            btn_frame,
            text="Xóa thiết bị",
            image=delete_icon,
            compound=tk.LEFT,
            command=self.delete_target,
        )
        delete_btn.image = delete_icon
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        export_icon = UIResources.get_icon_image("export")
        export_btn = ttk.Button(
            btn_frame,
            text="Xuất dữ liệu",
            image=export_icon,
            compound=tk.LEFT,
            command=self.export_target_data,
        )
        export_btn.image = export_icon
        export_btn.pack(side=tk.LEFT, padx=5)
    
    def refresh_targets(self):
        """Làm mới danh sách thiết bị từ database.
        
        Phương thức này sẽ gọi callback để lấy dữ liệu từ ứng dụng chính.
        """
        if self.callback:
            self.callback({"action": "get_targets", "callback": self.update_grid})
    
    def update_grid(self, targets: List[Dict[str, Any]]):
        """Cập nhật danh sách thiết bị với dữ liệu mới.
        
        Args:
            targets: Danh sách thông tin thiết bị
        """
        # Xóa dữ liệu cũ
        for widget in self.grid_frame.winfo_children():
            if int(widget.grid_info()["row"]) > 0:  # Bỏ qua hàng tiêu đề
                widget.destroy()
        
        # Reset hàng hiện tại
        self.grid_current_row = 1
        
        # Biến để lưu trữ các widget
        self.grid_rows = []
        
        # Thêm vào grid
        for target in targets:
            row_widgets = []
            row_frame = ttk.Frame(self.grid_frame)
            row_frame.grid(row=self.grid_current_row, column=0, columnspan=len(self.grid_columns), sticky="ew")
            
            # Tạo background màu xám nhạt cho hàng chẵn
            bg_color = "#f0f0f0" if self.grid_current_row % 2 == 0 else "white"
            
            for i, col in enumerate(self.grid_columns):
                # Lấy giá trị tương ứng với cột
                key = col["name"]
                value = str(target[key])
                
                # Tạo label cho ô dữ liệu
                cell = ttk.Label(
                    self.grid_frame,
                    text=value,
                    relief=tk.RIDGE,
                    borderwidth=1,
                    anchor=tk.CENTER,
                    background=bg_color,
                    width=col["width"]
                )
                
                cell.grid(row=self.grid_current_row, column=i, sticky="nsew", padx=1, pady=1)
                row_widgets.append(cell)
                
                # Đăng ký sự kiện click
                cell.bind("<Button-1>", lambda e, t_id=target["id"]: self.on_target_click(t_id))
            
            # Lưu trữ hàng hiện tại
            self.grid_rows.append({"id": target["id"], "widgets": row_widgets})
            self.grid_current_row += 1
    
    def on_target_click(self, target_id):
        """Xử lý khi click vào một hàng trong grid.
        
        Args:
            target_id: ID của thiết bị được chọn
        """
        # Lưu ID đã chọn
        self.selected_target_id = target_id
        
        # Highlight hàng được chọn
        for row in self.grid_rows:
            for widget in row["widgets"]:
                if row["id"] == target_id:
                    widget.configure(background="#e0f0ff")  # Màu highlight
                else:
                    # Khôi phục màu nền mặc định
                    row_index = self.grid_rows.index(row) + 1  # +1 vì hàng đầu tiên là tiêu đề
                    bg_color = "#f0f0f0" if row_index % 2 == 0 else "white"
                    widget.configure(background=bg_color)
        
        # Hiển thị thông tin chi tiết
        if self.callback:
            self.callback({
                "action": "get_target_details", 
                "target_id": target_id,
                "callback": self.display_target_details
            })
    
    def display_target_details(self, target: Dict[str, Any]):
        """Hiển thị thông tin chi tiết của thiết bị.
        
        Args:
            target: Thông tin chi tiết về thiết bị
        """
        if not target:
            return
            
        # Hiển thị thông tin chi tiết
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, f"ID: {target['id']}\n")
        self.detail_text.insert(
            tk.END, f"Tên thiết bị: {target['device_name']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Người dùng: {target['username']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Địa chỉ IP: {target['ip_address']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Địa chỉ MAC: {target['mac_address']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Hệ điều hành: {target['os_info']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Lần đầu kết nối: {target['first_seen']}\n"
        )
        self.detail_text.insert(
            tk.END, f"Lần cuối hoạt động: {target['last_seen']}\n"
        )
    
    def search_targets(self, event=None):
        """Tìm kiếm trong danh sách thiết bị.
        
        Args:
            event: Sự kiện kích hoạt tìm kiếm (tùy chọn)
        """
        search_text = self.target_search_var.get().lower()
        
        # Nếu không có từ khóa tìm kiếm, hiển thị tất cả
        if not search_text:
            for row in self.grid_rows:
                for i, widget in enumerate(row["widgets"]):
                    row_index = self.grid_rows.index(row) + 1
                    # Khôi phục màu nền mặc định trừ hàng đang được chọn
                    if row["id"] == self.selected_target_id:
                        widget.configure(background="#e0f0ff")  # Màu highlight
                    else:
                        bg_color = "#f0f0f0" if row_index % 2 == 0 else "white"
                        widget.configure(background=bg_color)
            return
        
        # Tìm kiếm và highlight kết quả
        for row in self.grid_rows:
            # Tạo text từ tất cả giá trị trong hàng
            row_text = " ".join([widget.cget("text").lower() for widget in row["widgets"]])
            
            if search_text in row_text:
                # Highlight các widget trong hàng phù hợp
                for widget in row["widgets"]:
                    if row["id"] == self.selected_target_id:
                        widget.configure(background="#e0f0ff")  # Giữ màu highlight cho hàng đang chọn
                    else:
                        widget.configure(background="#e0f7e0")  # Màu highlight tìm kiếm
            else:
                # Thiết lập màu bình thường cho các widget không phù hợp
                row_index = self.grid_rows.index(row) + 1
                for widget in row["widgets"]:
                    if row["id"] == self.selected_target_id:
                        widget.configure(background="#e0f0ff")  # Giữ màu highlight cho hàng đang chọn
                    else:
                        bg_color = "#f0f0f0" if row_index % 2 == 0 else "white"
                        widget.configure(background=bg_color)
    
    def view_target_data(self):
        """Xem dữ liệu chi tiết của thiết bị được chọn."""
        if not self.selected_target_id:
            messagebox.showinfo(
                "Thông báo", "Vui lòng chọn một thiết bị để xem dữ liệu"
            )
            return
        
        if self.callback:
            self.callback({
                "action": "view_target_data",
                "target_id": self.selected_target_id
            })
    
    def delete_target(self):
        """Xóa thiết bị và dữ liệu liên quan."""
        if not self.selected_target_id:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một thiết bị để xóa")
            return
        
        # Tìm thông tin tên thiết bị
        target_name = ""
        for row in self.grid_rows:
            if row["id"] == self.selected_target_id:
                target_name = row["widgets"][1].cget("text")  # Lấy tên thiết bị từ cột thứ 2
                break
        
        # Xác nhận trước khi xóa
        confirm = messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc chắn muốn xóa thiết bị '{target_name}' và tất cả dữ liệu liên quan?",
        )
        if not confirm:
            return
        
        if self.callback:
            self.callback({
                "action": "delete_target",
                "target_id": self.selected_target_id,
                "callback": self.on_target_deleted
            })
    
    def on_target_deleted(self, success: bool, message: str):
        """Xử lý sau khi xóa thiết bị.
        
        Args:
            success: True nếu xóa thành công, False nếu thất bại
            message: Thông báo kết quả
        """
        if success:
            # Cập nhật lại danh sách
            self.refresh_targets()
            
            # Xóa thông tin chi tiết
            self.detail_text.delete(1.0, tk.END)
            self.selected_target_id = None
            
            messagebox.showinfo("Thành công", message)
        else:
            messagebox.showerror("Lỗi", message)
    
    def export_target_data(self, target_id: Optional[int] = None):
        """Xuất dữ liệu của thiết bị ra file.
        
        Args:
            target_id: ID của thiết bị cần xuất dữ liệu (tùy chọn)
        """
        # Nếu không có target_id được truyền vào, lấy từ selected_target_id
        if target_id is None:
            if not self.selected_target_id:
                messagebox.showinfo(
                    "Thông báo", "Vui lòng chọn một thiết bị để xuất dữ liệu"
                )
                return
            target_id = self.selected_target_id
        
        # Lấy thông tin thiết bị
        if self.callback:
            self.callback({
                "action": "get_target_details", 
                "target_id": target_id,
                "callback": self.show_export_dialog
            })
    
    def show_export_dialog(self, target: Dict[str, Any]):
        """Hiển thị hộp thoại lưu file xuất dữ liệu.
        
        Args:
            target: Thông tin chi tiết về thiết bị
        """
        if not target:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin thiết bị")
            return
        
        # Hỏi người dùng nơi lưu file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"keylog_{target['device_name']}.txt",
        )
        
        if not file_path:
            return
        
        if self.callback:
            self.callback({
                "action": "export_target_data", 
                "target_id": target["id"],
                "file_path": file_path,
                "callback": self.on_export_complete
            })
    
    def on_export_complete(self, success: bool, message: str, file_path: Optional[str] = None):
        """Xử lý sau khi xuất dữ liệu.
        
        Args:
            success: True nếu xuất thành công, False nếu thất bại
            message: Thông báo kết quả
            file_path: Đường dẫn file xuất (chỉ khi success=True)
        """
        if success:
            result = messagebox.askyesno(
                "Thành công", f"{message}\n\nBạn có muốn mở file không?"
            )
            if result and file_path:
                if self.callback:
                    self.callback({
                        "action": "open_file",
                        "file_path": file_path
                    })
        else:
            messagebox.showerror("Lỗi", message)
    
    def get_frame(self):
        """Trả về frame chính để thêm vào container."""
        return self.frame