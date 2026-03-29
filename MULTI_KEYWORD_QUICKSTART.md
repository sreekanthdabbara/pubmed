# 🎯 Multi-Keyword Search - Quick Start

Your PubMed scraper now supports **multi-keyword search with sorting**!

---

## ✨ **What You Asked For**

✅ Search **multiple keywords** at once  
✅ Display results in **ascending order** by article count  
✅ See which topics have **more/fewer articles**  
✅ **Compare research volume** across keywords  

**All implemented!** 🎉

---

## 🚀 **How to Use**

### Option 1: Web Interface (Easiest)

1. **Run the multi-keyword app:**
   ```bash
   python app_multi_keyword.py
   ```

2. **Open browser:** http://localhost:5000

3. **Enter keywords** (one per line or comma-separated):
   ```
   lung cancer
   breast cancer
   prostate cancer
   ```

4. **Set max results per keyword:** e.g., 20

5. **Choose sort order:**
   - **Ascending** = Fewest articles first ⬆️
   - **Descending** = Most articles first ⬇️

6. **Click "Search All Keywords"**

7. **View results:**
   - Summary cards showing count for each keyword
   - Results sorted by article count
   - Click cards to jump to detailed results

---

### Option 2: API/Python Script

```python
import requests

response = requests.post('http://localhost:5000/api/search/multi', json={
    'keywords': ['lung cancer', 'breast cancer', 'prostate cancer'],
    'max_results_per_keyword': 50,
    'sort_order': 'ascending'  # or 'descending'
})

data = response.json()

# Display sorted results
for result in data['results']:
    print(f"{result['keyword']}: {result['count']} articles")
```

---

## 📊 **Example Output**

**Search:** lung cancer, breast cancer, prostate cancer  
**Sort:** Ascending (fewest first)

**Results:**
```
1. prostate cancer    →  15 articles  ← Fewest (shown first)
2. lung cancer        →  18 articles
3. breast cancer      →  22 articles  ← Most (shown last)
```

**Search:** Same keywords  
**Sort:** Descending (most first)

**Results:**
```
1. breast cancer      →  22 articles  ← Most (shown first)
2. lung cancer        →  18 articles
3. prostate cancer    →  15 articles  ← Fewest (shown last)
```

---

## 💡 **Use Cases**

### 1. Find Research Gaps (Use Ascending)
```
Keywords: rare disease 1, rare disease 2, rare disease 3
Result: Shows which disease is least studied → research opportunity!
```

### 2. Identify Hot Topics (Use Descending)
```
Keywords: treatment A, treatment B, treatment C
Result: Shows which treatment has most research → established field
```

### 3. Compare Over Time
```
Keywords: 
  COVID-19 AND 2020[pdat]
  COVID-19 AND 2021[pdat]
  COVID-19 AND 2022[pdat]
Result: See publication trends year by year
```

---

## 📥 **Export Features**

All export formats organize results by keyword:

**Excel Export:**
- Sheet 1: Summary (keywords + counts)
- Sheet 2-N: One sheet per keyword
- Last Sheet: All results combined

**CSV Export:**
- All results with "keyword" column
- Easy to filter/sort in Excel

**JSON Export:**
- Structured by keyword
- Perfect for further programming

---

## 📂 **Files You Need**

### Core Files:
- **app_multi_keyword.py** - Main application
- **index_multi.html** - Search page (put in templates/)
- **results_multi.html** - Results page (put in templates/)

### Optional:
- **example_multi_keyword.py** - Python usage examples
- **MULTI_KEYWORD_GUIDE.md** - Complete documentation

### Easy Option:
- **pubmed_scraper_with_multikeyword.zip** - Everything in one package!

---

## 🎯 **Setup Instructions**

### Step 1: Download Files

**Option A:** Download the ZIP
- Extract `pubmed_scraper_with_multikeyword.zip`
- All files already organized!

**Option B:** Download individual files
1. Download `app_multi_keyword.py`
2. Download `index_multi.html` → put in `templates/` folder
3. Download `results_multi.html` → put in `templates/` folder
4. (Use existing `base.html`, `style.css`, etc.)

### Step 2: Configure

Edit `app_multi_keyword.py` line 215:
```python
NCBI_EMAIL = "your.email@example.com"  # Change to your email
```

### Step 3: Install Dependencies

```bash
pip install flask biopython pandas openpyxl
```

### Step 4: Run!

```bash
python app_multi_keyword.py
```

Open: http://localhost:5000

---

## 🔍 **Quick Examples**

### Example 1: Cancer Comparison
```
Keywords (one per line):
lung cancer
breast cancer
prostate cancer
colon cancer

Results Per Keyword: 50
Sort: Descending

→ Shows which cancer type has most research
```

### Example 2: Drug Research
```
Keywords (comma-separated):
aspirin, ibuprofen, acetaminophen, naproxen

Results Per Keyword: 100
Sort: Descending

→ Compare research volume for each drug
```

### Example 3: Time Trends
```
Keywords:
machine learning AND 2020[pdat]
machine learning AND 2021[pdat]
machine learning AND 2022[pdat]
machine learning AND 2023[pdat]

Results Per Keyword: 200
Sort: Ascending

→ See how research grew year by year
```

---

## ⏱️ **Performance**

| Keywords | Results Each | Time     |
|----------|--------------|----------|
| 3        | 20          | ~1 min   |
| 5        | 50          | ~3 min   |
| 10       | 100         | ~15 min  |

---

## 🆘 **Troubleshooting**

**Templates not found?**
```bash
# Make sure folder structure is:
your-project/
├── app_multi_keyword.py
└── templates/
    ├── base.html
    ├── index_multi.html
    └── results_multi.html
```

**Still issues?**
- Download the ZIP file (has everything organized)
- OR use the standalone version (coming next if you need it)

---

## 📚 **Documentation**

- **MULTI_KEYWORD_GUIDE.md** - Full guide with examples
- **example_multi_keyword.py** - Python code examples

---

## 🎉 **Summary**

You can now:
- ✅ Search multiple keywords at once
- ✅ Sort by article count (ascending/descending)
- ✅ See results grouped by keyword
- ✅ Export organized data
- ✅ Compare research volumes

**Perfect for research gap analysis, trend tracking, and topic comparison!**

---

**Need help? Check MULTI_KEYWORD_GUIDE.md for detailed examples!** 📖
