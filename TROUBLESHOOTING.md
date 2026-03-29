# 🔧 Troubleshooting: "Unresolved reference 'pubmed_api_scraper'"

This error means your Flask app can't find the PubMed scraper module. Here are the solutions:

## ✅ Solution 1: Use the Standalone Version (EASIEST)

I've created **`app_standalone.py`** which has everything in one file!

### Steps:
1. Use `app_standalone.py` instead of `app.py`
2. Update your email on line 183
3. Run it:
```bash
python app_standalone.py
```

**That's it!** No import issues. ✅

---

## ✅ Solution 2: Fix the File Structure

If you want to use the original `app.py`, make sure files are organized correctly:

### Required Structure:
```
your-folder/
├── app.py                      ← Main app
├── pubmed_api_scraper.py       ← Must be in SAME folder
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   └── about.html
└── static/
    └── style.css
```

### Verify Setup:
```bash
python verify_setup.py
```

This script will check if everything is in the right place.

---

## ✅ Solution 3: Check Your Python Path

If files are in the right place but still not working:

### Option A: Run from the correct directory
```bash
cd /path/to/your/folder
python app.py
```

### Option B: Add the directory to Python path
```python
# At the top of app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pubmed_api_scraper import PubMedScraper
```

---

## 🔍 Quick Diagnosis

Run this command in your project folder:

### Windows:
```cmd
dir
```

### Mac/Linux:
```bash
ls -la
```

**You should see BOTH:**
- ✓ `app.py`
- ✓ `pubmed_api_scraper.py`

If `pubmed_api_scraper.py` is missing, download it from the files I provided!

---

## 🆘 Still Having Issues?

### Check 1: Are you in the right folder?
```bash
# Check current directory
pwd         # Mac/Linux
cd          # Windows

# You should be in the folder containing app.py
```

### Check 2: Is Python finding the file?
```bash
python -c "import pubmed_api_scraper; print('Success!')"
```

If this fails, the file isn't in the right place or Python can't see it.

### Check 3: IDE-specific issue?
If using PyCharm/VS Code:
- Right-click the project folder → "Mark Directory as Sources Root"
- Restart your IDE
- Rebuild the project index

---

## 📋 Checklist

- [ ] Both `app.py` and `pubmed_api_scraper.py` are in the same folder
- [ ] You're running the command from that folder
- [ ] All dependencies are installed (`pip install -r requirements.txt`)
- [ ] You've updated the email in the file
- [ ] `templates/` and `static/` folders exist

---

## 🎯 Recommended: Just Use the Standalone Version!

The easiest solution is to use **`app_standalone.py`**:

1. Delete the old files
2. Use `app_standalone.py` 
3. Update email (line 183)
4. Run: `python app_standalone.py`

No imports, no issues! 🎉

---

## 💬 Common Questions

**Q: Do I need both files?**  
A: Yes, if using `app.py`. OR just use `app_standalone.py` alone.

**Q: Can I rename pubmed_api_scraper.py?**  
A: Not recommended. If you do, update the import in `app.py`.

**Q: Why does the standalone version work?**  
A: It has the PubMedScraper class built directly into the file - no external imports needed!

---

**Need more help?** Run `python verify_setup.py` to diagnose the issue!
