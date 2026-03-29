"""
Multi-Keyword Search Example
Demonstrates how to use the multi-keyword search feature
"""

import requests
import json

# ============================================================================
# EXAMPLE 1: Compare Cancer Types
# ============================================================================

def example_cancer_comparison():
    """Compare research volume across different cancer types"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Comparing Cancer Types")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'lung cancer',
            'breast cancer',
            'prostate cancer',
            'colon cancer',
            'pancreatic cancer'
        ],
        'max_results_per_keyword': 50,
        'sort_order': 'descending'  # Most researched first
    })
    
    data = response.json()
    
    print(f"\nSearched {data['total_keywords']} cancer types:")
    print(f"Sort order: {data['sort_order']}\n")
    
    for idx, result in enumerate(data['results'], 1):
        print(f"{idx}. {result['keyword']:20s} - {result['count']:3d} articles")
    
    print("\n✅ Result: Shows which cancer types have the most research")


# ============================================================================
# EXAMPLE 2: Find Research Gaps
# ============================================================================

def example_research_gaps():
    """Find understudied topics using ascending sort"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Finding Research Gaps")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'alzheimer disease',
            'parkinson disease',
            'huntington disease',
            'ALS',
            'multiple sclerosis'
        ],
        'max_results_per_keyword': 100,
        'sort_order': 'ascending'  # Least researched first
    })
    
    data = response.json()
    
    print(f"\nNeurodegenerative diseases (ascending order):")
    print("=" * 50)
    
    for idx, result in enumerate(data['results'], 1):
        print(f"{idx}. {result['keyword']:25s} - {result['count']:4d} articles")
        if idx == 1:
            print("   ↑ LEAST researched (potential research gap)")
    
    print("\n✅ Result: Identifies which diseases need more research")


# ============================================================================
# EXAMPLE 3: Track Trends Over Time
# ============================================================================

def example_time_trends():
    """Track research trends across different years"""
    print("\n" + "="*60)
    print("EXAMPLE 3: COVID-19 Research Over Time")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'COVID-19 AND 2020[pdat]',
            'COVID-19 AND 2021[pdat]',
            'COVID-19 AND 2022[pdat]',
            'COVID-19 AND 2023[pdat]'
        ],
        'max_results_per_keyword': 200,
        'sort_order': 'ascending'
    })
    
    data = response.json()
    
    print("\nCOVID-19 publications by year:")
    print("=" * 50)
    
    for result in data['results']:
        year = result['keyword'].split('AND')[1].strip()[:4]
        count = result['count']
        bar = '█' * (count // 10)
        print(f"{year}: {bar} {count} articles")
    
    print("\n✅ Result: Visualizes research trend over time")


# ============================================================================
# EXAMPLE 4: Drug Comparison
# ============================================================================

def example_drug_comparison():
    """Compare research on different pain medications"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Pain Medication Research")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'aspirin',
            'ibuprofen',
            'acetaminophen',
            'naproxen'
        ],
        'max_results_per_keyword': 100,
        'sort_order': 'descending'
    })
    
    data = response.json()
    
    print("\nPain medications (most to least researched):")
    print("=" * 50)
    
    total = sum(r['count'] for r in data['results'])
    
    for idx, result in enumerate(data['results'], 1):
        percentage = (result['count'] / total) * 100
        print(f"{idx}. {result['keyword']:15s} - {result['count']:4d} articles ({percentage:.1f}%)")
    
    print(f"\nTotal articles: {total}")
    print("\n✅ Result: Shows relative research focus on each medication")


# ============================================================================
# EXAMPLE 5: Save Results to File
# ============================================================================

def example_save_results():
    """Search and save results to JSON file"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Saving Results to File")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'machine learning AND medicine',
            'artificial intelligence AND healthcare',
            'deep learning AND diagnosis'
        ],
        'max_results_per_keyword': 30,
        'sort_order': 'descending'
    })
    
    data = response.json()
    
    # Save to file
    filename = 'ai_medicine_research.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Saved results to: {filename}")
    print(f"Total keywords: {data['total_keywords']}")
    
    for result in data['results']:
        print(f"  - {result['keyword']}: {result['count']} articles")


# ============================================================================
# EXAMPLE 6: Extract Specific Data
# ============================================================================

def example_extract_data():
    """Extract and analyze specific fields from results"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Extracting Journal Names")
    print("="*60)
    
    response = requests.post('http://localhost:5000/api/search/multi', json={
        'keywords': [
            'CRISPR gene editing',
            'RNA interference'
        ],
        'max_results_per_keyword': 20,
        'sort_order': 'descending'
    })
    
    data = response.json()
    
    for result in data['results']:
        print(f"\n{result['keyword']} ({result['count']} articles):")
        print("-" * 50)
        
        # Extract unique journals
        journals = set()
        for article in result['articles']:
            if article['journal'] != 'N/A':
                journals.add(article['journal'])
        
        # Show top 5 journals
        for idx, journal in enumerate(list(journals)[:5], 1):
            print(f"  {idx}. {journal}")
    
    print("\n✅ Result: Shows which journals publish on each topic")


# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "Multi-Keyword Search Examples" + " "*18 + "║")
    print("╚" + "="*58 + "╝")
    
    print("\n⚠️  Make sure the app is running first:")
    print("   python app_multi_keyword.py")
    print("\n" + "="*60)
    
    try:
        # Uncomment the examples you want to run:
        
        example_cancer_comparison()
        # example_research_gaps()
        # example_time_trends()
        # example_drug_comparison()
        # example_save_results()
        # example_extract_data()
        
        print("\n" + "="*60)
        print("✅ Examples completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server")
        print("Make sure you've started the app first:")
        print("  python app_multi_keyword.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
