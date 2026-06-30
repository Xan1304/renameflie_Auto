import fitz
from PIL import Image
import os

def detect_blank_pages(pdf_path, brightness_threshold=0.95, include_small_marks=True):
    """
    Quét từng trang của PDF, phát hiện trang trắng hoặc gần trắng.
    
    Trả về dict:
    {
        "total_pages": int,
        "blank_pages": [1, 3, 5, ...],  # số trang (bắt đầu từ 1)
        "page_thumbnails": {1: "/path/thumb_p1.png", ...},
        "error": None hoặc str
    }
    """
    result = {
        "total_pages": 0,
        "blank_pages": [],
        "page_thumbnails": {},
        "error": None
    }

    try:
        doc = fitz.open(pdf_path)
        result["total_pages"] = len(doc)

        thumb_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "temp_thumbs")
        os.makedirs(thumb_dir, exist_ok=True)
        base = os.path.basename(pdf_path)

        for i, page in enumerate(doc):
            page_num = i + 1  # Hiển thị từ 1

            # Render trang ở 120 DPI (đủ để phân tích, không quá nặng)
            zoom = 120 / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            w, h = img.size

            # Lưu thumbnail trang này
            thumb_name = f"{base}.p{page_num}.png"
            thumb_path = os.path.join(thumb_dir, thumb_name)
            thumb = img.copy()
            thumb.thumbnail((400, 600))
            thumb.save(thumb_path)
            result["page_thumbnails"][page_num] = thumb_path

            # ── PHÂN TÍCH TRANG ─────────────────────────────────────
            # Bỏ viền mép 5% xung quanh (hay có vết máy scan)
            margin_x = int(w * 0.05)
            margin_y = int(h * 0.05)
            img_inner = img.crop((margin_x, margin_y,
                                   w - margin_x, h - margin_y))

            img_gray = img_inner.convert('L')
            pixels = list(img_gray.getdata())
            total = len(pixels)

            # Bước 1: % pixel sáng (> 240/255)
            bright_count = sum(1 for p in pixels if p > 240)
            bright_ratio = bright_count / total

            if bright_ratio < brightness_threshold:
                # Chắc chắn có nội dung → không phải trắng
                continue

            # Bước 2: Kiểm tra vùng tối liên tục (connected components)
            # Dùng phương pháp đơn giản: quét hàng ngang
            # Tìm hàng nào có > 80px liên tục tối (< 180) → có chữ/chữ ký
            iw, ih = img_gray.size
            has_content = False

            # Kiểm tra hàng ngang: dòng chữ đánh máy
            for row in range(0, ih, 3):  # bước nhảy 3px để nhanh hơn
                dark_run = 0
                max_dark_run = 0
                for col in range(iw):
                    pixel = img_gray.getpixel((col, row))
                    if pixel < 180:
                        dark_run += 1
                        max_dark_run = max(max_dark_run, dark_run)
                    else:
                        dark_run = 0
                if max_dark_run > 80:  # ~1 từ chữ đánh máy
                    has_content = True
                    break

            if has_content:
                continue

            # Kiểm tra vùng tối tập trung (chữ ký, con dấu)
            # Đếm tổng pixel tối trong từng ô 30x30
            if include_small_marks:
                # Chỉ bỏ qua nếu có cụm tối >= 30x30px
                block_size = 30
                for row in range(0, ih - block_size, block_size):
                    for col in range(0, iw - block_size, block_size):
                        dark_in_block = 0
                        for r in range(row, row + block_size):
                            for c in range(col, col + block_size):
                                if img_gray.getpixel((c, r)) < 150:
                                    dark_in_block += 1
                        # Nếu > 15% block là tối → có nội dung thật
                        if dark_in_block > (block_size * block_size * 0.15):
                            has_content = True
                            break
                    if has_content:
                        break
            else:
                # Không quan tâm vết nhỏ → chỉ dựa brightness_ratio
                pass

            if not has_content:
                result["blank_pages"].append(page_num)

        doc.close()

    except Exception as e:
        result["error"] = str(e)

    return result


def remove_blank_pages(pdf_path, pages_to_remove, output_path):
    """
    Xóa các trang trong danh sách pages_to_remove (số trang từ 1).
    Lưu file mới ra output_path.
    Trả về (success: bool, error: str hoặc None)
    """
    try:
        doc = fitz.open(pdf_path)
        total = len(doc)

        # Chuyển sang index 0-based, đảo ngược để xóa từ cuối lên
        indices = sorted(
            [p - 1 for p in pages_to_remove if 1 <= p <= total],
            reverse=True)

        for idx in indices:
            doc.delete_page(idx)

        doc.save(output_path)
        doc.close()
        return True, None

    except Exception as e:
        return False, str(e)
