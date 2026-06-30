import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from core.ocr import extract_pdf_info, is_tesseract_installed
from core.renamer import sort_files, generate_new_names, execute_rename, undo_last_rename
from gui.table import CustomTable
from gui.dialogs import ThumbnailDialog

class RenameTab(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg="#F0F2F5")
        self.main_window = main_window
        
        self.current_folder = ""
        self.pdf_files = []
        self.is_processing = False
        self.cancel_scan = False
        
        self._build_ui()

    def _build_ui(self):
        # ── Welcome Frame ──
        self.welcome_frame = tk.Frame(self, bg="#F0F2F5")
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        inner_welcome = tk.Frame(self.welcome_frame, bg="#F0F2F5")
        inner_welcome.place(relx=0.5, rely=0.4, anchor="center")
        
        lbl_title = tk.Label(inner_welcome, text="PDF Renamer Pro", font=("Segoe UI", 24, "bold"), fg="#1F2937", bg="#F0F2F5")
        lbl_title.pack(pady=(0, 20))
        
        btn_big_select = ttk.Button(inner_welcome, text="📁 Chọn thư mục để bắt đầu", style="Primary.TButton", command=self.select_folder)
        btn_big_select.pack(ipady=8, ipadx=16)

        # ── Main Frame ──
        self.main_frame = tk.Frame(self, bg="#F0F2F5")
        
        # Config card (nền trắng, bo góc)
        config_card = tk.Frame(self.main_frame, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        config_card.pack(fill=tk.X, pady=(0, 10))
        
        inner = tk.Frame(config_card, bg="#FFFFFF")
        inner.pack(fill=tk.X, padx=16, pady=12)
        
        # Row 1: Tiền tố + Số bắt đầu + Sắp xếp
        tk.Label(inner, text="Tiền tố", fg="#6B7280", bg="#FFFFFF", 
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(inner, text="Số bắt đầu", fg="#6B7280", bg="#FFFFFF",
                 font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(16,0))
        tk.Label(inner, text="Sắp xếp theo", fg="#6B7280", bg="#FFFFFF",
                 font=("Segoe UI", 9)).grid(row=0, column=4, sticky="w", padx=(16,0))
        tk.Label(inner, text="Thư mục nguồn", fg="#6B7280", bg="#FFFFFF",
                 font=("Segoe UI", 9)).grid(row=0, column=6, sticky="w", padx=(16,0))
        
        self.entry_prefix = ttk.Entry(inner, width=38, font=("Segoe UI", 10))
        self.entry_prefix.grid(row=1, column=0, sticky="ew", pady=(2,0))
        
        self.entry_start = ttk.Entry(inner, width=10, font=("Segoe UI", 10))
        self.entry_start.grid(row=1, column=2, sticky="ew", padx=(16,0), pady=(2,0))
        self.entry_start.insert(0, "001")
        
        self.cb_sort = ttk.Combobox(inner, 
            values=["Tên file gốc", "Ngày sửa file", "Số ký hiệu", "Ngày văn bản", "Số trang"], 
            state="readonly", width=16, font=("Segoe UI", 10))
        self.cb_sort.current(0)
        self.cb_sort.grid(row=1, column=4, sticky="ew", padx=(16,0), pady=(2,0))
        self.cb_sort.bind("<<ComboboxSelected>>", lambda e: self.re_sort_table())
        
        folder_frame = tk.Frame(inner, bg="#FFFFFF")
        folder_frame.grid(row=1, column=6, sticky="ew", padx=(16,0), pady=(2,0))
        
        ttk.Button(folder_frame, text="📁 Chọn", command=self.select_folder,
                   width=8).pack(side=tk.LEFT)
        self.lbl_folder = tk.Label(folder_frame, text="Chưa chọn", 
                                    fg="#9CA3AF", bg="#FFFFFF",
                                    font=("Segoe UI", 9), anchor="w", width=20)
        self.lbl_folder.pack(side=tk.LEFT, padx=(8,0))
        
        self.entry_prefix.bind("<KeyRelease>", lambda e: self.recalculate_table())
        self.entry_start.bind("<KeyRelease>", lambda e: self.recalculate_table())
        
        # Table card
        table_card = tk.Frame(self.main_frame, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.table = CustomTable(table_card, self.recalculate_table, self.view_thumbnail)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.table.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.configure(yscrollcommand=scrollbar.set)
        
        # Bottom bar
        bottom = tk.Frame(self.main_frame, bg="#FFFFFF", height=64)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)
        
        btn_frame = tk.Frame(bottom, bg="#FFFFFF")
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=12)
        
        self.btn_undo = ttk.Button(btn_frame, text="↩ Hoàn tác", 
                                    style="Warning.TButton", command=self.do_undo, state=tk.DISABLED)
        self.btn_undo.pack(side=tk.RIGHT, padx=(8,0))
        
        self.btn_rename = ttk.Button(btn_frame, text="✏ Đổi tên ngay", 
                                      style="Success.TButton", command=self.do_rename, state=tk.DISABLED)
        self.btn_rename.pack(side=tk.RIGHT, padx=(8,0))
        
        self.btn_scan = ttk.Button(btn_frame, text="🔍 Quét & Preview", 
                                    style="Primary.TButton", command=self.start_scan)
        self.btn_scan.pack(side=tk.RIGHT)
        
        status_frame = tk.Frame(bottom, bg="#FFFFFF")
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=12)
        
        self.lbl_status = tk.Label(status_frame, text="Sẵn sàng", 
                                    fg="#6B7280", bg="#FFFFFF", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                         maximum=100, style="green.Horizontal.TProgressbar",
                                         length=300)
        self.progress.pack(anchor="w", pady=(4,0))

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.lbl_folder.config(text=folder if len(folder) <= 40 else "..." + folder[-37:])
            
            # Switch frames
            self.welcome_frame.pack_forget()
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
            
            self.load_files_fast()

            if self.pdf_files:
                import re
                first_name = os.path.basename(self.pdf_files[0])
                parts = re.split(r'[-_]', first_name)
                suggest = parts[0] + "-" if len(parts) > 1 else first_name[:7]
                self.suggested_prefix = "VD: " + suggest
                
                if not self.entry_prefix.get() or self.entry_prefix.get().startswith("VD:"):
                    self.entry_prefix.delete(0, tk.END)
                    self.entry_prefix.insert(0, self.suggested_prefix)
                    self.entry_prefix.config(foreground="#9CA3AF")
                    
                def on_focus_in(e):
                    if self.entry_prefix.get() == self.suggested_prefix:
                        self.entry_prefix.delete(0, tk.END)
                        self.entry_prefix.config(foreground="#1B2A4A")
                        
                def on_focus_out(e):
                    if not self.entry_prefix.get().strip():
                        self.entry_prefix.insert(0, self.suggested_prefix)
                        self.entry_prefix.config(foreground="#9CA3AF")
                        
                self.entry_prefix.bind("<FocusIn>", on_focus_in)
                self.entry_prefix.bind("<FocusOut>", on_focus_out)

    def load_files_fast(self):
        self.pdf_files = [os.path.join(self.current_folder, f) for f in os.listdir(self.current_folder) if f.lower().endswith('.pdf')]
        self.lbl_status.config(text=f"Đã tải {len(self.pdf_files)} file PDF.")
        self.table.clear_all()
        
        results = []
        for pdf_path in self.pdf_files:
            file_data = {
                "path": pdf_path,
                "old_name": os.path.basename(pdf_path),
                "so_kh": None,
                "ngay_vb": None,
                "so_trang": None,
                "mtime": os.path.getmtime(pdf_path),
                "thumbnail_path": None,
                "checked": True,
                "manual_edit": False,
                "crop_sokh_path": None,
                "crop_ngay_path": None,
                "crop_trang_path": None,
                "status_text": "Chưa quét",
                "status_code": "idle",
                "ngay_str": ""
            }
            results.append(file_data)
            
        for data in results:
            self.table.insert_row(data)
            
        self.re_sort_table()
        self.btn_rename.config(state=tk.NORMAL if results else tk.DISABLED)

    def start_scan(self):
        all_data = self.table.get_all_data()
        if not all_data:
            messagebox.showinfo("Thông báo", "Vui lòng chọn thư mục có chứa file PDF trước.")
            return
            
        if self.is_processing:
            self.cancel_scan = True
            self.btn_scan.config(text="Đang dừng...", state=tk.DISABLED)
            return
            
        if not is_tesseract_installed():
            resp = messagebox.askyesno("Cảnh báo", "Không tìm thấy Tesseract OCR. OCR sẽ bị bỏ qua, bạn vẫn có thể tự sửa tên.\nBạn có muốn tiếp tục?")
            if not resp:
                return
                
        self.is_processing = True
        self.cancel_scan = False
        self.btn_scan.config(text="🛑 Dừng quét", style="Warning.TButton")
        self.btn_rename.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        # Run in thread
        threading.Thread(target=self.scan_thread, args=(all_data,), daemon=True).start()

    def scan_thread(self, all_data):
        total = len(all_data)
        
        for i, data in enumerate(all_data):
            if self.cancel_scan:
                break
                
            pdf_path = data["path"]
            
            # Extract info
            info = extract_pdf_info(pdf_path)
            
            data["so_kh"] = info.get("so_kh")
            data["ngay_vb"] = info.get("ngay_vb")
            data["so_trang"] = info.get("so_trang")
            data["thumbnail_path"] = info.get("thumbnail_path")
            data["crop_sokh_path"]  = info.get("crop_sokh_path")
            data["crop_ngay_path"]  = info.get("crop_ngay_path")
            data["crop_trang_path"] = info.get("crop_trang_path")
            
            # Determine Status
            if info.get("error"):
                data["status_text"] = "❌ Lỗi đọc"
                data["status_code"] = "error"
            elif info.get("so_kh"):
                data["status_text"] = "🟢 Sẵn sàng"
                data["status_code"] = "ok"
                data["ngay_str"] = info["ngay_vb"].strftime("%d/%m/%Y") if info.get("ngay_vb") else ""
            elif info.get("ngay_vb"):
                data["status_text"] = "🔵 Dùng ngày"
                data["status_code"] = "ok"
                data["ngay_str"] = info["ngay_vb"].strftime("%d/%m/%Y")
            else:
                data["status_text"] = "🔴 Không đọc được KH"
                data["status_code"] = "warn"
                data["ngay_str"] = ""
                
            # Update UI safely
            self.after(0, self.table.update_row_by_data, data)
            
            pct = int((i + 1) / total * 100)
            self.after(0, self.update_progress, pct, f"Đang quét {i+1}/{total} file...")
            
        self.after(0, self.finish_scan)

    def update_progress(self, val, text):
        self.progress_var.set(val)
        self.lbl_status.config(text=text)

    def finish_scan(self):
        self.re_sort_table()
        
        self.is_processing = False
        self.btn_scan.config(text="🔍 Quét & Preview", style="Primary.TButton", state=tk.NORMAL)
        self.btn_rename.config(state=tk.NORMAL)
        
        if self.cancel_scan:
            self.lbl_status.config(text=f"Đã dừng quét. Vui lòng kiểm tra lại bảng.")
        else:
            self.lbl_status.config(text="Quét hoàn tất. Vui lòng kiểm tra lại bảng trước khi Đổi tên.")

    def re_sort_table(self):
        """Sắp xếp lại bảng dựa theo lựa chọn trong Combobox."""
        all_data = self.table.get_all_data()
        if not all_data: return
        
        sort_mode = self.cb_sort.get()
        
        if sort_mode == "Tên file gốc":
            def sort_key(item):
                return item.get("old_name", "").lower()
        elif sort_mode == "Số ký hiệu":
            def sort_key(item):
                return (item.get("so_kh") if item.get("so_kh") is not None else float('inf'),
                        item.get("ngay_vb") or datetime.max,
                        item.get("mtime", 0))
        elif sort_mode == "Ngày văn bản":
            def sort_key(item):
                return (item.get("ngay_vb") or datetime.max,
                        item.get("so_kh") if item.get("so_kh") is not None else float('inf'),
                        item.get("mtime", 0))
        elif sort_mode == "Số trang":
            def sort_key(item):
                return (item.get("so_trang") if item.get("so_trang") is not None else float('inf'),
                        item.get("so_kh") if item.get("so_kh") is not None else float('inf'),
                        item.get("mtime", 0))
        else: # Ngày sửa file
            def sort_key(item):
                return (item.get("mtime", 0),
                        item.get("so_kh") if item.get("so_kh") is not None else float('inf'),
                        item.get("ngay_vb") or datetime.max)
                        
        sorted_data = sorted(all_data, key=sort_key)
        
        self.table.clear_all()
        for data in sorted_data:
            self.table.insert_row(data)
            
        self.recalculate_table()

    def recalculate_table(self):
        """Tính toán lại cột STT và Tên file mới khi có thay đổi."""
        prefix = self.entry_prefix.get()
        if prefix.startswith("VD:"):
            prefix = ""
        start_num_str = self.entry_start.get()
        
        all_data = self.table.get_all_data()
        
        new_names = generate_new_names(all_data, prefix, start_num_str)
        
        stt = 1
        for i, item_id in enumerate(self.table.get_children()):
            data = all_data[i]
            
            if data.get("checked", True):
                data["stt"] = str(stt)
                stt += 1
                
                # Cập nhật tên mới nếu chưa bị sửa tay
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
            if data.get("checked", True) and data.get("new_name") and data.get("new_name") != "-":
                old_p = data["path"]
                new_p = os.path.join(self.current_folder, data["new_name"])
                rename_plan.append({"old_path": old_p, "new_path": new_p})
                
        if not rename_plan:
            messagebox.showinfo("Thông báo", "Không có file nào được chọn để đổi tên.")
            return
            
        first_old = os.path.basename(rename_plan[0]["old_path"])
        prefix_val = self.entry_prefix.get() if not self.entry_prefix.get().startswith("VD:") else ""
        start_val = self.entry_start.get()
        
        msg = f"Sắp đổi tên {len(rename_plan)} file\nTừ: {first_old}...\nTiền tố: '{prefix_val}', bắt đầu từ {start_val}\nTiếp tục?"
        if not messagebox.askyesno("Xác nhận đổi tên", msg):
            return
            
        success, errors = execute_rename(rename_plan, self.current_folder)
        
        msg = f"Đã đổi tên thành công {success} file."
        if errors:
            msg += "\n\nCó lỗi xảy ra:\n" + "\n".join(errors[:5])
            if len(errors) > 5: msg += "\n..."
            
        messagebox.showinfo("Kết quả", msg)
        
        if success > 0:
            self.btn_undo.config(state=tk.NORMAL)
            # Quét lại hoặc clear
            self.load_files_fast()

    def do_undo(self):
        resp = messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hoàn tác lần đổi tên vừa rồi?")
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
