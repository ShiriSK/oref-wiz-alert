#!/usr/bin/env python3
"""
🚨 התרעות פיקוד העורף → נורה חכמה — V7
תמיכה ב: WiZ (WiFi) + BLE Bluetooth (LotusLamp)

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

# Try to import optional libraries
try:
    from pywizlight import wizlight, PilotBuilder, discovery
    HAS_WIZ = True
except ImportError:
    HAS_WIZ = False

try:
    from bleak import BleakClient, BleakScanner
    HAS_BLE = True
except ImportError:
    HAS_BLE = False

# ─── קובץ הגדרות ───
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "oref_wiz_config.json")
DEFAULT_CONFIG = {
    "light_type": "none",  # none, wiz, ble
    "wiz_ip": "",
    "ble_address": "",
    "my_city": "",
    "poll_interval_sec": 0.5,
    "alert_duration_sec": 60
}

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
# הנורה על לבן עמום ברוב הזמן, לבן בהיר באזעקה
STANDBY_COLOR = {"r": 10, "g": 10, "b": 10}  # כמעט כבויה
ALERT_BRIGHTNESS = {"r": 255, "g": 255, "b": 255}  # לבן מקסימלי

OREF_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_URL_BACKUP = "https://www.oref.org.il/warningMessages/alert/Alerts.json"
OREF_HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
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

# ─── Async helpers ───
def run_async(coro):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(coro)
    loop.close()

def run_async_return(coro):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(coro)
    loop.close()
    return result

# ─── WiZ Control ───
async def wiz_set_color(ip, r, g, b, brightness=255):
    if not HAS_WIZ:
        return
    bulb = wizlight(ip)
    await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=brightness))
    await bulb.async_close()

async def wiz_flash_and_set(ip, r, g, b):
    if not HAS_WIZ:
        return
    bulb = wizlight(ip)
    for i in range(6):
        br = 255 if i % 2 == 0 else 20
        await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=br))
        await asyncio.sleep(0.35)
    await bulb.turn_on(PilotBuilder(rgb=(r, g, b), brightness=255))
    await bulb.async_close()

async def discover_wiz_bulbs():
    if not HAS_WIZ:
        return []
    try:
        bulbs = await discovery.find_wizlights(wait_time=3)
        return [b.ip for b in bulbs]
    except:
        return []

# ─── BLE Control (LotusLamp) ───
BLE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

async def ble_set_color(address, r, g, b):
    if not HAS_BLE:
        return
    async with BleakClient(address, timeout=10) as client:
        cmd = bytes([0x7e, 0x00, 0x05, 0x03, r, g, b, 0x00, 0xef])
        await client.write_gatt_char(BLE_CHAR_UUID, cmd, response=False)

async def ble_turn_off(address):
    """הנורה על שחור (כבויה לגמרי)"""
    if not HAS_BLE:
        return
    async with BleakClient(address, timeout=10) as client:
        # שחור מלא
        cmd = bytes([0x7e, 0x00, 0x05, 0x03, 0, 0, 0, 0x00, 0xef])
        await client.write_gatt_char(BLE_CHAR_UUID, cmd, response=False)

async def ble_flash_and_set(address, r, g, b):
    if not HAS_BLE:
        return
    for i in range(6):
        if i % 2 == 0:
            await ble_set_color(address, r, g, b)
        else:
            await ble_set_color(address, 0, 0, 0)
        await asyncio.sleep(0.35)
    await ble_set_color(address, r, g, b)

async def discover_ble_devices():
    if not HAS_BLE:
        return []
    devices = await BleakScanner.discover(timeout=10)
    return devices

# ─── GUI ───
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚨 התרעות פיקוד העורף → נורה חכמה — V7")
        self.resizable(False, False)
        self.config_data = load_config()
        self.running = False
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        tk.Label(self, text="🚨 התרעות פיקוד העורף → נורה חכמה",
                 font=("Arial", 14, "bold")).pack(**pad)

        # באנר מצב דמו
        self.demo_banner = tk.Label(self,
            text="⚠️  מצב דמו — אין נורה מחוברת  ⚠️\nזה לא אמיתי — לבדיקה בלבד!",
            font=("Arial", 13, "bold"), fg="white", bg="#e67e22",
            pady=8)

        # ─── בחירת סוג נורה ───
        light_frame = ttk.LabelFrame(self, text="סוג נורה")
        light_frame.pack(fill="x", padx=12, pady=6)

        self.light_type_var = tk.StringVar(value=self.config_data.get("light_type", "none"))

        # ללא נורה
        ttk.Radiobutton(light_frame, text="ללא נורה (הבהוב חלון בלבד)",
                       variable=self.light_type_var, value="none",
                       command=self._on_light_type_change).grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # WiZ WiFi
        wiz_frame = ttk.Frame(light_frame)
        wiz_frame.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(wiz_frame, text="WiZ (WiFi):",
                       variable=self.light_type_var, value="wiz",
                       command=self._on_light_type_change).pack(side="left")
        self.wiz_ip_var = tk.StringVar(value=self.config_data.get("wiz_ip", ""))
        self.wiz_entry = ttk.Entry(wiz_frame, textvariable=self.wiz_ip_var, width=15)
        self.wiz_entry.pack(side="left", padx=5)
        self.wiz_scan_btn = ttk.Button(wiz_frame, text="🔍 סרוק", command=self._scan_wiz)
        self.wiz_scan_btn.pack(side="left")

        # BLE Bluetooth
        ble_frame = ttk.Frame(light_frame)
        ble_frame.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(ble_frame, text="Bluetooth (LotusLamp):",
                       variable=self.light_type_var, value="ble",
                       command=self._on_light_type_change).pack(side="left")
        self.ble_addr_var = tk.StringVar(value=self.config_data.get("ble_address", ""))
        self.ble_entry = ttk.Entry(ble_frame, textvariable=self.ble_addr_var, width=20)
        self.ble_entry.pack(side="left", padx=5)
        self.ble_scan_btn = ttk.Button(ble_frame, text="🔍 סרוק", command=self._scan_ble)
        self.ble_scan_btn.pack(side="left")

        # ─── הגדרות עיר ───
        city_frame = ttk.LabelFrame(self, text="הגדרות")
        city_frame.pack(fill="x", padx=12, pady=6)

        tk.Label(city_frame, text="העיר שלי:").grid(row=0, column=0, sticky="e", **pad)
        self.city_var = tk.StringVar(value=self.config_data.get("my_city", ""))
        self.city_combo = ttk.Combobox(city_frame, textvariable=self.city_var,
                                        width=25, state="normal")
        self.city_combo["values"] = CITIES
        self.city_combo.grid(row=0, column=1, sticky="w", padx=4)
        self.city_combo.set(self.config_data.get("my_city") or "בחרי עיר...")

        # Checkbox כל הארץ
        self.all_country_var = tk.BooleanVar(value=False)
        tk.Checkbutton(city_frame, text="🌍 הצג התרעות כל הארץ ביומן",
                       variable=self.all_country_var,
                       font=("Arial", 9)).grid(row=1, column=0, columnspan=2, pady=4, sticky="w", padx=8)

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

        self._on_light_type_change()

    def _on_light_type_change(self):
        lt = self.light_type_var.get()
        # Enable/disable relevant entry fields
        if lt == "wiz":
            self.wiz_entry.config(state="normal")
            self.wiz_scan_btn.config(state="normal")
            self.ble_entry.config(state="disabled")
            self.ble_scan_btn.config(state="disabled")
        elif lt == "ble":
            self.wiz_entry.config(state="disabled")
            self.wiz_scan_btn.config(state="disabled")
            self.ble_entry.config(state="normal")
            self.ble_scan_btn.config(state="normal")
        else:
            self.wiz_entry.config(state="disabled")
            self.wiz_scan_btn.config(state="disabled")
            self.ble_entry.config(state="disabled")
            self.ble_scan_btn.config(state="disabled")

    def _log(self, msg):
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

    # ─── סריקות ───
    def _scan_wiz(self):
        if not HAS_WIZ:
            messagebox.showerror("שגיאה", "ספריית pywizlight לא מותקנת.\nהריצי: pip install pywizlight")
            return
        self.wiz_scan_btn.config(state="disabled", text="⏳")
        self._log("🔍 מחפש נורות WiZ...")

        def _do():
            try:
                bulbs = run_async_return(discover_wiz_bulbs())
                if bulbs:
                    self.wiz_ip_var.set(bulbs[0])
                    self._log(f"✅ נמצאו {len(bulbs)} נורות: {', '.join(bulbs)}")
                else:
                    self._log("❌ לא נמצאו נורות WiZ")
            except Exception as e:
                self._log(f"❌ שגיאה: {e}")
            finally:
                self.wiz_scan_btn.config(state="normal", text="🔍 סרוק")

        threading.Thread(target=_do, daemon=True).start()

    def _scan_ble(self):
        if not HAS_BLE:
            messagebox.showerror("שגיאה", "ספריית bleak לא מותקנת.\nהריצי: pip install bleak")
            return
        self.ble_scan_btn.config(state="disabled", text="⏳")
        self._log("🔍 מחפש מכשירי Bluetooth...")

        def _do():
            try:
                devices = run_async_return(discover_ble_devices())
                if devices:
                    self._log(f"✅ נמצאו {len(devices)} מכשירים")
                    self.after(0, lambda: self._show_ble_selector(devices))
                else:
                    self._log("❌ לא נמצאו מכשירים")
            except Exception as e:
                self._log(f"❌ שגיאה: {e}")
            finally:
                self.ble_scan_btn.config(state="normal", text="🔍 סרוק")

        threading.Thread(target=_do, daemon=True).start()

    def _show_ble_selector(self, devices):
        win = tk.Toplevel(self)
        win.title("בחרי מכשיר Bluetooth")
        win.geometry("400x300")

        tk.Label(win, text="בחרי את הנורה:", font=("Arial", 10)).pack(pady=8)

        listbox = tk.Listbox(win, width=50, height=12, font=("Courier", 9))
        listbox.pack(padx=10, pady=5, fill="both", expand=True)

        for d in devices:
            name = d.name or "Unknown"
            listbox.insert("end", f"{name} | {d.address}")

        def select():
            sel = listbox.curselection()
            if sel:
                addr = devices[sel[0]].address
                self.ble_addr_var.set(addr)
                self._log(f"✅ נבחר: {addr}")
            win.destroy()

        tk.Button(win, text="בחר", command=select, font=("Arial", 10),
                  bg="#2ecc71", fg="white").pack(pady=8)

    # ─── בדיקת נורה ───
    def _test_lamp(self):
        lt = self.light_type_var.get()

        if lt == "none":
            self._log("💡 מצב ללא נורה - בדיקת הבהוב חלון")
            self._flash_window("#ff0000")
            return

        if lt == "wiz":
            ip = self.wiz_ip_var.get().strip()
            if not ip:
                messagebox.showwarning("חסר IP", "נא למלא IP של נורת WiZ")
                return
            self._log("🔦 בודק נורת WiZ...")
            def _do():
                try:
                    run_async(wiz_flash_and_set(ip, 255, 0, 0))
                    time.sleep(2)
                    run_async(wiz_set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
                    self._log("✅ נורה מגיבה!")
                except Exception as e:
                    self._log(f"❌ שגיאה: {e}")
            threading.Thread(target=_do, daemon=True).start()

        elif lt == "ble":
            addr = self.ble_addr_var.get().strip()
            if not addr:
                messagebox.showwarning("חסרת כתובת", "נא למלא כתובת Bluetooth")
                return
            self._log("🔦 בודק נורת Bluetooth...")
            def _do():
                try:
                    run_async(ble_flash_and_set(addr, 255, 0, 0))
                    time.sleep(2)
                    run_async(ble_turn_off(addr))  # כיבוי אחרי בדיקה
                    self._log("✅ נורה מגיבה!")
                except Exception as e:
                    self._log(f"❌ שגיאה: {e}")
            threading.Thread(target=_do, daemon=True).start()

    # ─── סימולציה ───
    def _simulate(self, cat):
        color = ALERT_COLORS.get(cat, {"r": 255, "g": 0, "b": 0, "name": "🔴 התרעה"})
        lt = self.light_type_var.get()

        self._log(f"🧪 סימולציה: {color['name']}")
        self._set_status(f"⚠️ סימולציה: {color['name']}", "orange", "🟠")

        # הבהוב חלון
        hex_color = "#{:02x}{:02x}{:02x}".format(
            min(color["r"], 200), min(color["g"], 200), min(color["b"], 200))
        self._flash_window(hex_color)

        # הבהוב נורה
        def _do():
            try:
                if lt == "wiz":
                    ip = self.wiz_ip_var.get().strip()
                    if ip:
                        run_async(wiz_flash_and_set(ip, color["r"], color["g"], color["b"]))
                        time.sleep(5)
                        # כיבוי אחרי סימולציה
                elif lt == "ble":
                    addr = self.ble_addr_var.get().strip()
                    if addr:
                        run_async(ble_flash_and_set(addr, color["r"], color["g"], color["b"]))
                        time.sleep(5)
                        run_async(ble_turn_off(addr))  # כיבוי אחרי סימולציה

                self._log("✅ סימולציה הסתיימה")
                self._set_status("מאזין להתרעות..." if self.running else "לא פעיל",
                                 "green" if self.running else "gray",
                                 "🟢" if self.running else "⚫")
            except Exception as e:
                self._log(f"❌ שגיאה: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def _flash_window(self, color):
        def _do():
            for i in range(6):
                bg = color if i % 2 == 0 else "SystemButtonFace"
                self.configure(bg=bg)
                time.sleep(0.35)
            self.configure(bg="SystemButtonFace")
        threading.Thread(target=_do, daemon=True).start()

    # ─── התחלה/עצירה ───
    def _start(self):
        city = self.city_var.get().strip()
        lt = self.light_type_var.get()

        if not city or city in ("בחרי עיר...", ""):
            messagebox.showwarning("חסר מידע", "נא לבחור עיר")
            return

        # Save config
        self.config_data["light_type"] = lt
        self.config_data["wiz_ip"] = self.wiz_ip_var.get().strip()
        self.config_data["ble_address"] = self.ble_addr_var.get().strip()
        self.config_data["my_city"] = city
        save_config(self.config_data)

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        if lt == "none":
            self._set_status("מצב דמו — ללא נורה", "orange", "🟠")
            self._log(f"▶ מצב דמו (ללא נורה) | עיר: {city}")
            self.demo_banner.pack(fill="x", padx=12, pady=4)
        else:
            self._set_status("מאזין להתרעות...", "green", "🟢")
            light_info = self.wiz_ip_var.get() if lt == "wiz" else self.ble_addr_var.get()
            self._log(f"▶ מתחיל מעקב | עיר: {city} | נורה: {light_info}")
            self.demo_banner.pack_forget()

        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._set_status("לא פעיל", "gray", "⚫")
        self.demo_banner.pack_forget()
        self._log("⏹ המעקב הופסק")

    def _monitor_loop(self):
        alert_active = False
        alert_end_time = 0
        last_alert_id = None
        seen_ids = set()
        lt = self.config_data["light_type"]
        wiz_ip = self.config_data["wiz_ip"]
        ble_addr = self.config_data["ble_address"]
        city = self.config_data["my_city"]

        # הנורה על עמעום מינימלי בהתחלה
        try:
            if lt == "ble" and ble_addr:
                run_async(ble_turn_off(ble_addr))
                self._log("💡 נורה על עמעום מינימלי - מוכנה להתרעות")
        except:
            pass

        while self.running:
            try:
                resp = requests.get(OREF_URL, headers=OREF_HEADERS, timeout=2)
                if not resp.text.strip():
                    resp = requests.get(OREF_URL_BACKUP, headers=OREF_HEADERS, timeout=2)

                raw = resp.text.strip()
                if raw.startswith('\ufeff'):
                    raw = raw[1:]
                raw = raw.strip()

                alerts = []
                if resp.status_code == 200 and raw and raw not in ['', '[]', '{}']:
                    try:
                        data = json.loads(raw)
                        if isinstance(data, dict) and "data" in data:
                            alerts = [data]
                        elif isinstance(data, list) and len(data) > 0:
                            alerts = data
                    except:
                        pass

                show_all = self.all_country_var.get()

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

                    # Skip early warning and end events
                    if cat == "14":
                        self._log(f"⚠️ התרעה מקדימה | {cities_str}")
                        continue
                    if cat == "10":
                        self._log(f"✅ האירוע הסתיים | {cities_str}")
                        continue

                    color = ALERT_COLORS.get(cat, {"r": 255, "g": 50, "b": 0, "name": "🟠 התרעה"})
                    self._log(f"🚨 {color['name']} | {cities_str}")

                    # Check city match for light activation
                    city_match = not city.strip() or any(
                        city.strip() == c.strip() or city.strip() in c.strip() or c.strip() in city.strip()
                        for c in alert.get("data", [])
                    )

                    if city_match and (not alert_active or alert_id != last_alert_id):
                        self._set_status(f"{color['name']}", "red", "🔴")
                        hex_color = "#{:02x}{:02x}{:02x}".format(
                            min(color["r"], 200), min(color["g"], 200), min(color["b"], 200))
                        self._flash_window(hex_color)

                        # Flash light
                        try:
                            if lt == "wiz" and wiz_ip:
                                run_async(wiz_flash_and_set(wiz_ip, color["r"], color["g"], color["b"]))
                            elif lt == "ble" and ble_addr:
                                run_async(ble_flash_and_set(ble_addr, color["r"], color["g"], color["b"]))
                        except Exception as e:
                            self._log(f"❌ נורה: {e}")

                        alert_active = True
                        last_alert_id = alert_id
                        alert_end_time = time.time() + self.config_data["alert_duration_sec"]

                # Return to normal after alert ends
                if not relevant and alert_active and time.time() > alert_end_time:
                    self._log("✅ ההתרעה הסתיימה — נורה על עמעום")
                    self._set_status("מאזין להתרעות...", "green", "🟢")
                    try:
                        if lt == "ble" and ble_addr:
                            run_async(ble_turn_off(ble_addr))
                    except:
                        pass
                    alert_active = False
                    last_alert_id = None

                # Clean old IDs
                if len(seen_ids) > 200:
                    seen_ids = set(list(seen_ids)[-100:])

            except Exception as e:
                pass  # Silent network errors

            time.sleep(self.config_data["poll_interval_sec"])

    def _on_close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
