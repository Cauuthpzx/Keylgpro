#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cấu hình chung cho ứng dụng Keylogger
"""

import os
import json
import logging
from pathlib import Path

# Thông tin ứng dụng
APP_NAME = "Keylogger Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Developer"

# Thư mục dữ liệu
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".keylogger")
DEFAULT_LOG_FILE = os.path.join(DEFAULT_DATA_DIR, "keystrokes.log")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "keylogger.db")

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    "buffer_size": 20,
    "flush_interval": 5.0,
    "log_dir": DEFAULT_DATA_DIR,
    "encrypt_log": False,
    "delete_after_export": False,
    "auto_start": False,
    "stealth_mode": True,
    "theme": "light"
}

class Config:
    """Quản lý cấu hình ứng dụng"""
    
    def __init__(self):
        """Khởi tạo đối tượng Config với cài đặt mặc định."""
        self.settings = DEFAULT_SETTINGS.copy()
        self.logger = logging.getLogger("keylogger.config")

        # Gán biến DB_PATH vào thuộc tính đối tượng để dùng bên ngoài
        self.DEFAULT_DB_PATH = DEFAULT_DB_PATH  # <<< ✅ CHÈN DÒNG NÀY Ở ĐÂY

        # Tạo thư mục dữ liệu nếu chưa tồn tại
        os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
        
        # Đường dẫn file cấu hình
        self.config_file = os.path.join(DEFAULT_DATA_DIR, "settings.json")
        
        # Tải cấu hình nếu có
        self.load_settings()
    
    def load_settings(self):
        """Tải cài đặt từ file cấu hình."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved_settings = json.load(f)
                
                # Cập nhật cài đặt, chỉ lấy các khóa hợp lệ
                for key in DEFAULT_SETTINGS:
                    if key in saved_settings:
                        self.settings[key] = saved_settings[key]
                
                self.logger.info("Đã tải cài đặt từ file")
            else:
                self.logger.info("Không tìm thấy file cài đặt, sử dụng cài đặt mặc định")
        except Exception as e:
            self.logger.error(f"Lỗi khi tải cài đặt: {e}")
    
    def save_settings(self):
        """Lưu cài đặt vào file cấu hình."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
            
            self.logger.info("Đã lưu cài đặt")
            return True
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu cài đặt: {e}")
            return False
    
    def get(self, key, default=None):
        """Lấy giá trị cài đặt theo khóa."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Đặt giá trị cài đặt theo khóa."""
        if key in DEFAULT_SETTINGS:
            self.settings[key] = value
            return True
        return False
    
    def reset_to_default(self):
        """Khôi phục cài đặt mặc định."""
        self.settings = DEFAULT_SETTINGS.copy()
        return True

# Tạo đối tượng config toàn cục
config = Config()