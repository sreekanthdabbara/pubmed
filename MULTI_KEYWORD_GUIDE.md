# 🔍 Multi-Keyword Search Guide

Search multiple keywords at once and see results sorted by article count!

---

## ✨ **What's New**

**Multi-Keyword Search** allows you to:
- ✅ Search **multiple keywords** in one request
- ✅ See results **sorted by article count** (ascending or descending)
- ✅ **Compare research volume** across different topics
- ✅ **Group results** by keyword
- ✅ **Export organized data** with separate sheets per keyword

---

## 🚀 **How to Use**

### Step 1: Enter Multiple Keywords

You can enter keywords in **two ways**:

**Option A: One per line**
```
lung cancer
breast cancer
prostate cancer
```

**Option B: Comma-separated**
```
lung cancer, breast cancer, prostate cancer
```

### Step 2: Set Parameters

- **Results Per Keyword**: How many articles to fetch for each keyword (1-10,000)
- **Sort Order**: 
  - **Ascending** = Fewest articles first (shows least-researched topics first)
  - **Descending** = Most articles first (shows most-researched topics first)

### Step 3: View Sorted Results

Results are displayed:
1. **Summary cards** - Quick overview sorted by count
2. **Detailed sections** - Full article listings per keyword
3. **Click cards** to jump to that keyword's results

### Step 4: Export

Export to **Excel**, **CSV**, or **JSON**:
- **Excel**: Separate sheet for each keyword + summary sheet
- **CSV**: All results combined with keyword column
- **JSON**: Structured data with keywords separated

---

## 📊 **Example Use Cases**

### 1. Compare Cancer Types
**Goal**: See which cancer types have more research

**Keywords:**
```
lung cancer
breast cancer
prostate cancer
colon cancer
pancreatic cancer
```

**Sort**: Descending (most first)

**Result**: Shows which cancer types have the most published research

---

### 2. Track Research Trends
**Goal**: Compare research volume across years

**Keywords:**
```
COVID-19 AND 2020[pdat]
COVID-19 AND 2021[pdat]
COVID-19 AND 2022[pdat]
COVID-19 AND 2023[pdat]
```

**Sort**: Ascending or Descending

**Result**: See how COVID-19 research evolved year by year

---

### 3. Compare Treatment Methods
**Goal**: See which treatments are most studied

**Keywords:**
```
chemotherapy AND cancer
immunotherapy AND cancer
radiation therapy AND cancer
targeted therapy AND cancer
```

**Sort**: Descending

**Result**: Identify most-researched treatment approaches

---

### 4. Drug Comparison
**Goal**: Compare research on different medications

**Keywords:**
```
aspirin
ibuprofen
acetaminophen
naproxen
```

**Sort**: Descending

**Result**: See which drugs have more research literature

---

### 5. Disease Subtypes
**Goal**: Compare different types of diabetes

**Keywords:**
```
type 1 diabetes
type 2 diabetes
gestational diabetes
```

**Sort**: Descending

**Result**: Understand relative research focus on each type

---

## 🎯 **Understanding Sort Orders**

### Ascending (Fewest First)
```
1. rare disease           (50 articles)   ← Least researched
2. uncommon condition     (200 articles)
3. moderate topic         (1,000 articles)
4. common disease         (5,000 articles)
5. major topic            (20,000 articles) ← Most researched
```

**Use when**: You want to find **understudied topics** or identify research gaps

### Descending (Most First)
```
1. major topic            (20,000 articles) ← Most researched
2. common disease         (5,000 articles)
3. moderate topic         (1,000 articles)
4. uncommon condition     (200 articles)
5. rare disease           (50 articles)   ← Least researched
```

**Use when**: You want to see **most-studied topics** first or prioritize high-volume research

---

## 💡 **Pro Tips**

### 1. Use Specific Queries
Instead of broad terms, use PubMed syntax:
```
# Less specific
cancer

# More specific
"lung cancer" AND treatment AND 2023[pdat]
```

### 2. Limit Results for Speed
- For quick comparisons: 10-50 per keyword
- For comprehensive analysis: 100-1,000 per keyword
- For research databases: 1,000-10,000 per keyword

### 3. Combine with Filters
```
breast cancer AND 2023[pdat]
breast cancer AND review[Publication Type]
breast cancer AND nature[Journal]
```

### 4. Group Related Topics
Search variations together:
```
alzheimer
alzheimer disease
Alzheimer's disease
AD dementia
```

### 5. Use Export for Analysis
Excel export creates:
- Summary sheet with all keyword counts
- Separate sheet for each keyword
- Combined "All Results" sheet

Perfect for further analysis in Excel or Python!

---

