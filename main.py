import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import mysql.connector
from datetime import datetime
import calendar

# --- GLOBAL TASARIM VE RENK AYARLARI ---
APP_FONT = ("Roboto", 10) 
TITLE_FONT = ("Roboto", 16, "bold")
NEON_CYAN = "#00f3ff"
NEON_GREEN = "#39ff14"
BG_DARK = "#222f3e"     
BG_DARKER = "#141d26"   
TEXT_LIGHT = "#ecf0f1"  

AYLAR_LISTESI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="185.224.1.5",
            user="root",        
            password="yqv3akq@XKZ_djt4ktd",        
            database="apartman_yonetim"
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Veritabanı Hatası", f"Bağlantı kurulamadı:\n{err}")
        return None

# --- OTOMATİK VERİTABANI ONARICI ---
def initialize_database():
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM kullanicilar LIKE 'blok'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE kullanicilar ADD COLUMN blok VARCHAR(10) DEFAULT 'A Blok'")
            cursor.execute("UPDATE kullanicilar SET blok = 'A Blok' WHERE blok IS NULL")

        cursor.execute("SHOW TABLES LIKE 'butce'")
        if not cursor.fetchone():
            cursor.execute("CREATE TABLE butce (id INT AUTO_INCREMENT PRIMARY KEY, blok VARCHAR(10) DEFAULT 'A Blok', ay VARCHAR(20), toplanan_aidat DECIMAL(10,2) DEFAULT 0, harcama DECIMAL(10,2) DEFAULT 0, detay TEXT)")
        else:
            cursor.execute("SHOW COLUMNS FROM butce LIKE 'blok'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE butce ADD COLUMN blok VARCHAR(10) DEFAULT 'A Blok'")
                cursor.execute("UPDATE butce SET blok = 'A Blok' WHERE blok IS NULL")

        for blok in ["A Blok", "B Blok"]:
            for ay in AYLAR_LISTESI:
                cursor.execute("SELECT id FROM butce WHERE blok=%s AND ay=%s", (blok, ay))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO butce (blok, ay, toplanan_aidat, harcama, detay) VALUES (%s, %s, 0, 0, '')", (blok, ay))

        cursor.execute("SHOW TABLES LIKE 'odemeler'")
        if not cursor.fetchone():
            cursor.execute("CREATE TABLE odemeler (id INT AUTO_INCREMENT PRIMARY KEY, blok VARCHAR(10) DEFAULT 'A Blok', daire_no INT, ay VARCHAR(20))")
        else:
            cursor.execute("SHOW COLUMNS FROM odemeler LIKE 'blok'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE odemeler ADD COLUMN blok VARCHAR(10) DEFAULT 'A Blok'")
                cursor.execute("UPDATE odemeler SET blok = 'A Blok' WHERE blok IS NULL")
        conn.commit()
    except Exception as e:
        print(f"Veritabanı Onarım Hatası: {e}")
    finally:
        conn.close()

