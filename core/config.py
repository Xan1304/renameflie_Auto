import os
import json

CONFIG_FILE = "config.json"
TEMPLATES_FILE = "templates.json"

DEFAULT_CONFIG = {
    "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
}

def load_config():
    """Tải cấu hình từ config.json. Nếu chưa có thì tạo mới."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Merge with default to ensure keys exist
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception as e:
        print(f"Lỗi khi đọc config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    """Lưu cấu hình vào config.json."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi lưu config: {e}")

def load_templates():
    """Tải danh sách các mẫu tiền tố & số bắt đầu."""
    if not os.path.exists(TEMPLATES_FILE):
        return {}
    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc templates: {e}")
        return {}

def save_templates(templates_data):
    """Lưu danh sách các mẫu."""
    try:
        with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi lưu templates: {e}")
