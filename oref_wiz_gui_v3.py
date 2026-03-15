#!/usr/bin/env python3
"""
🚨 התרעות פיקוד העורף → נורת WiZ — V4
אפליקציה עצמאית — ללא צורך בהתקנת Python

Developed by Shiri Schnapp Kashi
Contact: shiri@designservice.co.il
"""

import asyncio
import requests
import json
import time
import threading
import os
import socket
import tkinter as tk
from tkinter import ttk, messagebox
from pywizlight import wizlight, PilotBuilder, discovery

# ─── קובץ הגדרות ───
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "oref_wiz_config.json")
DEFAULT_CONFIG = {"wiz_ip": "", "my_city": "", "poll_interval_sec": 0.5, "alert_duration_sec": 60}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ─── צבעים ───
ALERT_COLORS = {
    "1":   {"r": 255, "g": 0,   "b": 0,   "name": "🔴 ירי רקטות",          "default_on": True},
    "2":   {"r": 255, "g": 0,   "b": 0,   "name": "🔴 ירי לא מזוהה",       "default_on": True},
    "3":   {"r": 255, "g": 140, "b": 0,   "name": "🟠 חדירת כלי טיס",      "default_on": True},
    "4":   {"r": 0,   "g": 220, "b": 0,   "name": "🟢 חדירת מחבלים",       "default_on": True},
    "13":  {"r": 255, "g": 0,   "b": 0,   "name": "🔴 פיגוע",               "default_on": True},
    "101": {"r": 0,   "g": 200, "b": 255, "name": "🔵 תרגיל",               "default_on": True},
    "5":   {"r": 128, "g": 0,   "b": 255, "name": "🟣 רעידת אדמה",          "default_on": False},
    "6":   {"r": 0,   "g": 255, "b": 100, "name": "🟢 חומרים רדיואקטיביים", "default_on": False},
    "7":   {"r": 255, "g": 255, "b": 0,   "name": "🟡 אירוע כימי",          "default_on": False},
    "8":   {"r": 0,   "g": 100, "b": 255, "name": "🔵 צונאמי",              "default_on": False},
}
NORMAL = {"r": 255, "g": 220, "b": 150, "brightness": 180}

OREF_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_URL_BACKUP = "https://www.oref.org.il/warningMessages/alert/Alerts.json"
OREF_HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