# ==========================================
# MODERN KAVİSLİ KART TASARIMI (TAM EKRAN UYUMLU)
# ==========================================
class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color, outline_color=None, shadow_color=BG_DARKER, radius=20, parent_bg=BG_DARK, fit_width=False, fit_height=True, **kwargs):
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.bg_color = bg_color
        self.outline_color = outline_color
        self.shadow_color = shadow_color
        self.radius = radius
        self.fit_width = fit_width 
        self.fit_height = fit_height
        
        self.inner_frame = tk.Frame(self, bg=self.bg_color)
        self.window_id = self.create_window(10, 10, window=self.inner_frame, anchor="nw")
        
        self.inner_frame.bind("<Configure>", self.on_inner_configure)
        self.bind("<Configure>", self.draw_background)

    def on_inner_configure(self, event):
        req_w = self.inner_frame.winfo_reqwidth() + 20
        req_h = self.inner_frame.winfo_reqheight() + 20
        
        try:
            cw = int(self.cget("width"))
            ch = int(self.cget("height"))
        except ValueError:
            cw, ch = 0, 0
            
        if self.fit_width and cw != req_w:
            self.config(width=req_w)
            
        if self.fit_height and ch != req_h:
            self.config(height=req_h)

    def draw_background(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1: return

        self.delete("bg")

        if self.shadow_color:
            self.round_rectangle(3, 3, w-2, h-2, radius=self.radius, fill=self.shadow_color, tags="bg")
        
        kwargs = {"fill": self.bg_color, "tags": "bg"}
        if self.outline_color:
            kwargs["outline"] = self.outline_color
            kwargs["width"] = 2
            
        self.round_rectangle(1, 1, w-4, h-4, radius=self.radius, **kwargs)
        self.tag_lower("bg")
        
        self.itemconfig(self.window_id, width=w-20, height=h-20)

    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                  x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius,
                  x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2,
                  x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

# ==========================================
# HAP (PILL) BUTON OLUŞTURUCU 
# ==========================================
def create_pill_button(parent, text, command, bg_color="#ecf0f1", fg_color="#222f3e", outline=None, hover_bg="#bdc3c7"):
    p_bg = parent.cget("bg") if hasattr(parent, 'cget') else BG_DARK
    card = RoundedFrame(parent, bg_color=bg_color, outline_color=outline, shadow_color=BG_DARKER, radius=16, parent_bg=p_bg, fit_width=True)
    
    lbl = tk.Label(card.inner_frame, text=text, font=("Roboto", 10, "bold"), bg=bg_color, fg=fg_color, cursor="hand2")
    lbl.pack(padx=10, pady=5) 
    
    def on_enter(e=None):
        card.itemconfig("bg", fill=hover_bg)
        card.inner_frame.config(bg=hover_bg)
        lbl.config(bg=hover_bg, fg=fg_color)
    def on_leave(e=None):
        card.itemconfig("bg", fill=bg_color)
        card.inner_frame.config(bg=bg_color)
        lbl.config(bg=bg_color, fg=fg_color)
    def on_click(e):
        command()
        
    for w in (card, card.inner_frame, lbl):
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", on_click)
        
    parent.after(10, on_leave)
    return card

# ==========================================
# PANELLER 
# ==========================================

class AnaSayfa(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header_frame = tk.Frame(self, bg=BG_DARK, pady=20, padx=20)
        header_frame.pack(fill="x")
        
        self.menu_btn = tk.Label(header_frame, text="☰", font=("Roboto", 24), bg=BG_DARK, fg=TEXT_LIGHT, cursor="hand2")
        self.menu_btn.pack(side="left", padx=(0, 20))
        self.menu_btn.bind("<Button-1>", lambda e: self.toggle_modern_menu())
        self.menu_btn.bind("<Enter>", lambda e: self.menu_btn.config(fg=NEON_CYAN))
        self.menu_btn.bind("<Leave>", lambda e: self.menu_btn.config(fg=TEXT_LIGHT))

        title_label = tk.Label(header_frame, text="Akıllı Site Yönetim Sistemi", font=("Roboto", 24, "bold"), fg=NEON_CYAN, bg=BG_DARK)
        title_label.pack(side="left", expand=True, anchor="w")

        self.auth_frame = tk.Frame(header_frame, bg=BG_DARK)
        self.auth_frame.pack(side="right")
        self.build_auth_buttons()

        self.content_frame = tk.Frame(self, bg=BG_DARK, padx=20, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        # DAHA KOMPAKT VE İNCE AİDAT SAYACI
        self.timer_card = RoundedFrame(self.content_frame, bg_color=BG_DARK, outline_color="#ffaa00", fit_height=True)
        self.timer_card.pack(side="bottom", fill="x", pady=(15, 0))
        
        tk.Label(self.timer_card.inner_frame, text="⏳ Aidatlar her ayın 30'unda toplanır.", font=("Roboto", 14, "bold"), fg="#ffaa00", bg=BG_DARK).pack(pady=(5, 0))
        
        timer_row = tk.Frame(self.timer_card.inner_frame, bg=BG_DARK)
        timer_row.pack(pady=(2, 5))
        tk.Label(timer_row, text="Kalan Süre: ", font=("Roboto", 14), fg="#aaaaaa", bg=BG_DARK).pack(side="left")
        self.timer_label = tk.Label(timer_row, text="Hesaplanıyor...", font=("Roboto", 16, "bold"), fg=TEXT_LIGHT, bg=BG_DARK)
        self.timer_label.pack(side="left")

        def create_modern_card(parent, title, color):
            # TAM EKRANA GÖRE ESNEME MODU (fit_height=False, expand=True)
            card = RoundedFrame(parent, bg_color=BG_DARK, outline_color=color, fit_height=False)
            card.pack(fill="both", expand=True, pady=10)
            
            tk.Label(card.inner_frame, text=title, font=TITLE_FONT, fg=color, bg=BG_DARK).pack(anchor="w", pady=(10, 5), padx=10)
            
            text_container = tk.Frame(card.inner_frame, bg=BG_DARK)
            text_container.pack(fill="both", expand=True, pady=(0, 10), padx=10)
            
            scrollbar = ttk.Scrollbar(text_container, orient="vertical", bootstyle="dark-round")
            scrollbar.pack(side="right", fill="y", padx=(5, 0))
            
            text_widget = tk.Text(text_container, bg=BG_DARK, fg=TEXT_LIGHT, font=("Roboto", 12), wrap="word", bd=0, highlightthickness=0)
            text_widget.pack(side="left", fill="both", expand=True)
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)
            
            return text_widget

        self.duyuru_text = create_modern_card(self.content_frame, "📢 DUYURULAR", NEON_CYAN)
        self.plan_text = create_modern_card(self.content_frame, "📅 PLANLAMALAR", NEON_GREEN)

        self.menu_window = None 
        self.update_data()
        self.update_timer()

    def build_auth_buttons(self):
        for widget in self.auth_frame.winfo_children():
            widget.destroy()

        if self.controller.current_username:
            if self.controller.current_user_role == "Yönetici":
                display_text = f"👤 {self.controller.current_username} (Yönetici)"
            else:
                b = self.controller.current_user_blok if self.controller.current_user_blok else ""
                d = self.controller.current_user_daire if self.controller.current_user_daire else ""
                display_text = f"👤 {self.controller.current_username}  |  {b} - Daire: {d}"

            user_card = RoundedFrame(self.auth_frame, bg_color=BG_DARKER, outline_color=NEON_CYAN, shadow_color=None, radius=14, parent_bg=BG_DARK, fit_width=True)
            user_card.pack(side="left", padx=15)
            user_lbl = tk.Label(user_card.inner_frame, text=display_text, font=("Roboto", 10, "bold"), bg=BG_DARKER, fg=NEON_CYAN)
            user_lbl.pack(padx=10, pady=5)

            p_btn = create_pill_button(self.auth_frame, "Panelim", self.go_to_panel, bg_color=NEON_CYAN, fg_color=BG_DARK, hover_bg="#00dce6")
            p_btn.pack(side="left", padx=5)

            l_btn = create_pill_button(self.auth_frame, "Çıkış Yap", self.do_logout, bg_color="#e74c3c", fg_color="white", hover_bg="#c0392b")
            l_btn.pack(side="left", padx=5)
        else:
            login_btn = create_pill_button(self.auth_frame, "Giriş Yap", self.open_login_window, bg_color=NEON_CYAN, fg_color=BG_DARK, hover_bg="#00dce6")
            login_btn.pack(side="right", padx=5)

    def go_to_panel(self):
        role = self.controller.current_user_role
        if role == "Yönetici":
            self.controller.show_frame("YoneticiPaneli")
        elif role == "Mülk Sahibi":
            self.controller.show_frame("MulkSahibiPaneli")
        elif role == "Kiracı":
            self.controller.show_frame("KiraciPaneli")

    def do_logout(self):
        self.controller.current_username = None
        self.controller.current_user_role = None
        self.controller.current_user_blok = None
        self.controller.current_user_daire = None
        self.build_auth_buttons()
        messagebox.showinfo("Çıkış İşlemi", "Oturumunuz başarıyla kapatıldı.")

    def update_timer(self):
        now = datetime.now()
        year = now.year
        month = now.month
        
        try:
            target = datetime(year, month, 30, 23, 59, 59)
        except ValueError:
            target = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
            
        if now > target:
            month += 1
            if month > 12:
                month = 1
                year += 1
            try:
                target = datetime(year, month, 30, 23, 59, 59)
            except ValueError:
                target = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
                
        diff = target - now
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        self.timer_label.config(text=f"{days} Gün {hours:02d}:{minutes:02d}:{seconds:02d}")
        self.after(1000, self.update_timer) 

    def toggle_modern_menu(self):
        if self.menu_window and self.menu_window.winfo_exists():
            self.menu_window.destroy()
            return

        x = self.winfo_rootx() + self.menu_btn.winfo_x()
        y = self.winfo_rooty() + self.menu_btn.winfo_y() + self.menu_btn.winfo_height() + 5

        self.menu_window = tk.Toplevel(self)
        self.menu_window.overrideredirect(True) 
        
        trans_color = "#000001"
        try:
            self.menu_window.attributes("-transparentcolor", trans_color)
        except:
            trans_color = BG_DARK 
            
        self.menu_window.configure(bg=trans_color)
        
        self.menu_window.geometry(f"+{x}+{y}")

        menu_card = RoundedFrame(self.menu_window, bg_color=BG_DARK, outline_color=NEON_CYAN, radius=15, parent_bg=trans_color)
        menu_card.pack(fill="both", expand=True, padx=5, pady=5)

        def create_menu_option(text, command, outline_color="#34495e", hover_color=NEON_CYAN):
            opt_bg = BG_DARK
            opt_card = RoundedFrame(menu_card.inner_frame, bg_color=opt_bg, outline_color=outline_color, shadow_color=None, radius=12, parent_bg=BG_DARK)
            opt_card.pack(fill="x", padx=15, pady=6)
            
            lbl = tk.Label(opt_card.inner_frame, text=text, font=("Roboto", 10, "bold"), bg=opt_bg, fg=TEXT_LIGHT, cursor="hand2")
            lbl.pack(padx=20, pady=8)
            
            def on_enter(e=None):
                opt_card.itemconfig("bg", outline=hover_color)
                lbl.config(fg=hover_color, bg=opt_bg)
                opt_card.inner_frame.config(bg=opt_bg)
            def on_leave(e=None):
                opt_card.itemconfig("bg", outline=outline_color)
                lbl.config(fg=TEXT_LIGHT, bg=opt_bg)
                opt_card.inner_frame.config(bg=opt_bg)
            def on_click(e):
                command()
                
            for w in (lbl, opt_card, opt_card.inner_frame):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
                
            menu_card.after(10, on_leave)

        create_menu_option("💰 Bütçe Yönetimi ve Harcamalar", lambda: [self.menu_window.destroy(), self.show_budget()])
        
        sep_canvas = tk.Canvas(menu_card.inner_frame, height=2, bg=BG_DARK, highlightthickness=0)
        sep_canvas.pack(fill="x", padx=30, pady=2)
        sep_canvas.bind("<Configure>", lambda e: sep_canvas.create_line(0, 1, e.width, 1, fill="#34495e", width=2, capstyle="round"))

        create_menu_option("💳 Aidat Öde", lambda: [self.menu_window.destroy(), self.open_payment_window()], hover_color=NEON_GREEN)
        
        self.menu_window.bind("<FocusOut>", lambda e: self.menu_window.destroy())
        self.menu_window.focus_set()

    def update_data(self):
        self.build_auth_buttons()
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mesaj FROM duyurular ORDER BY id DESC LIMIT 1")
            d_sonuc = cursor.fetchone()
            self.duyuru_text.config(state="normal")
            self.duyuru_text.delete(1.0, tk.END)
            self.duyuru_text.insert(tk.END, d_sonuc[0] if d_sonuc else "Duyuru yok.")
            self.duyuru_text.config(state="disabled")

            cursor.execute("SELECT mesaj FROM planlar ORDER BY id DESC LIMIT 1")
            p_sonuc = cursor.fetchone()
            self.plan_text.config(state="normal")
            self.plan_text.delete(1.0, tk.END)
            self.plan_text.insert(tk.END, p_sonuc[0] if p_sonuc else "Planlanan iş yok.")
            self.plan_text.config(state="disabled")
            conn.close()

    def open_login_window(self):
        login_win = ttk.Toplevel(self)
        login_win.title("Sisteme Giriş")
        login_win.geometry("380x480")
        
        container = ttk.Frame(login_win, padding=30)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Giriş Yapın", font=("Roboto", 20, "bold")).pack(pady=(0, 25))
        
        ttk.Label(container, text="Yetki:", font=APP_FONT).pack(anchor="w")
        role_var = tk.StringVar(value="Yönetici")
        cb = ttk.Combobox(container, textvariable=role_var, values=["Yönetici", "Mülk Sahibi", "Kiracı"], state="readonly", font=APP_FONT)
        cb.pack(fill="x", pady=5)

        ttk.Label(container, text="Kullanıcı Adı:", font=APP_FONT).pack(anchor="w", pady=(10, 0))
        kadi_entry = ttk.Entry(container, font=APP_FONT)
        kadi_entry.pack(fill="x", pady=5)

        ttk.Label(container, text="Şifre:", font=APP_FONT).pack(anchor="w", pady=(10, 0))
        sifre_entry = ttk.Entry(container, show="*", font=APP_FONT)
        sifre_entry.pack(fill="x", pady=5)

        def do_login():
            kadi = kadi_entry.get()
            sifre = sifre_entry.get()
            yetki = role_var.get()

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi=%s AND sifre=%s AND yetki=%s", (kadi, sifre, yetki))
                user = cursor.fetchone()
                conn.close()

                if user:
                    self.controller.current_user_role = yetki
                    self.controller.current_username = kadi
                    self.controller.current_user_blok = user.get("blok", "")
                    self.controller.current_user_daire = user.get("daire_no", "")

                    login_win.destroy()
                    self.build_auth_buttons() 
                    
                    if yetki == "Yönetici":
                        self.controller.show_frame("YoneticiPaneli")
                    elif yetki == "Mülk Sahibi":
                        self.controller.show_frame("MulkSahibiPaneli")
                    elif yetki == "Kiracı":
                        self.controller.show_frame("KiraciPaneli")
                else:
                    messagebox.showerror("Hata", "Hatalı kullanıcı adı, şifre veya yetki!")

        ttk.Button(container, text="Giriş Yap", command=do_login, bootstyle="info").pack(pady=35, fill="x")

    def show_budget(self):
        win = ttk.Toplevel(self)
        win.title("Aylık Bütçe ve Bilanço")
        win.geometry("950x750") 
        
        top_bar = tk.Frame(win, bg=BG_DARK)
        top_bar.pack(fill="x", padx=20, pady=15)

        self.secilen_b_blok = tk.StringVar(value="A Blok")

        menu_btn = tk.Menubutton(top_bar, text=" ☰ A Blok ", font=APP_FONT, bg=BG_DARK, fg=NEON_CYAN, activebackground=NEON_CYAN, activeforeground=BG_DARK, cursor="hand2", relief="flat", bd=0)
        menu_btn.pack(side="left")
        
        blok_menu = tk.Menu(menu_btn, tearoff=0, font=APP_FONT, bg=BG_DARK, fg=TEXT_LIGHT, activebackground=NEON_CYAN, activeforeground=BG_DARK)
        menu_btn.config(menu=blok_menu)

        tk.Label(top_bar, text="📊 Aylık Bütçe Raporu", font=TITLE_FONT, bg=BG_DARK, fg=TEXT_LIGHT).pack(side="left", padx=20)

        chart_frame = tk.Frame(win, bg=BG_DARK)
        chart_frame.pack(fill="x", pady=5)

        chart_title_label = tk.Label(chart_frame, text="", font=("Roboto", 18, "bold"), fg=NEON_CYAN, bg=BG_DARK)
        chart_title_label.pack(pady=(0, 15))

        canvas_width = 550
        canvas_height = 300
        c = tk.Canvas(chart_frame, width=canvas_width, height=canvas_height, bg=BG_DARK, highlightthickness=0)
        c.pack(pady=10)

        def draw_chart(g_title, t_aidat, t_harc, t_detay):
            c.delete("all")
            chart_title_label.config(text=f"{g_title} Bilançosu")
            
            kalan = t_aidat - t_harc
            toplam_butce = t_harc + kalan
            
            if toplam_butce > 0:
                harcama_derece = (t_harc / toplam_butce) * 360
                kalan_derece = (kalan / toplam_butce) * 360
            else:
                harcama_derece = 0
                kalan_derece = 359.999 

            if harcama_derece >= 360: harcama_derece = 359.999
            if kalan_derece >= 360: kalan_derece = 359.999

            cx, cy = canvas_width / 2, canvas_height / 2
            outer_radius = 115
            inner_radius = 80
            
            x0, y0 = cx - outer_radius, cy - outer_radius
            x1, y1 = cx + outer_radius, cy + outer_radius

            c.create_arc(x0, y0, x1, y1, start=90, extent=kalan_derece, fill=NEON_GREEN, outline=BG_DARK, width=2)
            c.create_arc(x0, y0, x1, y1, start=90+kalan_derece, extent=harcama_derece, fill="#ff0044", outline=BG_DARK, width=2)

            ix0, iy0 = cx - inner_radius, cy - inner_radius
            ix1, iy1 = cx + inner_radius, cy + inner_radius
            c.create_oval(ix0, iy0, ix1, iy1, fill=BG_DARK, outline=BG_DARK, width=2)

            c.create_text(cx, cy - 15, text="TOPLAM BÜTÇE", fill=TEXT_LIGHT, font=("Roboto", 10), anchor="center")
            c.create_text(cx, cy + 15, text=f"{toplam_butce:,.2f} ₺", fill=TEXT_LIGHT, font=("Roboto", 13, "bold"), anchor="center")
            
            text_margin = 35
            c.create_text(cx - outer_radius - text_margin, cy - 15, text="Harcama", fill="#ff0044", font=("Roboto", 11, "bold"), anchor="e")
            c.create_text(cx - outer_radius - text_margin, cy + 10, text=f"{t_harc:,.2f} ₺", fill="#ff0044", font=("Roboto", 14, "bold"), anchor="e")
            c.create_text(cx - outer_radius - text_margin, cy + 40, text=t_detay, fill="#aaaaaa", font=("Roboto", 9, "italic"), anchor="e", justify="right", width=140)

            c.create_text(cx + outer_radius + text_margin, cy - 15, text="Kalan", fill=NEON_GREEN, font=("Roboto", 11, "bold"), anchor="w")
            c.create_text(cx + outer_radius + text_margin, cy + 10, text=f"{kalan:,.2f} ₺", fill=NEON_GREEN, font=("Roboto", 14, "bold"), anchor="w")

        tree_frame = ttk.Frame(win)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)

        cols = ("Ay", "Aidat", "Harcama", "Kalan", "DetayGoster", "GercekDetay")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", bootstyle="info")
        
        tree.heading("Ay", text="Ay")
        tree.heading("Aidat", text="Toplanan Aidat")
        tree.heading("Harcama", text="Harcama")
        tree.heading("Kalan", text="Kalan Bütçe")
        tree.heading("DetayGoster", text="") 
        
        tree["displaycolumns"] = ("Ay", "Aidat", "Harcama", "Kalan", "DetayGoster")
        for col in ("Ay", "Aidat", "Harcama", "Kalan"):
            tree.column(col, anchor="center")
        tree.column("DetayGoster", anchor="center", width=150)
        tree.pack(fill="both", expand=True)

        def load_budget_data(blok_ismi):
            self.secilen_b_blok.set(blok_ismi)
            menu_btn.config(text=f" ☰ {blok_ismi} ")
            
            for item in tree.get_children():
                tree.delete(item)

            mevcut_ay = AYLAR_LISTESI[datetime.now().month - 1]

            conn = get_db_connection()
            rows = []
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM butce WHERE blok = %s", (blok_ismi,))
                rows = cursor.fetchall()
                conn.close()
            
            for ay in AYLAR_LISTESI:
                b = next((r for r in rows if r["ay"] == ay), None)
                if b:
                    t_aidat = float(b['toplanan_aidat'])
                    t_harcama = float(b['harcama'])
                    t_kalan = t_aidat - t_harcama
                    detay = b["detay"]
                else:
                    t_aidat = 0.0
                    t_harcama = 0.0
                    t_kalan = 0.0
                    detay = ""
                    
                tree.insert("", "end", values=(ay, f"{t_aidat:,.2f} ₺", f"{t_harcama:,.2f} ₺", f"{t_kalan:,.2f} ₺", "🔍 Harcama Detayları", detay))
            
            b_data = next((r for r in rows if r["ay"] == mevcut_ay), None)
            if b_data:
                draw_chart(f"{blok_ismi} - {b_data['ay']}", float(b_data["toplanan_aidat"]), float(b_data["harcama"]), b_data["detay"])
            else:
                draw_chart(f"{blok_ismi} - {mevcut_ay}", 0.0, 0.0, "")

        blok_menu.add_command(label="A Blok", command=lambda: load_budget_data("A Blok"))
        blok_menu.add_command(label="B Blok", command=lambda: load_budget_data("B Blok"))
        
        load_budget_data("A Blok")

        def on_click(event):
            item = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            
            if item:
                values = tree.item(item, "values")
                secilen_ay = values[0]
                secilen_blok = self.secilen_b_blok.get()
                
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM butce WHERE ay = %s AND blok = %s", (secilen_ay, secilen_blok))
                    b_data = cursor.fetchone()
                    conn.close()
                    
                    if b_data:
                        draw_chart(f"{secilen_blok} - {b_data['ay']}", float(b_data["toplanan_aidat"]), float(b_data["harcama"]), b_data["detay"])
                    else:
                        draw_chart(f"{secilen_blok} - {secilen_ay}", 0.0, 0.0, "")

                if col == "#5": 
                    detay = values[5] 
                    if detay and detay.strip() != "":
                        messagebox.showinfo("Yönetici Notu", f"Harcama Detayları:\n\n{detay}", parent=win)
                    
        tree.bind("<ButtonRelease-1>", on_click)

    def open_payment_window(self):
        pay_win = ttk.Toplevel(self)
        pay_win.title("Aidat Ödeme")
        pay_win.geometry("500x620")
        
        main_container = ttk.Frame(pay_win, padding=25)
        main_container.pack(fill="both", expand=True)

        ttk.Label(main_container, text="Güvenli Ödeme Portalı", font=TITLE_FONT, bootstyle="primary").pack(pady=(0, 20))

        method_var = tk.StringVar(value="Kart")
        opt_frame = ttk.Frame(main_container)
        opt_frame.pack(fill="x", pady=10)
        
        ttk.Radiobutton(opt_frame, text="Kredi Kartı ile Öde", variable=method_var, value="Kart", command=lambda: update_view(), bootstyle="success-toolbutton", width=20).pack(side="left", padx=5, expand=True, fill="x")
        ttk.Radiobutton(opt_frame, text="Havale / EFT Yap", variable=method_var, value="Havale", command=lambda: update_view(), bootstyle="info-toolbutton", width=20).pack(side="right", padx=5, expand=True, fill="x")
        
        frame_content = ttk.Frame(main_container, bootstyle="secondary", padding=20)
        frame_content.pack(fill="both", expand=True, pady=20)

        def update_view():
            for widget in frame_content.winfo_children(): widget.destroy()
            if method_var.get() == "Kart":
                
                ttk.Label(frame_content, text="Ödenecek Ay:", bootstyle="inverse-secondary", font=APP_FONT).pack(pady=(5, 2))
                ay_cb = ttk.Combobox(frame_content, values=AYLAR_LISTESI, state="readonly", font=APP_FONT)
                ay_cb.pack(pady=2, fill="x")
                mevcut_ay_idx = datetime.now().month - 1
                ay_cb.set(AYLAR_LISTESI[mevcut_ay_idx])

                ttk.Label(frame_content, text="Blok Seçiniz:", bootstyle="inverse-secondary", font=APP_FONT).pack(pady=(10, 2))
                blok_cb = ttk.Combobox(frame_content, values=["A Blok", "B Blok"], state="readonly", font=APP_FONT)
                blok_cb.pack(pady=2, fill="x")

                ttk.Label(frame_content, text="Daire Numarası Seçiniz:", bootstyle="inverse-secondary", font=APP_FONT).pack(pady=(10, 2))
                daire_cb = ttk.Combobox(frame_content, state="readonly", font=APP_FONT)
                daire_cb.pack(pady=2, fill="x")
                
                kullanici_daire = None
                kullanici_blok = "A Blok"

                if self.controller.current_username and self.controller.current_user_role in ["Mülk Sahibi", "Kiracı"]:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT daire_no, blok FROM kullanicilar WHERE kullanici_adi = %s", (self.controller.current_username,))
                        res = cursor.fetchone()
                        if res and res[0]:
                            kullanici_daire = str(res[0])
                            kullanici_blok = res[1] if res[1] else "A Blok"
                        conn.close()

                blok_cb.set(kullanici_blok)

                def refresh_daireler(event=None):
                    secilen_blok = blok_cb.get()
                    secilen_ay = ay_cb.get()

                    odenenler = []
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT daire_no FROM odemeler WHERE ay = %s AND blok = %s", (secilen_ay, secilen_blok))
                        odenenler = [str(r[0]) for r in cursor.fetchall()]
                        conn.close()

                    def strike(text):
                        return ''.join(c + '\u0336' for c in text)

                    daire_listesi = []
                    for i in range(1, 41):
                        str_i = str(i)
                        if str_i in odenenler:
                            daire_listesi.append(f"{strike(str_i)} (Ödendi)")
                        else:
                            daire_listesi.append(str_i)

                    daire_cb.config(values=daire_listesi)
                    
                    if kullanici_daire and secilen_blok == kullanici_blok:
                        if kullanici_daire in odenenler:
                            daire_cb.set(f"{strike(kullanici_daire)} (Ödendi)")
                        else:
                            daire_cb.set(kullanici_daire)
                    else:
                        daire_cb.set(daire_listesi[0])

                blok_cb.bind("<<ComboboxSelected>>", refresh_daireler)
                ay_cb.bind("<<ComboboxSelected>>", refresh_daireler)

                if kullanici_daire:
                    blok_cb.config(state="disabled")
                    daire_cb.config(state="disabled") 
                    ttk.Label(frame_content, text="🔒 Blok ve Daireniz otomatik seçilmiştir.", font=("Roboto", 9, "italic"), bootstyle="secondary").pack(pady=(0, 10))
                
                refresh_daireler() 

                def proceed():
                    secilen = daire_cb.get()
                    secilen_blok = blok_cb.get()
                    secilen_ay = ay_cb.get()
                    
                    if "(Ödendi)" in secilen:
                        messagebox.showerror("İşlem Reddedildi", f"Bu dairenin {secilen_ay} ayı aidatı zaten ödenmiş!", parent=pay_win)
                        return
                        
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        saf_daire_no = int(''.join(filter(str.isdigit, secilen)))
                        
                        cursor.execute("UPDATE butce SET toplanan_aidat = toplanan_aidat + 1500 WHERE ay = %s AND blok = %s", (secilen_ay, secilen_blok))
                        cursor.execute("INSERT INTO odemeler (blok, daire_no, ay) VALUES (%s, %s, %s)", (secilen_blok, saf_daire_no, secilen_ay))
                        conn.commit()
                        conn.close()

                    messagebox.showinfo("Yönlendiriliyor", f"{secilen_ay} ayı güvenli ödeme için sanal pos sayfasına yönlendiriliyorsunuz. Lütfen bekleyiniz...", parent=pay_win)
                    pay_win.destroy()

                ttk.Button(frame_content, text="Güvenli Ödeme Sayfasına Git", command=proceed, bootstyle="success").pack(pady=20, fill="x")
            else:
                info_style = "inverse-secondary"
                ttk.Label(frame_content, text="Alıcı: Özbirlik Sitesi Yönetimi", font=APP_FONT, bootstyle=info_style).pack(anchor="w", pady=2)
                ttk.Label(frame_content, text="Banka: X Bankası", font=APP_FONT, bootstyle=info_style).pack(anchor="w", pady=2)
                ttk.Label(frame_content, text="IBAN: TR12 0006 7000 1234 5678 90", font=("Roboto", 12, "bold"), bootstyle=info_style).pack(anchor="w", pady=(10, 20))
                
                note_frame = ttk.Frame(frame_content, bootstyle="warning", padding=10)
                note_frame.pack(fill="x")
                ttk.Label(note_frame, text="ÖNEMLİ NOT:\nHavale açıklama kısmına Daire Numaranızı\nve Adınızı Soyadınızı mutlaka yazınız!", font=("Roboto", 11, "bold"), bootstyle="inverse-warning", justify="center").pack()

        update_view()


class YoneticiPaneli(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self, bg=BG_DARK, pady=20, padx=20)
        header.pack(fill="x")
        tk.Label(header, text="Yönetici Paneli", font=TITLE_FONT, bg=BG_DARK, fg=NEON_CYAN).pack(side="left")
        
        self.user_info_container = tk.Frame(header, bg=BG_DARK)
        self.user_info_container.pack(side="left", padx=20)
        
        home_btn = create_pill_button(header, "Ana Sayfa", lambda: controller.show_frame("AnaSayfa"), bg_color=NEON_CYAN, fg_color=BG_DARK, hover_bg="#00dce6")
        home_btn.pack(side="right", padx=5)
        
        pass_btn = create_pill_button(header, "Şifre Değiştir", controller.change_password, bg_color="#f1c40f", fg_color=BG_DARK, hover_bg="#d4ac0d")
        pass_btn.pack(side="right", padx=5)

        btn_frame = ttk.Frame(self, padding=15)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="➕ Mülk Sahibi/Kiracı Ekle", command=self.add_user_window, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📊 Bütçe Güncelle", command=self.edit_budget_window, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💵 Elden Aidat Ekle", command=self.add_aidat_window, bootstyle="warning").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📅 Planları Düzenle", command=lambda: self.open_text_editor("planlar"), bootstyle="primary").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📢 Duyuruları Düzenle", command=lambda: self.open_text_editor("duyurular"), bootstyle="secondary").pack(side="left", padx=5)

        self.list_frame = ttk.Frame(self, padding=20)
        self.list_frame.pack(fill="both", expand=True)

        top_bar = tk.Frame(self.list_frame)
        top_bar.pack(fill="x", pady=(0, 10))
        
        ttk.Label(top_bar, text="Bina Sakinleri", font=TITLE_FONT).pack(side="left")

        self.secilen_blok = tk.StringVar(value="A Blok")
        blok_cb = ttk.Combobox(top_bar, textvariable=self.secilen_blok, values=["A Blok", "B Blok"], state="readonly", font=APP_FONT, width=10)
        blok_cb.pack(side="right")
        blok_cb.bind("<<ComboboxSelected>>", lambda e: self.update_data())

        cols = ("ID", "Daire Numarası", "Kullanıcı Adı", "Yetki")
        self.tree = ttk.Treeview(self.list_frame, columns=cols, show="headings", bootstyle="primary")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Daire Numarası", text="Daire Numarası")
        self.tree.heading("Kullanıcı Adı", text="Kullanıcı Adı")
        self.tree.heading("Yetki", text="Yetki")
        
        self.tree["displaycolumns"] = ("Daire Numarası", "Kullanıcı Adı", "Yetki")
        self.tree.column("Daire Numarası", anchor="center")
        self.tree.column("Kullanıcı Adı", anchor="center")
        self.tree.column("Yetki", anchor="center")
            
        self.tree.pack(fill="both", expand=True)

        self.context_menu = tk.Menu(self.tree, tearoff=0, font=APP_FONT, bg=BG_DARK, fg=TEXT_LIGHT, activebackground=NEON_CYAN, activeforeground=BG_DARK)
        self.context_menu.add_command(label="✏️ Güncelle", command=self.update_user_window)
        self.context_menu.add_command(label="🗑️ Sil", command=self.delete_user)

        def show_context_menu(event):
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)

        self.tree.bind("<Button-3>", show_context_menu) 
        self.tree.bind("<Button-2>", show_context_menu) 

    def update_data(self):
        for widget in self.user_info_container.winfo_children():
            widget.destroy()

        if self.controller.current_username:
            display_text = f"👤 {self.controller.current_username} (Sistem Yöneticisi)"
            ucard = RoundedFrame(self.user_info_container, bg_color=BG_DARKER, outline_color=NEON_CYAN, shadow_color=None, radius=14, parent_bg=BG_DARK, fit_width=True)
            ucard.pack(side="left")
            tk.Label(ucard.inner_frame, text=display_text, font=("Roboto", 10, "bold"), bg=BG_DARKER, fg=NEON_CYAN).pack(padx=10, pady=5)

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, daire_no, kullanici_adi, yetki FROM kullanicilar WHERE blok = %s ORDER BY daire_no", (self.secilen_blok.get(),))
            for row in cursor.fetchall(): 
                daire_gosterimi = row[1] if row[1] is not None else "Yönetim"
                self.tree.insert("", "end", values=(row[0], daire_gosterimi, row[2], row[3]))
            conn.close()

    def delete_user(self):
        selected = self.tree.selection()
        if not selected: return
        item = selected[0]
        user_id = self.tree.item(item, "values")[0]
        kadi = self.tree.item(item, "values")[2]

        if kadi == "admin":
            messagebox.showerror("Hata", "Sistem ana yöneticisini silemezsiniz!")
            return

        if messagebox.askyesno("Kullanıcı Sil", f"{kadi} adlı kullanıcıyı sistemden silmek istediğinize emin misiniz?"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kullanicilar WHERE id = %s", (user_id,))
                conn.commit()
                conn.close()
                self.update_data()
                messagebox.showinfo("Başarılı", "Kullanıcı kalıcı olarak silindi.")

    def update_user_window(self):
        selected = self.tree.selection()
        if not selected: return
        item = selected[0]
        user_id = self.tree.item(item, "values")[0]
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM kullanicilar WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            conn.close()

        if not user: return

        if user["kullanici_adi"] == "admin":
            messagebox.showerror("Hata", "Ana yönetici bilgileri buradan değiştirilemez!")
            return

        win = ttk.Toplevel(self)
        win.title("Kullanıcı Bilgilerini Güncelle")
        win.geometry("380x400")

        ttk.Label(win, text="Kullanıcı Adı:", font=APP_FONT).pack(pady=(20,5))
        kadi_ent = ttk.Entry(win, font=APP_FONT)
        kadi_ent.pack(pady=5, fill="x", padx=40)
        kadi_ent.insert(0, user["kullanici_adi"])

        ttk.Label(win, text="Şifre:", font=APP_FONT).pack(pady=5)
        sifre_ent = ttk.Entry(win, font=APP_FONT)
        sifre_ent.pack(pady=5, fill="x", padx=40)
        sifre_ent.insert(0, user["sifre"])

        ttk.Label(win, text="Yetki:", font=APP_FONT).pack(pady=5)
        yetki_cb = ttk.Combobox(win, values=["Mülk Sahibi", "Kiracı"], state="readonly", font=APP_FONT)
        yetki_cb.pack(pady=5, fill="x", padx=40)
        yetki_cb.set(user["yetki"])

        def save_changes():
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE kullanicilar SET kullanici_adi=%s, sifre=%s, yetki=%s WHERE id=%s", 
                               (kadi_ent.get(), sifre_ent.get(), yetki_cb.get(), user_id))
                conn.commit()
                conn.close()
                messagebox.showinfo("Başarılı", "Kullanıcı başarıyla güncellendi!", parent=win)
                win.destroy()
                self.update_data()

        ttk.Button(win, text="Değişiklikleri Kaydet", command=save_changes, bootstyle="success").pack(pady=25, fill="x", padx=40)

    def add_aidat_window(self):
        win = ttk.Toplevel(self)
        win.title("Elden Aidat Ekle")
        win.geometry("380x450")

        ttk.Label(win, text="Blok Seçin:", font=APP_FONT).pack(pady=(15, 2))
        blok_cb = ttk.Combobox(win, values=["A Blok", "B Blok"], state="readonly", font=APP_FONT)
        blok_cb.pack(pady=2, fill="x", padx=40)
        blok_cb.set("A Blok")

        ttk.Label(win, text="Ay Seçin:", font=APP_FONT).pack(pady=(10, 2))
        ay_cb = ttk.Combobox(win, values=AYLAR_LISTESI, state="readonly", font=APP_FONT)
        ay_cb.pack(pady=2, fill="x", padx=40)
        ay_cb.set(AYLAR_LISTESI[datetime.now().month - 1])

        ttk.Label(win, text="Daire Numarası Seçin:", font=APP_FONT).pack(pady=(10, 2))
        daire_cb = ttk.Combobox(win, state="readonly", font=APP_FONT)
        daire_cb.pack(pady=2, fill="x", padx=40)

        def refresh_daireler(event=None):
            secilen_blok = blok_cb.get()
            secilen_ay = ay_cb.get()

            odenenler = []
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT daire_no FROM odemeler WHERE ay = %s AND blok = %s", (secilen_ay, secilen_blok))
                odenenler = [str(r[0]) for r in cursor.fetchall()]
                conn.close()

            def strike(text): return ''.join(c + '\u0336' for c in text)

            daire_listesi = []
            for i in range(1, 41):
                str_i = str(i)
                if str_i in odenenler:
                    daire_listesi.append(f"{strike(str_i)} (Ödendi)")
                else:
                    daire_listesi.append(str_i)

            daire_cb.config(values=daire_listesi)
            daire_cb.set(daire_listesi[0])

        blok_cb.bind("<<ComboboxSelected>>", refresh_daireler)
        ay_cb.bind("<<ComboboxSelected>>", refresh_daireler)
        refresh_daireler() 

        ttk.Label(win, text="Ödenen Miktar (₺):", font=APP_FONT).pack(pady=(10, 2))
        miktar_ent = ttk.Entry(win, font=APP_FONT)
        miktar_ent.pack(pady=2, fill="x", padx=40)
        miktar_ent.insert(0, "1500")

        def save():
            secilen = daire_cb.get()
            secilen_blok = blok_cb.get()
            secilen_ay = ay_cb.get()
            miktar_str = miktar_ent.get()

            if "(Ödendi)" in secilen:
                messagebox.showerror("Hata", f"Bu dairenin {secilen_ay} ayı aidatı zaten ödenmiş!", parent=win)
                return

            try:
                miktar = float(miktar_str)
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli bir miktar giriniz!", parent=win)
                return

            saf_daire_no = int(''.join(filter(str.isdigit, secilen)))

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE butce SET toplanan_aidat = toplanan_aidat + %s WHERE ay = %s AND blok = %s", (miktar, secilen_ay, secilen_blok))
                cursor.execute("INSERT INTO odemeler (blok, daire_no, ay) VALUES (%s, %s, %s)", (secilen_blok, saf_daire_no, secilen_ay))
                conn.commit()
                conn.close()

                messagebox.showinfo("Başarılı", f"{secilen_blok} {saf_daire_no} Numaralı daire için {secilen_ay} ayı {miktar} ₺ sisteme eklendi!", parent=win)
                win.destroy()

        ttk.Button(win, text="Kaydet", command=save, bootstyle="success").pack(pady=25, fill="x", padx=40)


    def open_text_editor(self, table_name):
        win = ttk.Toplevel(self)
        title = "Planları Düzenle" if table_name == "planlar" else "Duyuruları Düzenle"
        win.title(title)
        win.geometry("550x450")
        
        ttk.Label(win, text=f"Mevcut {title.split()[0]} (Altına ekleme yapabilirsiniz):", font=APP_FONT).pack(pady=10, anchor="w", padx=15)
        
        txt = tk.Text(win, font=APP_FONT, wrap="word", height=10)
        txt.pack(fill="both", expand=True, padx=15, pady=5)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT mesaj FROM {table_name} ORDER BY id DESC LIMIT 1")
            sonuc = cursor.fetchone()
            if sonuc:
                txt.insert(tk.END, sonuc[0] + "\n")
            conn.close()
            
        def save():
            yeni_metin = txt.get(1.0, tk.END).strip()
            if yeni_metin:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(f"INSERT INTO {table_name} (mesaj) VALUES (%s)", (yeni_metin,))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Başarılı", f"{title.split()[0]} başarıyla kaydedildi!")
                    self.controller.frames["AnaSayfa"].update_data()
                    win.destroy()

        ttk.Button(win, text="Kaydet", command=save, bootstyle="success").pack(pady=15, fill="x", padx=15)

    def add_user_window(self):
        win = ttk.Toplevel(self)
        win.title("Kullanıcı Ekle")
        win.geometry("380x550") 
        
        ttk.Label(win, text="Eklenecek Blok:", font=APP_FONT).pack(pady=(20, 2))
        blok_cb = ttk.Combobox(win, values=["A Blok", "B Blok"], state="readonly", font=APP_FONT)
        blok_cb.pack(pady=2, fill="x", padx=40)
        blok_cb.set(self.secilen_blok.get()) 
        
        dolu_daireler = []
        def update_dolu_daireler(event=None):
            nonlocal dolu_daireler
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT daire_no FROM kullanicilar WHERE daire_no IS NOT NULL AND blok = %s", (blok_cb.get(),))
                dolu_daireler = [row[0] for row in cursor.fetchall()]
                conn.close()
                
            daire_listesi = []
            for i in range(1, 41):
                if i in dolu_daireler:
                    daire_listesi.append(f"{i} (Dolu)")
                else:
                    daire_listesi.append(str(i))
            daire_cb.config(values=daire_listesi)
            daire_cb.set(daire_listesi[0])

        blok_cb.bind("<<ComboboxSelected>>", update_dolu_daireler)

        ttk.Label(win, text="Daire Numarası:", font=APP_FONT).pack(pady=(10, 2))
        daire_cb = ttk.Combobox(win, state="readonly", font=APP_FONT)
        daire_cb.pack(pady=2, fill="x", padx=40)

        ttk.Label(win, text="Kullanıcı Adı:", font=APP_FONT).pack(pady=(10, 2))
        kadi = ttk.Entry(win, font=APP_FONT)
        kadi.pack(pady=2, fill="x", padx=40)
        
        ttk.Label(win, text="Şifre:", font=APP_FONT).pack(pady=(10, 2))
        sifre = ttk.Entry(win, show="*", font=APP_FONT)
        sifre.pack(pady=2, fill="x", padx=40)
        
        ttk.Label(win, text="Yetki:", font=APP_FONT).pack(pady=(10, 2))
        yetki = ttk.Combobox(win, values=["Mülk Sahibi", "Kiracı"], state="readonly", font=APP_FONT)
        yetki.pack(pady=2, fill="x", padx=40)
        yetki.set("Mülk Sahibi")

        update_dolu_daireler() 

        def save():
            secilen = daire_cb.get()
            
            if "(Dolu)" in secilen:
                messagebox.showerror("Hata", "Bu daireye zaten bir kullanıcı atanmış!\nLütfen listeden boş bir daire seçiniz.", parent=win)
                return

            secilen_daire_no = int(secilen)

            if not kadi.get() or not sifre.get():
                messagebox.showwarning("Uyarı", "Lütfen Kullanıcı Adı ve Şifre alanlarını doldurun.", parent=win)
                return

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, yetki, daire_no, blok) VALUES (%s, %s, %s, %s, %s)", 
                                   (kadi.get(), sifre.get(), yetki.get(), secilen_daire_no, blok_cb.get()))
                    conn.commit()
                    messagebox.showinfo("Başarılı", f"Kullanıcı başarıyla {blok_cb.get()} {secilen_daire_no} numaralı daireye atandı!")
                    win.destroy()
                    self.update_data()
                except: 
                    messagebox.showerror("Hata", "Bu kullanıcı adı zaten sistemde kayıtlı olabilir.", parent=win)
                conn.close()
                
        ttk.Button(win, text="Kaydet", command=save, bootstyle="success").pack(pady=25, fill="x", padx=40)

    def edit_budget_window(self):
        win = ttk.Toplevel(self)
        win.title("Bütçe Güncelle")
        win.geometry("380x500")
        
        ttk.Label(win, text="Blok Seçin:", font=APP_FONT).pack(pady=(15, 2))
        blok_cb = ttk.Combobox(win, values=["A Blok", "B Blok"], state="readonly", font=APP_FONT)
        blok_cb.pack(pady=2, fill="x", padx=40)
        blok_cb.set("A Blok")

        ttk.Label(win, text="Güncellenecek Ay:", font=APP_FONT).pack(pady=(10, 2))
        ay_cb = ttk.Combobox(win, values=AYLAR_LISTESI, state="readonly", font=APP_FONT)
        ay_cb.pack(pady=2, fill="x", padx=40)
        ay_cb.set(AYLAR_LISTESI[datetime.now().month - 1])

        ttk.Label(win, text="Toplanan Aidat (₺):", font=APP_FONT).pack(pady=(10, 2))
        aidat_ent = ttk.Entry(win, font=APP_FONT)
        aidat_ent.pack(pady=2, fill="x", padx=40)

        ttk.Label(win, text="Harcama (₺):", font=APP_FONT).pack(pady=(10, 2))
        harcama_ent = ttk.Entry(win, font=APP_FONT)
        harcama_ent.pack(pady=2, fill="x", padx=40)

        ttk.Label(win, text="Detay (Yönetici Notu):", font=APP_FONT).pack(pady=(10, 2))
        detay_ent = ttk.Entry(win, font=APP_FONT)
        detay_ent.pack(pady=2, fill="x", padx=40)

        def load_month_data(event=None):
            secilen_ay = ay_cb.get()
            secilen_blok = blok_cb.get()
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM butce WHERE ay=%s AND blok=%s", (secilen_ay, secilen_blok))
                data = cursor.fetchone()
                conn.close()
                
                aidat_ent.delete(0, tk.END)
                harcama_ent.delete(0, tk.END)
                detay_ent.delete(0, tk.END)
                
                if data:
                    aidat_ent.insert(0, str(data["toplanan_aidat"]))
                    harcama_ent.insert(0, str(data["harcama"]))
                    detay_ent.insert(0, data["detay"])
                    
        ay_cb.bind("<<ComboboxSelected>>", load_month_data)
        blok_cb.bind("<<ComboboxSelected>>", load_month_data)
        load_month_data() 
        
        def save():
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE butce SET toplanan_aidat=%s, harcama=%s, detay=%s WHERE ay=%s AND blok=%s", 
                               (aidat_ent.get(), harcama_ent.get(), detay_ent.get(), ay_cb.get(), blok_cb.get()))
                conn.commit()
                conn.close()
                messagebox.showinfo("Başarılı", f"{blok_cb.get()} {ay_cb.get()} ayı bütçesi güncellendi!")
                win.destroy()
                
        ttk.Button(win, text="Bütçeyi Güncelle", command=save, bootstyle="success").pack(pady=25, fill="x", padx=40)


