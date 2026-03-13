#!/usr/bin/env python3
"""
🚨 התרעות פיקוד העורף → נורת WiZ — V3
אפליקציה עצמאית — ללא צורך בהתקנת Python

Developed by Shiri Schnapp Kashi
Contact: shiri@designservice.co.il
"""

import asyncio
import requests
import json
import time
import threading
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pywizlight import wizlight, PilotBuilder

# ─── קובץ הגדרות ───
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "oref_wiz_config.json")

DEFAULT_CONFIG = {
    "wiz_ip": "",
    "my_city": "",
    "poll_interval_sec": 2,
    "alert_duration_sec": 60,
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
    # תמיד פעילים
    "1":   {"r": 255, "g": 0,   "b": 0,   "name": "🔴 ירי רקטות",        "default_on": True},
    "2":   {"r": 255, "g": 0,   "b": 0,   "name": "🔴 ירי לא מזוהה",     "default_on": True},
    "3":   {"r": 255, "g": 50,  "b": 0,   "name": "🔴 חדירת כלי טיס",    "default_on": True},
    "4":   {"r": 0,   "g": 220, "b": 0,   "name": "🟢 חדירת מחבלים",     "default_on": True},
    "13":  {"r": 255, "g": 0,   "b": 0,   "name": "🔴 פיגוע",             "default_on": True},
    "101": {"r": 0,   "g": 200, "b": 255, "name": "🔵 תרגיל",             "default_on": True},
    # כבויים כברירת מחדל — המשתמש בוחר
    "5":   {"r": 128, "g": 0,   "b": 255, "name": "🟣 רעידת אדמה",        "default_on": False},
    "6":   {"r": 0,   "g": 255, "b": 100, "name": "🟢 חומרים רדיואקטיביים","default_on": False},
    "7":   {"r": 255, "g": 255, "b": 0,   "name": "🟡 אירוע כימי",        "default_on": False},
    "8":   {"r": 0,   "g": 100, "b": 255, "name": "🔵 צונאמי",             "default_on": False},
}
NORMAL = {"r": 255, "g": 220, "b": 150, "brightness": 180}

OREF_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
}

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

