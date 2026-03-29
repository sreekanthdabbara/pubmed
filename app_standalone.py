"""
PubMed Abstract Scraper - Standalone Flask Application
All-in-one file version (no separate imports needed)
"""

from flask import Flask, render_template, request, jsonify, send_file
from Bio import Entrez
import pandas as pd
import json
import io
import time
from typing import List, Dict
from datetime import datetime

# ============================================================================
# PUBMED SCRAPER CLASS (Built-in)
# ============================================================================

class PubMedScraper:
    def __init__(self, email: str):
        """Initialize PubMed scraper with your email (required by NCBI)"""
        Entrez.email = email
        
    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed and return list of PubMed IDs"""
        print(f"Searching PubMed for: {query}")
        
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            sort="relevance"
        )
        
        results = Entrez.read(handle)
        handle.close()
        
        id_list = results["IdList"]
        print(f"Found {len(id_list)} articles")
        
        return id_list
    
    def fetch_abstracts(self, pmid_list: List[str]) -> List[Dict]:
        """Fetch article details including abstracts for given PubMed IDs"""
        articles = []
        batch_size = 10
        
        for i in range(0, len(pmid_list), batch_size):
            batch = pmid_list[i:i + batch_size]
            print(f"Fetching articles {i+1} to {min(i+batch_size, len(pmid_list))}...")
            
            try:
                handle = Entrez.efetch(
                    db="pubmed",
                    id=batch,
                    rettype="abstract",
                    retmode="xml"
                )
                
                records = Entrez.read(handle)
                handle.close()
                
                for record in records['PubmedArticle']:
                    article_data = self._parse_article(record)
                    articles.append(article_data)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching batch: {e}")
                continue
        
        return articles
    
    def _parse_article(self, record) -> Dict:
        """Parse article record and extract relevant information"""
        try:
            article = record['MedlineCitation']['Article']
            pmid = str(record['MedlineCitation']['PMID'])
            
            # Extract title
            title = article.get('ArticleTitle', 'N/A')
            
            # Extract abstract
            abstract = 'N/A'
            if 'Abstract' in article:
                abstract_parts = article['Abstract'].get('AbstractText', [])
                if abstract_parts:
                    if isinstance(abstract_parts, list):
                        abstract = ' '.join([str(part) for part in abstract_parts])
                    else:
                        abstract = str(abstract_parts)
            
            # Extract authors
            authors = []
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'LastName' in author and 'ForeName' in author:
                        authors.append(f"{author['ForeName']} {author['LastName']}")
            
            # Extract journal
            journal = article.get('Journal', {}).get('Title', 'N/A')
            
            # Extract publication date
            pub_date = 'N/A'
            if 'Journal' in article and 'JournalIssue' in article['Journal']:
                pub_date_info = article['Journal']['JournalIssue'].get('PubDate', {})
                year = pub_date_info.get('Year', '')
                month = pub_date_info.get('Month', '')
                pub_date = f"{month} {year}".strip()
            
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': ', '.join(authors) if authors else 'N/A',
                'journal': journal,
                'publication_date': pub_date,
                'url': url
            }
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return {
                'pmid': 'Error',
                'title': 'Error',
                'abstract': 'Error parsing article',
                'authors': 'N/A',
                'journal': 'N/A',
                'publication_date': 'N/A',
                'url': 'N/A'
            }
    
    def search_and_extract(self, query: str, max_results: int = 100) -> pd.DataFrame:
        """Complete workflow: search and extract abstracts"""
        pmid_list = self.search_pubmed(query, max_results)
        
        if not pmid_list:
            print("No results found")
            return pd.DataFrame()
        
        articles = self.fetch_abstracts(pmid_list)
        df = pd.DataFrame(articles)
        
        return df


# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# IMPORTANT: Change this to your email!
NCBI_EMAIL = "your.email@example.com"
scraper = PubMedScraper(email=NCBI_EMAIL)

# Store recent searches
recent_searches = []


@app.route('/')
def index():
    """Home page with search form"""
    return render_template('index.html', recent_searches=recent_searches[:10])


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    try:
        query = request.form.get('query', '').strip()
        max_results = int(request.form.get('max_results', 20))
        
        if not query:
            return render_template('index.html', 
                                 error="Please enter a search term",
                                 recent_searches=recent_searches[:10])
        
        if max_results < 1 or max_results > 500:
            return render_template('index.html',
                                 error="Number of results must be between 1 and 500",
                                 recent_searches=recent_searches[:10])
        
        # Perform search
        results_df = scraper.search_and_extract(query, max_results)
        
        if results_df.empty:
            return render_template('index.html',
                                 error=f"No results found for '{query}'",
                                 recent_searches=recent_searches[:10])
        
        results = results_df.to_dict('records')
        
        # Store search
        search_record = {
            'query': query,
            'count': len(results),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        recent_searches.insert(0, search_record)
        if len(recent_searches) > 50:
            recent_searches.pop()
        
        return render_template('results_multi.html',
                             query=query,
                             results=results,
                             total=len(results))
    
    except Exception as e:
        return render_template('index.html',
                             error=f"An error occurred: {str(e)}",
                             recent_searches=recent_searches[:10])


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching (returns JSON)"""
    try:
        data = request.get_json()
        
        query = data.get('query', '').strip()
        max_results = int(data.get('max_results', 20))
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        if max_results < 1 or max_results > 500:
            return jsonify({'error': 'max_results must be between 1 and 500'}), 400
        
        results_df = scraper.search_and_extract(query, max_results)
        
        if results_df.empty:
            return jsonify({
                'query': query,
                'count': 0,
                'results': []
            })
        
        results = results_df.to_dict('records')
        
        return jsonify({
            'query': query,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/<format>')
def export(format):
    """Export results"""
    try:
        query = request.args.get('query', '')
        max_results = int(request.args.get('max_results', 20))
        
        if not query:
            return "No query provided", 400
        
        results_df = scraper.search_and_extract(query, max_results)
        
        if results_df.empty:
            return "No results to export", 404
        
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            output = io.StringIO()
            results_df.to_csv(output, index=False)
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'pubmed_{safe_query}_{timestamp}.csv'
            )
        
        elif format == 'json':
            output = results_df.to_json(orient='records', indent=2)
            
            return send_file(
                io.BytesIO(output.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'pubmed_{safe_query}_{timestamp}.json'
            )
        
        elif format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results_df.to_excel(writer, index=False, sheet_name='Results')
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'pubmed_{safe_query}_{timestamp}.xlsx'
            )
        
        else:
            return "Invalid format", 400
    
    except Exception as e:
        return f"Export error: {str(e)}", 500


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'email': NCBI_EMAIL,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🧬 PubMed Abstract Scraper")
    print("=" * 60)
    print(f"Email configured: {NCBI_EMAIL}")
    if NCBI_EMAIL == "your.email@example.com":
        print("⚠️  WARNING: Please update your email in this file!")
        print("   Line 183: NCBI_EMAIL = 'your.email@example.com'")
    print("=" * 60)
    print("Starting server at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
