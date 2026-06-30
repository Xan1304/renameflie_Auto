import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from core.blank_detector import detect_blank_pages, remove_blank_pages

class FindBlankTab(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg="#F0F2F5")
        self.main_window = main_window
        self.scan_results = []   # Kết quả sau khi quét xong
        self.is_processing = False
        self.last_output_paths = {}
        self._build_ui()

    def _build_ui(self):
        # ── Khu vực cấu hình ────────────────────────────────────────
        config_card = tk.Frame(self, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        config_card.pack(fill=tk.X, padx=16, pady=(12, 8))

        inner = tk.Frame(config_card, bg="#FFFFFF")
        inner.pack(fill=tk.X, padx=16, pady=12)

        # Hàng 1: labels
        tk.Label(inner, text="Đường dẫn thư mục", fg="#6B7280",
                 bg="#FFFFFF", font=("Segoe UI", 9)).grid(
                     row=0, column=0, sticky="w")
        tk.Label(inner, text="Ngưỡng trắng (%)", fg="#6B7280",
                 bg="#FFFFFF", font=("Segoe UI", 9)).grid(
                     row=0, column=2, sticky="w", padx=(24, 0))

        # Hàng 2: controls
        folder_frame = tk.Frame(inner, bg="#FFFFFF")
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        self.lbl_folder = tk.Label(
            folder_frame,
            text="Chưa chọn thư mục",
            fg="#9CA3AF", bg="#F3F4F6",
            font=("Segoe UI", 9),
            anchor="w", padx=8,
            relief="flat", bd=1, width=50)
        self.lbl_folder.pack(side=tk.LEFT, ipady=6)

        ttk.Button(folder_frame, text="📁 Chọn thư mục",
                   command=self._select_folder).pack(
                       side=tk.LEFT, padx=(8, 0))

        # Slider ngưỡng
        slider_frame = tk.Frame(inner, bg="#FFFFFF")
        slider_frame.grid(row=1, column=2, sticky="w",
                          padx=(24, 0), pady=(2, 0))

        tk.Label(slider_frame, text="85%", fg="#9CA3AF",
                 bg="#FFFFFF", font=("Segoe UI", 8)).pack(side=tk.LEFT)

        self.threshold_var = tk.DoubleVar(value=95)
        slider = ttk.Scale(slider_frame, from_=85, to=99,
                           variable=self.threshold_var,
                           orient="horizontal", length=140)
        slider.pack(side=tk.LEFT, padx=4)

        tk.Label(slider_frame, text="99%", fg="#9CA3AF",
                 bg="#FFFFFF", font=("Segoe UI", 8)).pack(side=tk.LEFT)

        self.lbl_threshold = tk.Label(
            slider_frame, text="95%",
            fg="#1A56DB", bg="#FFFFFF",
            font=("Segoe UI", 9, "bold"))
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
            variable=self.include_marks_var
        ).grid(row=1, column=4, padx=(24, 0), sticky="w")

        inner.columnconfigure(0, weight=1)

        # ── Bảng kết quả ────────────────────────────────────────────
        table_card = tk.Frame(self, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        cols = ("check", "stt", "filename", "total_pages",
                "blank_pages", "preview", "status")
        self.tree = ttk.Treeview(table_card, columns=cols,
                                  show="headings", selectmode="browse")

        self.tree.heading("check",       text="☑")
        self.tree.heading("stt",         text="STT")
        self.tree.heading("filename",    text="Tên file")
        self.tree.heading("total_pages", text="Số trang")
        self.tree.heading("blank_pages", text="Trang trắng phát hiện")
        self.tree.heading("preview",     text="Xem trước")
        self.tree.heading("status",      text="Trạng thái")

        self.tree.column("check",       width=40,  anchor="center")
        self.tree.column("stt",         width=50,  anchor="center")
        self.tree.column("filename",    width=280, anchor="w")
        self.tree.column("total_pages", width=80,  anchor="center")
        self.tree.column("blank_pages", width=200, anchor="center")
        self.tree.column("preview",     width=80,  anchor="center")
        self.tree.column("status",      width=130, anchor="center")

        self.tree.tag_configure("even", background="#F8FAFC")
        self.tree.tag_configure("odd",  background="#FFFFFF")

        sb = ttk.Scrollbar(table_card, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<ButtonRelease-1>", self._on_click)

        self._item_data = {}  # item_id → result dict

        # ── Thanh dưới cùng ─────────────────────────────────────────
        bottom = tk.Frame(self, bg="#FFFFFF", height=90)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        # Phải: nút (Pack trước để đảm bảo đủ không gian)
        btn_frame = tk.Frame(bottom, bg="#FFFFFF")
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=12)

        self.btn_undo = ttk.Button(
            btn_frame, text="↩ Hoàn tác",
            style="Warning.TButton",
            command=self._do_undo,
            state=tk.DISABLED)
        self.btn_undo.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_save = ttk.Button(
            btn_frame, text="💾 Lưu",
            style="Success.TButton",
            command=self._do_delete,
            state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_scan = ttk.Button(
            btn_frame, text="🔍 Quét trang trắng",
            style="Primary.TButton",
            command=self._start_scan)
        self.btn_scan.pack(side=tk.RIGHT)

        # Trái: Khu vực trạng thái và lưu
        left_bottom = tk.Frame(bottom, bg="#FFFFFF")
        left_bottom.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=8)

        # Cấu hình lưu
        save_frame = tk.Frame(left_bottom, bg="#FFFFFF")
        save_frame.pack(anchor="w", pady=(0, 4))
        
        self.save_mode = tk.StringVar(value="overwrite")
        
        tk.Radiobutton(
            save_frame,
            text="Ghi đè file gốc",
            variable=self.save_mode, value="overwrite",
            bg="#FFFFFF", font=("Segoe UI", 9),
            command=self._on_mode_change).pack(side=tk.LEFT)

        self.lbl_warning = tk.Label(
            save_frame, text="(Thao tác này không thể hoàn tác)",
            fg="#DC2626", bg="#FFFFFF", font=("Segoe UI", 9, "italic")
        )
        self.lbl_warning.pack(side=tk.LEFT, padx=(4, 12))

        tk.Radiobutton(
            save_frame,
            text="Lưu vào thư mục mới",
            variable=self.save_mode, value="new_folder",
            bg="#FFFFFF", font=("Segoe UI", 9),
            command=self._on_mode_change).pack(side=tk.LEFT)
            
        tk.Label(save_frame, text="Tên thư mục:",
                 fg="#6B7280", bg="#FFFFFF",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(12, 4))

        self.entry_subfolder = ttk.Entry(save_frame, width=14)
        self.entry_subfolder.insert(0, "cleaned")
        self.entry_subfolder.pack(side=tk.LEFT)
        self.entry_subfolder.config(state=tk.DISABLED)

        # Status and progress
        self.lbl_status = tk.Label(
            left_bottom, text="Sẵn sàng",
            fg="#6B7280", bg="#FFFFFF", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            left_bottom, variable=self.progress_var,
            maximum=100,
            style="green.Horizontal.TProgressbar",
            length=300)
        self.progress.pack(anchor="w", pady=(2, 0))

    # ── Helpers ─────────────────────────────────────────────────────
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục PDF")
        if folder:
            self.current_folder = folder
            display = folder if len(folder) <= 55 else "..." + folder[-52:]
            self.lbl_folder.config(text=display, fg="#1F2937")

    def _start_scan(self):
        if self.is_processing: return
        if not hasattr(self, "current_folder") or not self.current_folder:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục trước.")
            return

        # Xóa bảng cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_data.clear()
        self.scan_results.clear()
        self.last_output_paths.clear()

        self.is_processing = True
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.btn_undo.config(state=tk.DISABLED)

        thread = threading.Thread(target=self._scan_thread, daemon=True)
        thread.start()

    def _scan_thread(self):
        folder = self.current_folder
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
            info["path"] = path
            info["checked"] = len(info["blank_pages"]) > 0

            self.after(0, self._append_row, info)
            self.scan_results.append(info)

            pct = int((i + 1) / total * 100)
            self.after(0, lambda v=pct: self.progress_var.set(v))

        self.after(0, self._finish_scan)

    def _append_row(self, info):
        blank = info["blank_pages"]
        has_blank = len(blank) > 0
        has_error = bool(info.get("error"))

        check_str  = "☑" if info["checked"] else "☐"
        blank_str  = (", ".join(f"Trang {p}" for p in blank)
                      if blank else ("N/A" if has_error else "None"))
        total_str  = str(info["total_pages"]) if not has_error else "--"
        status_str = ("🟢 Có trang trắng" if has_blank
                      else ("❌ Lỗi đọc" if has_error else "⚪ Sạch"))

        idx = len(self._item_data) + 1
        tag = "even" if idx % 2 == 0 else "odd"
        item_id = self.tree.insert(
            "", "end", tags=(tag,),
            values=(check_str, f"{idx:02d}", info["filename"],
                    total_str, blank_str, "🔍", status_str))
        self._item_data[item_id] = info

    def _update_status(self, current, total, text):
        blank_found = sum(
            1 for r in self.scan_results if r["blank_pages"])
        self.lbl_status.config(
            text=f"{text}  |  Đã tìm thấy {blank_found} file có trang trắng")

    def _finish_scan(self):
        self.is_processing = False
        self.btn_scan.config(state=tk.NORMAL)
        self._update_total_status()

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        col = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        col_idx = int(col[1:]) - 1
        data = self._item_data.get(item_id)
        if not data: return

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
                    # Cập nhật UI bảng
                    vals = list(self.tree.item(item_id, "values"))
                    blank_str = (", ".join(f"Trang {p}" for p in data["blank_pages"])
                                 if data["blank_pages"] else "None")
                    vals[4] = blank_str
                    
                    # Nếu có trang được chọn, tự động tick file đó, ngược lại bỏ tick
                    data["checked"] = len(data["blank_pages"]) > 0
                    vals[0] = "☑" if data["checked"] else "☐"
                    
                    # Update status column
                    vals[6] = "🟢 Có trang trắng" if data["blank_pages"] else "⚪ Sạch"
                    
                    self.tree.item(item_id, values=vals)
                    
                    # Cập nhật tổng số trên thanh trạng thái
                    self._update_total_status()

                MultiThumbnailDialog(
                    self.main_window, 
                    f"Xem trước: {data['filename']}", 
                    data["page_thumbnails"], 
                    detected_blanks=data.get("blank_pages", []),
                    on_confirm=on_confirm
                )

    def _update_total_status(self):
        total_files = len(self.scan_results)
        total_pages = sum(r.get("total_pages", 0) for r in self.scan_results)
        total_blank = sum(len(r.get("blank_pages", [])) for r in self.scan_results)
        
        self.lbl_status.config(
            text=f"Quét xong. Tổng cộng: {total_files} file | {total_pages} trang | {total_blank} trang trắng")
            
        has_any = any(r.get("checked") and r.get("blank_pages") for r in self.scan_results)
        self.btn_save.config(state=tk.NORMAL if has_any else tk.DISABLED)

    def _on_mode_change(self):
        if self.save_mode.get() == "new_folder":
            self.entry_subfolder.config(state=tk.NORMAL)
            self.lbl_warning.config(text="")
            if hasattr(self, 'last_output_paths') and self.last_output_paths:
                self.btn_undo.config(state=tk.NORMAL)
        else:
            self.entry_subfolder.config(state=tk.DISABLED)
            self.lbl_warning.config(text="(Thao tác này không thể hoàn tác)")
            if hasattr(self, 'btn_undo'):
                self.btn_undo.config(state=tk.DISABLED)

    def _do_delete(self):
        checked = [(iid, d) for iid, d in self._item_data.items() if d.get("checked") and d.get("blank_pages")]
        if not checked:
            messagebox.showinfo("Thông báo", "Không có file nào được chọn để xóa trang trắng.")
            return

        mode = self.save_mode.get()
        if mode == "overwrite":
            confirm = messagebox.askyesno(
                "Xác nhận",
                f"Sẽ GHI ĐÈ {len(checked)} file gốc.\nThao tác này KHÔNG THỂ hoàn tác.\n\nTiếp tục?")
            if not confirm: return

        self.btn_save.config(state=tk.DISABLED)
        self.btn_undo.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.DISABLED)
        thread = threading.Thread(
            target=self._delete_thread,
            args=(checked, mode),
            daemon=True)
        thread.start()

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
                out_dir = os.path.join(self.current_folder, subfolder)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, fname)
                ok, err = remove_blank_pages(src, blank_p, out_path)

            status = "✅ Hoàn tất" if ok else f"❌ Lỗi: {err}"
            if ok and out_path:
                self.last_output_paths[src] = {"out": out_path, "mode": mode}

            self.after(0, self._update_row_status, item_id, status)
            pct = int((i + 1) / total * 100)
            self.after(0, lambda v=pct: self.progress_var.set(v))

        self.after(0, self._finish_delete, mode)

    def _update_row_status(self, item_id, status):
        vals = list(self.tree.item(item_id, "values"))
        vals[6] = status  # Update column 6 (Status)
        self.tree.item(item_id, values=vals)

    def _finish_delete(self, mode):
        done = sum(1 for src, info in self.last_output_paths.items() if info["mode"] == mode)
        self.lbl_status.config(
            text=f"Hoàn tất! Đã lưu {done} file.")
        
        self.btn_scan.config(state=tk.NORMAL)
        
        if mode == "new_folder" and self.last_output_paths:
            self.btn_undo.config(state=tk.NORMAL)

        if done > 0:
            messagebox.showinfo("Kết quả", f"Đã xóa trang trắng thành công và lưu {done} file PDF.")
            # Clear table giống tab đổi tên
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._item_data.clear()
            self.scan_results.clear()
            self.btn_save.config(state=tk.DISABLED)
            self.lbl_status.config(text=f"Đã lưu thành công {done} file. Vui lòng quét lại nếu cần.")
        else:
            self.btn_save.config(state=tk.NORMAL)

    def _do_undo(self):
        if not self.last_output_paths: return
        confirm = messagebox.askyesno(
            "Hoàn tác",
            "Xóa các file đã tạo trong thư mục mới?")
        if not confirm: return

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
        messagebox.showinfo("Hoàn tác", f"Đã xóa {removed} file khỏi thư mục mới.")

    def get_results(self):
        return self.scan_results
