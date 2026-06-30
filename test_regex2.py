import re

tests = [
    "An Tây, ngày 01 tháng 02năm 2019",
    "ngày 01 tháng 02 năm 2019",
    "An Tay, ngdy 01 thdng 02nam 2019",
    "ngày 15 tháng 07 năm 2024",
    "An Tay, ngdy Ol tfng O2ndm 2019",
    "ngay 12-05-2023",
    "12/05/2023"
]

pattern = r'([0-9oOlI]{1,2})[^\d]{1,15}?([0-9oOlI]{1,2})[^\d]{1,15}?(\d{4})'

def clean_num(s):
    s = s.lower().replace('o', '0').replace('l', '1').replace('i', '1')
    return int(s)

with open("test_out3.txt", "w", encoding="utf-8") as f:
    for t in tests:
        match = re.search(pattern, t, re.IGNORECASE)
        if match:
            d, m, y = match.groups()
            try:
                d = clean_num(d)
                m = clean_num(m)
                y = int(y)
                f.write(f"[{t}] -> {d}/{m}/{y}\n")
            except Exception as e:
                f.write(f"[{t}] -> ERROR {e}\n")
        else:
            f.write(f"[{t}] -> NO MATCH\n")
