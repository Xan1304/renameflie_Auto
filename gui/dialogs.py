import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import csv
import glob

from core.config import load_config, save_config, load_templates, save_templates

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cài đặt")
        self.geometry("500x150")
        self.resizable(False, False)
        
        self.config = load_config()
        
        # Header Navy
        header = tk.Frame(self, bg="#1B2A4A", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="⚙ Cài đặt hệ thống", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#1B2A4A").pack(side=tk.LEFT, padx=16)
        
        # UI
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Đường dẫn Tesseract OCR:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.entry_path = ttk.Entry(frame, width=50)
        self.entry_path.grid(row=1, column=0, sticky="we", padx=(0, 10))
        self.entry_path.insert(0, self.config.get("tesseract_path", ""))
        
        btn_browse = ttk.Button(frame, text="Duyệt...", command=self.browse_path)
        btn_browse.grid(row=1, column=1)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0), sticky="e")
        
        ttk.Button(btn_frame, text="Lưu", command=self.save, style="Success.TButton").pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Hủy", command=self.destroy).pack(side=tk.RIGHT)
        
        self.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.transient(parent)
        self.grab_set()
        
    def browse_path(self):
        path = filedialog.askopenfilename(
            title="Chọn file Tesseract OCR",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, os.path.normpath(path))
            
    def save(self):
        self.config["tesseract_path"] = self.entry_path.get()
        save_config(self.config)
        self.destroy()

