"""
Flask Web Application for PubMed Abstract Scraper
A user-friendly web interface to search PubMed and extract abstracts
"""

from flask import Flask, render_template, request, jsonify, send_file
from pubmed_api_scraper import PubMedScraper
import pandas as pd
import json
import io
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize scraper (you can change the email)
NCBI_EMAIL = "sreekanth.dabbara@gmail.com"  # IMPORTANT: Change this to your email
scraper = PubMedScraper(email=NCBI_EMAIL)

# Store recent searches in memory (in production, use a database)
recent_searches = []


@app.route('/')
def index():
    """Home page with search form"""
    return render_template('index.html', recent_searches=recent_searches[:10])


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    try:
        # Get search parameters
        query = request.form.get('query', '').strip()
        max_results = int(request.form.get('max_results', 20))
        
        if not query:
            return render_template('index.html', 
                                 error="Please enter a search term",
                                 recent_searches=recent_searches[:10])
        
        # Validate max_results
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
        
        # Convert to list of dictionaries for template
        results = results_df.to_dict('records')
        
        # Store search in recent searches
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
        
        # Perform search
        results_df = scraper.search_and_extract(query, max_results)
        
        if results_df.empty:
            return jsonify({
                'query': query,
                'count': 0,
                'results': []
            })
        
        # Convert to JSON
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
    """Export results (triggered from results page)"""
    try:
        # Get results from session/cache (in production, use proper session management)
        # For now, we'll re-run the search based on query params
        query = request.args.get('query', '')
        max_results = int(request.args.get('max_results', 20))
        
        if not query:
            return "No query provided", 400
        
        # Get results
        results_df = scraper.search_and_extract(query, max_results)
        
        if results_df.empty:
            return "No results to export", 404
        
        # Generate filename
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export based on format
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
    # IMPORTANT: Change debug=False in production
    app.run(debug=True, host='0.0.0.0', port=5000)
