import os
import tkinter as tk
from tkinter import ttk

from core.ocr import cleanup_thumbnails

# ═══════════════════════════════════════════════════════════
#  BẢNG MÀU CHUẨN HÓA — Corporate/Office Style
# ═══════════════════════════════════════════════════════════
COLORS = {
    "bg_app":       "#F1F3F6",
    "bg_card":      "#FFFFFF",
    "bg_header":    "#1B2A4A",
    "bg_table_alt": "#F8FAFC",
    "text_primary":   "#1B2A4A",
    "text_secondary": "#6B7280",
    "text_inverse":   "#FFFFFF",
    "text_muted":     "#9CA3AF",
    "accent":         "#2563EB",
    "accent_hover":   "#1D4ED8",
    "accent_light":   "#DBEAFE",
    "btn_success":    "#059669",
    "btn_success_hv": "#047857",
    "btn_warning":    "#D97706",
    "btn_warning_hv": "#B45309",
    "btn_danger":     "#DC2626",
    "border":         "#E2E8F0",
    "border_focus":   "#2563EB",
    "row_selected_bg": "#DBEAFE",
    "row_selected_fg": "#1E40AF",
}

FONTS = {
    "app_title": ("Segoe UI", 13, "bold"),
    "heading":   ("Segoe UI", 11, "bold"),
    "body":      ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small":     ("Segoe UI", 9),
    "small_it":  ("Segoe UI", 9, "italic"),
    "caption":   ("Segoe UI", 8),
    "welcome":   ("Segoe UI", 22, "bold"),
}

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("PDF Renamer Pro")
        self.geometry("1080x720")
        self.minsize(1000, 680)
        self.configure(bg=COLORS["bg_app"])
        
        # Configure fonts and styles
        self.setup_styles()
        
        self.build_ui()
        
        # Phím tắt toàn cục
        self._bind_global_shortcuts()
        
        # Tự động dọn dẹp ảnh tạm khi tắt
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # Nền mặc định
        style.configure(".", background=COLORS["bg_app"], font=FONTS["body"])
        
        # Frame Card
        style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
        
        # Header tiêu đề app
        style.configure("AppTitle.TLabel", font=FONTS["app_title"], foreground=COLORS["accent"], background=COLORS["bg_card"])
        
        # Label thường
        style.configure("TLabel", background=COLORS["bg_app"], font=FONTS["body"])
        
        # Bảng
        style.configure("Treeview", 
            rowheight=38, 
            font=FONTS["body"],
            background=COLORS["bg_card"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0)
        style.configure("Treeview.Heading", 
            font=FONTS["body_bold"],
            background=COLORS["bg_table_alt"],
            foreground=COLORS["text_primary"],
            borderwidth=0,
            padding=(4, 8)) # Tăng padding dọc
        style.map("Treeview", 
            background=[("selected", COLORS["row_selected_bg"])], 
            foreground=[("selected", COLORS["row_selected_fg"])])
        
        # Nút Quét & Preview — xanh dương
        style.configure("Primary.TButton", 
            background=COLORS["accent"], foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"], padding=(16, 8))
        style.map("Primary.TButton", background=[("active", COLORS["accent_hover"])])
        
        # Nút Đổi tên ngay — xanh lá
        style.configure("Success.TButton", 
            background=COLORS["btn_success"], foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"], padding=(16, 8))
        style.map("Success.TButton", background=[("active", COLORS["btn_success_hv"])])
        
        # Nút Hoàn tác — vàng cam
        style.configure("Warning.TButton", 
            background=COLORS["btn_warning"], foreground=COLORS["text_inverse"],
            font=FONTS["body_bold"], padding=(16, 8))
        style.map("Warning.TButton", background=[("active", COLORS["btn_warning_hv"])])
        
        # Entry / Combobox
        style.configure("TEntry", padding=(8, 6), font=FONTS["body"])
        style.configure("TCombobox", padding=(8, 6), font=FONTS["body"])
        
        # Progressbar
        style.configure("green.Horizontal.TProgressbar", 
            troughcolor=COLORS["border"], 
            background=COLORS["accent"],
            thickness=8)

    def build_ui(self):
        # Header màu Navy đậm
        header = tk.Frame(self, bg=COLORS["bg_header"], height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="✏  PDF Renamer Pro",
                 font=FONTS["app_title"],
                 fg=COLORS["text_inverse"], bg=COLORS["bg_header"]).pack(side=tk.LEFT, padx=20, pady=14)

        # Line phân cách Header và nội dung
        sep = tk.Frame(self, bg=COLORS["accent"], height=2)
        sep.pack(fill=tk.X)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Tab 1
        from gui.tab_rename import RenameTab
        self.tab_rename = RenameTab(self.notebook, self)
        self.notebook.add(self.tab_rename, text="  Đổi tên PDF  ")

        # Tab 2
        from gui.tab_find_blank import FindBlankTab
        self.tab_find = FindBlankTab(self.notebook, self)
        self.notebook.add(self.tab_find, text="  Tìm trang trắng  ")

        # Style notebook tabs
        style = ttk.Style()
        style.configure("TNotebook", background=COLORS["bg_app"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        font=FONTS["body"],
                        padding=(16, 8),
                        background=COLORS["border"],
                        foreground=COLORS["text_secondary"])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["bg_card"])],
                  foreground=[("selected", COLORS["accent"])],
                  font=[("selected", FONTS["body_bold"])],
                  expand=[("selected", [1, 1, 1, 0])])

    def _bind_global_shortcuts(self):
        self.bind("<Control-1>", lambda e: self.notebook.select(0))
        self.bind("<Control-2>", lambda e: self.notebook.select(1))
        self.bind("<Control-q>", lambda e: self.on_closing())
        self.bind("<Control-Q>", lambda e: self.on_closing())

    def _on_tab_changed(self, event):
        idx = self.notebook.index("current")
        if idx == 0:
            self.title("PDF Renamer Pro — Đổi tên PDF")
        else:
            self.title("PDF Renamer Pro — Tìm trang trắng")

    def on_closing(self):
        cleanup_thumbnails()
        self.destroy()
