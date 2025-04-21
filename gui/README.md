# Keylogger Pro

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)

Keylogger Pro là một ứng dụng theo dõi bàn phím với giao diện người dùng hiện đại, được phát triển với mục đích **giáo dục và nghiên cứu**.

## ⚠️ Cảnh báo đạo đức & pháp lý

Ứng dụng này chỉ nên được sử dụng trên các thiết bị mà bạn có quyền sở hữu hoặc được sự đồng ý rõ ràng. Việc sử dụng keylogger để theo dõi người khác mà không có sự đồng ý là vi phạm quyền riêng tư và có thể vi phạm pháp luật tại nhiều quốc gia.

## Tính năng chính

- 🔑 **Theo dõi keystrokes** với hiệu suất cao
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
│   └── utils.py           # Tiện ích chung
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

## Phát triển

### Mở rộng tính năng

1. **Thêm loại file mồi mới**:
   - Bổ sung phương thức mới trong `BaitFileGenerator`
   - Cập nhật UI trong `BaitFrame`

2. **Trích xuất thêm dữ liệu**:
   - Tạo module trích xuất mới trong thư mục `extractors/`
   - Thêm tab mới trong giao diện

3. **Bổ sung cách mã hóa**:
   - Mở rộng các hàm trong `core/utils.py`

## Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Liên hệ

Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ qua email: example@example.com