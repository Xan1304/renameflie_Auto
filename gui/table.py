import os
import tkinter as tk
from tkinter import ttk

class ImageTooltip:
    """Popup ảnh hiện khi hover, ẩn khi rời chuột."""
    
    def __init__(self, treeview):
        self.tv = treeview
        self.popup = None
        self.current_img = None
        self._after_id = None
    
    def show(self, img_path, x, y):
        """Hiện popup ảnh tại tọa độ màn hình (x, y)."""
        self.hide()
        if not img_path or not os.path.exists(img_path):
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(img_path)
            
            self.popup = tk.Toplevel(self.tv)
            self.popup.wm_overrideredirect(True)  # Không có border/titlebar
            self.popup.wm_attributes("-topmost", True)
            self.popup.configure(bg="#1F2937")
            
            # Border effect
            outer = tk.Frame(self.popup, bg="#374151", padx=2, pady=2)
            outer.pack()
            
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(outer, image=photo, bg="#FFFFFF")
            lbl.image = photo  # Giữ tham chiếu
            lbl.pack()
            
            self.current_img = photo
            
            # Đặt vị trí popup: ưu tiên hiện bên phải con trỏ, tránh ra ngoài màn hình
            self.popup.update_idletasks()
            pw = self.popup.winfo_width()
            ph = self.popup.winfo_height()
            sw = self.tv.winfo_screenwidth()
            sh = self.tv.winfo_screenheight()
            
            px = x + 16
            py = y + 8
            if px + pw > sw: px = x - pw - 8
            if py + ph > sh: py = y - ph - 8
            
            self.popup.geometry(f"+{px}+{py}")
            
        except Exception as e:
            self.hide()
    
    def hide(self):
        if self.popup:
            try:
                self.popup.destroy()
            except:
                pass
            self.popup = None
            self.current_img = None

