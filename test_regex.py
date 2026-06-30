import re

tests = [
    "An Tây, ngày 01 tháng 02năm 2019",
    "ngày 01 tháng 02 năm 2019",
    "An Tay, ngay 01 thang 02nam 2019",
    "ngày 15 tháng 07 năm 2024"
]

pattern = r'(?i)ng\D*?(\d{1,2})\D*?th\D*?(\d{1,2})\D*?n\D*?(\d{4})'

with open("test_out2.txt", "w", encoding="utf-8") as f:
    for t in tests:
        match = re.search(pattern, t)
        f.write(f"[{t}] -> {match.groups() if match else 'NO MATCH'}\n")
