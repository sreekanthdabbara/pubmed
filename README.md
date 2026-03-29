# PubMed Abstract Scraper

A Python application to search PubMed and extract article abstracts.

## 🎯 Recommended Approach: API-Based Scraper

**Use `pubmed_api_scraper.py`** - This uses PubMed's official E-utilities API.

### Advantages:
✅ **Faster** - Batch retrieval of articles  
✅ **More reliable** - Official API with guaranteed data structure  
✅ **Respectful** - Follows PubMed's terms of service  
✅ **Richer data** - Get structured metadata easily  
✅ **No blocking** - Less likely to be rate-limited  

## 📦 Installation

### Step 1: Install Python
Make sure you have Python 3.7+ installed.

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
# For API scraper (recommended)
pip install biopython pandas openpyxl

# For web scraper (not recommended)
pip install requests beautifulsoup4 lxml pandas
```

## 🚀 Usage

### Method 1: API-Based Scraper (RECOMMENDED)

```python
from pubmed_api_scraper import PubMedScraper

# Initialize with your email (required by NCBI)
scraper = PubMedScraper(email="your.email@example.com")

# Search and extract abstracts
results = scraper.search_and_extract(
    query="lung cancer",
    max_results=50
)

# Results are returned as a pandas DataFrame
print(results.head())

# Save to files
results.to_csv("results.csv", index=False)
results.to_json("results.json", orient='records', indent=2)
results.to_excel("results.xlsx", index=False)
```

### Running the Example

1. **Edit the script** - Open `pubmed_api_scraper.py`
2. **Change the EMAIL** on line 159:
   ```python
   EMAIL = "your.email@example.com"  # Replace with your actual email
   ```
3. **Change the search term** on line 164:
   ```python
   search_term = "lung cancer"  # Change to your search term
   ```
4. **Run it:**
   ```bash
   python pubmed_api_scraper.py
   ```

### Method 2: Web Scraper (Alternative)

⚠️ **Not recommended** - Slower and less reliable

```bash
python pubmed_web_scraper.py
```

## 📊 Output Format

The scraper returns a DataFrame with these columns:

| Column | Description |
|--------|-------------|
| `pmid` | PubMed ID |
| `title` | Article title |
| `abstract` | Full abstract text |
| `authors` | Comma-separated author list |
| `journal` | Journal name |
| `publication_date` | Publication date |
| `url` | Direct link to PubMed article |

## 📝 Example Queries

```python
# Cancer research
results = scraper.search_and_extract("breast cancer treatment", max_results=100)

# Specific gene
results = scraper.search_and_extract("BRCA1 mutation", max_results=50)

# Complex query
results = scraper.search_and_extract(
    "lung cancer AND immunotherapy AND clinical trial",
    max_results=200
)

# Date range (in PubMed format)
results = scraper.search_and_extract(
    "COVID-19 AND 2023[pdat]",
    max_results=100
)
```

## 🔍 Advanced PubMed Search Syntax

You can use PubMed's advanced search syntax:

- **AND/OR/NOT operators**: `"lung cancer AND treatment"`
- **Phrase search**: `"machine learning"`
- **Field tags**: `"cancer[Title]"`, `"smith[Author]"`
- **Date filters**: `"2020:2023[pdat]"`
- **Journal**: `"nature[journal]"`

Examples:
```python
# Articles from 2022-2023 only
"breast cancer AND 2022:2023[pdat]"

# Specific journal
"immunotherapy AND nature[journal]"

# Title search
"machine learning[Title] AND cancer"

# Review articles only
"lung cancer AND review[Publication Type]"
```

## ⚙️ Customization

### Adjust Results Per Batch

In `pubmed_api_scraper.py`, modify batch size:

```python
batch_size = 10  # Change from 10 to your preferred size (max 500)
```

### Add More Fields

Extend the `_parse_article` method to extract additional fields:

```python
# Add DOI
doi = article.get('ELocationID', [{}])[0].get('#text', 'N/A')

# Add keywords
keywords = article.get('KeywordList', [[]])[0]

# Add MeSH terms
mesh_terms = [term['DescriptorName'] for term in record.get('MeshHeadingList', [])]
```

## 🚨 Important Notes

### Rate Limiting
- NCBI requests you make no more than 3 requests per second
- The script includes delays to respect this
- Register for an API key to increase limits: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

### Email Requirement
- NCBI requires an email for API access
- This allows them to contact you if there's a problem
- Your email is NOT used for marketing

### Large Datasets
- For >10,000 results, consider:
  1. Breaking into multiple queries
  2. Using date ranges to chunk data
  3. Running overnight with error handling

## 🐛 Troubleshooting

### "No module named 'Bio'"
```bash
pip install biopython
```

### "HTTP Error 429: Too Many Requests"
- You're making requests too fast
- Increase the `time.sleep()` value
- Get an API key from NCBI

### Empty Abstracts
- Some articles don't have abstracts (editorials, letters)
- Check if `abstract == 'N/A'` in your results

### Connection Errors
- Check your internet connection
- PubMed might be temporarily down
- Try again in a few minutes

## 📚 Resources

- [PubMed E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [Biopython Entrez Tutorial](https://biopython.org/docs/1.75/api/Bio.Entrez.html)
- [PubMed Search Tips](https://pubmed.ncbi.nlm.nih.gov/help/)

## 🔄 Converting to Java

If you need a Java version:

1. Use the **PubMed E-utilities REST API** directly
2. HTTP client: Apache HttpClient or OkHttp
3. XML parsing: Jackson or JAXB
4. Example endpoint:
   ```
   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer&retmax=100
   ```

Java is more verbose for this task - Python is recommended.

## 📄 License

Free to use for research and educational purposes. Respect PubMed's terms of service.