# ─── רשימת ערים קבועה ───
CITIES = sorted([
    "אבו גוש", "אבו סנאן", "אבו קורינאת (שבט)", "אום אל-פחם", "אום אל-קוטוף",
    "אופקים", "אור יהודה", "אור עקיבא", "אורנית", "אחיהוד", "אחיסמך", "אילת",
    "אכסאל", "אל-בטוף", "אל-עזאזמה", "אלון שבות", "אלוני אבא", "אלעד",
    "אלקנה", "אמירים", "אמנון", "אעבלין", "אפרת", "אקרה", "אראבה",
    "אריאל", "אשדוד", "אשקלון", "באקה אל-גרביה", "באר יעקב", "באר שבע",
    "באר שבע - דרום", "באר שבע - מזרח", "באר שבע - מערב", "באר שבע - צפון",
    "בית אל", "בית דגן", "בית ג'ן", "בית הגדי", "בית חנן", "בית חנניה",
    "בית יצחק-שער חפר", "בית לחם הגלילית", "בית מאיר", "בית נקופה",
    "בית עריף", "בית שאן", "בית שמש", "בית שמש - גבעת שרת",
    "בית שמש - נווה אברהם", "בית שמש - רמות", "בני ברק", "בני עי\"ש",
    "בנימינה-גבעת עדה", "בסמ\"ה", "בסמת טבעון", "ביר אל-מכסור", "בקה-ג'ת",
    "בר יוחאי", "ברקן", "ג'דיידה-מכר", "ג'לג'וליה", "ג'סר א-זרקא",
    "ג'ת", "גבעת אבני", "גבעת ברנר", "גבעת זאב", "גבעת שמואל",
    "גבעתיים", "גדרה", "גולן", "גזר", "גילת", "גן יבנה", "גני תקווה",
    "גנות", "גפן", "גרופית", "דאלית אל-כרמל", "דבורייה", "דגניה א",
    "דגניה ב", "דימונה", "דליה", "דלתון", "דמיידה", "דקל", "דריג'את",
    "הוד השרון", "הוד השרון - כפר המכבי", "הוד השרון - מגשימים",
    "הוד השרון - נווה ימין", "הוד השרון - צהלה", "הרצליה", "הרצליה - מזרח",
    "הרצליה - מערב", "זבארגה (שבט)", "זיקים", "זכרון יעקב", "זמר",
    "חדרה", "חדרה - מזרח", "חדרה - מערב", "חוסנייה", "חולון", "חולית",
    "חיפה - כרמל ועיר תחתית", "חיפה - מפרץ", "חיפה - נווה שאנן ורמות",
    "חיפה - קריות", "חיפה - שמן", "חמאם", "חצור הגלילית", "חצרים",
    "טבריה", "טורעאן", "טייבה", "טירה", "טירת כרמל", "טל שחר",
    "טללים", "יבנה", "יד מרדכי", "יהוד-מונוסון", "יודפת", "יוקנעם עילית",
    "יזרעאל", "יכיני", "ינוח-ג'ת", "ירוחם", "ירושלים", "ירושלים - דרום",
    "ירושלים - מזרח", "ירושלים - מערב", "ירושלים - צפון", "כאבול",
    "כאוכב אבו אל-היג'א", "כברי", "כוכב יאיר-צור יגאל", "כוכב מיכאל",
    "כיסופים", "כישור", "כפר ברא", "כפר ג'ת", "כפר יאסיף", "כפר יונה",
    "כפר כנא", "כפר מנדא", "כפר מצר", "כפר נהר הירדן", "כפר סבא",
    "כפר סמיע", "כפר עבודה", "כפר קאסם", "כפר קרע", "כפר שמריהו",
    "כרמיאל", "כרמים", "לוד", "לכיש", "מבוא חורון", "מבוא מודיעים",
    "מגאר", "מגדל העמק", "מגדל תפן", "מודיעין-מכבים-רעות", "מועאוויה",
    "מזכרת בתיה", "מחניים", "מטולה", "מיתר", "מכמנים", "מעיין ברוך",
    "מעלה אדומים", "מעלה גלבוע", "מעלה החמישה", "מעלה עירון",
    "מעלות-תרשיחא", "מצפה אביב", "מצפה אילן", "מצפה רמון",
    "מרכז שפירא", "משגב עם", "משהד", "נאות הכיכר", "נהריה",
    "נוף הגליל", "נועם", "נורית", "נחל עוז", "נחם", "ניצן",
    "ניצן ב", "ניר בנים", "ניר גלים", "ניר עם", "נס ציונה",
    "נצרת", "נצרת עילית", "נשר", "נתיבות", "נתניה",
    "נתניה - מזרח", "נתניה - מערב", "נתניה - צפון",
    "סאג'ור", "סביון", "סח'נין", "סמר", "ספיר",
    "עומר", "עוספיא", "עילבון", "עין קינייא", "עכו",
    "עמקה", "עפולה", "עראבה", "ערד", "פדואל",
    "פוריידיס", "פרדס חנה-כרכור", "פתח תקווה",
    "פתח תקווה - דרום", "פתח תקווה - מזרח", "פתח תקווה - מערב",
    "צפת", "קדומים", "קדימה-צורן", "קלנסווה", "קציר",
    "קרית אונו", "קרית אתא", "קרית ביאליק", "קרית גת",
    "קרית טבעון", "קרית ים", "קרית מלאכי", "קרית מוצקין",
    "קרית שמונה", "ראש העין", "ראש פינה", "ראשון לציון",
    "ראשון לציון - מזרח", "ראשון לציון - מערב",
    "רהט", "רחובות", "רמות השבים", "רמלה", "רמת גן",
    "רמת גן - מזרח", "רמת גן - מערב",
    "רמת השרון", "רמת ישי", "רעננה", "שדרות",
    "שוהם", "שלומי", "שפרעם", "תל אביב - דרום",
    "תל אביב - מזרח", "תל אביב - מרכז העיר",
    "תל אביב - צפון", "תל מונד", "תמרת",
    "שתולה", "ערב אל עראמשה", "מתת", "סאסא",
    "אבו עמאר (שבט)", "זרזיר", "חורה", "חורפיש",
    "כפר חיטים", "כפר מכר", "כפר ריינה",
    "לקיה", "מעיליא", "ניר יצחק",
    "ערערה", "ערערה-בנגב", "פקיעין",
    "קציר-חריש", "ראמה", "שאר ישוב",
    "שגב-שלום", "הר אדר", "גבעות בר",
])

