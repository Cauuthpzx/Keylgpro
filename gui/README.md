# Keylogger Pro

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.1.0-green.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)

Keylogger Pro là một ứng dụng theo dõi bàn phím và chụp màn hình với giao diện người dùng hiện đại, được phát triển với mục đích **giáo dục và nghiên cứu**.

## ⚠️ Cảnh báo đạo đức & pháp lý

Ứng dụng này chỉ nên được sử dụng trên các thiết bị mà bạn có quyền sở hữu hoặc được sự đồng ý rõ ràng. Việc sử dụng keylogger để theo dõi người khác mà không có sự đồng ý là vi phạm quyền riêng tư và có thể vi phạm pháp luật tại nhiều quốc gia.

## Tính năng chính

- 🔑 **Theo dõi keystrokes** với hiệu suất cao
- 📷 **Chụp màn hình thông minh** với phát hiện thay đổi
- 🖥️ **Quản lý nhiều thiết bị** trong một giao diện
- 📊 **Xuất dữ liệu** ra nhiều định dạng
- 🔒 **Mã hóa dữ liệu** bảo mật
- 📁 **Tạo file mồi** cho nhiều nền tảng
- 🍪 **Trích xuất cookie** từ trình duyệt
- 🎨 **Giao diện người dùng hiện đại**

## Cấu trúc dự án

```
keylogger/
├── core/                  # Các module cốt lõi
│   ├── __init__.py
│   ├── keylogger.py       # Chức năng theo dõi bàn phím
│   ├── database.py        # Quản lý cơ sở dữ liệu
│   ├── system_info.py     # Thu thập thông tin hệ thống
│   ├── utils.py           # Tiện ích chung
│   └── screenshot.py      # Chức năng chụp màn hình
├── extractors/            # Các module trích xuất dữ liệu
│   ├── __init__.py
│   └── browser_cookie_extractor.py
├── generators/            # Các module tạo file mồi
│   ├── __init__.py
│   └── bait_generator.py
├── gui/                   # Giao diện người dùng
│   ├── __init__.py
│   ├── app.py             # Class ứng dụng chính
│   ├── resources.py       # Tài nguyên giao diện (icons, themes)
│   └── frames/            # Các frame cho từng tab
│       ├── __init__.py
│       ├── keylogger_frame.py
│       ├── management_frame.py
│       ├── bait_frame.py
│       ├── cookie_frame.py
│       ├── screenshot_frame.py  # Giao diện chụp màn hình
│       ├── settings_frame.py
│       └── about_frame.py
├── config.py              # Cấu hình ứng dụng
├── main.py                # Điểm khởi đầu ứng dụng
└── README.md              # Tài liệu
```

## Yêu cầu hệ thống

- Python 3.6 hoặc cao hơn
- Thư viện:
  - `pynput`: Theo dõi sự kiện bàn phím
  - `ttkbootstrap`: Giao diện hiện đại
  - `pillow`: Xử lý hình ảnh
  - `cryptography`: Mã hóa dữ liệu
  - `openpyxl`: Xuất dữ liệu Excel
  - `numpy`: Xử lý dữ liệu và so sánh hình ảnh
  - `requests`: Giao tiếp HTTP và tải lên từ xa
  - `apscheduler`: Lên lịch tác vụ

## Cài đặt

1. Clone repository:
   ```
   git clone https://github.com/username/keylogger.git
   cd keylogger
   ```

2. Cài đặt các thư viện cần thiết:
   ```
   pip install -r requirements.txt
   ```

3. Chạy ứng dụng:
   ```
   python main.py
   ```

## Hướng dẫn sử dụng

### Theo dõi bàn phím

1. Chọn tab "Theo dõi bàn phím"
2. Thiết lập đường dẫn lưu log
3. Chọn các tùy chọn (tự khởi động, chế độ ẩn)
4. Bấm "Bắt đầu theo dõi"

### Chụp màn hình

