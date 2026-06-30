import os
import tkinter as tk
from tkinter import ttk

from core.ocr import cleanup_thumbnails

# ═══════════════════════════════════════════════════════════
#  BẢNG MÀU CHUẨN HÓA — Corporate/Office Style
#  Tất cả màu sắc tập trung 1 chỗ, dễ thay đổi đồng bộ
# ═══════════════════════════════════════════════════════════
COLORS = {
    # Nền
    "bg_app":       "#F1F3F6",   # [THAY ĐỔI] Xám xanh lạnh thay vì #F0F2F5 — chuyên nghiệp hơn
    "bg_card":      "#FFFFFF",
    "bg_header":    "#1B2A4A",   # [THAY ĐỔI] Header xanh navy đậm thay vì trắng — tạo điểm nhấn
    "bg_table_alt": "#F8FAFC",

    # Chữ
    "text_primary":   "#1B2A4A", # [THAY ĐỔI] Xanh navy (thống nhất với header) thay #1F2937
    "text_secondary": "#6B7280",
    "text_inverse":   "#FFFFFF",
    "text_muted":     "#9CA3AF",

    # Brand / Accent
    "accent":         "#2563EB", # [THAY ĐỔI] Xanh dương chuẩn hơn, sáng hơn #1A56DB
    "accent_hover":   "#1D4ED8",
    "accent_light":   "#DBEAFE",

    # Nút hành động
    "btn_success":    "#059669", # Xanh lá đậm
    "btn_success_hv": "#047857",
    "btn_warning":    "#D97706", # [THAY ĐỔI] Cam amber thanh hơn #FF8A00
    "btn_warning_hv": "#B45309",
    "btn_danger":     "#DC2626",

    # Viền & phân cách
    "border":         "#E2E8F0", # [THAY ĐỔI] Nhạt hơn một chút, tinh tế
    "border_focus":   "#2563EB",

    # Trạng thái
    "row_selected_bg": "#DBEAFE",
    "row_selected_fg": "#1E40AF",
}

