"""
PubMed Abstract Scraper using Official E-utilities API
This is the RECOMMENDED approach - it's faster, more reliable, and respects PubMed's terms of service.

Requirements:
pip install biopython pandas
"""

from Bio import Entrez
import pandas as pd
import time
from typing import List, Dict
import json

class PubMedScraper:
    def __init__(self, email: str):
        """
        Initialize PubMed scraper with your email (required by NCBI)
        
        Args:
            email: Your email address (NCBI requires this)
        """
        Entrez.email = email
        
    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search PubMed and return list of PubMed IDs
        
        Args:
            query: Search term (e.g., "lung cancer", "breast cancer treatment")
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of PubMed IDs
        """
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
        """
        Fetch article details including abstracts for given PubMed IDs
        
        Args:
            pmid_list: List of PubMed IDs
            
        Returns:
            List of dictionaries containing article information
        """
        articles = []
        
        # Fetch in batches of 10 to avoid overwhelming the server
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
                
                # Be polite to NCBI servers
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
                    # Handle structured abstracts
                    if isinstance(abstract_parts, list):
                        abstract = ' '.join([str(part) for part in abstract_parts])
                    else:
                        abstract = str(abstract_parts)
            
            # Extract authors and affiliations
            authors = []
            affiliations = []
            countries = set()  # Use set to avoid duplicates
            
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'LastName' in author and 'ForeName' in author:
                        authors.append(f"{author['ForeName']} {author['LastName']}")
                    
                    # Extract affiliation information
                    if 'AffiliationInfo' in author:
                        for aff_info in author['AffiliationInfo']:
                            if 'Affiliation' in aff_info:
                                affiliation = aff_info['Affiliation']
                                affiliations.append(affiliation)
                                
                                # Extract country from affiliation
                                country = self._extract_country(affiliation)
                                if country:
                                    countries.add(country)
            
            # Join countries for display
            country_str = ', '.join(sorted(countries)) if countries else 'N/A'
            affiliation_str = '; '.join(affiliations[:3]) if affiliations else 'N/A'  # Limit to first 3
            
            # Extract journal and publication date
            journal = article.get('Journal', {}).get('Title', 'N/A')
            
            pub_date = 'N/A'
            if 'Journal' in article and 'JournalIssue' in article['Journal']:
                pub_date_info = article['Journal']['JournalIssue'].get('PubDate', {})
                year = pub_date_info.get('Year', '')
                month = pub_date_info.get('Month', '')
                pub_date = f"{month} {year}".strip()
            
            # Create PubMed URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': ', '.join(authors) if authors else 'N/A',
                'affiliation': affiliation_str,
                'country': country_str,
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
                'affiliation': 'N/A',
                'country': 'N/A',
                'journal': 'N/A',
                'publication_date': 'N/A',
                'url': 'N/A'
            }
    
    def _extract_country(self, affiliation: str) -> str:
        """
        Extract country from affiliation string
        
        Args:
            affiliation: Affiliation text from PubMed
            
        Returns:
            Country name or None
        """
        # Common country patterns in affiliations
        # Most affiliations end with country name
        common_countries = {
            'USA': ['USA', 'United States', 'U.S.A', 'America'],
            'UK': ['UK', 'United Kingdom', 'England', 'Scotland', 'Wales', 'Northern Ireland'],
            'China': ['China', 'P.R. China', 'PR China', "People's Republic of China"],
            'Germany': ['Germany', 'Deutschland'],
            'France': ['France'],
            'Japan': ['Japan'],
            'Canada': ['Canada'],
            'Australia': ['Australia'],
            'Italy': ['Italy', 'Italia'],
            'Spain': ['Spain', 'España'],
            'Netherlands': ['Netherlands', 'The Netherlands', 'Holland'],
            'Switzerland': ['Switzerland', 'Schweiz'],
            'Sweden': ['Sweden'],
            'India': ['India'],
            'Brazil': ['Brazil', 'Brasil'],
            'South Korea': ['South Korea', 'Korea', 'Republic of Korea'],
            'Israel': ['Israel'],
            'Belgium': ['Belgium'],
            'Austria': ['Austria'],
            'Denmark': ['Denmark'],
            'Norway': ['Norway'],
            'Finland': ['Finland'],
            'Poland': ['Poland'],
            'Russia': ['Russia', 'Russian Federation'],
            'Turkey': ['Turkey'],
            'Mexico': ['Mexico'],
            'Argentina': ['Argentina'],
            'Singapore': ['Singapore'],
            'Taiwan': ['Taiwan'],
            'Hong Kong': ['Hong Kong'],
            'New Zealand': ['New Zealand'],
            'Ireland': ['Ireland'],
            'Portugal': ['Portugal'],
            'Greece': ['Greece'],
            'Czech Republic': ['Czech Republic', 'Czechia'],
            'Hungary': ['Hungary'],
            'Romania': ['Romania'],
            'Thailand': ['Thailand'],
            'Malaysia': ['Malaysia'],
            'South Africa': ['South Africa'],
            'Egypt': ['Egypt'],
            'Saudi Arabia': ['Saudi Arabia'],
            'UAE': ['UAE', 'United Arab Emirates'],
            'Pakistan': ['Pakistan'],
            'Bangladesh': ['Bangladesh'],
            'Vietnam': ['Vietnam'],
            'Indonesia': ['Indonesia'],
            'Philippines': ['Philippines'],
            'Chile': ['Chile'],
            'Colombia': ['Colombia'],
            'Peru': ['Peru'],
        }
        
        # Check for country patterns
        affiliation_upper = affiliation.upper()
        
        for country, patterns in common_countries.items():
            for pattern in patterns:
                if pattern.upper() in affiliation_upper:
                    return country
        
        # If no match found, try to extract last part after comma
        # Many affiliations end with ", Country"
        parts = affiliation.split(',')
        if len(parts) > 1:
            last_part = parts[-1].strip()
            # Check if last part is a country
            for country, patterns in common_countries.items():
                for pattern in patterns:
                    if last_part.upper() == pattern.upper():
                        return country
        
        return None
    
    def search_and_extract(self, query: str, max_results: int = 100) -> pd.DataFrame:
        """
        Complete workflow: search and extract abstracts
        
        Args:
            query: Search term
            max_results: Maximum number of results
            
        Returns:
            DataFrame with article information
        """
        # Search
        pmid_list = self.search_pubmed(query, max_results)
        
        if not pmid_list:
            print("No results found")
            return pd.DataFrame()
        
        # Fetch abstracts
        articles = self.fetch_abstracts(pmid_list)
        
        # Convert to DataFrame
        df = pd.DataFrame(articles)
        
        return df


def main():
    """Example usage"""
    
    # IMPORTANT: Replace with your email
    EMAIL = "your.email@example.com"
    
    # Initialize scraper
    scraper = PubMedScraper(email=EMAIL)
    
    # Search query
    search_term = "lung cancer"  # Change this to your search term
    max_results = 20  # Number of articles to retrieve
    
    # Get results
    results_df = scraper.search_and_extract(search_term, max_results)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"Retrieved {len(results_df)} articles")
    print(f"{'='*80}\n")
    
    # Show first few abstracts
    for idx, row in results_df.head(3).iterrows():
        print(f"Title: {row['title']}")
        print(f"PMID: {row['pmid']}")
        print(f"URL: {row['url']}")
        print(f"Authors: {row['authors']}")
        print(f"Journal: {row['journal']}")
        print(f"Date: {row['publication_date']}")
        print(f"Abstract: {row['abstract'][:200]}...")
        print(f"\n{'-'*80}\n")
    
    # Save to CSV
    output_file = f"pubmed_{search_term.replace(' ', '_')}_abstracts.csv"
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    
    # Save to JSON
    json_file = f"pubmed_{search_term.replace(' ', '_')}_abstracts.json"
    results_df.to_json(json_file, orient='records', indent=2)
    print(f"Results saved to: {json_file}")
    
    # Save to Excel (optional)
    try:
        excel_file = f"pubmed_{search_term.replace(' ', '_')}_abstracts.xlsx"
        results_df.to_excel(excel_file, index=False)
        print(f"Results saved to: {excel_file}")
    except ImportError:
        print("Install openpyxl to save as Excel: pip install openpyxl")


if __name__ == "__main__":
    main()
