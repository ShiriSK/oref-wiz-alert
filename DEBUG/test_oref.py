import requests
import json
import time

OREF_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

print("בודק חיבור לפיקוד העורף...")
print("לחץ Ctrl+C לעצירה\n")

while True:
    try:
        resp = requests.get(OREF_URL, headers=OREF_HEADERS, timeout=2)
        raw = resp.text.strip()
        
        # ניקוי BOM
        if raw.startswith('\ufeff'):
            raw = raw[1:]
        raw = raw.strip()
        
        ts = time.strftime("%H:%M:%S")
        
        if raw and raw not in ['', '[]', '{}']:
            print(f"[{ts}] 🚨 יש התרעה!")
            print(f"    {raw[:200]}")
            print()
        else:
            print(f"[{ts}] אין התרעה (ריק)")
            
    except Exception as e:
        print(f"[{ts}] שגיאה: {e}")
    
    time.sleep(0.5)
