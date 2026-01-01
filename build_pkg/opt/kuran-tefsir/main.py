import sys
import requests
import sqlite3
import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw, Gdk, GLib

class QuranApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.kuran.uygulamasi.tam.tefsir',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        self.db_path = os.path.join(os.path.expanduser("~"), ".kuran_v5_full.db")
        self.current_zoom = 30
        self.css_provider = Gtk.CssProvider()
        
        self.tr_names = [
            "Fatiha", "Bakara", "Âl-i İmrân", "Nisâ", "Mâide", "En'âm", "A'râf", "Enfâl", "Tevbe", "Yunus",
            "Hûd", "Yusuf", "Ra'd", "İbrahim", "Hicr", "Nahl", "İsrâ", "Kehf", "Meryem", "Tâhâ",
            "Enbiyâ", "Hac", "Mü'minûn", "Nûr", "Furkân", "Şuarâ", "Neml", "Kasas", "Ankebût", "Rûm",
            "Lokmân", "Secde", "Ahzâb", "Sebe'", "Fâtır", "Yâsîn", "Sâffât", "Sâd", "Zümer", "Mü'min",
            "Fussilet", "Şûrâ", "Zuhruf", "Duhân", "Câsiye", "Ahkâf", "Muhammed", "Fetih", "Hucurât", "Kâf",
            "Zâriyât", "Tûr", "Necm", "Kamer", "Rahmân", "Vâkıa", "Hadîd", "Mücâdele", "Haşr", "Mümtehine",
            "Saf", "Cuma", "Münâfikûn", "Tegâbün", "Talâk", "Tahrîm", "Mülk", "Kalem", "Hâkka", "Meâric",
            "Nûh", "Cin", "Müzzemmil", "Müddessir", "Kıyâme", "İnsân", "Mürselât", "Nebe'", "Nâziât", "Abese",
            "Tekvîr", "İnfitâr", "Mutaffifîn", "İnşikâk", "Burûc", "Târık", "A'lâ", "Gâşiye", "Fecr", "Beled",
            "Şems", "Leyl", "Duha", "İnşirah", "Tîn", "Alak", "Kadir", "Beyyine", "Zilzâl", "Âdiyât",
            "Kâria", "Tekâsür", "Asr", "Hümeze", "Fîl", "Kureyş", "Mâûn", "Kevser", "Kâfirûn", "Nasr",
            "Tebbet", "İhlâs", "Felak", "Nâs"
        ]

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS surahs 
                          (id INTEGER PRIMARY KEY, name TEXT, turkishName TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ayahs 
                          (id INTEGER PRIMARY KEY, surah_id INTEGER, 
                           ayah_num INTEGER, arabic TEXT, turkish TEXT, tafsir TEXT)''')
        # HIZLANDIRMA: Veritabanı indeksi ekliyoruz
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_surah_id ON ayahs(surah_id)")
        conn.commit()
        conn.close()

    def do_activate(self):
        self.init_database()
        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_title("Hızlı Kur'an-ı Kerim")
        self.win.set_default_size(1150, 850)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request=280)
        sidebar_box.add_css_class("sidebar-dark-turquaz")
        
        self.search_entry = Gtk.SearchEntry(placeholder_text="Sure ara...", margin_start=12, margin_end=12, margin_top=15, margin_bottom=10)
        self.search_entry.connect("search-changed", lambda e: self.surah_listbox.invalidate_filter())
        sidebar_box.append(self.search_entry)

        scrolled_sidebar = Gtk.ScrolledWindow(vexpand=True)
        self.surah_listbox = Gtk.ListBox()
        self.surah_listbox.add_css_class("surah-list-bg")
        self.surah_listbox.set_filter_func(self.filter_surahs)
        self.surah_listbox.connect("row-activated", self.on_surah_selected)
        scrolled_sidebar.set_child(self.surah_listbox)
        sidebar_box.append(scrolled_sidebar)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        right_box.add_css_class("main-turquaz")
        
        header = Adw.HeaderBar()
        self.global_search_entry = Gtk.SearchEntry(placeholder_text="Meallerde ara...", width_request=300)
        self.global_search_entry.connect("activate", self.on_global_search_triggered)
        header.set_title_widget(self.global_search_entry)

        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_out = Gtk.Button(icon_name="zoom-out-symbolic")
        btn_out.connect("clicked", lambda b: self.change_zoom(-2))
        btn_in = Gtk.Button(icon_name="zoom-in-symbolic")
        btn_in.connect("clicked", lambda b: self.change_zoom(2))
        zoom_box.append(btn_out); zoom_box.append(btn_in)
        header.pack_end(zoom_box)
        right_box.append(header)

        self.content_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.content_listbox = Gtk.ListBox()
        self.content_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.content_listbox.add_css_class("ayah-list-area")
        self.content_scroll.set_child(self.content_listbox)
        right_box.append(self.content_scroll)

        main_box.append(sidebar_box); main_box.append(right_box)
        self.win.set_content(main_box)
        self.update_ui_style()
        self.win.present()
        self.load_data()

    def update_ui_style(self):
        css_data = f"""
            .sidebar-dark-turquaz, .surah-list-bg {{ background-color: #008080; color: white; }}
            .surah-list-bg label {{ color: #e0f2f1; font-weight: 500; }}
            .surah-list-bg listrow:hover {{ background-color: #006666; }}
            .main-turquaz, .ayah-list-area, scrolledwindow {{ background-color: #f2fafa; }}
            .arabic-text {{ font-size: {self.current_zoom}px; font-family: "Amiri", serif; color: #c62828; margin-bottom: 15px; font-weight: bold; }}
            .turkish-text {{ font-size: {max(14, self.current_zoom - 12)}px; line-height: 1.8; color: #006064; }}
            .tefsir-box {{ background-color: #ffffff; padding: 22px; border-radius: 18px; border: 1px solid #b2dfdb; margin-top: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.06); }}
            .tefsir-text {{ font-size: {max(13, self.current_zoom - 15)}px; color: #263238; }}
            .surah-info {{ font-size: 14px; color: #00897b; font-weight: bold; margin-bottom: 12px; }}
            listrow {{ background-color: transparent; }}
        """
        self.css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ayahs")
        if cursor.fetchone()[0] == 0:
            try:
                s_res = requests.get("http://api.alquran.cloud/v1/surah").json()['data']
                m_res = requests.get("http://api.alquran.cloud/v1/quran/tr.diyanet").json()['data']['surahs']
                a_res = requests.get("http://api.alquran.cloud/v1/quran/quran-simple").json()['data']['surahs']
                for i in range(114):
                    tr_name = self.tr_names[i]
                    cursor.execute("INSERT OR REPLACE INTO surahs (id, name, turkishName) VALUES (?, ?, ?)", (i+1, s_res[i]['name'], tr_name))
                    for ay_idx in range(len(m_res[i]['ayahs'])):
                        cursor.execute("INSERT INTO ayahs (surah_id, ayah_num, arabic, turkish, tafsir) VALUES (?, ?, ?, ?, ?)",
                                       (i+1, ay_idx+1, a_res[i]['ayahs'][ay_idx]['text'], m_res[i]['ayahs'][ay_idx]['text'], f"{tr_name} suresi {ay_idx+1}. ayet tefsiri."))
                conn.commit()
            except: pass
        
        cursor.execute("SELECT id, turkishName FROM surahs ORDER BY id")
        for row in cursor.fetchall():
            self.surah_listbox.append(Gtk.Label(label=f"{row[0]}. {row[1]}", xalign=0, margin_start=15, margin_top=10, margin_bottom=10))
        conn.close()
        self.display_surah(1)

    def display_surah(self, surah_num):
        self.clear_content()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT turkishName FROM surahs WHERE id = ?", (surah_num,))
        s_name = cursor.fetchone()[0]
        cursor.execute("SELECT arabic, turkish, tafsir, ayah_num FROM ayahs WHERE surah_id = ?", (surah_num,))
        rows = cursor.fetchall()
        conn.close()

        # HIZLANDIRMA: Ayetleri sırayla (parça parça) yükle
        def load_incremental(index=0):
            if index < len(rows):
                row = rows[index]
                self.add_ayah_to_list(row[0], row[1], row[2], f"{s_name} - Ayet: {row[3]}")
                # Bir sonraki ayeti 10ms sonra yükle (Arayüzü dondurmaz)
                GLib.timeout_add(10, load_incremental, index + 1)
            return False

        load_incremental()

    def add_ayah_to_list(self, arabic, turkish, tafsir, info):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=50, margin_end=50, margin_top=30, margin_bottom=30, hexpand=True)
        info_l = Gtk.Label(label=info, halign=Gtk.Align.CENTER); info_l.add_css_class("surah-info"); vbox.append(info_l)
        ar_l = Gtk.Label(label=arabic, wrap=True, halign=Gtk.Align.CENTER); ar_l.set_justify(Gtk.Justification.CENTER); ar_l.add_css_class("arabic-text"); vbox.append(ar_l)
        tr_l = Gtk.Label(label=turkish, wrap=True, halign=Gtk.Align.CENTER); tr_l.set_justify(Gtk.Justification.CENTER); tr_l.add_css_class("turkish-text"); vbox.append(tr_l)
        
        btn = Gtk.Button(label="Tefsir Göster ↓", halign=Gtk.Align.CENTER, margin_top=12); vbox.append(btn)
        rev = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
        t_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); t_box.add_css_class("tefsir-box")
        t_l = Gtk.Label(label=tafsir, wrap=True, halign=Gtk.Align.CENTER); t_l.set_justify(Gtk.Justification.CENTER); t_l.add_css_class("tefsir-text"); t_box.append(t_l)
        rev.set_child(t_box); vbox.append(rev)
        
        btn.connect("clicked", lambda b: (rev.set_reveal_child(not rev.get_reveal_child()), b.set_label("Tefsir Kapat ↑" if rev.get_reveal_child() else "Tefsir Göster ↓")))
        vbox.append(Gtk.Separator(margin_top=35))
        self.content_listbox.append(vbox)

    def filter_surahs(self, row):
        t = self.search_entry.get_text().lower()
        return not t or t in row.get_child().get_label().lower()

    def on_surah_selected(self, lb, row):
        self.display_surah(int(row.get_child().get_label().split('.')[0]))

    def on_global_search_triggered(self, entry):
        q = entry.get_text().lower()
        if len(q) < 2: return
        self.clear_content()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT a.arabic, a.turkish, a.tafsir, s.turkishName, a.ayah_num FROM ayahs a JOIN surahs s ON a.surah_id = s.id WHERE a.turkish LIKE ? OR a.tafsir LIKE ?", (f'%{q}%', f'%{q}%'))
        for r in cursor.fetchall(): self.add_ayah_to_list(r[0], r[1], r[2], f"{r[3]} - Ayet: {r[4]}")
        conn.close()

    def clear_content(self):
        while c := self.content_listbox.get_first_child(): self.content_listbox.remove(c)
        self.content_scroll.get_vadjustment().set_value(0)

    def change_zoom(self, delta):
        self.current_zoom = max(16, min(self.current_zoom + delta, 90))
        self.update_ui_style()

if __name__ == '__main__':
    app = QuranApp()
    app.run(sys.argv)