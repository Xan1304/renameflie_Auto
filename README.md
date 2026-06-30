# PDF Renamer Pro

Ứng dụng desktop tự động đổi tên file PDF dựa trên dữ liệu trích xuất từ văn bản (Số ký hiệu và Ngày văn bản) thông qua OCR.
Được thiết kế đặc biệt cho các loại văn bản hành chính Việt Nam.

## Hướng dẫn cài đặt

1. Cài đặt các thư viện Python cần thiết:
   ```cmd
   pip install -r requirements.txt
   ```

2. **YÊU CẦU QUAN TRỌNG:** Cài đặt Tesseract OCR:
   - Tải bộ cài Tesseract tại: [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - Trong quá trình cài đặt, hãy đảm bảo chọn tải ngôn ngữ **Vietnamese (vie)** trong mục *Additional language data (download)*.
   - Nếu bạn cài đặt vào thư mục khác với mặc định (`C:\Program Files\Tesseract-OCR\tesseract.exe`), vui lòng vào menu **Cài đặt** trong ứng dụng để cập nhật lại đường dẫn.

## Hướng dẫn chạy ứng dụng

Chạy trực tiếp mã nguồn bằng Python:
```cmd
python main.py
```

## Hướng dẫn đóng gói thành file .exe (Tùy chọn)

Nếu bạn muốn tạo ra một file thực thi độc lập (không cần cài sẵn Python trên máy khác):

1. Cài đặt thư viện `pyinstaller`:
   ```cmd
   pip install pyinstaller
   ```

2. Chạy lệnh đóng gói:
   ```cmd
   pyinstaller --onefile --windowed main.py
   ```

3. File `main.exe` (hay `PDF Renamer Pro.exe` nếu bạn đổi tên) sẽ được tạo ra trong thư mục `dist/`.