class MulkSahibiPaneli(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self, bg=BG_DARK, pady=20, padx=20)
        header.pack(fill="x")
        tk.Label(header, text="Mülk Sahibi Paneli", font=TITLE_FONT, bg=BG_DARK, fg=NEON_CYAN).pack(side="left")
        
        self.user_info_container = tk.Frame(header, bg=BG_DARK)
        self.user_info_container.pack(side="left", padx=20)

        home_btn = create_pill_button(header, "Ana Sayfa", lambda: controller.show_frame("AnaSayfa"), bg_color=NEON_CYAN, fg_color=BG_DARK, hover_bg="#00dce6")
        home_btn.pack(side="right", padx=5)
        
        pass_btn = create_pill_button(header, "Şifre Değiştir", controller.change_password, bg_color="#f1c40f", fg_color=BG_DARK, hover_bg="#d4ac0d")
        pass_btn.pack(side="right", padx=5)

        btn_frame = ttk.Frame(self, padding=15)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="💳 Aidat Durumu", command=self.show_aidat_durumu, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🏠 Kiracı İşlemleri", command=self.kiraci_islemleri_window, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="👥 Aile Sakinleri", command=self.show_aile_sakinleri, bootstyle="light").pack(side="left", padx=5)

        self.content_area = ttk.Frame(self, padding=20)
        self.content_area.pack(fill="both", expand=True)

    def update_data(self): 
        for w in self.user_info_container.winfo_children():
            w.destroy()
            
        if self.controller.current_username:
            b = self.controller.current_user_blok if self.controller.current_user_blok else ""
            d = self.controller.current_user_daire if self.controller.current_user_daire else ""
            display_text = f"👤 {self.controller.current_username}  |  {b} - Daire: {d}"
            
            ucard = RoundedFrame(self.user_info_container, bg_color=BG_DARKER, outline_color=NEON_CYAN, shadow_color=None, radius=14, parent_bg=BG_DARK, fit_width=True)
            ucard.pack(side="left")
            tk.Label(ucard.inner_frame, text=display_text, font=("Roboto", 10, "bold"), bg=BG_DARKER, fg=NEON_CYAN).pack(padx=10, pady=5)
            
        self.show_aidat_durumu() 

    def show_aidat_durumu(self):
        for w in self.content_area.winfo_children(): w.destroy()
        
        ttk.Label(self.content_area, text="📊 Yıllık Aidat Durumu", font=TITLE_FONT).pack(anchor="w", pady=10)
        
        tree = ttk.Treeview(self.content_area, columns=("Ay", "Miktar", "Durum"), show="headings", bootstyle="info")
        tree.heading("Ay", text="Ay")
        tree.heading("Miktar", text="Aidat Miktarı")
        tree.heading("Durum", text="Durum")
        tree.column("Ay", anchor="center")
        tree.column("Miktar", anchor="center")
        tree.column("Durum", anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        
        odenen_aylar = []
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("CREATE TABLE IF NOT EXISTS odemeler (id INT AUTO_INCREMENT PRIMARY KEY, blok VARCHAR(10), daire_no INT, ay VARCHAR(20))")
                
                cursor.execute("SELECT daire_no, blok FROM kullanicilar WHERE kullanici_adi=%s", (self.controller.current_username,))
                user_info = cursor.fetchone()
                
                if user_info and user_info["daire_no"]:
                    u_blok = user_info["blok"] if user_info["blok"] else "A Blok"
                    cursor.execute("SELECT ay FROM odemeler WHERE blok=%s AND daire_no=%s", (u_blok, user_info["daire_no"]))
                    odenen_aylar = [row["ay"] for row in cursor.fetchall()]
            except Exception as e:
                pass
            finally:
                conn.close()
        
        for ay in AYLAR_LISTESI:
            durum = "✅ Ödendi" if ay in odenen_aylar else "❌ Ödenmedi"
            tree.insert("", "end", values=(ay, "1.500 ₺", durum))

    def kiraci_islemleri_window(self):
        win = ttk.Toplevel(self)
        win.title("Kiracı İşlemleri")
        win.geometry("380x380")

        owner_daire = None
        owner_blok = None
        kiraci = None
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT daire_no, blok FROM kullanicilar WHERE kullanici_adi = %s", (self.controller.current_username,))
            res = cursor.fetchone()
            if res:
                owner_daire = res["daire_no"]
                owner_blok = res["blok"]
            
            cursor.execute("SELECT id, kullanici_adi FROM kullanicilar WHERE daire_no = %s AND blok = %s AND yetki = 'Kiracı'", (owner_daire, owner_blok))
            kiraci = cursor.fetchone()
            conn.close()

        ttk.Label(win, text=f"Daireniz: {owner_blok} - No: {owner_daire}", font=TITLE_FONT, bootstyle="primary").pack(pady=(20,10))

        if kiraci:
            ttk.Label(win, text="Mevcut Kiracınız:", font=APP_FONT).pack(pady=5)
            ttk.Label(win, text=kiraci["kullanici_adi"], font=("Roboto", 14, "bold"), bootstyle="danger").pack(pady=5)

            def remove_tenant():
                if messagebox.askyesno("Onay", f"{kiraci['kullanici_adi']} adlı kiracıyı sistemden silmek istediğinize emin misiniz?", parent=win):
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM kullanicilar WHERE id = %s", (kiraci["id"],))
                        conn.commit()
                        conn.close()
                        messagebox.showinfo("Başarılı", "Kiracı sistemden çıkartıldı.", parent=win)
                        win.destroy()

            ttk.Button(win, text="Kiracıyı Sistemden Çıkart", command=remove_tenant, bootstyle="danger").pack(pady=20, fill="x", padx=40)

        else:
            ttk.Label(win, text="Yeni Kiracı Ekle", font=APP_FONT).pack(pady=5)

            ttk.Label(win, text="Kullanıcı Adı:", font=APP_FONT).pack(pady=2)
            kadi_ent = ttk.Entry(win, font=APP_FONT)
            kadi_ent.pack(pady=2, fill="x", padx=40)

            ttk.Label(win, text="Şifre:", font=APP_FONT).pack(pady=2)
            sifre_ent = ttk.Entry(win, show="*", font=APP_FONT)
            sifre_ent.pack(pady=2, fill="x", padx=40)

            def add_tenant():
                kadi = kadi_ent.get()
                sifre = sifre_ent.get()
                if not kadi or not sifre:
                    messagebox.showerror("Hata", "Tüm alanları doldurun!", parent=win)
                    return
                
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, yetki, daire_no, blok) VALUES (%s, %s, %s, %s, %s)", 
                                       (kadi, sifre, "Kiracı", owner_daire, owner_blok))
                        conn.commit()
                        messagebox.showinfo("Başarılı", "Kiracı başarıyla eklendi!", parent=win)
                        win.destroy()
                    except:
                        messagebox.showerror("Hata", "Bu kullanıcı adı zaten alınmış olabilir.", parent=win)
                    conn.close()

            ttk.Button(win, text="Kiracı Olarak Kaydet", command=add_tenant, bootstyle="success").pack(pady=25, fill="x", padx=40)

    def show_aile_sakinleri(self):
        for w in self.content_area.winfo_children(): w.destroy()
        
        ttk.Label(self.content_area, text="👥 Aile Sakinleri Yönetimi", font=TITLE_FONT).pack(anchor="w", pady=10)
        
        input_frame = ttk.Frame(self.content_area)
        input_frame.pack(fill="x", pady=10)
        
        ttk.Label(input_frame, text="Yeni Sakin İsim Soyisim:", font=APP_FONT).pack(side="left", padx=5)
        yeni_sakin_ent = ttk.Entry(input_frame, font=APP_FONT, width=30)
        yeni_sakin_ent.pack(side="left", padx=5)
        
        def add_sakin():
            isim = yeni_sakin_ent.get()
            if isim:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO aile_sakinleri (kiraci_kullanici_adi, sakin_adi) VALUES (%s, %s)", (self.controller.current_username, isim))
                    conn.commit()
                    conn.close()
                    self.show_aile_sakinleri()

        def delete_sakin():
            selected = self.tree.selection()
            if not selected: return
            item = selected[0]
            sakin_adi = self.tree.item(item, "values")[0]

            if messagebox.askyesno("Sil", f"{sakin_adi} adlı aile sakinini silmek istediğinize emin misiniz?"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM aile_sakinleri WHERE kiraci_kullanici_adi = %s AND sakin_adi = %s LIMIT 1", (self.controller.current_username, sakin_adi))
                    conn.commit()
                    conn.close()
                    self.show_aile_sakinleri()

        ttk.Button(input_frame, text="Ekle", command=add_sakin, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(input_frame, text="Seçileni Sil", command=delete_sakin, bootstyle="danger").pack(side="left", padx=5)

        self.tree = ttk.Treeview(self.content_area, columns=("Sakin Adı",), show="headings", bootstyle="info")
        self.tree.heading("Sakin Adı", text="İsim Soyisim")
        self.tree.column("Sakin Adı", anchor="center")
        self.tree.pack(fill="both", expand=True, pady=10)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sakin_adi FROM aile_sakinleri WHERE kiraci_kullanici_adi = %s", (self.controller.current_username,))
            for row in cursor.fetchall(): 
                self.tree.insert("", "end", values=row)
            conn.close()


class KiraciPaneli(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self, bg=BG_DARK, pady=20, padx=20)
        header.pack(fill="x")
        tk.Label(header, text="Kiracı Paneli", font=TITLE_FONT, bg=BG_DARK, fg=NEON_CYAN).pack(side="left")
        
        self.user_info_container = tk.Frame(header, bg=BG_DARK)
        self.user_info_container.pack(side="left", padx=20)

        home_btn = create_pill_button(header, "Ana Sayfa", lambda: controller.show_frame("AnaSayfa"), bg_color=NEON_CYAN, fg_color=BG_DARK, hover_bg="#00dce6")
        home_btn.pack(side="right", padx=5)
        
        pass_btn = create_pill_button(header, "Şifre Değiştir", controller.change_password, bg_color="#f1c40f", fg_color=BG_DARK, hover_bg="#d4ac0d")
        pass_btn.pack(side="right", padx=5)

        btn_frame = ttk.Frame(self, padding=15)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="💳 Aidat Durumu", command=self.show_aidat_durumu, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="👥 Aile Sakinleri", command=self.show_aile_sakinleri, bootstyle="light").pack(side="left", padx=5)

        self.content_area = ttk.Frame(self, padding=20)
        self.content_area.pack(fill="both", expand=True)

    def update_data(self):
        for w in self.user_info_container.winfo_children():
            w.destroy()

        if self.controller.current_username:
            b = self.controller.current_user_blok if self.controller.current_user_blok else ""
            d = self.controller.current_user_daire if self.controller.current_user_daire else ""
            display_text = f"👤 {self.controller.current_username}  |  {b} - Daire: {d}"
            
            ucard = RoundedFrame(self.user_info_container, bg_color=BG_DARKER, outline_color=NEON_CYAN, shadow_color=None, radius=14, parent_bg=BG_DARK, fit_width=True)
            ucard.pack(side="left")
            tk.Label(ucard.inner_frame, text=display_text, font=("Roboto", 10, "bold"), bg=BG_DARKER, fg=NEON_CYAN).pack(padx=10, pady=5)

        self.show_aidat_durumu()

    def show_aidat_durumu(self):
        for w in self.content_area.winfo_children(): w.destroy()
        
        ttk.Label(self.content_area, text="📊 Yıllık Aidat Durumu", font=TITLE_FONT).pack(anchor="w", pady=10)
        
        tree = ttk.Treeview(self.content_area, columns=("Ay", "Miktar", "Durum"), show="headings", bootstyle="info")
        tree.heading("Ay", text="Ay")
        tree.heading("Miktar", text="Aidat Miktarı")
        tree.heading("Durum", text="Durum")
        tree.column("Ay", anchor="center")
        tree.column("Miktar", anchor="center")
        tree.column("Durum", anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        
        odenen_aylar = []
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("CREATE TABLE IF NOT EXISTS odemeler (id INT AUTO_INCREMENT PRIMARY KEY, blok VARCHAR(10), daire_no INT, ay VARCHAR(20))")
                
                cursor.execute("SELECT daire_no, blok FROM kullanicilar WHERE kullanici_adi=%s", (self.controller.current_username,))
                user_info = cursor.fetchone()
                
                if user_info and user_info["daire_no"]:
                    u_blok = user_info["blok"] if user_info["blok"] else "A Blok"
                    cursor.execute("SELECT ay FROM odemeler WHERE blok=%s AND daire_no=%s", (u_blok, user_info["daire_no"]))
                    odenen_aylar = [row["ay"] for row in cursor.fetchall()]
            except Exception as e:
                pass
            finally:
                conn.close()
                
        for ay in AYLAR_LISTESI:
            durum = "✅ Ödendi" if ay in odenen_aylar else "❌ Ödenmedi"
            tree.insert("", "end", values=(ay, "1.500 ₺", durum))

    def show_aile_sakinleri(self):
        for w in self.content_area.winfo_children(): w.destroy()
        
        ttk.Label(self.content_area, text="👥 Aile Sakinleri Yönetimi", font=TITLE_FONT).pack(anchor="w", pady=10)
        
        input_frame = ttk.Frame(self.content_area)
        input_frame.pack(fill="x", pady=10)
        ttk.Label(input_frame, text="Yeni Sakin İsim Soyisim:", font=APP_FONT).pack(side="left", padx=5)
        yeni_sakin_ent = ttk.Entry(input_frame, font=APP_FONT, width=30)
        yeni_sakin_ent.pack(side="left", padx=5)
        
        def add_sakin():
            isim = yeni_sakin_ent.get()
            if isim:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO aile_sakinleri (kiraci_kullanici_adi, sakin_adi) VALUES (%s, %s)", (self.controller.current_username, isim))
                    conn.commit()
                    conn.close()
                    self.show_aile_sakinleri()

        def delete_sakin():
            selected = self.tree.selection()
            if not selected: return
            item = selected[0]
            sakin_adi = self.tree.item(item, "values")[0]

            if messagebox.askyesno("Sil", f"{sakin_adi} adlı aile sakinini silmek istediğinize emin misiniz?"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM aile_sakinleri WHERE kiraci_kullanici_adi = %s AND sakin_adi = %s LIMIT 1", (self.controller.current_username, sakin_adi))
                    conn.commit()
                    conn.close()
                    self.show_aile_sakinleri()

        ttk.Button(input_frame, text="Ekle", command=add_sakin, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(input_frame, text="Seçileni Sil", command=delete_sakin, bootstyle="danger").pack(side="left", padx=5)

        self.tree = ttk.Treeview(self.content_area, columns=("Sakin Adı",), show="headings", bootstyle="info")
        self.tree.heading("Sakin Adı", text="İsim Soyisim")
        self.tree.column("Sakin Adı", anchor="center")
        self.tree.pack(fill="both", expand=True, pady=10)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sakin_adi FROM aile_sakinleri WHERE kiraci_kullanici_adi = %s", (self.controller.current_username,))
            for row in cursor.fetchall(): 
                self.tree.insert("", "end", values=row)
            conn.close()

# ==========================================
# ANA SİSTEM BAŞLATICI
# ==========================================
class ApartmanYonetimSistemi(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero") 
        self.title("Akıllı Site Yönetim Sistemi")
        self.geometry("1100x800")
        
        style = ttk.Style()
        style.configure('.', font=APP_FONT, background=BG_DARK, foreground=TEXT_LIGHT)
        style.configure('TButton', font=("Roboto", 10, "bold"), padding=(10, 6))
        style.configure('Treeview', font=("Roboto", 10), rowheight=35, borderwidth=0, background=BG_DARK, fieldbackground=BG_DARK, foreground=TEXT_LIGHT)
        style.map('Treeview', background=[('selected', NEON_CYAN)], foreground=[('selected', BG_DARK)])
        style.configure('Treeview.Heading', font=("Roboto", 11, "bold"), background=BG_DARKER, foreground=TEXT_LIGHT, borderwidth=0, padding=10)
        
        initialize_database()

        self.current_user_role = None 
        self.current_username = None
        self.current_user_blok = None
        self.current_user_daire = None
        
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.frames = {}
        
        for F in (AnaSayfa, YoneticiPaneli, MulkSahibiPaneli, KiraciPaneli):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show_frame("AnaSayfa")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'update_data'):
            frame.update_data()

    def change_password(self):
        if not self.current_username: return
        win = ttk.Toplevel(self)
        win.title("Şifre Değiştir")
        win.geometry("350x250")
        
        ttk.Label(win, text="Yeni şifrenizi giriniz:", font=APP_FONT).pack(pady=(25,10))
        sifre_entry = ttk.Entry(win, show="*", font=APP_FONT)
        sifre_entry.pack(pady=10, fill="x", padx=40)
        
        def save():
            yeni = sifre_entry.get()
            if yeni:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE kullanicilar SET sifre = %s WHERE kullanici_adi = %s", (yeni, self.current_username))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Başarılı", "Şifreniz başarıyla güncellendi!")
                    win.destroy()
        ttk.Button(win, text="Şifreyi Güncelle", command=save, bootstyle="success").pack(pady=20, fill="x", padx=40)

if __name__ == "__main__":
    app = ApartmanYonetimSistemi()
    app.mainloop()