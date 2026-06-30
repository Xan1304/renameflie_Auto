import os
from core.ocr import extract_pdf_info

test_folder = r"d:\vibe_coding\dat_ten_file_Auto\test\110"
count = 0
if os.path.exists(test_folder):
    for f in os.listdir(test_folder):
        if f.lower().endswith(".pdf"):
            pdf_path = os.path.join(test_folder, f)
            print(f"Testing {pdf_path}...")
            result = extract_pdf_info(pdf_path)
            print(f"Result: {result}")
            if result.get("error"):
                print(f"Error detail: {result['error']}")
            count += 1
            if count >= 2: break
else:
    print(f"Test folder {test_folder} not found.")
