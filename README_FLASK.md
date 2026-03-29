# 🧬 PubMed Abstract Scraper - Flask Web Application

A modern, user-friendly web interface for searching PubMed and extracting research article abstracts.

![Flask](https://img.shields.io/badge/Flask-2.3.0-green)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🔍 **Intuitive Search Interface** - Easy-to-use web interface for PubMed searches
- 📊 **Bulk Extraction** - Retrieve up to 500 articles at once
- 📥 **Multiple Export Formats** - Download results as CSV, JSON, or Excel
- 🚀 **Fast & Reliable** - Uses official NCBI E-utilities API
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔗 **REST API** - Programmatic access for developers
- 📚 **Recent Searches** - Track your search history
- 💡 **Search Examples** - Quick-start templates for common queries

## 🎯 Quick Start

### 1. Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Clone or download the repository
cd pubmed-scraper

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `app.py` and update the email address (required by NCBI):

```python
# Line 15 in app.py
NCBI_EMAIL = "your.email@example.com"  # Change this!
```

### 4. Run the Application

```bash
python app.py
```

The application will start at: **http://localhost:5000**

Open your browser and navigate to this URL to start using the application!

## 📁 Project Structure

```
pubmed-scraper/
├── app.py                      # Main Flask application
├── pubmed_api_scraper.py       # PubMed API wrapper
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Home/search page
│   ├── results.html           # Results display
│   └── about.html             # About page
├── static/                     # Static files
│   └── style.css              # Stylesheet
└── README_FLASK.md            # This file
```

## 🔧 Usage

### Web Interface

1. **Navigate to Home Page**
   - Open http://localhost:5000 in your browser

2. **Enter Search Query**
   - Type your search term (e.g., "lung cancer")
   - Use PubMed syntax for advanced searches
   - Set number of results (1-500)

3. **View Results**
   - Browse articles with full abstracts
   - Click article titles to view on PubMed
   - Copy abstracts with one click

4. **Export Data**
   - Download results in CSV, JSON, or Excel format
   - Use for further analysis or research

### REST API

The application also provides a REST API for programmatic access.

#### Search Endpoint

```bash
POST /api/search
Content-Type: application/json

{
  "query": "lung cancer",
  "max_results": 20
}
```

**Example with curl:**

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "breast cancer", "max_results": 10}'
```

**Example with Python:**

```python
import requests

response = requests.post('http://localhost:5000/api/search', json={
    'query': 'CRISPR gene editing',
    'max_results': 15
})

data = response.json()
print(f"Found {data['count']} articles")
for article in data['results']:
    print(f"- {article['title']}")
```

**Response Format:**

```json
{
  "query": "lung cancer",
  "count": 20,
  "results": [
    {
      "pmid": "12345678",
      "title": "Article Title Here",
      "abstract": "Full abstract text...",
      "authors": "John Doe, Jane Smith",
      "journal": "Nature Medicine",
      "publication_date": "2023 Jan",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ]
}
```

## 🔍 Advanced Search Tips

### Boolean Operators
```
lung cancer AND treatment
breast cancer OR prostate cancer
cancer NOT review
```

### Phrase Search
```
"machine learning"
"gene therapy"
```

### Field Tags
```
smith[Author]          # Search by author
cancer[Title]          # Search in title
nature[Journal]        # Search by journal
```

### Date Filters
```
cancer AND 2023[pdat]           # Published in 2023
treatment AND 2020:2023[pdat]   # Published 2020-2023
```

### Publication Types
```
cancer AND review[Publication Type]
treatment AND "clinical trial"[Publication Type]
```

### Combined Examples
```
"lung cancer" AND immunotherapy AND 2022:2024[pdat]
BRCA1[Title] AND smith[Author]
COVID-19 AND nature[Journal] AND 2023[pdat]
```

## 🚀 Deployment

### Development Server

```bash
# Run with debug mode (development only)
python app.py
```

### Production Deployment

#### Option 1: Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option 2: uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Run with uWSGI
uwsgi --http :5000 --wsgi-file app.py --callable app --processes 4
```

#### Option 3: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t pubmed-scraper .
docker run -p 5000:5000 pubmed-scraper
```

### Environment Variables

For production, use environment variables instead of hardcoding:

```python
# In app.py
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
NCBI_EMAIL = os.environ.get('NCBI_EMAIL', 'your.email@example.com')
```

Set environment variables:

```bash
export SECRET_KEY='your-production-secret-key'
export NCBI_EMAIL='your.email@example.com'
```

## ⚙️ Configuration Options

### Rate Limiting

To respect NCBI's servers, the scraper includes delays. Adjust in `pubmed_api_scraper.py`:

```python
# Line 91 - batch size (default: 10)
batch_size = 10

# Line 108 - delay between batches (default: 0.5 seconds)
time.sleep(0.5)
```

### Maximum Results

Change the maximum allowed results in `app.py`:

```python
# Line 39 - max results validation
if max_results < 1 or max_results > 500:  # Change 500 to your limit
```

### Session Management

For production, implement proper session management or database storage:

```python
# Replace in-memory storage with database
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///searches.db'
db = SQLAlchemy(app)
```

## 🔐 Security Considerations

### For Production Deployment:

1. **Change Secret Key**
   ```python
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
   ```

2. **Disable Debug Mode**
   ```python
   app.run(debug=False)
   ```

3. **Use HTTPS**
   - Deploy behind a reverse proxy (Nginx, Apache)
   - Use SSL certificates (Let's Encrypt)

4. **Add Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=get_remote_address)
   
   @app.route('/api/search', methods=['POST'])
   @limiter.limit("10 per minute")
   def api_search():
       # ...
   ```

5. **Input Validation**
   - Already implemented for query and max_results
   - Add CSRF protection for forms in production

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Search test
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 5}'
```

### Test the Web Interface

1. Open http://localhost:5000
2. Try example searches
3. Export data in different formats
4. Check mobile responsiveness

## 📊 Performance Optimization

### Caching

Add Redis caching for repeated searches:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=3600)
def search_pubmed(query, max_results):
    # ...
```

### Background Tasks

Use Celery for long-running searches:

```python
from celery import Celery

celery = Celery(app.name, broker='redis://localhost:6379/0')

@celery.task
def async_search(query, max_results):
    # ...
```

## 🐛 Troubleshooting

### "No module named 'Bio'"
```bash
pip install biopython
```

### "Address already in use"
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
python app.py --port 8000
```

### "Email is required by NCBI"
- Make sure you've updated `NCBI_EMAIL` in `app.py`
- NCBI requires a valid email for API access

### Empty Results
- Check your search query syntax
- Try a simpler search term
- Verify internet connection

### Slow Performance
- Reduce `max_results`
- Increase batch size in `pubmed_api_scraper.py`
- Implement caching

## 📚 Additional Resources

- [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/)
- [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Biopython Tutorial](https://biopython.org/DIST/docs/tutorial/Tutorial.html)

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

- Add user authentication
- Implement saved searches
- Add data visualization
- Create batch processing
- Add more export formats
- Improve mobile UI
- Add internationalization

## 📄 License

This project is open source and available for educational and research purposes.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please respect PubMed's [terms of service](https://www.ncbi.nlm.nih.gov/home/about/policies/). Do not overload NCBI servers with excessive requests.

## 💬 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the PubMed API documentation
3. Submit an issue on GitHub

---

**Made with ❤️ for researchers and developers**