class TemplateDialog(tk.Toplevel):
    def __init__(self, parent, current_prefix, current_start, apply_callback):
        super().__init__(parent)
        self.title("Quản lý Mẫu")
        self.geometry("400x300")
        
        self.apply_callback = apply_callback
        self.current_prefix = current_prefix
        self.current_start = current_start
        self.templates = load_templates()
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Danh sách mẫu
        self.listbox = tk.Listbox(frame, font=("Segoe UI", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        for name in self.templates:
            self.listbox.insert(tk.END, name)
            
        # Các nút thao tác
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Lưu hiện tại", command=self.save_current).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Áp dụng", command=self.apply_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Xóa", command=self.delete_template).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Đóng", command=self.destroy).pack(side=tk.RIGHT)
        
        self.transient(parent)
        self.grab_set()
        
    def save_current(self):
        name = tk.simpledialog.askstring("Lưu mẫu", "Nhập tên mẫu mới:", parent=self)
        if name:
            self.templates[name] = {
                "prefix": self.current_prefix,
                "start": self.current_start
            }
            save_templates(self.templates)
            self.listbox.insert(tk.END, name)
            
    def apply_template(self):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            data = self.templates[name]
            self.apply_callback(data["prefix"], data["start"])
            self.destroy()
            
    def delete_template(self):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            del self.templates[name]
            save_templates(self.templates)
            self.listbox.delete(selection[0])

class HistoryDialog(tk.Toplevel):
    def __init__(self, parent, current_folder):
        super().__init__(parent)
        self.title("Lịch sử đổi tên")
        self.geometry("600x400")
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Combobox chọn file log
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Chọn file log:").pack(side=tk.LEFT)
        self.cb_log = ttk.Combobox(top_frame, state="readonly", width=40)
        self.cb_log.pack(side=tk.LEFT, padx=(10, 0))
        
        # Bảng lịch sử
        cols = ("time", "old", "new")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        self.tree.heading("time", text="Thời gian")
        self.tree.heading("old", text="Tên cũ")
        self.tree.heading("new", text="Tên mới")
        self.tree.column("time", width=150)
        self.tree.column("old", width=200)
        self.tree.column("new", width=200)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load logs
        self.log_files = []
        if current_folder and os.path.exists(current_folder):
            pattern = os.path.join(current_folder, "rename_log_*.csv")
            self.log_files = sorted(glob.glob(pattern), reverse=True)
            
        if self.log_files:
            self.cb_log['values'] = [os.path.basename(f) for f in self.log_files]
            self.cb_log.current(0)
            self.cb_log.bind("<<ComboboxSelected>>", self.load_log_data)
            self.load_log_data(None)
        else:
            self.cb_log.set("Không có dữ liệu")
            
        self.transient(parent)
        self.grab_set()
        
    def load_log_data(self, event):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        idx = self.cb_log.current()
        if idx >= 0:
            log_path = self.log_files[idx]
            try:
                with open(log_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.tree.insert("", "end", values=(row.get('Thời gian', ''), row.get('Tên cũ', ''), row.get('Tên mới', '')))
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file log: {e}")

class ThumbnailDialog(tk.Toplevel):
    def __init__(self, parent, image_path):
        super().__init__(parent)
        self.title("Xem trước trang 1")
        
        # Bỏ viền window tiêu chuẩn, hoặc giữ viền nhưng bind ESC
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<FocusOut>", lambda e: self.destroy())
        
        try:
            img = Image.open(image_path)
            
            # Tính toán kích thước dựa trên chiều cao màn hình (khoảng 85%)
            screen_h = parent.winfo_screenheight()
            target_h = int(screen_h * 0.85)
            target_w = int(target_h * (img.width / img.height))
            
            # Resize ảnh (dùng LANCZOS để mượt hơn)
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            self.tk_image = ImageTk.PhotoImage(img)
            lbl = tk.Label(self, image=self.tk_image)
            lbl.pack()
            
            # Căn giữa cửa sổ con theo cửa sổ cha
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
            self.geometry(f"+{x}+{y}")
            
        except Exception as e:
            tk.Label(self, text=f"Lỗi hiển thị ảnh:\n{e}").pack(padx=20, pady=20)
            
        self.transient(parent)
        self.focus_set()

class MultiThumbnailDialog(tk.Toplevel):
    def __init__(self, parent, title, thumbnails_dict, detected_blanks=None, on_confirm=None):
        super().__init__(parent)
        self.title(title)
        
        self.detected_blanks = detected_blanks or []
        self.on_confirm = on_confirm
        
        # Kích thước
        screen_h = parent.winfo_screenheight()
        target_h = int(screen_h * 0.85)
        self.geometry(f"520x{target_h}")
        
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Bottom frame for Confirm button
        bottom_frame = tk.Frame(self, bg="#FFFFFF", height=60)
        bottom_frame.pack(side="bottom", fill="x")
        bottom_frame.pack_propagate(False)
        
        btn_confirm = ttk.Button(bottom_frame, text="✔ Xác nhận", style="Success.TButton", command=self._confirm)
        btn_confirm.pack(side="right", padx=20, pady=10)
        
        ttk.Label(bottom_frame, text="* Tick chọn để đánh dấu trang cần xóa", font=("Segoe UI", 9, "italic"), background="#FFFFFF", foreground="#6B7280").pack(side="left", padx=20)
        
        # Khu vực cuộn
        # Header Navy
        header = tk.Frame(self, bg="#1B2A4A", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🔍 Chế độ xem trước", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#1B2A4A").pack(side=tk.LEFT, padx=16)
        
        self.canvas = tk.Canvas(self, bg="#F3F4F6")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0F2F5")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_mouse(event, bind=True):
            if bind:
                self.bind_all("<MouseWheel>", _on_mousewheel)
            else:
                self.unbind_all("<MouseWheel>")
                
        self.bind("<Enter>", lambda e: _bind_mouse(e, True))
        self.bind("<Leave>", lambda e: _bind_mouse(e, False))
        
        # Clean up mousewheel binding on destroy
        def _on_destroy(event):
            if event.widget == self:
                self.unbind_all("<MouseWheel>")
        self.bind("<Destroy>", _on_destroy)
        
        # Chỉnh kích thước scrollable frame bằng width của canvas để nó center
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def _configure_canvas(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", _configure_canvas)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.tk_images = [] # giữ reference ảnh
        self.page_vars = {} # lưu trạng thái check của từng trang
        self.page_frames = {}
        self.page_overlays = {}
        
        # Tải từng ảnh
        for page_num in sorted(thumbnails_dict.keys()):
            img_path = thumbnails_dict[page_num]
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    # Resize để vừa chiều rộng popup (~450px)
                    target_w = 420
                    target_h_img = int(target_w * (img.height / img.width))
                    img = img.resize((target_w, target_h_img), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.tk_images.append(tk_img)
                    
                    is_blank = page_num in self.detected_blanks
                    var = tk.BooleanVar(value=is_blank)
                    self.page_vars[page_num] = var
                    
                    frame = tk.Frame(self.scrollable_frame, bg="#FFFFFF", bd=2)
                    frame.pack(pady=10, padx=10, anchor="center")
                    self.page_frames[page_num] = frame
                    
                    top_bar = tk.Frame(frame, bg="#FFFFFF")
                    top_bar.pack(fill="x", padx=10, pady=(5, 0))
                    
                    lbl_title = tk.Label(top_bar, text=f"Trang {page_num}", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#374151")
                    lbl_title.pack(side="left")
                    
                    chk = ttk.Checkbutton(top_bar, text="Xóa trang này", variable=var, command=lambda p=page_num: self._toggle_page(p))
                    chk.pack(side="right")
                    
                    img_container = tk.Frame(frame, bg="#FFFFFF")
                    img_container.pack(padx=8, pady=8)
                    
                    lbl_img = tk.Label(img_container, image=tk_img, bg="#FFFFFF")
                    lbl_img.pack()
                    
                    # Lớp phủ dấu X đỏ
                    overlay = tk.Label(img_container, text="❌", font=("Arial", 72), fg="red", bg="#FFFFFF")
                    self.page_overlays[page_num] = overlay
                    
                    self._toggle_page(page_num) # Cập nhật UI ngay lập tức
                    
                except Exception as e:
                    tk.Label(self.scrollable_frame, text=f"Lỗi tải trang {page_num}: {e}").pack()
        
        self.transient(parent)
        self.focus_set()
        
    def _toggle_page(self, page_num):
        is_selected = self.page_vars[page_num].get()
        frame = self.page_frames[page_num]
        overlay = self.page_overlays[page_num]
        
        if is_selected:
            frame.config(highlightbackground="#FCA5A5", highlightcolor="#FCA5A5", highlightthickness=2)
            overlay.place(relx=0.5, rely=0.5, anchor="center")
        else:
            frame.config(highlightbackground="#FFFFFF", highlightcolor="#FFFFFF", highlightthickness=2)
            overlay.place_forget()
            
    def _confirm(self):
        if self.on_confirm:
            selected_pages = [p for p, var in self.page_vars.items() if var.get()]
            self.on_confirm(selected_pages)
        self.destroy()
