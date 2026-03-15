# 🚨 OrefWiz Alert — V3

מערכת התרעות חזותית לחירשים וכבדי שמיעה

![OrefWiz Alert GUI](GUI_WIZ_ALERT.png)

> Developed by **Shiri Schnapp Kashi** | [shiri@designservice.co.il](mailto:shiri@designservice.co.il)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

---

## 💡 הרעיון

אנשים חירשים וכבדי שמיעה לא שומעים את צופר האזעקה. 
המערכת הזו מתחברת לפיקוד העורף ומפעילה נורה חכמה (WiZ) בצבע אדום כשיש התרעה.

## ✨ תכונות

- 🔴 הבהוב נורה חכמה בעת התרעה
- 📍 סינון לפי עיר או "כל הארץ"
- 🎨 צבעים שונים לסוגי התרעות שונים
- 📱 תמיכה בטלגרם (בוט)
- 💻 ממשק גרפי פשוט בעברית
- ⚡ בדיקה כל 0.5 שניות

## 🚀 התקנה מהירה

### דרישות
- Python 3.9 ומעלה
- נורת WiZ חכמה (אופציונלי)

### שלבים

```bash
# 1. Clone the repository
git clone https://github.com/ShiriSK/oref-wiz-alert.git
cd oref-wiz-alert

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python oref_wiz_gui_v3.py
```

## 📁 מבנה הפרויקט

```
oref-wiz-alert/
├── oref_wiz_gui_v3.py    # Main GUI application
├── test_oref.py          # Test script for API connection
├── debug/
│   └── oref_debug.py     # Debug version with extra logging
├── requirements.txt
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## 🔧 שימוש

1. **הפעל את התוכנה** - `python oref_wiz_gui_v3.py`
2. **בחר עיר** - או סמן "כל הארץ"
3. **הכנס IP של נורה** (אופציונלי) - מצא באפליקציית WiZ
4. **לחץ "התחל מעקב"**

### ללא נורה
התוכנה תעבוד גם ללא נורה - תציג התרעות ביומן ותבהב את החלון.

### עם נורת WiZ
1. התקן את אפליקציית WiZ
2. חבר את הנורה לרשת
3. מצא את ה-IP בהגדרות הנורה
4. הכנס את ה-IP בתוכנה

## 🐛 דיבוג

אם יש בעיות, הרץ את גרסת הדיבוג:

```bash
python debug/oref_debug.py
```

זה יציג לוגים מפורטים של מה שמגיע מהשרת.

## 📱 בוט טלגרם

ראה את הקובץ `telegram_bot.py` להפעלת בוט טלגרם שישלח התרעות.

## ⚠️ הערות חשובות

- המערכת מסתמכת על API של פיקוד העורף
- ההתרעות נשארות באתר רק מספר שניות
- מומלץ להשאיר את התוכנה רצה ברקע

## 🤝 תרומה

תרומות מתקבלות בברכה! ראה [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 רישיון

MIT License - ראה [LICENSE](LICENSE)

---

**שימו לב:** זו מערכת עזר בלבד. תמיד הקשיבו להנחיות פיקוד העורף הרשמיות.
