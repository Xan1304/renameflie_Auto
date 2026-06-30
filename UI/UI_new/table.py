import os
import tkinter as tk
from tkinter import ttk

from gui.main_window import COLORS, FONTS  # [THAY ĐỔI] Palette tập trung


class ImageTooltip:
    """Popup ảnh hiện khi hover — [THAY ĐỔI] thêm delay nhỏ để tránh flicker."""

    DELAY_MS = 300  # [THAY ĐỔI] Chờ 300ms trước khi hiện tooltip

    def __init__(self, treeview):
        self.tv = treeview
        self.popup = None
        self.current_img = None
        self._after_id = None

    def show(self, img_path, x, y):
        """Hiện popup ảnh tại tọa độ màn hình (x, y) sau một delay nhỏ."""
        self.hide()
        if not img_path or not os.path.exists(img_path):
            return
        # [THAY ĐỔI] Delay để tránh tooltip nháy khi di chuyển nhanh
        self._after_id = self.tv.after(
            self.DELAY_MS, self._do_show, img_path, x, y)

    def _do_show(self, img_path, x, y):
        try:
            from PIL import Image, ImageTk
            img = Image.open(img_path)

            self.popup = tk.Toplevel(self.tv)
            self.popup.wm_overrideredirect(True)
            self.popup.wm_attributes("-topmost", True)
            # [THAY ĐỔI] Nền tooltip đồng bộ với palette
            self.popup.configure(bg=COLORS["text_primary"])

            outer = tk.Frame(self.popup,
                             bg=COLORS["border"],
                             padx=2, pady=2)
            outer.pack()

            # [THAY ĐỔI] Label tiêu đề nhỏ phía trên ảnh
            tk.Label(outer,
                     text="Xem trước vùng OCR",
                     font=FONTS["caption"],
                     fg=COLORS["text_muted"],
                     bg=COLORS["border"],
                     pady=2).pack(fill=tk.X)

            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(outer, image=photo, bg=COLORS["bg_card"])
            lbl.image = photo
            lbl.pack()

            self.current_img = photo

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

        except Exception:
            self.hide()

    def hide(self):
        if self._after_id:
            try:
                self.tv.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self.popup:
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
            self.current_img = None