# ─── GUI ───
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚨 התרעות פיקוד העורף → WiZ — V3")
        self.resizable(False, False)
        self.config = load_config()
        self.running = False
        self.monitor_thread = None
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # כותרת
        tk.Label(self, text="🚨 התרעות פיקוד העורף → נורת WiZ",
                 font=("Arial", 14, "bold")).pack(**pad)

        # הגדרות
        frame = ttk.LabelFrame(self, text="הגדרות")
        frame.pack(fill="x", padx=12, pady=6)

        tk.Label(frame, text="IP של הנורה:").grid(row=0, column=0, sticky="e", **pad)
        self.ip_var = tk.StringVar(value=self.config["wiz_ip"])
        tk.Entry(frame, textvariable=self.ip_var, width=20).grid(row=0, column=1, sticky="w", **pad)
        tk.Label(frame, text="(מצא ב: אפליקציית WiZ → Settings → Device IP)",
                 fg="gray", font=("Arial", 8)).grid(row=0, column=2, sticky="w")

        tk.Label(frame, text="העיר שלי:").grid(row=1, column=0, sticky="e", **pad)
        self.city_var = tk.StringVar(value=self.config["my_city"])
        tk.Entry(frame, textvariable=self.city_var, width=20).grid(row=1, column=1, sticky="w", **pad)
        tk.Label(frame, text='(בעברית, לדוגמה: "אום אל-פחם")',
                 fg="gray", font=("Arial", 8)).grid(row=1, column=2, sticky="w")

        # התרעות אופציונליות
        opt_frame = ttk.LabelFrame(self, text="התרעות נוספות (כבויות כברירת מחדל)")
        opt_frame.pack(fill="x", padx=12, pady=4)

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
            tk.Checkbutton(opt_frame, text=name, variable=var,
                          font=("Arial", 9)).grid(row=0, column=i, padx=8, pady=4)

        # כפתורים
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

        # סטטוס
        status_frame = ttk.LabelFrame(self, text="סטטוס")
        status_frame.pack(fill="x", padx=12, pady=6)

        self.status_dot = tk.Label(status_frame, text="⚫", font=("Arial", 18))
        self.status_dot.grid(row=0, column=0, padx=8)

        self.status_label = tk.Label(status_frame, text="לא פעיל",
                                     font=("Arial", 11))
        self.status_label.grid(row=0, column=1, sticky="w")

        # לוג
        log_frame = ttk.LabelFrame(self, text="יומן")
        log_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.log_box = tk.Text(log_frame, height=8, width=55,
                               font=("Courier", 9), state="disabled",
                               bg="#1e1e1e", fg="#d4d4d4")
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

    def _log(self, msg):
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
        ip = self.ip_var.get().strip()
        city = self.city_var.get().strip()
        if not ip or not city:
            messagebox.showwarning("חסר מידע", "נא למלא IP של הנורה ושם העיר")
            return
        self.config["wiz_ip"] = ip
        self.config["my_city"] = city
        save_config(self.config)

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._set_status("מאזין להתרעות...", "green", "🟢")
        self._log(f"▶ מתחיל מעקב | עיר: {city} | נורה: {ip}")

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._set_status("לא פעיל", "gray", "⚫")
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

    def _monitor_loop(self):
        alert_active = False
        alert_end_time = 0
        last_alert_id = None
        ip = self.config["wiz_ip"]
        city = self.config["my_city"]

        # נורה לצבע רגיל בהתחלה
        try:
            run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
        except:
            pass

        while self.running:
            try:
                resp = requests.get(OREF_URL, headers=OREF_HEADERS, timeout=4)
                alerts = []
                if resp.status_code == 200 and resp.text.strip():
                    data = resp.json()
                    if isinstance(data, dict) and "data" in data:
                        alerts = [data]
                    elif isinstance(data, list):
                        alerts = data

                my_alerts = [
                    a for a in alerts
                    if any(city in c or c in city for c in a.get("data", []))
                    and (
                        ALERT_COLORS.get(str(a.get("cat","")), {}).get("default_on", True)
                        or self.optional_vars.get(str(a.get("cat","")), tk.BooleanVar(value=False)).get()
                    )
                ]

                if my_alerts:
                    alert = my_alerts[0]
                    alert_id = alert.get("id", "")
                    cat = str(alert.get("cat", ""))
                    color = ALERT_COLORS.get(cat, {"r": 255, "g": 50, "b": 0, "name": "🟠 התרעה"})

                    if not alert_active or alert_id != last_alert_id:
                        cities_str = ", ".join(alert.get("data", []))
                        self._log(f"🚨 {color['name']} | {cities_str}")
                        self._set_status(f"{color['name']}", "red", "🔴")
                        try:
                            run_async(flash_and_set(ip, color["r"], color["g"], color["b"]))
                        except Exception as e:
                            self._log(f"❌ נורה: {e}")
                        alert_active = True
                        last_alert_id = alert_id
                        alert_end_time = time.time() + self.config["alert_duration_sec"]
                else:
                    if alert_active and time.time() > alert_end_time:
                        self._log("✅ ההתרעה הסתיימה — חזרה לצבע רגיל")
                        self._set_status("מאזין להתרעות...", "green", "🟢")
                        try:
                            run_async(set_color(ip, NORMAL["r"], NORMAL["g"], NORMAL["b"], NORMAL["brightness"]))
                        except:
                            pass
                        alert_active = False
                        last_alert_id = None

            except Exception as e:
                self._log(f"⚠️ שגיאת רשת: {e}")

            time.sleep(self.config["poll_interval_sec"])

    def _on_close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