1. Chọn tab "Chụp màn hình"
2. Thiết lập thông số:
   - Thư mục lưu ảnh
   - Thời gian giữa các lần chụp
   - Vùng chụp (toàn màn hình hoặc vùng cụ thể)
   - Định dạng và chất lượng ảnh
3. Tùy chọn cấu hình nâng cao:
   - Chụp theo phát hiện thay đổi (tiết kiệm không gian lưu trữ)
   - Mã hóa ảnh chụp với AES
   - Giới hạn lưu trữ (thời gian/dung lượng)
   - Tải lên máy chủ từ xa
4. Bấm "Bắt đầu chụp" để kích hoạt
5. Sử dụng các nút điều khiển để tạm dừng/tiếp tục hoặc xem lại ảnh

### Quản lý thiết bị

1. Chọn tab "Quản lý thiết bị"
2. Nhấn "Làm mới danh sách" để cập nhật
3. Chọn thiết bị để xem chi tiết

### Tạo file mồi

1. Chọn tab "Tạo file mồi"
2. Nhập thông tin cần thiết
3. Chọn loại file mồi
4. Bấm "Tạo file mồi"

### Trích xuất cookie

1. Chọn tab "Trích xuất cookie"
2. Chọn thư mục lưu kết quả
3. Bấm "Trích xuất cookie"

## Tính năng chụp màn hình

Module mới bổ sung các tính năng chụp màn hình nâng cao:

### Tính năng cơ bản
- **Chụp toàn màn hình** hoặc vùng chỉ định
- **Lên lịch tự động** theo khoảng thời gian tùy chỉnh
- **Hỗ trợ nhiều định dạng** (PNG, JPEG) với chất lượng tùy chỉnh
- **Xem trước ảnh** ngay trong ứng dụng

### Tính năng nâng cao
- **Phát hiện thay đổi**: Chỉ chụp khi màn hình có thay đổi, tiết kiệm dung lượng lưu trữ
- **Mã hóa AES**: Bảo vệ ảnh chụp khỏi truy cập trái phép
- **Quản lý lưu trữ thông minh**:
  - Tự động xóa ảnh cũ sau X ngày
  - Giới hạn tổng dung lượng sử dụng
- **Thumbnail tự động**: Tạo ảnh thu nhỏ cho xem trước nhanh
- **Tải lên từ xa**: Gửi ảnh tự động đến máy chủ từ xa
- **Metadata EXIF**: Lưu thông tin thiết bị, thời gian và người dùng
- **Tạm dừng/Tiếp tục**: Kiểm soát quá trình chụp linh hoạt

### Các cải tiến mới
- Phát hiện thay đổi thông minh để tiết kiệm dung lượng lưu trữ
- Trích xuất vùng màn hình cụ thể từ ảnh đã chụp
- Xem trước ảnh trực tiếp trong ứng dụng
- Tải lên máy chủ từ xa tự động
- Ghi log ra stdout ngoài file log
- Kiểm soát dung lượng thông minh
- Hỗ trợ tạm dừng/tiếp tục thay vì chỉ có bắt đầu/dừng
- Bổ sung metadata vào ảnh chụp

## Phát triển

### Mở rộng tính năng

1. **Thêm loại file mồi mới**:
   - Bổ sung phương thức mới trong `BaitFileGenerator`
   - Cập nhật UI trong `BaitFrame`

2. **Mở rộng chức năng chụp màn hình**:
   - Tích hợp OCR để trích xuất văn bản từ ảnh
   - Thêm bộ lọc hình ảnh cho ảnh chụp
   - Bổ sung hỗ trợ quay video

3. **Trích xuất thêm dữ liệu**:
   - Tạo module trích xuất mới trong thư mục `extractors/`
   - Thêm tab mới trong giao diện

4. **Bổ sung cách mã hóa**:
   - Mở rộng các hàm trong `core/utils.py`

## Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Liên hệ

Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ qua email: example@example.com