class CustomTable(ttk.Treeview):
    """[THAY ĐỔI] Bảng chính — tên cột và độ rộng được điều chỉnh hợp lý hơn."""

    # Định nghĩa cột tập trung — dễ điều chỉnh
    COL_DEFS = {
        "updown":  ("☰",            40,  "center"),
        "check":   ("☑",            40,  "center"),
        "stt":     ("STT",          50,  "center"),
        "old":     ("Tên file gốc", 160, "w"),
        "sokh":    ("Số KH",        80,  "center"),
        "ngay":    ("Ngày VB",      100, "center"),  # [THAY ĐỔI] "Ngày" → "Ngày VB" rõ hơn
        "sotrang": ("Trang",        60,  "center"),  # [THAY ĐỔI] 50→60 đủ hiển thị icon
        "new":     ("Tên file mới", 210, "w"),       # [THAY ĐỔI] 200→210
        "status":  ("Trạng thái",   155, "center"),  # [THAY ĐỔI] 150→155
        "view":    ("Xem",          50,  "center"),
    }

    def __init__(self, parent, on_recalculate_names, on_view_thumbnail):
        self.columns = list(self.COL_DEFS.keys())
        super().__init__(parent, columns=self.columns,
                         show="headings", selectmode="browse")

        self.on_recalculate = on_recalculate_names
        self.on_view = on_view_thumbnail

        # ── Cấu hình cột ───────────────────────────────────────────
        for col, (heading, width, anchor) in self.COL_DEFS.items():
            self.heading(col, text=heading)
            self.column(col, width=width, anchor=anchor,
                        minwidth=30)

        # ── Tags ───────────────────────────────────────────────────
        self.tag_configure("even", background=COLORS["bg_table_alt"])
        self.tag_configure("odd",  background=COLORS["bg_card"])
        # [THAY ĐỔI] Tag màu cho trạng thái — phân biệt nhanh hơn bằng màu dòng
        self.tag_configure("status_ok",
                           background="#F0FDF4")  # Xanh nhạt — OK
        self.tag_configure("status_warn",
                           background="#FFFBEB")  # Vàng nhạt — Cần chú ý
        self.tag_configure("status_error",
                           background="#FEF2F2")  # Đỏ nhạt — Lỗi

        # ── Events ─────────────────────────────────────────────────
        self.bind("<ButtonPress-1>",   self.on_press)
        self.bind("<B1-Motion>",       self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)

        self.file_data_map = {}
        self.editing_entry = None
        self.drag_item = None
        self.drag_y = 0

        self.bind("<<TreeviewSelect>>", self._on_select)
        self.on_select_callback = None

        self.tooltip = ImageTooltip(self)
        self._hovered_item = None
        self._hovered_col  = None

        self.bind("<Motion>", self._on_motion_hover)
        self.bind("<Leave>",  self._on_leave_hover)

        # [THAY ĐỔI] Double-click trên cột tên mới để edit nhanh
        self.bind("<Double-Button-1>", self._on_double_click)

    # ── Hover Tooltip ───────────────────────────────────────────────
    def _on_motion_hover(self, event):
        if self.editing_entry:
            self.tooltip.hide()
            return

        region = self.identify_region(event.x, event.y)
        if region != "cell":
            self.tooltip.hide()
            return

        item_id = self.identify_row(event.y)
        col     = self.identify_column(event.x)
        col_idx = int(col[1:]) - 1

        # Chỉ hiện tooltip cho cột Số KH(4), Ngày(5), Trang(6)
        if col_idx not in (4, 5, 6):
            self.tooltip.hide()
            self._hovered_item = None
            return

        if item_id == self._hovered_item and col == self._hovered_col:
            return

        self._hovered_item = item_id
        self._hovered_col  = col

        data = self.file_data_map.get(item_id)
        if not data:
            self.tooltip.hide()
            return

        crop_map = {
            4: "crop_sokh_path",
            5: "crop_ngay_path",
            6: "crop_trang_path",
        }
        img_path = data.get(crop_map[col_idx])

        self.tooltip.show(img_path, event.x_root, event.y_root)

    def _on_leave_hover(self, event):
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

    # ── Insert / Update ─────────────────────────────────────────────
    def insert_row(self, file_data):
        item_id = self.insert("", "end")
        self.file_data_map[item_id] = file_data
        self.update_row_display(item_id)
        self.apply_zebra_stripes()
        return item_id

    def update_row_display(self, item_id):
        data = self.file_data_map.get(item_id)
        if not data:
            return

        check_str  = "☑" if data.get("checked", True) else "☐"
        status     = data.get("status_text", "")
        status_code = data.get("status_code", "idle")

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
            "🔍"))

        # [THAY ĐỔI] Cập nhật tag màu dòng theo trạng thái
        if status_code == "ok":
            self.item(item_id, tags=("status_ok",))
        elif status_code == "warn":
            self.item(item_id, tags=("status_warn",))
        elif status_code == "error":
            self.item(item_id, tags=("status_error",))

    def update_row_by_data(self, data):
        for item_id, d in self.file_data_map.items():
            if d is data:
                self.update_row_display(item_id)
                break

    def get_all_data(self):
        return [self.file_data_map[iid]
                for iid in self.get_children()
                if iid in self.file_data_map]

    def apply_zebra_stripes(self):
        """Áp dụng zebra striping — chỉ cho dòng chưa có status tag."""
        for i, item in enumerate(self.get_children()):
            current_tags = self.item(item, "tags")
            # Nếu đang có status tag thì không ghi đè
            if any(t in current_tags for t in
                   ("status_ok", "status_warn", "status_error")):
                continue
            tag = "even" if i % 2 == 0 else "odd"
            self.item(item, tags=(tag,))

    # ── Drag & Drop ─────────────────────────────────────────────────
    def on_press(self, event):
        region = self.identify_region(event.x, event.y)
        if region == "cell":
            self.drag_item = self.identify_row(event.y)
            self.drag_y = event.y

    def on_motion(self, event):
        if not self.drag_item:
            return
        if abs(event.y - self.drag_y) < 5:
            return
        target = self.identify_row(event.y)
        if target and target != self.drag_item:
            idx = self.index(target)
            self.move(self.drag_item, self.parent(self.drag_item), idx)

    def on_release(self, event):
        if self.drag_item:
            if abs(event.y - self.drag_y) >= 5:
                self.apply_zebra_stripes()
                self.on_recalculate()
                self.drag_item = None
                return
        self.drag_item = None
        self.handle_click(event)

    # ── Click Handler ───────────────────────────────────────────────
    def handle_click(self, event):
        if self.editing_entry:
            self.editing_entry.destroy()
            self.editing_entry = None

        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return

        column  = self.identify_column(event.x)
        item_id = self.identify_row(event.y)
        if not item_id:
            return

        col_idx = int(column[1:]) - 1
        data    = self.file_data_map[item_id]

        # Cột ☑ — toggle
        if col_idx == 1:
            data["checked"] = not data.get("checked", True)
            self.update_row_display(item_id)
            self.on_recalculate()

        # Cột Tên file mới — click để edit
        elif col_idx == 7:
            self.start_edit(item_id, column, "new_name")

        # Cột Xem 🔍
        elif col_idx == 9:
            if data.get("thumbnail_path"):
                self.on_view(data["thumbnail_path"])

    def _on_double_click(self, event):
        """[THAY ĐỔI] Double-click trên cột Tên file mới → edit ngay."""
        region  = self.identify_region(event.x, event.y)
        column  = self.identify_column(event.x)
        item_id = self.identify_row(event.y)
        if region == "cell" and item_id and int(column[1:]) - 1 == 7:
            self.start_edit(item_id, column, "new_name")

    # ── Inline Edit ─────────────────────────────────────────────────
    def start_edit(self, item_id, column, field_name):
        self.tooltip.hide()
        bbox = self.bbox(item_id, column)
        if not bbox:
            return

        x, y, w, h = bbox
        data = self.file_data_map[item_id]

        entry = ttk.Entry(self, font=FONTS["body"])
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, data.get(field_name, "") or "")
        entry.select_range(0, tk.END)   # [THAY ĐỔI] Chọn tất cả khi mở edit
        entry.focus_set()

        def on_save(event=None):
            new_val = entry.get().strip()
            if field_name == "so_kh":
                if new_val:
                    try:
                        data["so_kh"] = int(new_val)
                    except ValueError:
                        pass
            else:
                data[field_name] = new_val
                if field_name == "new_name" and new_val:
                    data["manual_edit"] = True

            entry.destroy()
            self.editing_entry = None
            self.update_row_display(item_id)
            self.on_recalculate()

        def on_cancel(event=None):
            entry.destroy()
            self.editing_entry = None

        entry.bind("<Return>",  on_save)
        entry.bind("<Tab>",     on_save)   # [THAY ĐỔI] Tab cũng lưu và di chuyển
        entry.bind("<Escape>",  on_cancel)
        entry.bind("<FocusOut>", on_save)

        self.editing_entry = entry

    def clear_all(self):
        for item in self.get_children():
            self.delete(item)
        self.file_data_map.clear()
