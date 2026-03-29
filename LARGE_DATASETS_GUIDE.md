# 📊 Guide: Searching for 40,000+ Results

Yes, you can search for 40,000 or even 100,000 results! Here's everything you need to know.

---

## ⏱️ **Time Estimates**

| Results | Approximate Time |
|---------|-----------------|
| 1,000   | ~2 minutes |
| 5,000   | ~10 minutes |
| 10,000  | ~20 minutes |
| 40,000  | **~60-80 minutes** |
| 100,000 | ~3-4 hours |

**Why so long?** NCBI rate limits API requests to prevent server overload. We must be polite!

---

## 🚀 **Quick Fix: Modify Existing Code**

### Option 1: Edit Current Files (Simple)

Open **`app.py`** or **`app_standalone.py`** and find this line (around line 39):

```python
if max_results < 1 or max_results > 500:  # ← Change 500 to 100000
```

Change it to:

```python
if max_results < 1 or max_results > 100000:  # Now supports 100,000!
```

**That's it!** Now you can enter 40,000 in the web form.

---

### Option 2: Use the Large Dataset Version (Better)

I've created **`app_large_datasets.py`** with:
- ✅ Support for 100,000 results
- ✅ Progress tracking
- ✅ Optimized batching
- ✅ Better error handling
- ✅ Memory efficiency

**Use this for large searches!**

---

## ⚙️ **Optimizations for Large Datasets**

### 1. Increase Batch Size

In `pubmed_api_scraper.py`, change line 91:

```python
batch_size = 100  # Instead of 10 - fetches more at once
```

### 2. Adjust Sleep Time (Carefully!)

Line 108 - reduce delay slightly:

```python
time.sleep(0.3)  # Instead of 0.5 - faster but still polite
```

⚠️ **Don't go below 0.3 seconds** or NCBI might block you!

### 3. Use Smaller Batches for Stability

For 40,000+ results, smaller batches = more stable:

```python
batch_size = 50  # More requests but less likely to fail
```

---

## 💾 **Memory & Storage Considerations**

### File Sizes for 40,000 Results:

- **CSV**: ~50-80 MB
- **JSON**: ~100-150 MB  
- **Excel**: ~60-100 MB

### RAM Usage:
- ~500 MB - 1 GB during processing
- Most computers can handle this fine

---

## 🎯 **Best Practices for Large Searches**

### 1. **Use API Instead of Web Interface**

For 40,000 results, use the API endpoint:

```python
import requests
import json

response = requests.post('http://localhost:5000/api/search', json={
    'query': 'lung cancer',
    'max_results': 40000
})

data = response.json()

# Save to file
with open('results.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### 2. **Run Overnight**

For huge datasets:
```bash
# Start in background (Linux/Mac)
nohup python app_large_datasets.py &

# Then make your request
# Results will be ready in the morning!
```

### 3. **Split into Chunks**

Instead of 40,000 at once, do 4 searches of 10,000:

```python
# Use date filters
queries = [
    "cancer AND 2023[pdat]",
    "cancer AND 2022[pdat]",
    "cancer AND 2021[pdat]",
    "cancer AND 2020[pdat]"
]

for query in queries:
    # Search and save each
```

### 4. **Use Specific Queries**

Narrow your search to reduce results:

```python
# Instead of:
"cancer"  # 40,000+ results

# Try:
"lung cancer AND treatment AND 2023[pdat]"  # More focused
```

---

## 🔧 **Example: Fetching 40,000 Results**

### Using the Web Interface:

1. Open http://localhost:5000
2. Enter query: `breast cancer`
3. Enter max results: `40000`
4. Click Search
5. **Wait ~60-80 minutes**
6. Download when complete

### Using Python Script:

```python
from pubmed_api_scraper import PubMedScraper

scraper = PubMedScraper(email="your.email@example.com")

print("Starting search for 40,000 results...")
print("This will take approximately 60-80 minutes...")

results = scraper.search_and_extract(
    query="lung cancer",
    max_results=40000
)

print(f"Retrieved {len(results)} articles!")

# Save to CSV
results.to_csv("lung_cancer_40k.csv", index=False)
print("Saved to lung_cancer_40k.csv")
```

---

## ⚠️ **Important Warnings**

### 1. **NCBI Rate Limiting**
- Don't make multiple large requests simultaneously
- Wait at least 30 minutes between large searches
- NCBI may temporarily block your IP if you're too aggressive

### 2. **Don't Interrupt**
- Once started, let it finish
- Interrupting wastes the work done so far
- Use `Ctrl+C` carefully

### 3. **Check Available Results**
- Not all queries have 40,000 results
- The scraper will get whatever exists (up to your max)

### 4. **Disk Space**
- Make sure you have 500MB+ free space
- Large Excel files can be slow to open

---

## 📈 **Monitoring Progress**

### In Terminal:
You'll see output like:
```
Searching PubMed for: lung cancer
Found 40000 articles
Fetching articles 1 to 100...
Fetching articles 101 to 200...
...
```

### With Progress Tracking (app_large_datasets.py):
Check progress via API:
```bash
curl http://localhost:5000/api/progress/search_123456
```

---

## 🆘 **Troubleshooting Large Searches**

### "Connection timeout"
- NCBI servers busy
- Wait 5 minutes and try again
- Reduce batch size

### "Empty results after long wait"
- Check your query syntax
- Try a simpler search first
- Verify internet connection

### "Memory error"
- Close other programs
- Reduce max_results
- Use the optimized version

### "Takes forever"
- This is normal!
- 40,000 results legitimately takes 60+ minutes
- Consider splitting into smaller searches

---

## 💡 **Pro Tips**

1. **Test First**: Try 100 results to verify query works
2. **Save Incrementally**: Modify code to save every 1,000 results
3. **Use Filters**: Date ranges reduce result counts
4. **Schedule Wisely**: Run overnight or during low-usage times
5. **Have Backup**: NCBI can go down - be prepared to retry

---

## 🎯 **Recommended Workflow for 40,000 Results**

```bash
# 1. Test with small sample
python -c "
from pubmed_api_scraper import PubMedScraper
s = PubMedScraper('your@email.com')
results = s.search_and_extract('your query', 100)
print(f'Found {len(results)} results')
"

# 2. If results look good, do the full search
# Use app_large_datasets.py for best experience
python app_large_datasets.py

# 3. In browser, enter 40000 and start search
# 4. Go do something else for an hour!
# 5. Come back and download your data
```

---

**Bottom Line:** Yes, 40,000 results work! Just be patient and use the optimized version for best results. ⏳
