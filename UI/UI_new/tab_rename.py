import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from core.ocr import extract_pdf_info, is_tesseract_installed
from core.renamer import sort_files, generate_new_names, execute_rename, undo_last_rename
from gui.table import CustomTable
from gui.dialogs import ThumbnailDialog

# [THAY ĐỔI] Import palette tập trung từ main_window thay vì hard-code màu rải rác
from gui.main_window import COLORS, FONTS


class RenameTab(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=COLORS["bg_app"])
        self.main_window = main_window

        self.current_folder = ""
        self.pdf_files = []
        self.is_processing = False
        self.cancel_scan = False

        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────
    def _build_ui(self):
        # ══ WELCOME FRAME ══════════════════════════════════════════
        # Hiện khi chưa chọn thư mục
        self.welcome_frame = tk.Frame(self, bg=COLORS["bg_app"])
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        self._build_welcome(self.welcome_frame)

        # ══ MAIN FRAME ═════════════════════════════════════════════
        # Hiện sau khi đã chọn thư mục
        self.main_frame = tk.Frame(self, bg=COLORS["bg_app"])
        # (chưa pack — sẽ pack khi select_folder được gọi)

        self._build_config_card(self.main_frame)
        self._build_table_card(self.main_frame)
        self._build_bottom_bar(self.main_frame)

    # ── Welcome ──────────────────────────────────────────────────
    def _build_welcome(self, parent):
        """[THAY ĐỔI] Welcome được đặt ở giữa màn hình với layout cân đối hơn."""
        center = tk.Frame(parent, bg=COLORS["bg_app"])
        center.place(relx=0.5, rely=0.42, anchor="center")

        # Biểu tượng lớn
        # [THAY ĐỔI] Thêm icon frame để tạo visual interest
        icon_bg = tk.Frame(center,
                           bg=COLORS["accent_light"],
                           width=72, height=72)
        icon_bg.pack(pady=(0, 16))
        icon_bg.pack_propagate(False)
        tk.Label(icon_bg,
                 text="📄",
                 font=("Segoe UI", 32),
                 bg=COLORS["accent_light"]).place(relx=0.5, rely=0.5, anchor="center")

        # Tiêu đề
        tk.Label(center,
                 text="PDF Renamer Pro",
                 font=FONTS["welcome"],
                 fg=COLORS["text_primary"],
                 bg=COLORS["bg_app"]).pack()

        # Mô tả ngắn
        # [THAY ĐỔI] Thêm subtitle để người dùng mới hiểu ngay chức năng
        tk.Label(center,
                 text="Chọn thư mục để tải và xử lý hàng loạt file PDF",
                 font=FONTS["small"],
                 fg=COLORS["text_secondary"],
                 bg=COLORS["bg_app"]).pack(pady=(4, 20))

        ttk.Button(center,
                   text="📁  Chọn thư mục để bắt đầu",
                   style="Primary.TButton",
                   command=self.select_folder).pack(ipady=6, ipadx=8)

        # [THAY ĐỔI] Thêm gợi ý phím tắt bên dưới nút
        tk.Label(center,
                 text="Hoặc nhấn Ctrl+1 để trở lại tab này",
                 font=FONTS["caption"],
                 fg=COLORS["text_muted"],
                 bg=COLORS["bg_app"]).pack(pady=(8, 0))

    # ── Config Card ────────────────────────────────────────────────
    def _build_config_card(self, parent):
        """[THAY ĐỔI] Card cấu hình — gom nhóm các control liên quan, border rõ ràng."""
        card = tk.Frame(parent,
                        bg=COLORS["bg_card"],
                        relief="flat", bd=0,
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill=tk.X, padx=16, pady=(12, 0))

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill=tk.X, padx=16, pady=12)

        # ── HÀNG NHÃN (labels phía trên) ────────────────────────
        lbl_cfg = [
            ("Tiền tố",       0),
            ("Số bắt đầu",    2),
            ("Sắp xếp theo",  4),
            ("Thư mục nguồn", 6),
        ]
        for text, col in lbl_cfg:
            tk.Label(inner, text=text,
                     fg=COLORS["text_secondary"],
                     bg=COLORS["bg_card"],
                     font=FONTS["small"]).grid(
                         row=0, column=col, sticky="w",
                         padx=(0 if col == 0 else 16, 0))

        # ── HÀNG CONTROLS ──────────────────────────────────────
        # Tiền tố
        self.entry_prefix = ttk.Entry(inner, width=36, font=FONTS["body"])
        self.entry_prefix.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        # [THAY ĐỔI] Placeholder text gợi ý (giả lập với FocusIn/FocusOut)
        self._add_placeholder(self.entry_prefix, "VD: QĐ-UBND, CV-PNV...")

        # Số bắt đầu
        self.entry_start = ttk.Entry(inner, width=10, font=FONTS["body"])
        self.entry_start.grid(row=1, column=2, sticky="ew",
                              padx=(16, 0), pady=(3, 0))
        self.entry_start.insert(0, "001")

        # Sắp xếp
        self.cb_sort = ttk.Combobox(
            inner,
            values=["Tên file gốc", "Ngày sửa file",
                    "Số ký hiệu", "Ngày văn bản", "Số trang"],
            state="readonly", width=16, font=FONTS["body"])
        self.cb_sort.current(0)
        self.cb_sort.grid(row=1, column=4, sticky="ew",
                          padx=(16, 0), pady=(3, 0))
        self.cb_sort.bind("<<ComboboxSelected>>",
                          lambda e: self.re_sort_table())

        # Thư mục nguồn
        folder_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        folder_frame.grid(row=1, column=6, sticky="ew",
                          padx=(16, 0), pady=(3, 0))

        # [THAY ĐỔI] Nút chọn thư mục dùng Secondary style (outline) thay vì default
        ttk.Button(folder_frame, text="📁 Đổi",
                   style="Secondary.TButton",
                   command=self.select_folder,
                   width=7).pack(side=tk.LEFT)

        self.lbl_folder = tk.Label(
            folder_frame,
            text="Chưa chọn",
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
            font=FONTS["small"],
            anchor="w",
            width=24)
        self.lbl_folder.pack(side=tk.LEFT, padx=(8, 0))

        # ── KeyRelease bindings ──────────────────────────────────
        self.entry_prefix.bind("<KeyRelease>",
                               lambda e: self.recalculate_table())
        self.entry_start.bind("<KeyRelease>",
                              lambda e: self.recalculate_table())

        inner.columnconfigure(0, weight=3)
        inner.columnconfigure(2, weight=1)
        inner.columnconfigure(4, weight=2)
        inner.columnconfigure(6, weight=3)

    # ── Table Card ─────────────────────────────────────────────────
    def _build_table_card(self, parent):
        """Bảng danh sách file PDF."""
        # [THAY ĐỔI] Card bao quanh bảng với border rõ — tách biệt với bg
        card = tk.Frame(parent,
                        bg=COLORS["bg_card"],
                        relief="flat", bd=0,
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 0))

        self.table = CustomTable(card, self.recalculate_table, self.view_thumbnail)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # [THAY ĐỔI] Scrollbar styling — dùng ttk để đồng bộ theme
        scrollbar = ttk.Scrollbar(card, orient="vertical",
                                  command=self.table.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.configure(yscrollcommand=scrollbar.set)

        # [THAY ĐỔI] Mousewheel scroll trên bảng
        self.table.bind("<MouseWheel>",
                        lambda e: self.table.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))

    # ── Bottom Bar ────────────────────────────────────────────────
    def _build_bottom_bar(self, parent):
        """[THAY ĐỔI] Bottom bar có chiều cao cố định, separator ở trên."""
        # Đường kẻ phân cách
        sep = tk.Frame(parent, bg=COLORS["border"], height=1)
        sep.pack(fill=tk.X, padx=16)

        bottom = tk.Frame(parent, bg=COLORS["bg_card"], height=68)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        # ── Nút bên phải ──────────────────────────────────────────
        btn_frame = tk.Frame(bottom, bg=COLORS["bg_card"])
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=14)

        self.btn_undo = ttk.Button(
            btn_frame, text="↩  Hoàn tác",
            style="Warning.TButton",
            command=self.do_undo,
            state=tk.DISABLED)
        self.btn_undo.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_rename = ttk.Button(
            btn_frame, text="✏  Đổi tên ngay",
            style="Success.TButton",
            command=self.do_rename,
            state=tk.DISABLED)
        self.btn_rename.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_scan = ttk.Button(
            btn_frame, text="🔍  Quét & Preview",
            style="Primary.TButton",
            command=self.start_scan)
        self.btn_scan.pack(side=tk.RIGHT)

        # ── Trạng thái bên trái ────────────────────────────────────
        status_frame = tk.Frame(bottom, bg=COLORS["bg_card"])
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True,
                          padx=20, pady=10)

        self.lbl_status = tk.Label(
            status_frame,
            text="Sẵn sàng",
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_card"],
            font=FONTS["small"],
            anchor="w")
        self.lbl_status.pack(anchor="w")

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            maximum=100,
            style="Corporate.Horizontal.TProgressbar",
            length=320)                 # [THAY ĐỔI] 300→320
        self.progress.pack(anchor="w", pady=(4, 0))

        # [THAY ĐỔI] Gợi ý phím tắt inline trong bottom bar
        tk.Label(status_frame,
                 text="Ctrl+1 / Ctrl+2 — chuyển tab nhanh",
                 font=FONTS["caption"],
                 fg=COLORS["text_muted"],
                 bg=COLORS["bg_card"]).pack(anchor="w", pady=(2, 0))

    # ── Helpers ──────────────────────────────────────────────────
    def _add_placeholder(self, entry, placeholder_text):
        """[THAY ĐỔI] Thêm placeholder vào Entry (Tkinter không có sẵn)."""
        entry.insert(0, placeholder_text)
        entry.config(foreground=COLORS["text_muted"])

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(foreground=COLORS["text_primary"])

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder_text)
                entry.config(foreground=COLORS["text_muted"])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _get_prefix(self):
        """Lấy tiền tố, bỏ qua nếu đang là placeholder."""
        val = self.entry_prefix.get()
        placeholders = ["VD: QĐ-UBND, CV-PNV..."]
        if val in placeholders:
            return ""
        return val

    # ── Logic (giữ nguyên, chỉ cập nhật style calls) ──────────────
    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Chọn thư mục chứa file PDF")
        if folder:
            self.current_folder = folder
            # [THAY ĐỔI] Hiển thị đường dẫn rút gọn thông minh hơn
            display = (folder if len(folder) <= 38
                       else "…" + folder[-35:])
            self.lbl_folder.config(
                text=display,
                fg=COLORS["text_primary"])

            self.welcome_frame.pack_forget()
            self.main_frame.pack(fill=tk.BOTH, expand=True,
                                 padx=0, pady=0)

            self.load_files_fast()

    def load_files_fast(self):
        self.pdf_files = [
            os.path.join(self.current_folder, f)
            for f in os.listdir(self.current_folder)
            if f.lower().endswith(".pdf")]

        count = len(self.pdf_files)
        self.lbl_status.config(
            text=f"Đã tải {count} file PDF.")
        self.table.clear_all()

        results = []
        for pdf_path in self.pdf_files:
            file_data = {
                "path":           pdf_path,
                "old_name":       os.path.basename(pdf_path),
                "so_kh":          None,
                "ngay_vb":        None,
                "so_trang":       None,
                "mtime":          os.path.getmtime(pdf_path),
                "thumbnail_path": None,
                "checked":        True,
                "manual_edit":    False,
                "crop_sokh_path": None,
                "crop_ngay_path": None,
                "crop_trang_path": None,
                "status_text":    "Chưa quét",
                "status_code":    "idle",
                "ngay_str":       ""
            }
            results.append(file_data)

        for data in results:
            self.table.insert_row(data)

        self.re_sort_table()
        self.btn_rename.config(
            state=tk.NORMAL if results else tk.DISABLED)

    def start_scan(self):
        all_data = self.table.get_all_data()
        if not all_data:
            messagebox.showinfo(
                "Thông báo",
                "Vui lòng chọn thư mục có chứa file PDF trước.")
            return

        if self.is_processing:
            self.cancel_scan = True
            self.btn_scan.config(text="Đang dừng…", state=tk.DISABLED)
            return

        if not is_tesseract_installed():
            resp = messagebox.askyesno(
                "Cảnh báo",
                "Không tìm thấy Tesseract OCR.\n"
                "OCR sẽ bị bỏ qua, bạn vẫn có thể tự sửa tên.\n\n"
                "Bạn có muốn tiếp tục?")
            if not resp:
                return

        self.is_processing = True
        self.cancel_scan = False
        # [THAY ĐỔI] Text nút rõ hơn khi đang chạy
        self.btn_scan.config(text="⏹  Dừng quét",
                             style="Warning.TButton")
        self.btn_rename.config(state=tk.DISABLED)
        self.progress_var.set(0)

        threading.Thread(
            target=self.scan_thread,
            args=(all_data,),
            daemon=True).start()

    def scan_thread(self, all_data):
        total = len(all_data)

        for i, data in enumerate(all_data):
            if self.cancel_scan:
                break

            pdf_path = data["path"]
            info = extract_pdf_info(pdf_path)

            data["so_kh"]          = info.get("so_kh")
            data["ngay_vb"]        = info.get("ngay_vb")
            data["so_trang"]       = info.get("so_trang")
            data["thumbnail_path"] = info.get("thumbnail_path")
            data["crop_sokh_path"] = info.get("crop_sokh_path")
            data["crop_ngay_path"] = info.get("crop_ngay_path")
            data["crop_trang_path"]= info.get("crop_trang_path")

            if info.get("error"):
                data["status_text"] = "❌ Lỗi đọc"
                data["status_code"] = "error"
            elif info.get("so_kh"):
                data["status_text"] = "✅ Sẵn sàng"  # [THAY ĐỔI] 🟢→✅ nhất quán
                data["status_code"] = "ok"
                data["ngay_str"] = (
                    info["ngay_vb"].strftime("%d/%m/%Y")
                    if info.get("ngay_vb") else "")
            elif info.get("ngay_vb"):
                data["status_text"] = "🔵 Dùng ngày"
                data["status_code"] = "ok"
                data["ngay_str"] = info["ngay_vb"].strftime("%d/%m/%Y")
            else:
                data["status_text"] = "⚠ Không đọc được KH"  # [THAY ĐỔI] 🔴→⚠
                data["status_code"] = "warn"
                data["ngay_str"] = ""

            self.after(0, self.table.update_row_by_data, data)

            pct = int((i + 1) / total * 100)
            self.after(0, self.update_progress,
                       pct, f"Đang quét {i+1}/{total} file…")

        self.after(0, self.finish_scan)

    def update_progress(self, val, text):
        self.progress_var.set(val)
        self.lbl_status.config(text=text)

    def finish_scan(self):
        self.re_sort_table()

        self.is_processing = False
        self.btn_scan.config(
            text="🔍  Quét & Preview",
            style="Primary.TButton",
            state=tk.NORMAL)
        self.btn_rename.config(state=tk.NORMAL)

        if self.cancel_scan:
            self.lbl_status.config(
                text="Đã dừng quét. Vui lòng kiểm tra lại bảng.")
        else:
            self.lbl_status.config(
                text="Quét hoàn tất. Vui lòng kiểm tra tên file trước khi Đổi tên.")

    def re_sort_table(self):
        all_data = self.table.get_all_data()
        if not all_data:
            return

        sort_mode = self.cb_sort.get()

        if sort_mode == "Tên file gốc":
            def sort_key(item):
                return item.get("old_name", "").lower()
        elif sort_mode == "Số ký hiệu":
            def sort_key(item):
                return (
                    item.get("so_kh") if item.get("so_kh") is not None
                    else float("inf"),
                    item.get("ngay_vb") or datetime.max,
                    item.get("mtime", 0))
        elif sort_mode == "Ngày văn bản":
            def sort_key(item):
                return (
                    item.get("ngay_vb") or datetime.max,
                    item.get("so_kh") if item.get("so_kh") is not None
                    else float("inf"),
                    item.get("mtime", 0))
        elif sort_mode == "Số trang":
            def sort_key(item):
                return (
                    item.get("so_trang") if item.get("so_trang") is not None
                    else float("inf"),
                    item.get("so_kh") if item.get("so_kh") is not None
                    else float("inf"),
                    item.get("mtime", 0))
        else:  # Ngày sửa file
            def sort_key(item):
                return (
                    item.get("mtime", 0),
                    item.get("so_kh") if item.get("so_kh") is not None
                    else float("inf"),
                    item.get("ngay_vb") or datetime.max)

        sorted_data = sorted(all_data, key=sort_key)
        self.table.clear_all()
        for data in sorted_data:
            self.table.insert_row(data)
        self.recalculate_table()

    def recalculate_table(self):
        prefix = self._get_prefix()   # [THAY ĐỔI] Dùng helper để bỏ placeholder
        start_num_str = self.entry_start.get()

        all_data = self.table.get_all_data()
        new_names = generate_new_names(all_data, prefix, start_num_str)

        stt = 1
        for i, item_id in enumerate(self.table.get_children()):
            data = all_data[i]
            if data.get("checked", True):
                data["stt"] = str(stt)
                stt += 1
                if not data.get("manual_edit"):
                    data["new_name"] = new_names[i]
            else:
                data["stt"] = "-"
                data["new_name"] = "-"
            self.table.update_row_display(item_id)

    def do_rename(self):
        all_data = self.table.get_all_data()
        rename_plan = []

        for data in all_data:
            if (data.get("checked", True)
                    and data.get("new_name")
                    and data.get("new_name") != "-"):
                old_p = data["path"]
                new_p = os.path.join(self.current_folder, data["new_name"])
                rename_plan.append({"old_path": old_p, "new_path": new_p})

        if not rename_plan:
            messagebox.showinfo(
                "Thông báo",
                "Không có file nào được chọn để đổi tên.")
            return

        # [THAY ĐỔI] Thêm xác nhận trước khi đổi tên hàng loạt
        confirm = messagebox.askyesno(
            "Xác nhận đổi tên",
            f"Sẽ đổi tên {len(rename_plan)} file.\n\nBạn có muốn tiếp tục?")
        if not confirm:
            return

        success, errors = execute_rename(rename_plan, self.current_folder)

        msg = f"Đã đổi tên thành công {success} file."
        if errors:
            msg += "\n\nCó lỗi xảy ra:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n…"

        messagebox.showinfo("Kết quả", msg)

        if success > 0:
            self.btn_undo.config(state=tk.NORMAL)
            self.load_files_fast()

    def do_undo(self):
        resp = messagebox.askyesno(
            "Xác nhận",
            "Bạn có chắc muốn hoàn tác lần đổi tên vừa rồi?")
        if resp:
            success, errors = undo_last_rename()
            msg = f"Đã khôi phục {success} file."
            if errors:
                msg += "\nLỗi:\n" + "\n".join(errors)
            messagebox.showinfo("Hoàn tác", msg)
            self.btn_undo.config(state=tk.DISABLED)

    def view_thumbnail(self, img_path):
        if os.path.exists(img_path):
            ThumbnailDialog(self.main_window, img_path)
