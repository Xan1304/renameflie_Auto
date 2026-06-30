import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance
from datetime import datetime
from core.config import load_config

def setup_tesseract():
    """Thiết lập đường dẫn Tesseract từ config."""
    config = load_config()
    pytesseract.pytesseract.tesseract_cmd = config.get("tesseract_path", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

def is_tesseract_installed():
    """Kiểm tra xem Tesseract có sẵn sàng hay không."""
    setup_tesseract()
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def extract_pdf_info(pdf_path):
    setup_tesseract()
    result = {
        "so_kh": None, "ngay_vb": None,
        "so_trang": None, "thumbnail_path": None,
        "error": None,
        "crop_sokh_path": None, "crop_ngay_path": None, "crop_trang_path": None
    }

    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            result["error"] = "File PDF rỗng"
            return result

        page = doc[0]
        zoom = 200 / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        w, h = img.size

        # Lưu thumbnail
        thumb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_thumbs")
        os.makedirs(thumb_dir, exist_ok=True)
        base = os.path.basename(pdf_path)

        thumbnail = img.copy()
        thumbnail.thumbnail((1000, 1400))
        thumb_path = os.path.join(thumb_dir, base + ".thumb.png")
        thumbnail.save(thumb_path)
        result["thumbnail_path"] = thumb_path

        # Lưu ảnh crop cho tooltip hover
        def save_crop(box, suffix, size):
            cropped = img.crop(box).resize(size, Image.Resampling.LANCZOS)
            path = os.path.join(thumb_dir, base + f".{suffix}.png")
            cropped.save(path)
            return path

        result["crop_sokh_path"]  = save_crop((0, int(h*0.05), int(w*0.38), int(h*0.30)), "sokh",  (320, 160))
        result["crop_ngay_path"]  = save_crop((int(w*0.45), int(h*0.04), w, int(h*0.22)), "ngay",  (320, 140))
        result["crop_trang_path"] = save_crop((int(w*0.58), 0, w, int(h*0.06)),            "trang", (200, 70))

        # ── Tiền xử lý ảnh ──────────────────────────────────────────
        def preprocess(image, scale=2):
            image = image.resize(
                (image.width * scale, image.height * scale),
                Image.Resampling.LANCZOS)
            gray = image.convert('L')
            gray = ImageEnhance.Contrast(gray).enhance(2.5)
            gray = ImageEnhance.Sharpness(gray).enhance(2.0)
            # Ngưỡng adaptive: dùng 150 cho chữ viết tay (tối hơn)
            return gray.point(lambda p: 255 if p > 150 else 0)

        # ── OCR Số KH (góc trên TRÁI) ───────────────────────────────
        img_left = img.crop((0, 0, int(w * 0.38), int(h * 0.5)))
        text_left = pytesseract.image_to_string(preprocess(img_left), lang='vie+eng')

        # Pattern 1: "Số: 13/..." hoặc "Số 09 -..." (kể cả OCR nhầm S→S6, S→56)
        patterns_sokh = [
            r'[Ss][ốoO06ố][\s:\.]*(\d+)',   # Số: 13 / Số 09 / S6: 5
            r'[Ss](?:ố|o|0|6)[\s:\.]*(\d+)', # dạng unicode tường minh
            r'\bS[o0O6ố][\s:]*(\d+)',         # fallback ngắn
        ]
        for pat in patterns_sokh:
            m = re.search(pat, text_left)
            if m:
                val = int(m.group(1))
                # Lọc số quá lớn (>999) có thể là số năm bị nhận nhầm
                if val <= 999:
                    result["so_kh"] = val
                    break

        # ── OCR Số trang (góc TRÊN CÙNG bên phải, rất nhỏ) ─────────
        # Dùng vùng nhỏ hơn (6% chiều cao) để tránh đọc chữ bên dưới
        # Đã tắt theo yêu cầu user: chỉ để hình thu nhỏ, không ghi số trang tự động
        # box_trang = (int(w * 0.60), 0, w, int(h * 0.06))
        # img_trang = img.crop(box_trang)
        # img_trang_proc = preprocess(img_trang, scale=3)
        # text_trang = pytesseract.image_to_string(...)
        result["so_trang"] = None

        # ── OCR Ngày (góc trên PHẢI) ────────────────────────────────
        img_right = img.crop((int(w * 0.40), 0, w, int(h * 0.33)))
        text_right = pytesseract.image_to_string(preprocess(img_right), lang='vie+eng')

        def clean_num(s):
            return int(s.lower()
                       .replace('o','0').replace('O','0')
                       .replace('l','1').replace('I','1'))

        ngay_vb = None

        # Pattern 1: "ngày DD tháng MM năm YYYY" (tiếng Việt, OCR có thể sai dấu)
        m = re.search(
            r'(?i)ng[aà][yỳ]\s*([0-9oOlI]{1,2})\s*th[aá]ng\s*([0-9oOlI]{1,2})\s*n[aă]m\s*(\d{4})',
            text_right)
        if m:
            try:
                ngay_vb = datetime(clean_num(m.group(3)), clean_num(m.group(2)), clean_num(m.group(1)))
            except ValueError:
                pass

        # Pattern 2: dạng số thô DD MM YYYY (khi OCR không nhận ra chữ)
        if not ngay_vb:
            m = re.search(
                r'([0-9oOlI]{1,2})[^\d]{1,15}?([0-9oOlI]{1,2})[^\d]{1,15}?(\d{4})',
                text_right, re.IGNORECASE)
            if m:
                try:
                    d = clean_num(m.group(1))
                    mo = clean_num(m.group(2))
                    y = int(m.group(3))
                    if 1 <= d <= 31 and 1 <= mo <= 12 and 1990 <= y <= 2100:
                        ngay_vb = datetime(y, mo, d)
                except ValueError:
                    pass

        # Pattern 3: fallback dd/mm/yyyy hoặc dd-mm-yyyy
        if not ngay_vb:
            m = re.search(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})', text_right)
            if m:
                try:
                    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    if 1 <= d <= 31 and 1 <= mo <= 12 and 1990 <= y <= 2100:
                        ngay_vb = datetime(y, mo, d)
                except ValueError:
                    pass

        result["ngay_vb"] = ngay_vb
        doc.close()
        
    except Exception as e:
        result["error"] = str(e)
        
    return result

def cleanup_thumbnails():
    """Xóa các thumbnail tạm thời khi tắt app."""
    thumb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_thumbs")
    if os.path.exists(thumb_dir):
        for f in os.listdir(thumb_dir):
            try:
                os.remove(os.path.join(thumb_dir, f))
            except:
                pass
