import os
from datetime import datetime

# Biến toàn cục để lưu trạng thái Undo (Tên mới: Tên cũ)
last_rename_mapping = {}

def sort_files(file_data_list):
    """
    Sắp xếp danh sách file theo thứ tự ưu tiên:
    1. Số KH (int)
    2. Ngày văn bản (datetime)
    3. Ngày sửa đổi file (float - timestamp)
    
    file_data_list là list các dict:
    {
        "path": "đường dẫn đầy đủ",
        "so_kh": int hoặc None,
        "ngay_vb": datetime hoặc None,
        "mtime": float
    }
    """
    def sort_key(item):
        # Python sort tuple theo thứ tự từ trái qua phải.
        # Nếu so_kh có giá trị, dùng nó. Nếu không, cho giá trị rất lớn để đẩy xuống dưới.
        k1 = item.get("so_kh") if item.get("so_kh") is not None else float('inf')
        
        # Tương tự với ngày văn bản. Nếu không có, cho ngày ở tương lai xa.
        k2 = item.get("ngay_vb")
        if k2 is None:
            k2 = datetime.max
            
        # mtime
        k3 = item.get("mtime", 0)
        
        return (k1, k2, k3)
        
    return sorted(file_data_list, key=sort_key)

def generate_new_names(sorted_files, prefix, start_num_str):
    """
    Tạo danh sách tên mới dựa vào tiền tố và số bắt đầu.
    Bỏ qua các file không được tích (checked = False).
    start_num_str là string để đếm độ dài (vd "043" -> length 3).
    """
    num_length = len(start_num_str)
    try:
        current_num = int(start_num_str)
    except ValueError:
        current_num = 1
        num_length = max(3, len(start_num_str))
        
    result = []
    
    for item in sorted_files:
        if not item.get("checked", True):
            result.append(None)
            continue
            
        # Định dạng số với padding 0 (leading zeros)
        num_str = str(current_num).zfill(num_length)
        new_name = f"{prefix}{num_str}.pdf"
        result.append(new_name)
        
        current_num += 1
        
    return result

def execute_rename(rename_plan, folder_path):
    """
    Thực hiện đổi tên thực tế.
    rename_plan là list các dict: {"old_path": str, "new_name": str, "new_path": str}
    """
    global last_rename_mapping
    last_rename_mapping.clear()
    
    success_count = 0
    errors = []
    
    # Đổi tên
    for item in rename_plan:
        old_path = item["old_path"]
        new_path = item["new_path"]
        
        if old_path == new_path:
            continue
            
        try:
            # Kiểm tra nếu file đích đã tồn tại
            if os.path.exists(new_path) and old_path.lower() != new_path.lower():
                errors.append(f"Lỗi {os.path.basename(old_path)}: File đích {os.path.basename(new_path)} đã tồn tại.")
                continue
                
            os.rename(old_path, new_path)
            last_rename_mapping[new_path] = old_path
            success_count += 1
        except Exception as e:
            errors.append(f"Lỗi đổi tên {os.path.basename(old_path)}: {str(e)}")
            
    return success_count, errors

def undo_last_rename():
    """
    Hoàn tác thao tác đổi tên gần nhất.
    """
    global last_rename_mapping
    if not last_rename_mapping:
        return False, "Không có lịch sử để hoàn tác."
        
    success = 0
    errors = []
    for new_path, old_path in list(last_rename_mapping.items()): # dùng list() để tránh RuntimeError khi thay đổi dict
        try:
            os.rename(new_path, old_path)
            success += 1
            # Xóa khỏi dict
            del last_rename_mapping[new_path]
        except Exception as e:
            errors.append(f"Lỗi khôi phục {os.path.basename(new_path)}: {str(e)}")
            
    return success, errors