# ─── WiZ ───
def run_async(coro):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(coro)
    loop.close()

async def set_color(ip, r, g, b, brightness=255):
    bulb = wizlight(ip)
    await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=brightness))
    await bulb.async_close()

async def flash_and_set(ip, r, g, b):
    bulb = wizlight(ip)
    for i in range(6):
        br = 255 if i % 2 == 0 else 20
        await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=br))
        await asyncio.sleep(0.35)
    await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=255))
    await bulb.async_close()

async def discover_wiz_bulbs():
    """סריקת רשת לאיתור נורות WiZ"""
    try:
        bulbs = await discovery.find_wizlights(wait_time=3)
        return [b.ip for b in bulbs]
    except:
        return []

def get_local_broadcast():
    """קבלת כתובת broadcast של הרשת המקומית"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.255"
    except:
        return "192.168.1.255"

# ─── GUI ───
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚨 התרעות פיקוד העורף → WiZ — V4")
        self.resizable(False, False)
        self.config_data = load_config()
        self.running = False
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        tk.Label(self, text="🚨 התרעות פיקוד העורף → נורת WiZ",
                 font=("Arial", 14, "bold")).pack(**pad)

        # באנר מצב דמו — מוסתר כברירת מחדל
        self.demo_banner = tk.Label(self,
            text="⚠️  מצב דמו — אין נורה מחוברת  ⚠️\nזה לא אמיתי — לבדיקה בלבד!",
            font=("Arial", 13, "bold"), fg="white", bg="#e67e22",
            pady=8)
        # יוצג רק כשאין IP

        # ─── הגדרות ───
        frame = ttk.LabelFrame(self, text="הגדרות")
        frame.pack(fill="x", padx=12, pady=6)

        # IP נורה + כפתור סריקה
        tk.Label(frame, text="IP של הנורה:").grid(row=0, column=0, sticky="e", **pad)
        self.ip_var = tk.StringVar(value=self.config_data["wiz_ip"])
        tk.Entry(frame, textvariable=self.ip_var, width=18).grid(row=0, column=1, sticky="w", padx=4)
        self.scan_btn = tk.Button(frame, text="🔍 סרוק רשת",
                                  font=("Arial", 9), command=self._scan_network)
        self.scan_btn.grid(row=0, column=2, padx=4)
        tk.Label(frame, text="(לדוגמה: 192.168.1.45 — מצא ב: WiZ App ← Settings ← Device IP)",
                 fg="gray", font=("Arial", 8)).grid(row=0, column=3, sticky="w")

        # עיר — Combobox עם רשימה קבועה
        tk.Label(frame, text="העיר שלי:").grid(row=1, column=0, sticky="e", **pad)
        self.city_var = tk.StringVar(value=self.config_data["my_city"])
        self.city_combo = ttk.Combobox(frame, textvariable=self.city_var,
                                        width=25, state="normal")
        self.city_combo["values"] = CITIES
        self.city_combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=4)
        self.city_combo.set(self.config_data["my_city"] or "בחרי עיר...")
        # סגירת תפריט בלחיצת Enter או Tab
        self.city_combo.bind("<Return>", lambda e: self.city_combo.event_generate("<Escape>"))
        self.city_combo.bind("<Tab>", lambda e: self.city_combo.event_generate("<Escape>"))
        self.city_combo.bind("<<ComboboxSelected>>", lambda e: self.focus())
        tk.Label(frame, text="(בחרי מהרשימה או הקלידי ידנית)",
                 fg="gray", font=("Arial", 8)).grid(row=1, column=3, sticky="w")

        # ─── סימולציה ───
        sim_frame = ttk.LabelFrame(self, text="סימולציה — בדיקה ללא אזעקה אמיתית")
        sim_frame.pack(fill="x", padx=12, pady=4)

        sim_alerts = [
            ("1",   "🔴 רקטות",  "#e74c3c", "white"),
            ("4",   "🟢 מחבלים", "#2ecc71", "white"),
            ("101", "🔵 תרגיל",  "#3498db", "white"),
        ]
        for i, (cat, name, bg, fg) in enumerate(sim_alerts):
            tk.Button(sim_frame, text=name, font=("Arial", 10, "bold"), width=14,
                      bg=bg, fg=fg,
                      command=lambda c=cat: self._simulate(c)
                      ).grid(row=0, column=i, padx=8, pady=6)

        self.extra_sim_visible = False
        self.extra_sim_btn = tk.Button(sim_frame, text="+ עוד",
                                       font=("Arial", 8), fg="gray",
                                       relief="flat", command=self._toggle_extra_sim)
        self.extra_sim_btn.grid(row=0, column=3, padx=4)

        self.extra_sim_frame = tk.Frame(sim_frame)
        extra_alerts = [("3", "🔴 כלי טיס"), ("5", "🟣 רעידה"), ("7", "🟡 כימי")]
        for i, (cat, name) in enumerate(extra_alerts):
            tk.Button(self.extra_sim_frame, text=name, font=("Arial", 9), width=12,
                      command=lambda c=cat: self._simulate(c)
                      ).grid(row=0, column=i, padx=4, pady=4)

        # ─── כפתורים ראשיים ───
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8)

        self.start_btn = tk.Button(btn_frame, text="▶  התחל מעקב",
                                   bg="#2ecc71", fg="white", font=("Arial", 11, "bold"),
                                   width=16, command=self._start)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(btn_frame, text="⏹  עצור",
                                  bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                                  width=16, command=self._stop, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=6)

        tk.Button(btn_frame, text="🔦 בדוק נורה",
                  font=("Arial", 10), width=14,
                  command=self._test_lamp).grid(row=0, column=2, padx=6)

        # ─── הגדרות מתקדמות (מוסתרות) ───
        self.adv_visible = False
        adv_toggle = tk.Button(self, text="⚙️ הגדרות מתקדמות ▼",
                               font=("Arial", 8), fg="gray", relief="flat",
                               command=self._toggle_advanced)
        adv_toggle.pack(pady=2)
        self.adv_toggle_btn = adv_toggle

        self.adv_frame = ttk.LabelFrame(self, text="הגדרות מתקדמות")
        self.optional_vars = {}
        optional_alerts = [
            ("5",  "🟣 רעידת אדמה"),
            ("8",  "🔵 צונאמי"),
            ("7",  "🟡 אירוע כימי"),
            ("6",  "🟢 חומרים רדיואקטיביים"),
        ]
        for i, (cat, name) in enumerate(optional_alerts):
            var = tk.BooleanVar(value=False)
            self.optional_vars[cat] = var
            tk.Checkbutton(self.adv_frame, text=name, variable=var,
                           font=("Arial", 9)).grid(row=0, column=i, padx=8, pady=4)

        # Checkbox כל הארץ
        self.all_country_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.adv_frame, text="🌍 הצג התרעות כל הארץ ביומן",
                       variable=self.all_country_var,
                       font=("Arial", 9, "bold")).grid(row=1, column=0, columnspan=4, pady=4, sticky="w", padx=8)

        # ─── סטטוס ───
        status_frame = ttk.LabelFrame(self, text="סטטוס")
        status_frame.pack(fill="x", padx=12, pady=6)
        self.status_dot = tk.Label(status_frame, text="⚫", font=("Arial", 18))
        self.status_dot.grid(row=0, column=0, padx=8)
        self.status_label = tk.Label(status_frame, text="לא פעיל", font=("Arial", 11))
        self.status_label.grid(row=0, column=1, sticky="w")

        # ─── יומן ───
        log_frame = ttk.LabelFrame(self, text="יומן")
        log_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.log_box = tk.Text(log_frame, height=8, width=60,
                               font=("Courier", 9), state="disabled",
                               bg="#1e1e1e", fg="#d4d4d4")
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        tk.Label(self, text="Developed by Shiri Schnapp Kashi | shiri@designservice.co.il",
                 fg="gray", font=("Arial", 7)).pack(pady=2)

    # ─── הגדרות מתקדמות ───
    def _toggle_advanced(self):
        if self.adv_visible:
            self.adv_frame.pack_forget()
            self.adv_toggle_btn.config(text="⚙️ הגדרות מתקדמות ▼")
        else:
            self.adv_frame.pack(fill="x", padx=12, pady=4)
            self.adv_toggle_btn.config(text="⚙️ הגדרות מתקדמות ▲")
        self.adv_visible = not self.adv_visible

    # ─── סריקת רשת ───
    def _scan_network(self):
        self.scan_btn.config(state="disabled", text="⏳ סורק...")
        self._log("🔍 מחפש נורות WiZ ברשת...")

        def _do():
            try:
                bulbs = run_async_return(discover_wiz_bulbs())
                if bulbs:
                    self.ip_var.set(bulbs[0])
                    self._log(f"✅ נמצאו {len(bulbs)} נורות: {', '.join(bulbs)}")
                    if len(bulbs) > 1:
                        # אם יש יותר מנורה אחת — הצג תפריט בחירה
                        self._show_bulb_selector(bulbs)
                else:
                    self._log("❌ לא נמצאו נורות WiZ ברשת")
                    messagebox.showinfo("לא נמצאו נורות",
                        "לא נמצאו נורות WiZ אוטומטית.\nנסי להזין את ה-IP ידנית מאפליקציית WiZ.")
            except Exception as e:
                self._log(f"❌ שגיאה בסריקה: {e}")
            finally:
                self.scan_btn.config(state="normal", text="🔍 סרוק רשת")

        threading.Thread(target=_do, daemon=True).start()

    def _show_bulb_selector(self, bulbs):
        win = tk.Toplevel(self)
        win.title("בחרי נורה")
        tk.Label(win, text="נמצאו מספר נורות — בחרי אחת:",
                 font=("Arial", 10)).pack(padx=12, pady=8)
        for ip in bulbs:
            tk.Button(win, text=ip, font=("Arial", 10), width=20,
                      command=lambda i=ip: [self.ip_var.set(i), win.destroy()]
                      ).pack(pady=3)

    def _toggle_extra_sim(self):
        if self.extra_sim_visible:
            self.extra_sim_frame.grid_remove()
            self.extra_sim_btn.config(text="+ עוד אפשרויות")
        else:
            self.extra_sim_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=4)
            self.extra_sim_btn.config(text="− פחות")
        self.extra_sim_visible = not self.extra_sim_visible

    def _log(self, msg):
        # התעלם משגיאות טכניות
        if any(x in msg for x in ["UTF-8 BOM", "utf-8-sig", "Expecting value", "JSONDecodeError"]):
            return
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_box.config(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _set_status(self, text, color, dot):
        self.status_label.config(text=text)
        self.status_dot.config(text=dot, fg=color)

    def _start(self):
        city = self.city_var.get().strip()
        ip = self.ip_var.get().strip()
        if not city or city in ("בחרי עיר...", "⏳ טוען ערים..."):
            messagebox.showwarning("חסר מידע", "נא לבחור עיר")
            return
        if not ip:
            if not messagebox.askyesno("ללא נורה",
                "לא הוזן IP של נורה.\nהמעקב יעבוד — ביומן ובהבהוב החלון בלבד.\nלהמשיך?"):
                return
        self.config_data["wiz_ip"] = ip
        self.config_data["my_city"] = city
        save_config(self.config_data)
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        if ip:
            self._set_status("מאזין להתרעות...", "green", "🟢")
            self.title("🚨 התרעות פיקוד העורף → WiZ — V4")
            self._log(f"▶ מתחיל מעקב | עיר: {city} | נורה: {ip}")
            self.demo_banner.pack_forget()
        else:
            self._set_status("מצב דמו — ללא נורה", "orange", "🟠")
            self.title("🚨 התרעות פיקוד העורף → WiZ — V4 | ⚠️ מצב דמו — ללא נורה")
            self._log(f"▶ מצב דמו (ללא נורה) | עיר: {city} | ביומן ובהבהוב בלבד")
            self.demo_banner.pack(fill="x", padx=12, pady=4)
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._set_status("לא פעיל", "gray", "⚫")
        self.title("🚨 התרעות פיקוד העורף → WiZ — V4")
        self.demo_banner.pack_forget()
        self._log("⏹ המעקב הופסק")

    def _test_lamp(self):
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showwarning("חסר IP", "נא למלא את ה-IP של הנורה")
            return
        self._log("🔦 בודק חיבור לנורה...")
        def _do():
            try:
                run_async(flash_and_set(ip, 255, 0, 0))
                time.sleep(2)
                run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
                self._log("✅ נורה מגיבה בהצלחה!")
            except Exception as e:
                self._log(f"❌ שגיאה: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _simulate(self, cat):
        color = ALERT_COLORS.get(cat, {"r": 255, "g": 0, "b": 0, "name": "🔴 התרעה"})
        ip = self.ip_var.get().strip()
        if ip:
            self._log(f"🧪 סימולציה: {color['name']}")
            self._set_status(f"⚠️ סימולציה: {color['name']}", "orange", "🟠")
        else:
            self._log(f"🧪 סימולציה דמו (ללא נורה): {color['name']}")
            self._set_status(f"⚠️ דמו בלבד — ללא נורה: {color['name']}", "orange", "🟠")

        # הבהוב החלון בכל מקרה
        hex_color = "#{:02x}{:02x}{:02x}".format(
            min(color["r"], 200), min(color["g"], 200), min(color["b"], 200))
        self._flash_window(hex_color)

        if ip:
            def _do():
                try:
                    run_async(flash_and_set(ip, color["r"], color["g"], color["b"]))
                    time.sleep(5)
                    run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
                    self._log("✅ סימולציה הסתיימה")
                    self._set_status("מאזין להתרעות..." if self.running else "לא פעיל",
                                     "green" if self.running else "gray",
                                     "🟢" if self.running else "⚫")
                except Exception as e:
                    self._log(f"❌ שגיאה בנורה: {e}")
            threading.Thread(target=_do, daemon=True).start()
        else:
            self._log("💡 מציג בממשק בלבד — אין נורה")
            self.after(5000, lambda: [
                self._set_status("מצב דמו — ללא נורה" if self.running else "לא פעיל",
                                 "orange" if self.running else "gray",
                                 "🟠" if self.running else "⚫"),
                self.configure(bg="SystemButtonFace")
            ])

    def _flash_window(self, color):
        """הבהוב חלון הממשק בצבע ההתרעה"""
        def _do():
            for i in range(6):
                bg = color if i % 2 == 0 else "SystemButtonFace"
                self.configure(bg=bg)
                time.sleep(0.35)
            self.configure(bg=color)
        threading.Thread(target=_do, daemon=True).start()

    def _monitor_loop(self):
        alert_active = False
        alert_end_time = 0
        last_alert_id = None
        seen_ids = set()
        ip = self.config_data["wiz_ip"]
        city = self.config_data["my_city"]
        try:
            run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
        except:
            pass

        while self.running:
            try:
                resp = requests.get(OREF_URL, headers=OREF_HEADERS, timeout=2)
                if not resp.text.strip():
                    resp = requests.get(OREF_URL_BACKUP, headers=OREF_HEADERS, timeout=2)
                alerts = []
                raw = resp.text.strip()
                
                # ניקוי BOM
                if raw.startswith('\ufeff'):
                    raw = raw[1:]
                raw = raw.strip()
                
                if resp.status_code == 200 and raw and raw not in ['', '[]', '{}']:
                    # לוג דיבוג
                    self._log(f"📡 קיבלתי: {raw[:100]}...")
                    try:
                        data = json.loads(raw)
                        if isinstance(data, dict) and "data" in data:
                            alerts = [data]
                        elif isinstance(data, list) and len(data) > 0:
                            alerts = data
                    except Exception as e:
                        self._log(f"❌ שגיאת פרסור: {e}")

                show_all = self.all_country_var.get()

                # סינון — ברירת מחדל: עיר. אם "כל הארץ" מסומן: הכל
                def is_relevant(a):
                    if show_all:
                        return True
                    if not city.strip():
                        return True
                    return any(
                        city.strip() == c.strip() or
                        city.strip() in c.strip() or
                        c.strip() in city.strip()
                        for c in a.get("data", [])
                    )

                relevant = [a for a in alerts if is_relevant(a)]

                for alert in relevant:
                    alert_id = alert.get("id", "")
                    if not alert_id or alert_id in seen_ids:
                        continue
                    seen_ids.add(alert_id)

                    cat = str(alert.get("cat", ""))
                    cities_str = ", ".join(alert.get("data", []))

                    # התרעה מקדימה
                    if cat == "14":
                        self._log(f"⚠️ התרעה מקדימה — בדקות הקרובות | {cities_str}")
                        self._set_status("⚠️ התרעה מקדימה", "orange", "🟠")
                        continue

                    # התרעת סיום (cat 10 או cat 13 עם "הסתיים")
                    if cat == "10" or (cat == "13" and "הסתיים" in alert.get("title", "")):
                        self._log(f"✅ האירוע הסתיים | {cities_str}")
                        continue

                    color = ALERT_COLORS.get(cat, {"r": 255, "g": 50, "b": 0, "name": "🟠 התרעה"})
                    enabled = (ALERT_COLORS.get(cat, {}).get("default_on", True)
                               or self.optional_vars.get(cat, tk.BooleanVar(value=False)).get())
                    if not enabled:
                        continue

                    self._log(f"🚨 {color['name']} | {cities_str}")

                    # פעולות רק אם העיר תואמת (גם במצב כל הארץ — נורה רק לעיר שלי)
                    city_match = not city.strip() or any(
                        city.strip() == c.strip() or city.strip() in c.strip() or c.strip() in city.strip()
                        for c in alert.get("data", [])
                    )
                    if city_match and (not alert_active or alert_id != last_alert_id):
                        self._set_status(f"{color['name']}", "red", "🔴")
                        hex_color = "#{:02x}{:02x}{:02x}".format(
                            min(color["r"], 200), min(color["g"], 200), min(color["b"], 200))
                        self._flash_window(hex_color)
                        if ip:
                            try:
                                run_async(flash_and_set(ip, color["r"], color["g"], color["b"]))
                            except Exception as e:
                                self._log(f"❌ נורה: {e}")
                        alert_active = True
                        last_alert_id = alert_id
                        alert_end_time = time.time() + self.config_data["alert_duration_sec"]

                if not relevant and alert_active and time.time() > alert_end_time:
                    self._log("✅ ההתרעה הסתיימה — חזרה לצבע רגיל")
                    self._set_status("מאזין להתרעות...", "green", "🟢")
                    try:
                        run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
                    except:
                        pass
                    alert_active = False
                    last_alert_id = None

            except Exception as e:
                pass  # שגיאות רשת — בשקט

            time.sleep(self.config_data["poll_interval_sec"])

    def _on_close(self):
        self.running = False
        self.destroy()


def run_async_return(coro):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(coro)
    loop.close()
    return result


if __name__ == "__main__":
    app = App()
    app.mainloop()