## 📁 **Export Format Details**

### CSV Export
```csv
pmid,title,abstract,authors,journal,publication_date,url,keyword
12345678,Title 1,...,Authors,Journal,2023,URL,lung cancer
23456789,Title 2,...,Authors,Journal,2023,URL,lung cancer
34567890,Title 3,...,Authors,Journal,2023,URL,breast cancer
```

### JSON Export
```json
{
  "search_date": "20240214_120000",
  "sort_order": "ascending",
  "total_keywords": 3,
  "keywords": [
    {
      "keyword": "lung cancer",
      "article_count": 50,
      "articles": [...]
    },
    {
      "keyword": "breast cancer",
      "article_count": 120,
      "articles": [...]
    }
  ]
}
```

### Excel Export
```
Sheet 1: Summary
- Keyword | Article Count
- lung cancer | 50
- breast cancer | 120

Sheet 2: lung cancer
- All articles for lung cancer

Sheet 3: breast cancer
- All articles for breast cancer

Sheet 4: All Results
- Combined data from all keywords
```

---

## 🔧 **API Usage**

### Using the Multi-Keyword API

**Endpoint**: `POST /api/search/multi`

**Request:**
```json
{
  "keywords": ["lung cancer", "breast cancer", "prostate cancer"],
  "max_results_per_keyword": 20,
  "sort_order": "ascending"
}
```

**Response:**
```json
{
  "total_keywords": 3,
  "sort_order": "ascending",
  "results": [
    {
      "keyword": "prostate cancer",
      "count": 15,
      "articles": [...]
    },
    {
      "keyword": "lung cancer",
      "count": 18,
      "articles": [...]
    },
    {
      "keyword": "breast cancer",
      "count": 22,
      "articles": [...]
    }
  ]
}
```

**Python Example:**
```python
import requests

response = requests.post('http://localhost:5000/api/search/multi', json={
    'keywords': ['lung cancer', 'breast cancer', 'prostate cancer'],
    'max_results_per_keyword': 50,
    'sort_order': 'descending'
})

data = response.json()

for result in data['results']:
    print(f"{result['keyword']}: {result['count']} articles")
```

---

## ⏱️ **Time Estimates**

| Keywords | Results Each | Total Time |
|----------|--------------|------------|
| 3        | 20          | ~1 minute  |
| 5        | 50          | ~3 minutes |
| 10       | 100         | ~15 minutes|
| 20       | 100         | ~30 minutes|
| 5        | 1,000       | ~30 minutes|

*Times are approximate and depend on NCBI server load*

---

## ⚠️ **Important Notes**

### Rate Limiting
- The scraper respects NCBI rate limits
- Multiple keywords are processed sequentially (not parallel)
- Be patient with large searches

### Duplicate Handling
- Articles appearing in multiple keyword results will be listed separately
- Each keyword's results are independent
- Use the "All Results" Excel sheet to see combined unique articles

### Memory Considerations
- 10 keywords × 1,000 results = ~100MB memory
- Large searches (20+ keywords with 1,000+ each) may need time
- Consider running in batches if memory is limited

### Best Practices
1. **Test first**: Try 10 results per keyword to verify queries
2. **Limit keywords**: 3-10 keywords is optimal for most use cases
3. **Use filters**: Add date ranges or journal filters to refine
4. **Export regularly**: Don't rely on browser display for large datasets
5. **Be specific**: More specific queries = more relevant results

---

## 🆘 **Troubleshooting**

### "No results for some keywords"
- Check keyword spelling
- Try broader terms
- Use PubMed syntax correctly

### "Search taking too long"
- Reduce results per keyword
- Reduce number of keywords
- Check NCBI server status

### "Export file too large"
- Reduce results per keyword
- Export fewer keywords at once
- Use CSV instead of Excel for very large datasets

---

## 🎓 **Research Applications**

### Literature Review
Compare research volume across:
- Different diseases
- Treatment approaches
- Time periods
- Journals or institutions

### Gap Analysis
Use ascending sort to find:
- Understudied topics
- Emerging research areas
- Niche subjects needing attention

### Trend Analysis
Track changes over time:
- Year-by-year publication trends
- Emerging vs. declining topics
- Research hot spots

### Comparative Studies
Compare entities:
- Drug efficacy studies
- Disease prevalence research
- Treatment modalities
- Diagnostic methods

---

## 📚 **Additional Resources**

- [PubMed Search Guide](https://pubmed.ncbi.nlm.nih.gov/help/)
- [Advanced Search Syntax](https://www.ncbi.nlm.nih.gov/books/NBK3827/)
- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

---

**Happy Multi-Keyword Searching! 🔬**