class CustomTable(ttk.Treeview):
    def __init__(self, parent, on_recalculate_names, on_view_thumbnail):
        self.columns = ("updown", "check", "stt", "old", "sokh", "ngay", "sotrang", "new", "status", "view")
        super().__init__(parent, columns=self.columns, show="headings", selectmode="browse")
        
        self.on_recalculate = on_recalculate_names
        self.on_view = on_view_thumbnail
        
        # Cấu hình các cột
        self.heading("updown", text="☰")
        self.column("updown", width=40, anchor="center")
        
        self.heading("check", text="☑")
        self.column("check", width=40, anchor="center")
        
        self.heading("stt", text="STT")
        self.column("stt", width=50, anchor="center")
        
        self.heading("old", text="Tên file gốc")
        self.column("old", width=150, anchor="w")
        
        self.heading("sokh", text="Số KH")
        self.column("sokh", width=80, anchor="center")
        
        self.heading("ngay", text="Ngày")
        self.column("ngay", width=100, anchor="center")
        
        self.heading("sotrang", text="Trang")
        self.column("sotrang", width=50, anchor="center")
        
        self.heading("new", text="Tên file mới")
        self.column("new", width=200, anchor="w")
        
        self.heading("status", text="Trạng thái")
        self.column("status", width=150, anchor="center")
        
        self.heading("view", text="Xem")
        self.column("view", width=50, anchor="center")
        
        # Tags cho zebra striping và màu sắc
        self.tag_configure("even", background="#F8FAFC")
        self.tag_configure("odd", background="#FFFFFF")
        self.tag_configure("ok_row", background="#E1EFFE") # Xanh dương nhạt
        self.tag_configure("warn_row", background="#FEF3C7") # Vàng nhạt
        self.tag_configure("error_row", background="#FEE2E2") # Đỏ nhạt
        
        # Bắt sự kiện kéo thả và click
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Double-1>", self.handle_double_click)
        
        self.file_data_map = {} # map item_id -> dict dữ liệu file
        self.editing_entry = None
        self.drag_item = None
        self.drag_y = 0
        
        self.bind("<<TreeviewSelect>>", self._on_select)
        self.on_select_callback = None
        
        self.tooltip = ImageTooltip(self)
        self._hovered_item = None
        self._hovered_col = None

        self.bind("<Motion>", self._on_motion_hover)
        self.bind("<Leave>", self._on_leave_hover)

    def _on_motion_hover(self, event):
        """Khi di chuột trong bảng — kiểm tra có đang ở cột Số KH/Ngày/Trang không."""
        if hasattr(self, '_tooltip_after_id') and self._tooltip_after_id:
            self.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None
            
        if self.editing_entry:
            self.tooltip.hide()
            return
            
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            self.tooltip.hide()
            return
        
        item_id = self.identify_row(event.y)
        col    = self.identify_column(event.x)  # "#1", "#2", ...
        col_idx = int(col[1:]) - 1  # 0-based
        
        # Chỉ xử lý cột Số KH(4), Ngày(5), Trang(6)
        if col_idx not in (4, 5, 6):
            self.tooltip.hide()
            self._hovered_item = None
            return
        
        # Nếu đang hover cùng ô → không làm gì (tránh flicker)
        if item_id == self._hovered_item and col == self._hovered_col:
            return
        
        self._hovered_item = item_id
        self._hovered_col  = col
        
        data = self.file_data_map.get(item_id)
        if not data:
            self.tooltip.hide()
            return
        
        # Lấy đúng ảnh crop tương ứng với cột
        crop_map = {
            4: "crop_sokh_path",
            5: "crop_ngay_path",
            6: "crop_trang_path",
        }
        img_path = data.get(crop_map[col_idx])
        
        # Tọa độ màn hình
        x_screen = event.x_root
        y_screen = event.y_root
        
        self._tooltip_after_id = self.after(300, lambda: self.tooltip.show(img_path, x_screen, y_screen))

    def _on_leave_hover(self, event):
        """Khi chuột rời khỏi bảng — ẩn tooltip."""
        if hasattr(self, '_tooltip_after_id') and self._tooltip_after_id:
            self.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None
        self.tooltip.hide()
        self._hovered_item = None
        self._hovered_col  = None

    def _on_select(self, event):
        selected = self.selection()
        if selected and self.on_select_callback:
            item_id = selected[0]
            data = self.file_data_map.get(item_id)
            if data:
                self.on_select_callback(data)

    def insert_row(self, file_data):
        """Thêm một dòng dữ liệu vào bảng."""
        item_id = self.insert("", "end")
        self.file_data_map[item_id] = file_data
        self.update_row_display(item_id)
        self.apply_zebra_stripes()
        return item_id
        
    def update_row_display(self, item_id):
        """Cập nhật hiển thị của 1 dòng dựa trên dữ liệu."""
        data = self.file_data_map.get(item_id)
        if not data: return
        
        check_str = "☑" if data.get("checked", True) else "☐"
        status = data.get("status_text", "")
        
        self.item(item_id, values=(
            "☰", 
            check_str, 
            data.get("stt", ""), 
            data.get("old_name", ""),
            data.get("so_kh", "") or "",
            data.get("ngay_str", ""),
            str(data.get("so_trang")) if data.get("so_trang") else "🖼️",
            data.get("new_name", ""),
            status,
            "🔍"
        ))

    def update_row_by_data(self, data):
        """Tìm item_id chứa data và update giao diện."""
        for item_id, d in self.file_data_map.items():
            if d is data:
                self.update_row_display(item_id)
                break

    def get_all_data(self):
        """Lấy danh sách dữ liệu theo thứ tự hiển thị hiện tại."""
        result = []
        for item_id in self.get_children():
            result.append(self.file_data_map[item_id])
        return result

    def apply_zebra_stripes(self):
        """Áp dụng màu nền xen kẽ và theo trạng thái."""
        for i, item in enumerate(self.get_children()):
            data = self.file_data_map.get(item)
            if data:
                status_code = data.get("status_code", "idle")
                if status_code == "ok":
                    tags = ("ok_row",)
                elif status_code == "warn":
                    tags = ("warn_row",)
                elif status_code == "error":
                    tags = ("error_row",)
                else:
                    tags = ("even",) if i % 2 == 0 else ("odd",)
            else:
                tags = ("even",) if i % 2 == 0 else ("odd",)
            self.item(item, tags=tags)

    def on_press(self, event):
        region = self.identify_region(event.x, event.y)
        if region == "cell":
            self.drag_item = self.identify_row(event.y)
            self.drag_y = event.y

    def on_motion(self, event):
        if not self.drag_item: return
        # Nếu di chuyển chuột ít hơn 5px thì bỏ qua
        if abs(event.y - self.drag_y) < 5: return
        
        target = self.identify_row(event.y)
        if target and target != self.drag_item:
            idx = self.index(target)
            self.move(self.drag_item, self.parent(self.drag_item), idx)

    def on_release(self, event):
        if self.drag_item:
            # Nếu đã kéo đi xa hơn 5px (Drag & Drop)
            if abs(event.y - self.drag_y) >= 5:
                self.apply_zebra_stripes()
                self.on_recalculate()
                self.drag_item = None
                return # Bỏ qua click
                
        self.drag_item = None
        self.handle_click(event)

    def handle_click(self, event):
        """Xử lý sự kiện click thật sự trên các cột đặc biệt."""
        if self.editing_entry:
            self.editing_entry.destroy()
            self.editing_entry = None
            
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.identify_column(event.x)
        item_id = self.identify_row(event.y)
        
        if not item_id:
            return
            
        col_idx = int(column[1:]) - 1
        data = self.file_data_map[item_id]
        
        # Cột ☑
        if col_idx == 1:
            data["checked"] = not data.get("checked", True)
            self.update_row_display(item_id)
            self.on_recalculate()
                
        # Cột Xem 🔍
        elif col_idx == 9:
            if data.get("thumbnail_path"):
                self.on_view(data["thumbnail_path"])

    def handle_double_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region != "cell": return
        column = self.identify_column(event.x)
        item_id = self.identify_row(event.y)
        if not item_id: return
        col_idx = int(column[1:]) - 1
        
        # Cột Tên file mới
        if col_idx == 7:
            self.start_edit(item_id, column, "new_name")

    def start_edit(self, item_id, column, field_name):
        self.tooltip.hide()
        bbox = self.bbox(item_id, column)
        if not bbox: return
        
        x, y, w, h = bbox
        data = self.file_data_map[item_id]
        
        entry = ttk.Entry(self)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, data.get(field_name, "") or "")
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        def on_save(event=None):
            new_val = entry.get().strip()
            
            if field_name == "so_kh":
                if new_val:
                    try: data["so_kh"] = int(new_val)
                    except ValueError: pass
                else: data["so_kh"] = None
            elif field_name == "so_trang":
                if new_val:
                    try: data["so_trang"] = int(new_val)
                    except ValueError: pass
                else: data["so_trang"] = None
            elif field_name == "ngay_str":
                data["ngay_str"] = new_val
                if new_val:
                    try:
                        from datetime import datetime
                        data["ngay_vb"] = datetime.strptime(new_val, "%d/%m/%Y")
                    except Exception:
                        pass
                else: data["ngay_vb"] = None
            elif field_name == "new_name":
                if new_val == "":
                    data["manual_edit"] = False
                else:
                    data["new_name"] = new_val
                    data["manual_edit"] = True 
                
            entry.destroy()
            self.editing_entry = None
            self.update_row_display(item_id)
            self.on_recalculate()
            
        def on_tab(event):
            on_save()
            next_item = self.next(item_id)
            if next_item:
                self.selection_set(next_item)
                self.focus(next_item)
                self.see(next_item)
                self.after(50, lambda: self.start_edit(next_item, column, field_name))
            return "break"
            
        entry.bind("<Return>", on_save)
        entry.bind("<FocusOut>", on_save)
        entry.bind("<Tab>", on_tab)
        entry.bind("<Escape>", lambda e: entry.destroy())
        
        self.editing_entry = entry

    def clear_all(self):
        for item in self.get_children():
            self.delete(item)
        self.file_data_map.clear()
