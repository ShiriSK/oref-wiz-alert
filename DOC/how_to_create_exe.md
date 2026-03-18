# 🛠️ מדריך: איך ליצור קובץ EXE מסקריפט Python

## 📜 על הפרויקט
קובץ זה עבר **35 עדכונים** במהלך הפיתוח!
שם הקובץ נשמר כ-V3 כדי לשמור על ההיסטוריה ב-Git.

---

## מה זה עושה?
הופך את קובץ ה-Python שלך לקובץ EXE אחד שרץ על כל מחשב Windows - **בלי צורך להתקין Python**.

---

## 📋 שלב 1: התקנת PyInstaller

פתח CMD והרץ:
```cmd
pip install pyinstaller
```

---

## 📋 שלב 2: יצירת קובץ EXE

### אפשרות א': קובץ EXE בודד (הכי פשוט)
```cmd
pyinstaller --onefile --noconsole oref_wiz_gui_v3.py
```

### אפשרות ב': עם אייקון מותאם
```cmd
pyinstaller --onefile --noconsole --icon=icon.ico oref_wiz_gui_v3.py
```

---

## 📋 שלב 3: איפה הקובץ?

אחרי ההרצה, הקובץ יהיה בתיקייה:
```
dist\oref_wiz_gui_v3.exe
```

---

## 🔧 הסבר על הפרמטרים

| פרמטר | הסבר |
|--------|-------|
| `--onefile` | יוצר קובץ EXE בודד (במקום תיקייה עם הרבה קבצים) |
| `--noconsole` | מסתיר את חלון ה-CMD השחור (לאפליקציות GUI) |
| `--icon=X.ico` | מוסיף אייקון מותאם לקובץ |
| `--name="X"` | שם הקובץ הסופי |
| `--windowed` | כמו noconsole (אפשר להשתמש בשניהם) |

---

## ⚠️ בעיות נפוצות ופתרונות

### בעיה 1: האנטיוירוס חוסם את הקובץ
**פתרון:** זה נורמלי. תוסיף חריגה באנטיוירוס או השתמש ב-`--key` להצפנה:
```cmd
pyinstaller --onefile --noconsole --key=mypassword123 oref_wiz_gui_v3.py
```

### בעיה 2: הקובץ גדול מדי
**פתרון:** השתמש ב-`--exclude-module` להסרת מודולים מיותרים:
```cmd
pyinstaller --onefile --noconsole --exclude-module=matplotlib --exclude-module=numpy oref_wiz_gui_v3.py
```

### בעיה 3: חסר DLL או מודול
**פתרון:** הוסף את המודול ידנית:
```cmd
pyinstaller --onefile --noconsole --hidden-import=requests oref_wiz_gui_v3.py
```

### בעיה 4: הקובץ לא רץ במחשב אחר
**פתרון:** ודא שהמחשב השני הוא Windows 10/11 64-bit (אם בנית על 64-bit).

---

## 📁 מבנה התיקיות אחרי הבנייה

```
project/
├── oref_wiz_gui_v3.py      ← הקובץ המקורי (35 עדכונים!)
├── oref_wiz_gui_v3.spec    ← קובץ הגדרות (נוצר אוטומטית)
├── build/                   ← קבצים זמניים (אפשר למחוק)
└── dist/
    └── oref_wiz_gui_v3.exe  ← ⭐ הקובץ הסופי!
```

---

## 🚀 פקודה מלאה מומלצת

```cmd
pyinstaller --onefile --noconsole --icon=alert.ico oref_wiz_gui_v3.py
```

---

## 💡 טיפים

1. **בדוק על המחשב שלך קודם** - הרץ את ה-EXE ממש מתיקיית `dist` (לא מקיצור דרך)

2. **מחק build ו-spec אם יש בעיות** - לפעמים קבצים ישנים גורמים לבעיות:
   ```cmd
   rmdir /s /q build
   del *.spec
   ```

3. **העתק רק את ה-EXE** - זה כל מה שצריך, לא צריך את שאר התיקיות

4. **שים לב לגודל** - קובץ EXE של Python יכול להיות 20-50MB, זה נורמלי

---

## 📱 להפצה

כשהקובץ מוכן:
1. העתק את `dist\oref_wiz_gui_v3.exe` לכל מחשב
2. לחץ עליו פעמיים
3. זה עובד! 🎉

---

## 🔄 עדכון גרסה

כל פעם שתשנה את הקוד:
1. ערוך את קובץ ה-Python
2. הרץ שוב את פקודת PyInstaller
3. ה-EXE החדש יחליף את הישן ב-`dist/`

---

*נוצר עבור פרויקט התרעות פיקוד העורף*
