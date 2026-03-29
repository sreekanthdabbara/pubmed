# ⚡ Quick Start Guide

Get your PubMed Scraper running in 3 minutes!

## 🚀 Super Fast Setup

### Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

### Step 2: Configure Email (30 seconds)

Open `app.py` and change line 15:

```python
NCBI_EMAIL = "your.email@example.com"  # ← Put your email here
```

### Step 3: Run the App (10 seconds)

```bash
python run.py
```

Or directly:

```bash
python app.py
```

### Step 4: Open in Browser

Navigate to: **http://localhost:5000**

🎉 **Done!** You're ready to search PubMed!

---

## 📖 First Search

1. Type "lung cancer" in the search box
2. Set results to 10
3. Click "Search PubMed"
4. View your results with full abstracts!

---

## 💡 Tips

- Use the example search cards on the home page
- Try advanced searches: `breast cancer AND treatment`
- Export results to CSV for analysis
- Check the About page for more search tips

---

## 🔧 Troubleshooting

**"No module named 'flask'"**
```bash
pip install flask biopython pandas
```

**"Address already in use"**
```bash
# Use a different port
python app.py --port 8000
```

**Can't access http://localhost:5000**
- Make sure the app is running
- Try http://127.0.0.1:5000
- Check your firewall settings

---

## 📚 Need More Help?

- Read `README_FLASK.md` for detailed documentation
- Check `README.md` for the API version
- Visit the About page in the app

---

**Happy Researching! 🧬**