FONTS = {
    # [THAY ĐỔI] Chuẩn hóa: Segoe UI cho tất cả — dùng size rõ ràng
    "app_title": ("Segoe UI", 13, "bold"),
    "heading":   ("Segoe UI", 11, "bold"),
    "body":      ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small":     ("Segoe UI", 9),
    "small_it":  ("Segoe UI", 9, "italic"),
    "caption":   ("Segoe UI", 8),
    "welcome":   ("Segoe UI", 22, "bold"),  # [THAY ĐỔI] 24→22 để vừa hơn
}


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PDF Renamer Pro")
        self.geometry("1080x720")        # [THAY ĐỔI] Tăng thêm 80px ngang — thở hơn
        self.minsize(1000, 680)
        self.configure(bg=COLORS["bg_app"])

        # Thiết lập icon nếu có
        try:
            self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        self.setup_styles()
        self.build_ui()

        # Phím tắt toàn cục
        self._bind_global_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ── Styles ──────────────────────────────────────────────────────
    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # ── Nền mặc định ────────────────────────────────────────────
        style.configure(".",
            background=COLORS["bg_app"],
            font=FONTS["body"])

        # ── Frame Card ──────────────────────────────────────────────
        style.configure("Card.TFrame",
            background=COLORS["bg_card"],
            relief="flat")

        # ── Label ───────────────────────────────────────────────────
        style.configure("TLabel",
            background=COLORS["bg_app"],
            font=FONTS["body"])
        style.configure("Card.TLabel",
            background=COLORS["bg_card"],
            font=FONTS["body"])

        # ── Notebook (Tabs) ──────────────────────────────────────────
        # [THAY ĐỔI] Tab dùng đường gạch dưới thay vì background tối/sáng
        style.configure("TNotebook",
            background=COLORS["bg_app"],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab",
            font=FONTS["body"],
            padding=(20, 9),            # [THAY ĐỔI] Padding lớn hơn, thoáng hơn
            background=COLORS["bg_app"],
            foreground=COLORS["text_secondary"],
            borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["bg_card"])],
            foreground=[("selected", COLORS["accent"])],
            font=[("selected", FONTS["body_bold"])],  # [THAY ĐỔI] Tab active bold
            expand=[("selected", [1, 1, 1, 0])])

        # ── Treeview (Bảng) ─────────────────────────────────────────
        style.configure("Treeview",
            rowheight=40,               # [THAY ĐỔI] 38→40 — ít dày đặc hơn
            font=FONTS["body"],
            background=COLORS["bg_card"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            relief="flat")
        style.configure("Treeview.Heading",
            font=FONTS["body_bold"],
            background="#EEF2F7",        # [THAY ĐỔI] Heading nhẹ hơn, phân biệt rõ hơn
            foreground=COLORS["text_primary"],
            borderwidth=0,
            relief="flat",
            padding=(6, 8))             # [THAY ĐỔI] Thêm padding heading
        style.map("Treeview",
            background=[("selected", COLORS["row_selected_bg"])],
            foreground=[("selected", COLORS["row_selected_fg"])])
        style.map("Treeview.Heading",
            background=[("active", "#DDE4EF")])

        # ── Nút PRIMARY (Xanh dương — Quét) ─────────────────────────
        style.configure("Primary.TButton",
            background=COLORS["accent"],
            foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"],
            padding=(18, 8),            # [THAY ĐỔI] Padding đều hơn
            relief="flat",
            borderwidth=0)
        style.map("Primary.TButton",
            background=[
                ("active",   COLORS["accent_hover"]),
                ("disabled", "#93C5FD")])

        # ── Nút SUCCESS (Xanh lá — Lưu / Đổi tên) ──────────────────
        style.configure("Success.TButton",
            background=COLORS["btn_success"],
            foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"],
            padding=(18, 8),
            relief="flat",
            borderwidth=0)
        style.map("Success.TButton",
            background=[
                ("active",   COLORS["btn_success_hv"]),
                ("disabled", "#6EE7B7")])

        # ── Nút WARNING (Cam — Hoàn tác) ────────────────────────────
        style.configure("Warning.TButton",
            background=COLORS["btn_warning"],
            foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"],
            padding=(18, 8),
            relief="flat",
            borderwidth=0)
        style.map("Warning.TButton",
            background=[
                ("active",   COLORS["btn_warning_hv"]),
                ("disabled", "#FCD34D")])

        # ── Nút thứ cấp (Outline — Duyệt / Chọn thư mục) ───────────
        # [THAY ĐỔI] Thêm style Secondary để phân biệt với Primary
        style.configure("Secondary.TButton",
            background=COLORS["bg_card"],
            foreground=COLORS["accent"],
            font=FONTS["body"],
            padding=(12, 7),
            relief="flat",
            borderwidth=1)
        style.map("Secondary.TButton",
            background=[("active", COLORS["accent_light"])],
            foreground=[("active", COLORS["accent_hover"])])

        # ── Entry ────────────────────────────────────────────────────
        style.configure("TEntry",
            padding=(8, 7),             # [THAY ĐỔI] Tăng padding dọc để đủ chiều cao
            fieldbackground=COLORS["bg_card"],
            borderwidth=1,
            relief="solid")
        style.map("TEntry",
            bordercolor=[
                ("focus", COLORS["border_focus"]),
                ("!focus", COLORS["border"])])

        # ── Combobox ─────────────────────────────────────────────────
        style.configure("TCombobox",
            padding=(8, 7),
            fieldbackground=COLORS["bg_card"])
        style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["bg_card"])],
            bordercolor=[("focus", COLORS["border_focus"])])

        # ── Progressbar ──────────────────────────────────────────────
        style.configure("Corporate.Horizontal.TProgressbar",  # [THAY ĐỔI] Tên mới rõ hơn
            troughcolor="#E5E7EB",
            background=COLORS["accent"],    # [THAY ĐỔI] Màu xanh brand thay xanh lá
            thickness=6,                    # [THAY ĐỔI] 8→6 px tinh tế hơn
            borderwidth=0)

        # Giữ tên cũ để tương thích ngược với các Tab
        style.configure("green.Horizontal.TProgressbar",
            troughcolor="#E5E7EB",
            background=COLORS["btn_success"],
            thickness=6,
            borderwidth=0)

        # ── Scrollbar ────────────────────────────────────────────────
        style.configure("TScrollbar",
            troughcolor=COLORS["bg_app"],
            background=COLORS["border"],
            borderwidth=0,
            arrowsize=14)

        # ── Checkbutton ──────────────────────────────────────────────
        style.configure("TCheckbutton",
            background=COLORS["bg_card"],
            font=FONTS["body"])

        # ── Scale ────────────────────────────────────────────────────
        style.configure("TScale",
            background=COLORS["bg_card"],
            troughcolor=COLORS["border"])

    # ── UI ──────────────────────────────────────────────────────────
    def build_ui(self):
        self.configure(bg=COLORS["bg_app"])

        # ── HEADER ──────────────────────────────────────────────────
        # [THAY ĐỔI] Header từ trắng → navy tối — tạo visual hierarchy rõ ràng
        header = tk.Frame(self, bg=COLORS["bg_header"], height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Logo / Tên app
        logo_frame = tk.Frame(header, bg=COLORS["bg_header"])
        logo_frame.pack(side=tk.LEFT, padx=20, pady=0, fill=tk.Y)

        tk.Label(logo_frame,
                 text="✦",                 # [THAY ĐỔI] Icon ✏ → ✦ — tinh tế, dễ đọc hơn
                 font=("Segoe UI", 16),
                 fg=COLORS["accent"],
                 bg=COLORS["bg_header"]).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(logo_frame,
                 text="PDF Renamer Pro",
                 font=FONTS["app_title"],
                 fg=COLORS["text_inverse"],
                 bg=COLORS["bg_header"]).pack(side=tk.LEFT)

        # [THAY ĐỔI] Thêm version label nhỏ bên phải header
        tk.Label(header,
                 text="v0.0.1",
                 font=FONTS["caption"],
                 fg="#6B8CC7",              # Xanh nhạt để không quá nổi
                 bg=COLORS["bg_header"]).pack(side=tk.RIGHT, padx=20)

        # ── NOTEBOOK ────────────────────────────────────────────────
        # [THAY ĐỔI] Thêm separator mỏng giữa header và notebook
        sep = tk.Frame(self, bg=COLORS["border"], height=1)
        sep.pack(fill=tk.X)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Đổi tên
        from gui.tab_rename import RenameTab
        self.tab_rename = RenameTab(self.notebook, self)
        self.notebook.add(self.tab_rename, text="  Đổi tên PDF  ")

        # Tab 2: Tìm trang trắng
        from gui.tab_find_blank import FindBlankTab
        self.tab_find = FindBlankTab(self.notebook, self)
        self.notebook.add(self.tab_find, text="  Tìm trang trắng  ")

        # [THAY ĐỔI] Bind Ctrl+Tab để chuyển tab nhanh
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        """Cập nhật tiêu đề window theo tab đang chọn."""
        tab_names = ["Đổi tên PDF", "Tìm trang trắng"]
        try:
            idx = self.notebook.index("current")
            self.title(f"PDF Renamer Pro — {tab_names[idx]}")
        except Exception:
            pass

    def _bind_global_shortcuts(self):
        """[THAY ĐỔI] Phím tắt toàn cục — UX tiện lợi cho môi trường văn phòng."""
        # Ctrl+1 / Ctrl+2 chuyển tab
        self.bind_all("<Control-Key-1>",
                      lambda e: self.notebook.select(0))
        self.bind_all("<Control-Key-2>",
                      lambda e: self.notebook.select(1))
        # Ctrl+Q thoát
        self.bind_all("<Control-q>", lambda e: self.on_closing())

    def on_closing(self):
        cleanup_thumbnails()
        self.destroy()
