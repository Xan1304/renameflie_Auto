import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from core.blank_detector import detect_blank_pages, remove_blank_pages
from gui.main_window import COLORS, FONTS  # [THAY ĐỔI] Palette tập trung


class FindBlankTab(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=COLORS["bg_app"])
        self.main_window = main_window
        self.current_folder = ""
        self.scan_results = []
        self.is_processing = False
        self.last_output_paths = {}
        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_config_card()
        self._build_table_card()
        self._build_bottom_bar()

    # ── Config Card ────────────────────────────────────────────────
    def _build_config_card(self):
        """[THAY ĐỔI] Card cấu hình đồng bộ với tab Đổi tên: border nhất quán."""
        card = tk.Frame(self,
                        bg=COLORS["bg_card"],
                        relief="flat", bd=0,
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill=tk.X, padx=16, pady=(12, 0))

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill=tk.X, padx=16, pady=12)

        # ── Nhãn hàng trên ──────────────────────────────────────
        tk.Label(inner, text="Đường dẫn thư mục",
                 fg=COLORS["text_secondary"],
                 bg=COLORS["bg_card"],
                 font=FONTS["small"]).grid(
                     row=0, column=0, sticky="w")

        tk.Label(inner, text="Ngưỡng phát hiện trang trắng (%)",
                 fg=COLORS["text_secondary"],
                 bg=COLORS["bg_card"],
                 font=FONTS["small"]).grid(
                     row=0, column=2, sticky="w", padx=(24, 0))

        # ── Controls hàng dưới ──────────────────────────────────
        # Thư mục
        folder_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        self.lbl_folder = tk.Label(
            folder_frame,
            text="Chưa chọn thư mục",
            fg=COLORS["text_muted"],
            bg="#F3F4F6",
            font=FONTS["small"],
            anchor="w", padx=8,
            relief="flat", bd=0,
            width=48)
        self.lbl_folder.pack(side=tk.LEFT, ipady=7)

        # [THAY ĐỔI] Nút Chọn thư mục dùng Secondary style nhất quán
        ttk.Button(folder_frame,
                   text="📁  Chọn thư mục",
                   style="Secondary.TButton",
                   command=self._select_folder).pack(
                       side=tk.LEFT, padx=(8, 0))

        # Slider ngưỡng
        slider_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        slider_frame.grid(row=1, column=2, sticky="w",
                          padx=(24, 0), pady=(3, 0))

        tk.Label(slider_frame, text="85%",
                 fg=COLORS["text_muted"],
                 bg=COLORS["bg_card"],
                 font=FONTS["caption"]).pack(side=tk.LEFT)

        self.threshold_var = tk.DoubleVar(value=95)
        slider = ttk.Scale(
            slider_frame, from_=85, to=99,
            variable=self.threshold_var,
            orient="horizontal", length=150)  # [THAY ĐỔI] 140→150
        slider.pack(side=tk.LEFT, padx=4)

        tk.Label(slider_frame, text="99%",
                 fg=COLORS["text_muted"],
                 bg=COLORS["bg_card"],
                 font=FONTS["caption"]).pack(side=tk.LEFT)

        # [THAY ĐỔI] Badge hiển thị giá trị ngưỡng — nổi bật hơn
        self.lbl_threshold = tk.Label(
            slider_frame, text="95%",
            fg=COLORS["text_inverse"],
            bg=COLORS["accent"],
            font=FONTS["small_it"],
            padx=6, pady=2, bd=0)
        self.lbl_threshold.pack(side=tk.LEFT, padx=(8, 0))

        self.threshold_var.trace_add(
            "write",
            lambda *a: self.lbl_threshold.config(
                text=f"{int(self.threshold_var.get())}%"))

        # Checkbox vết mực nhỏ
        self.include_marks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            inner,
            text="Bao gồm vết mực nhỏ",
            variable=self.include_marks_var,
            style="TCheckbutton"
        ).grid(row=1, column=4, padx=(24, 0), sticky="w")

        inner.columnconfigure(0, weight=1)

    # ── Table Card ─────────────────────────────────────────────────
    def _build_table_card(self):
        """[THAY ĐỔI] Bảng kết quả — chiều rộng cột được điều chỉnh hợp lý hơn."""
        card = tk.Frame(self,
                        bg=COLORS["bg_card"],
                        relief="flat", bd=0,
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 0))

        cols = ("check", "stt", "filename", "total_pages",
                "blank_pages", "preview", "status")
        self.tree = ttk.Treeview(
            card, columns=cols,
            show="headings", selectmode="browse")

        # ── Headings ──────────────────────────────────────────────
        headings = {
            "check":       ("☑",                  40,  "center"),
            "stt":         ("STT",                 50,  "center"),
            "filename":    ("Tên file",            290, "w"),
            "total_pages": ("Số trang",             80, "center"),
            "blank_pages": ("Trang trắng phát hiện", 220, "center"), # [THAY ĐỔI] 200→220
            "preview":     ("Xem trước",            90, "center"),   # [THAY ĐỔI] 80→90
            "status":      ("Trạng thái",          140, "center"),
        }
        for col, (text, width, anchor) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor,
                             minwidth=40)

        # [THAY ĐỔI] Tags màu nhất quán với tab Đổi tên
        self.tree.tag_configure("even", background=COLORS["bg_table_alt"])
        self.tree.tag_configure("odd",  background=COLORS["bg_card"])

        sb = ttk.Scrollbar(card, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<ButtonRelease-1>", self._on_click)

        # [THAY ĐỔI] Mousewheel scroll
        self.tree.bind(
            "<MouseWheel>",
            lambda e: self.tree.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))

        self._item_data = {}

    # ── Bottom Bar ─────────────────────────────────────────────────
    def _build_bottom_bar(self):
        """[THAY ĐỔI] Bottom bar đồng bộ với tab Đổi tên: separator + bg trắng."""
        sep = tk.Frame(self, bg=COLORS["border"], height=1)
        sep.pack(fill=tk.X, padx=16, side=tk.BOTTOM, before=None)

        # Sử dụng pack thay vì side=BOTTOM để tránh đè lên card bảng
        bottom = tk.Frame(self, bg=COLORS["bg_card"], height=90)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        # ── Nút bên phải ─────────────────────────────────────────
        btn_frame = tk.Frame(bottom, bg=COLORS["bg_card"])
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=14)

        self.btn_undo = ttk.Button(
            btn_frame, text="↩  Hoàn tác",
            style="Warning.TButton",
            command=self._do_undo,
            state=tk.DISABLED)
        self.btn_undo.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_save = ttk.Button(
            btn_frame, text="💾  Lưu",
            style="Success.TButton",
            command=self._do_delete,
            state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_scan = ttk.Button(
            btn_frame, text="🔍  Quét trang trắng",
            style="Primary.TButton",
            command=self._start_scan)
        self.btn_scan.pack(side=tk.RIGHT)

        # ── Cấu hình lưu + trạng thái bên trái ──────────────────
        left_bottom = tk.Frame(bottom, bg=COLORS["bg_card"])
        left_bottom.pack(side=tk.LEFT, fill=tk.BOTH,
                         expand=True, padx=20, pady=8)

        # Radio lưu file
        save_frame = tk.Frame(left_bottom, bg=COLORS["bg_card"])
        save_frame.pack(anchor="w", pady=(0, 4))

        self.save_mode = tk.StringVar(value="overwrite")

        # [THAY ĐỔI] Dùng tk.Radiobutton với fg nhất quán
        rb_style = dict(
            variable=self.save_mode,
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            font=FONTS["small"],
            activebackground=COLORS["bg_card"],
            command=self._on_mode_change)

        tk.Radiobutton(
            save_frame,
            text="Ghi đè file gốc",
            value="overwrite",
            **rb_style).pack(side=tk.LEFT)

        self.lbl_warning = tk.Label(
            save_frame,
            text="(Không thể hoàn tác)",
            fg=COLORS["btn_danger"],
            bg=COLORS["bg_card"],
            font=FONTS["small_it"])
        self.lbl_warning.pack(side=tk.LEFT, padx=(4, 12))

        tk.Radiobutton(
            save_frame,
            text="Lưu vào thư mục mới",
            value="new_folder",
            **rb_style).pack(side=tk.LEFT)

        tk.Label(save_frame,
                 text="Tên thư mục:",
                 fg=COLORS["text_secondary"],
                 bg=COLORS["bg_card"],
                 font=FONTS["small"]).pack(side=tk.LEFT, padx=(12, 4))

        self.entry_subfolder = ttk.Entry(save_frame, width=14)
        self.entry_subfolder.insert(0, "cleaned")
        self.entry_subfolder.pack(side=tk.LEFT)
        self.entry_subfolder.config(state=tk.DISABLED)

        # Trạng thái & Progressbar
        self.lbl_status = tk.Label(
            left_bottom,
            text="Sẵn sàng",
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_card"],
            font=FONTS["small"],
            anchor="w")
        self.lbl_status.pack(anchor="w")

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            left_bottom,
            variable=self.progress_var,
            maximum=100,
            style="Corporate.Horizontal.TProgressbar",
            length=320)
        self.progress.pack(anchor="w", pady=(2, 0))

    # ── Helpers ──────────────────────────────────────────────────
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục PDF")
        if folder:
            self.current_folder = folder
            display = (folder if len(folder) <= 55
                       else "…" + folder[-52:])
            self.lbl_folder.config(
                text=display,
                fg=COLORS["text_primary"])

    def _start_scan(self):
        if self.is_processing:
            return
        if not self.current_folder:
            messagebox.showwarning("Cảnh báo",
                                   "Vui lòng chọn thư mục trước.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_data.clear()
        self.scan_results.clear()
        self.last_output_paths.clear()

        self.is_processing = True
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.btn_undo.config(state=tk.DISABLED)

        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        folder    = self.current_folder
        threshold = self.threshold_var.get() / 100.0
        include_marks = self.include_marks_var.get()

        pdf_files = sorted([
            f for f in os.listdir(folder)
            if f.lower().endswith(".pdf")])
        total = len(pdf_files)

        for i, fname in enumerate(pdf_files):
            path = os.path.join(folder, fname)
            self.after(0, self._update_status,
                       i + 1, total,
                       f"Đang quét {i+1}/{total}: {fname}")

            info = detect_blank_pages(path, threshold, include_marks)
            info["filename"] = fname
            info["path"]     = path
            info["checked"]  = len(info["blank_pages"]) > 0

            self.after(0, self._append_row, info)
            self.scan_results.append(info)

            pct = int((i + 1) / total * 100)
            self.after(0, lambda v=pct: self.progress_var.set(v))

        self.after(0, self._finish_scan)

    def _append_row(self, info):
        blank    = info["blank_pages"]
        has_blank = len(blank) > 0
        has_error = bool(info.get("error"))

        check_str  = "☑" if info["checked"] else "☐"
        blank_str  = (
            ", ".join(f"Trang {p}" for p in blank)
            if blank else ("N/A" if has_error else "—"))
        total_str  = str(info["total_pages"]) if not has_error else "--"
        # [THAY ĐỔI] Status text nhất quán với tab Đổi tên
        status_str = ("✅ Có trang trắng" if has_blank
                      else ("❌ Lỗi đọc" if has_error else "⚪ Sạch"))

        idx = len(self._item_data) + 1
        tag = "even" if idx % 2 == 0 else "odd"
        item_id = self.tree.insert(
            "", "end", tags=(tag,),
            values=(check_str, f"{idx:02d}", info["filename"],
                    total_str, blank_str, "🔍", status_str))
        self._item_data[item_id] = info

    def _update_status(self, current, total, text):
        blank_found = sum(1 for r in self.scan_results if r["blank_pages"])
        self.lbl_status.config(
            text=f"{text}  |  Tìm thấy {blank_found} file có trang trắng")

    def _finish_scan(self):
        self.is_processing = False
        self.btn_scan.config(state=tk.NORMAL)
        self._update_total_status()

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col     = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        col_idx = int(col[1:]) - 1
        data = self._item_data.get(item_id)
        if not data:
            return

        # Cột checkbox (0)
        if col_idx == 0:
            data["checked"] = not data["checked"]
            vals = list(self.tree.item(item_id, "values"))
            vals[0] = "☑" if data["checked"] else "☐"
            self.tree.item(item_id, values=vals)
            self._update_total_status()

        # Cột xem trước (5)
        elif col_idx == 5:
            if data.get("page_thumbnails"):
                from gui.dialogs import MultiThumbnailDialog

                def on_confirm(selected_pages):
                    data["blank_pages"] = sorted(selected_pages)
                    vals = list(self.tree.item(item_id, "values"))
                    blank_str = (
                        ", ".join(f"Trang {p}" for p in data["blank_pages"])
                        if data["blank_pages"] else "—")
                    vals[4] = blank_str
                    data["checked"] = len(data["blank_pages"]) > 0
                    vals[0] = "☑" if data["checked"] else "☐"
                    vals[6] = ("✅ Có trang trắng"
                               if data["blank_pages"] else "⚪ Sạch")
                    self.tree.item(item_id, values=vals)
                    self._update_total_status()

                MultiThumbnailDialog(
                    self.main_window,
                    f"Xem trước: {data['filename']}",
                    data["page_thumbnails"],
                    detected_blanks=data.get("blank_pages", []),
                    on_confirm=on_confirm)

    def _update_total_status(self):
        total_files = len(self.scan_results)
        total_pages = sum(r.get("total_pages", 0) for r in self.scan_results)
        total_blank = sum(len(r.get("blank_pages", [])) for r in self.scan_results)

        self.lbl_status.config(
            text=(f"Quét xong — "
                  f"{total_files} file  |  "
                  f"{total_pages} trang  |  "
                  f"{total_blank} trang trắng"))  # [THAY ĐỔI] Dấu ngăn cách rõ hơn

        has_any = any(
            r.get("checked") and r.get("blank_pages")
            for r in self.scan_results)
        self.btn_save.config(state=tk.NORMAL if has_any else tk.DISABLED)

    def _on_mode_change(self):
        if self.save_mode.get() == "new_folder":
            self.entry_subfolder.config(state=tk.NORMAL)
            self.lbl_warning.config(text="")
            if self.last_output_paths:
                self.btn_undo.config(state=tk.NORMAL)
        else:
            self.entry_subfolder.config(state=tk.DISABLED)
            self.lbl_warning.config(text="(Không thể hoàn tác)")
            self.btn_undo.config(state=tk.DISABLED)

    def _do_delete(self):
        checked = [
            (iid, d) for iid, d in self._item_data.items()
            if d.get("checked") and d.get("blank_pages")]
        if not checked:
            messagebox.showinfo(
                "Thông báo",
                "Không có file nào được chọn để xóa trang trắng.")
            return

        mode = self.save_mode.get()
        if mode == "overwrite":
            confirm = messagebox.askyesno(
                "Xác nhận ghi đè",
                f"Sẽ GHI ĐÈ {len(checked)} file gốc.\n"
                f"Thao tác này KHÔNG THỂ hoàn tác.\n\nTiếp tục?")
            if not confirm:
                return

        self.btn_save.config(state=tk.DISABLED)
        self.btn_undo.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.DISABLED)
        threading.Thread(
            target=self._delete_thread,
            args=(checked, mode),
            daemon=True).start()

    def _delete_thread(self, checked_items, mode):
        subfolder = self.entry_subfolder.get().strip() or "cleaned"
        total = len(checked_items)
        self.last_output_paths.clear()

        for i, (item_id, data) in enumerate(checked_items):
            fname   = data["filename"]
            src     = data["path"]
            blank_p = data["blank_pages"]

            self.after(0, self.lbl_status.config,
                       {"text": f"Đang xử lý {i+1}/{total}: {fname}"})

            if mode == "overwrite":
                import tempfile, shutil
                tmp = src + ".tmp_clean.pdf"
                ok, err = remove_blank_pages(src, blank_p, tmp)
                if ok:
                    shutil.move(tmp, src)
                    out_path = src
                else:
                    out_path = None
            else:
                out_dir  = os.path.join(self.current_folder, subfolder)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, fname)
                ok, err  = remove_blank_pages(src, blank_p, out_path)

            status = "✅ Hoàn tất" if ok else f"❌ Lỗi: {err}"
            if ok and out_path:
                self.last_output_paths[src] = {"out": out_path, "mode": mode}

            self.after(0, self._update_row_status, item_id, status)
            pct = int((i + 1) / total * 100)
            self.after(0, lambda v=pct: self.progress_var.set(v))

        self.after(0, self._finish_delete, mode)

    def _update_row_status(self, item_id, status):
        vals = list(self.tree.item(item_id, "values"))
        vals[6] = status
        self.tree.item(item_id, values=vals)

    def _finish_delete(self, mode):
        done = sum(
            1 for src, info in self.last_output_paths.items()
            if info["mode"] == mode)
        self.lbl_status.config(text=f"Hoàn tất! Đã lưu {done} file.")
        self.btn_scan.config(state=tk.NORMAL)

        if done > 0:
            messagebox.showinfo(
                "Kết quả",
                f"Đã xóa trang trắng và lưu {done} file PDF thành công.")
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._item_data.clear()
            self.scan_results.clear()
            self.btn_save.config(state=tk.DISABLED)
            self.lbl_status.config(
                text=f"Đã lưu {done} file. Quét lại nếu cần.")
        else:
            self.btn_save.config(state=tk.NORMAL)

        if mode == "new_folder" and self.last_output_paths:
            self.btn_undo.config(state=tk.NORMAL)

    def _do_undo(self):
        if not self.last_output_paths:
            return
        confirm = messagebox.askyesno(
            "Hoàn tác",
            "Xóa các file đã tạo trong thư mục mới?")
        if not confirm:
            return

        removed = 0
        for src, info in self.last_output_paths.items():
            if info["mode"] == "new_folder":
                try:
                    if os.path.exists(info["out"]):
                        os.remove(info["out"])
                        removed += 1
                except Exception:
                    pass

        self.last_output_paths.clear()
        self.btn_undo.config(state=tk.DISABLED)
        messagebox.showinfo("Hoàn tác",
                            f"Đã xóa {removed} file khỏi thư mục mới.")

    def get_results(self):
        return self.scan_results
