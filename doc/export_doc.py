import os
from pathlib import Path

def main():
    # Lấy thư mục chứa script hiện tại (doc/)
    script_dir = Path(__file__).resolve().parent
    # Thư mục gốc của dự án (thư mục cha của doc/)
    target_dir = script_dir.parent
    
    # Tự động lấy tên thư mục dự án làm tên file (ví dụ: dat_ten_file_Auto)
    name = target_dir.name
    version = "0.0.1"
    
    if not target_dir.exists():
        print("Khong tim thay thu muc du an")
        return

    file_name = f"{name}_v{version}.txt"
    output_file = script_dir / file_name

    # Các thư mục không muốn quét
    exclude_dirs = {'.git', 'venv', '.venv', '__pycache__', 'temp_thumbs', 'doc'}

    with open(output_file, 'w', encoding='utf-8') as out_f:
        for root, dirs, files in os.walk(target_dir):
            # Lọc bỏ các thư mục không cần thiết
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # Đọc các file Python (.py)
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    out_f.write(f"\nFILE: {file_path}\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as in_f:
                            content = in_f.read()
                        out_f.write(content)
                        out_f.write("\n")
                    except Exception as e:
                        print(f"Loi khi doc file {file_path}: {e}")

    print(f"Export xong: {file_name}")

if __name__ == "__main__":
    main()
