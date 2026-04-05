"""
PubMed Scraper - Multi-Keyword Search Version
Search multiple keywords and display results sorted by article count
"""

import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from Bio import Entrez
import pandas as pd
import json
import io
import time
import re
import requests as http_requests
from typing import List, Dict, Tuple
from datetime import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  pdfplumber not installed — PDF text extraction disabled.")
    print("   Run: pip install pdfplumber")

# ============================================================================
# MULTI-KEYWORD PUBMED SCRAPER
# ============================================================================

class MultiKeywordPubMedScraper:
    def __init__(self, email: str, api_key: str = None):
        """
        Initialize PubMed scraper.

        Args:
            email:   Your email (required by NCBI).
            api_key: Optional NCBI API key — raises rate limit from 3 to 10
                     req/sec and speeds up large fetches significantly.
                     Get a free key at: https://www.ncbi.nlm.nih.gov/account/
        """
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        # Rate-limit: 3 req/s without key, 10 req/s with key
        self._min_interval = 0.11 if api_key else 0.34
        # Thread-safe lock so parallel workers don't race on Entrez calls
        self._lock = threading.Lock()

    def search_pubmed(self, query: str, max_results: int = 500) -> tuple:
        """Search PubMed and return (id_list, ncbi_total_count)."""
        print(f"  [search] {query!r} (max {max_results})")
        try:
            with self._lock:
                handle = Entrez.esearch(
                    db="pubmed",
                    term=query,
                    retmax=max_results,
                    sort="relevance",
                    usehistory="y",
                )
                results = Entrez.read(handle)
                handle.close()

            id_list    = results.get("IdList", [])
            ncbi_total = int(results.get("Count", len(id_list)))
            print(f"  [search] {len(id_list)} fetched / {ncbi_total} total for {query!r}")
            return id_list, ncbi_total

        except Exception as e:
            print(f"  [search] error for {query!r}: {e}")
            return [], 0

    def fetch_more(self, query: str, offset: int, batch: int = 500) -> List[Dict]:
        """Fetch the next batch of articles starting at offset. Used by Load More."""
        try:
            with self._lock:
                handle = Entrez.esearch(
                    db="pubmed",
                    term=query,
                    retmax=batch,
                    retstart=offset,
                    sort="relevance",
                )
                results = Entrez.read(handle)
                handle.close()
                time.sleep(self._min_interval)

            id_list = results.get("IdList", [])
            if not id_list:
                return []
            return self.fetch_abstracts(id_list)
        except Exception as e:
            print(f"  [fetch_more] error: {e}")
            return []

    def fetch_abstracts(self, pmid_list: List[str]) -> List[Dict]:
        """Fetch article details in large batches with minimal sleep."""
        if not pmid_list:
            return []

        articles = []
        # NCBI allows up to 10,000 per efetch; 500 is a safe sweet spot
        batch_size = 500

        for i in range(0, len(pmid_list), batch_size):
            batch = pmid_list[i:i + batch_size]
            try:
                with self._lock:
                    handle = Entrez.efetch(
                        db="pubmed",
                        id=batch,
                        rettype="abstract",
                        retmode="xml",
                    )
                    records = Entrez.read(handle)
                    handle.close()
                    time.sleep(self._min_interval)

                for record in records.get("PubmedArticle", []):
                    art = self._parse_article(record)
                    if art:
                        articles.append(art)

            except Exception as e:
                print(f"  [fetch] batch {i}-{i+batch_size} error: {e}")
                time.sleep(1)   # back off on error
                continue

        return articles
    
    def _parse_article(self, record) -> Dict:
        """Parse article record and extract relevant information"""
        try:
            article = record['MedlineCitation']['Article']
            pmid = str(record['MedlineCitation']['PMID'])
            
            title = article.get('ArticleTitle', 'N/A')
            
            abstract = 'N/A'
            if 'Abstract' in article:
                abstract_parts = article['Abstract'].get('AbstractText', [])
                if abstract_parts:
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
            
            journal = article.get('Journal', {}).get('Title', 'N/A')
            
            pub_date = 'N/A'
            if 'Journal' in article and 'JournalIssue' in article['Journal']:
                pub_date_info = article['Journal']['JournalIssue'].get('PubDate', {})
                year = pub_date_info.get('Year', '')
                month = pub_date_info.get('Month', '')
                pub_date = f"{month} {year}".strip()
            
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            # ── Publication types (e.g. Review, Clinical Trial) ──────────
            pub_types = []
            try:
                pt_list = article.get('PublicationTypeList', [])
                for pt in pt_list:
                    pt_str = str(pt).strip()
                    if pt_str and pt_str.lower() not in ('journal article',):
                        pub_types.append(pt_str)
                # If only "Journal Article" existed, keep it as fallback
                if not pub_types:
                    for pt in pt_list:
                        pub_types.append(str(pt).strip())
            except Exception:
                pass
            publication_types = '; '.join(pub_types) if pub_types else 'N/A'
            # Primary label = first meaningful type (shown as badge)
            pub_type_label = pub_types[0] if pub_types else 'N/A'
            # ────────────────────────────────────────────────────────────

            # ── PMC / Free full-text detection ──────────────────────────
            pmc_id = None
            is_free_pmc = False
            pmc_url = None
            pdf_url = None

            try:
                id_list = record.get('PubmedData', {}).get('ArticleIdList', [])
                for article_id in id_list:
                    if hasattr(article_id, 'attributes') and \
                            article_id.attributes.get('IdType') == 'pmc':
                        pmc_id = str(article_id)
                        break

                if pmc_id:
                    is_free_pmc = True
                    pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            except Exception:
                pass
            # ────────────────────────────────────────────────────────────

            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': ', '.join(authors) if authors else 'N/A',
                'affiliation': affiliation_str,
                'country': country_str,
                'journal': journal,
                'publication_date': pub_date,
                'publication_type': publication_types,
                'pub_type_label': pub_type_label,
                'url': url,
                'pmc_id': pmc_id or 'N/A',
                'is_free_pmc': is_free_pmc,
                'pmc_url': pmc_url or '',
                'pdf_url': pdf_url or '',
            }
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None
    
    def _extract_country(self, affiliation: str) -> str:
        """Extract country from affiliation string"""
        # Common country patterns in affiliations
        common_countries = {
            'USA': ['USA', 'United States', 'U.S.A', 'America'],
            'UK': ['UK', 'United Kingdom', 'England', 'Scotland', 'Wales'],
            'China': ['China', 'P.R. China', 'PR China'],
            'Germany': ['Germany'],
            'France': ['France'],
            'Japan': ['Japan'],
            'Canada': ['Canada'],
            'Australia': ['Australia'],
            'Italy': ['Italy'],
            'Spain': ['Spain'],
            'Netherlands': ['Netherlands', 'The Netherlands'],
            'Switzerland': ['Switzerland'],
            'Sweden': ['Sweden'],
            'India': ['India'],
            'Brazil': ['Brazil'],
            'South Korea': ['South Korea', 'Korea'],
            'Israel': ['Israel'],
            'Belgium': ['Belgium'],
            'Austria': ['Austria'],
            'Denmark': ['Denmark'],
            'Norway': ['Norway'],
            'Finland': ['Finland'],
            'Poland': ['Poland'],
            'Russia': ['Russia'],
            'Turkey': ['Turkey'],
            'Mexico': ['Mexico'],
            'Singapore': ['Singapore'],
            'Taiwan': ['Taiwan'],
            'Hong Kong': ['Hong Kong'],
            'New Zealand': ['New Zealand'],
            'Ireland': ['Ireland'],
            'Portugal': ['Portugal'],
        }
        
        affiliation_upper = affiliation.upper()
        
        for country, patterns in common_countries.items():
            for pattern in patterns:
                if pattern.upper() in affiliation_upper:
                    return country
        
        return None
    
    def _fetch_one_keyword(self, keyword: str, max_results: int) -> tuple:
        """Worker: search + fetch for a single keyword. Returns (keyword, df, ncbi_total)."""
        kw = keyword.strip()
        pmid_list, ncbi_total = self.search_pubmed(kw, max_results)
        if not pmid_list:
            return kw, pd.DataFrame(), ncbi_total
        articles = self.fetch_abstracts(pmid_list)
        articles = [a for a in articles if a is not None]
        if not articles:
            return kw, pd.DataFrame(), ncbi_total
        df = pd.DataFrame(articles)
        df["keyword"] = kw
        return kw, df, ncbi_total

    def search_multiple_keywords(
        self, keywords: List[str], max_results_per_keyword: int = 500
    ) -> Dict[str, pd.DataFrame]:
        """
        Search all keywords in parallel using a thread pool.

        Without an API key  → 3 workers (3 req/s NCBI limit).
        With an API key     → 5 workers (stays well under 10 req/s limit).
        """
        max_workers = 5 if getattr(Entrez, "api_key", None) else 3
        all_results: Dict[str, pd.DataFrame] = {}

        print(f"\nSearching {len(keywords)} keyword(s) with {max_workers} parallel workers...")

        # ncbi_totals stores the real NCBI count so results page can show Load More
        ncbi_totals: Dict[str, int] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(self._fetch_one_keyword, kw, max_results_per_keyword): kw
                for kw in keywords
            }
            for future in as_completed(futures):
                kw_label = futures[future]
                try:
                    kw, df, ncbi_total = future.result()
                    all_results[kw]  = df
                    ncbi_totals[kw]  = ncbi_total
                    print(f"  ✓ {kw!r}: {len(df)} fetched / {ncbi_total} total")
                except Exception as e:
                    print(f"  ✗ {kw_label!r}: {e}")
                    kw = kw_label.strip()
                    all_results[kw] = pd.DataFrame()
                    ncbi_totals[kw] = 0

        return all_results, ncbi_totals
    
    def sort_results_by_count(self, results: Dict[str, pd.DataFrame], ascending: bool = True) -> OrderedDict:
        """
        Sort results dictionary by number of articles (ascending or descending)
        
        Args:
            results: Dictionary of keyword -> DataFrame
            ascending: True for ascending order, False for descending
            
        Returns:
            OrderedDict sorted by article count
        """
        # Create list of (keyword, count, dataframe) tuples
        keyword_counts = [(kw, len(df), df) for kw, df in results.items()]
        
        # Sort by count
        keyword_counts.sort(key=lambda x: x[1], reverse=not ascending)
        
        # Convert back to OrderedDict
        sorted_results = OrderedDict()
        for kw, count, df in keyword_counts:
            sorted_results[kw] = df
        
        return sorted_results

    def _terms_from_keyword(self, keyword: str) -> List[str]:
        """Strip PubMed query syntax and return plain search terms."""
        cleaned = re.sub(r'\[\w+\]', '', keyword)
        cleaned = re.sub(r'\b(AND|OR|NOT)\b', ' ', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[\"\(\)]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
        return [t for t in cleaned.split() if len(t) > 1]

    def compute_keyword_scores(
        self,
        all_results: Dict[str, pd.DataFrame],
        keywords: List[str],
    ) -> Dict[str, pd.DataFrame]:
        """
        Vectorised scoring — runs in milliseconds instead of minutes.

        keyword_match_count  — how many searched keywords this PMID appeared in
        keyword_total_hits   — total plain-term occurrences in title + abstract
        """
        # ── PMID → set of matched keywords ─────────────────────────────
        # Tells us exactly which keywords each article appeared in
        pmid_kw_set: Dict[str, set] = {}
        for kw, df in all_results.items():
            if df.empty:
                continue
            for pmid in df["pmid"].astype(str):
                pmid_kw_set.setdefault(pmid, set()).add(kw)

        # ── Per-keyword term patterns (for individual hit counts) ────────
        # kw_patterns: keyword -> compiled regex of its plain terms
        kw_patterns: Dict[str, re.Pattern] = {}
        for kw in keywords:
            terms = self._terms_from_keyword(kw)
            if terms:
                kw_patterns[kw] = re.compile(
                    "|".join(re.escape(t) for t in terms), re.IGNORECASE
                )

        # Combined pattern for total hits across ALL keywords
        all_terms = list({t for terms in
                          [self._terms_from_keyword(kw) for kw in keywords]
                          for t in terms})
        combined_pattern = re.compile(
            "|".join(re.escape(t) for t in all_terms), re.IGNORECASE
        ) if all_terms else None

        # ── Annotate each DataFrame ──────────────────────────────────────
        updated: Dict[str, pd.DataFrame] = {}
        for kw, df in all_results.items():
            if df.empty:
                updated[kw] = df
                continue

            df = df.copy()
            pmids = df["pmid"].astype(str)

            # keyword_match_count — how many searched keywords this article appeared in
            df["keyword_match_count"] = pmids.map(
                lambda p: len(pmid_kw_set.get(p, {kw}))
            ).astype(int)

            # matched_keywords — the actual keyword names (semicolon-separated)
            df["matched_keywords"] = pmids.map(
                lambda p: "; ".join(sorted(pmid_kw_set.get(p, {kw})))
            )

            # keyword_total_hits — total term occurrences across all keywords
            text_series = (
                df["title"].fillna("") + " " + df["abstract"].fillna("")
            ).str.lower()

            if combined_pattern:
                df["keyword_total_hits"] = text_series.apply(
                    lambda t: len(combined_pattern.findall(t))
                )
            else:
                df["keyword_total_hits"] = 0

            # per_keyword_hits — "lung cancer:5; breast cancer:2" style breakdown
            def per_kw_hits(text):
                parts = []
                for k, pat in kw_patterns.items():
                    count = len(pat.findall(text))
                    if count > 0:
                        parts.append(f"{k}: {count}")
                return "; ".join(parts) if parts else ""

            df["per_keyword_hits"] = text_series.apply(per_kw_hits)

            updated[kw] = df

        return updated


# ============================================================================
# PDF TEXT EXTRACTION HELPER
# ============================================================================

EXCEL_CELL_LIMIT = 32_000  # Excel hard limit is 32,767 chars per cell


def fetch_pdf_text(pdf_url: str) -> str:
    """
    Fetch full text for a free PMC article using the official PMC XML API
    (Entrez efetch db=pmc). Strips the References section and returns
    complete body text in document order, preserving all paragraphs.
    """
    if not pdf_url:
        return ''

    # ── Extract PMC ID from the URL ──────────────────────────────────────
    pmc_match = re.search(r'PMC(\d+)', pdf_url, re.IGNORECASE)
    if not pmc_match:
        return 'Could not extract PMC ID from URL'

    pmc_numeric_id = pmc_match.group(1)

    try:
        # ── Fetch full-text XML via Entrez ────────────────────────────────
        handle = Entrez.efetch(
            db='pmc',
            id=pmc_numeric_id,
            rettype='full',
            retmode='xml',
        )
        xml_bytes = handle.read()
        handle.close()

        # ── Parse XML ─────────────────────────────────────────────────────
        from xml.etree import ElementTree as ET
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return 'Could not parse PMC XML response'

        # Tags whose entire subtree content should be skipped
        # (but NOT their .tail — tail belongs to the parent level)
        SKIP_CONTENT = {
            'ref-list',    # References list
            'fn-group',    # Footnotes
            'glossary',    # Glossary
            'ack',         # Acknowledgements
            'xref',        # Inline citation numbers  e.g. [1]
            'ext-link',    # External hyperlinks
            'uri',         # URLs
            'graphic',     # Image placeholders
            'media',       # Media elements
            'supplementary-material',
        }

        # Tags that represent block-level breaks (add newline before/after)
        BLOCK_TAGS = {
            'p', 'title', 'sec', 'list-item', 'caption',
            'table-wrap', 'fig', 'disp-formula', 'def-item',
        }

        def local(tag):
            """Strip namespace prefix from tag name."""
            return tag.split('}')[-1] if '}' in tag else tag

        def walk(el):
            """
            Recursively collect text in document order.

            Returns a string that preserves:
              el.text  — text immediately inside the opening tag
              children — each child's full text contribution
              el.tail  — text immediately after the closing tag (parent context)

            When el is in SKIP_CONTENT its internal text and children are
            suppressed, but el.tail is still returned (it belongs to the
            parent paragraph, not to the skipped element).
            """
            tag = local(el.tag)

            # Skipped element: return only tail so parent paragraph stays intact
            if tag in SKIP_CONTENT:
                return el.tail or ''

            parts = []

            # Block elements get a leading newline so paragraphs don't run together
            if tag in BLOCK_TAGS:
                parts.append('\n')

            # Text directly inside this element (before any child)
            if el.text:
                parts.append(el.text)

            # Recurse into every child; walk() returns child text + child.tail
            for child in el:
                parts.append(walk(child))

            # Trailing newline for block elements
            if tag in BLOCK_TAGS:
                parts.append('\n')

            # Tail: text after this element's closing tag (belongs to parent)
            if el.tail:
                parts.append(el.tail)

            return ''.join(parts)

        # ── Find body (try JATS namespace first, then bare) ───────────────
        ns = 'http://jats.nlm.nih.gov'
        body = (root.find(f'{{{ns}}}body') or
                root.find(f'.//{{{ns}}}body') or
                root.find('.//body'))

        if body is not None:
            raw = walk(body)
        else:
            # Fallback: whole document minus front/back matter
            raw = walk(root)

        # ── Clean up whitespace ───────────────────────────────────────────
        # Collapse runs of spaces (but keep newlines)
        lines = []
        for line in raw.splitlines():
            line = re.sub(r'[ \t]+', ' ', line).strip()
            lines.append(line)

        # Collapse 3+ consecutive blank lines into 2
        full_text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()

        if not full_text:
            return 'No text could be extracted for this article'

        # ── Strip References section if it survived ───────────────────────
        ref_pat = re.compile(
            r'\n\s*(?:REFERENCES?|Reference List|BIBLIOGRAPHY|Bibliography)\s*\n',
            re.IGNORECASE
        )
        m = ref_pat.search(full_text)
        if m:
            full_text = full_text[:m.start()].rstrip()

        # Return full text — truncation for Excel is applied in the Excel
        # writer path only so CSV and JSON always get the complete content
        return full_text

    except Exception as e:
        return f'Error fetching full text: {str(e)}'


# ── Desired column order in all exports ─────────────────────────────────────
EXPORT_COLUMNS = [
    'keyword',
    'pmid',
    'title',
    'publication_type',
    'authors',
    'affiliation',
    'country',
    'journal',
    'publication_date',
    'abstract',
    'pmc_id',
    'url',
    'keyword_match_count',
    'matched_keywords',
    'per_keyword_hits',
    'keyword_total_hits',
    'Free article complete content',   # added by add_full_text_column
    'pdf_total_keyword_hits',          # keyword hit count in PDF full text
    'pdf_per_keyword_hits',            # per-keyword breakdown in PDF
]

# Columns that should never appear in exports
EXPORT_DROP = {'pub_type_label', 'pdf_url', 'pmc_url', 'is_free_pmc'}


def clean_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Drop internal columns, enforce friendly column order, rename headers."""
    df = df.copy()

    # Drop unwanted columns
    drop = [c for c in EXPORT_DROP if c in df.columns]
    if drop:
        df = df.drop(columns=drop)

    # Reorder: put known columns first, then anything extra
    ordered = [c for c in EXPORT_COLUMNS if c in df.columns]
    extras  = [c for c in df.columns if c not in set(EXPORT_COLUMNS)]
    df = df[ordered + extras]

    # Friendly header rename
    rename_map = {
        'pmid':                          'PMID',
        'title':                         'Title',
        'publication_type':              'Publication Type',
        'authors':                       'Authors',
        'affiliation':                   'Affiliation',
        'country':                       'Country',
        'journal':                       'Journal',
        'publication_date':              'Publication Date',
        'abstract':                      'Abstract',
        'pmc_id':                        'PMC ID',
        'url':                           'PubMed URL',
        'keyword':                       'Keyword',
        'keyword_match_count':           'Keyword Match Count',
        'matched_keywords':              'Matched Keywords',
        'per_keyword_hits':              'Hits Per Keyword',
        'keyword_total_hits':            'Total Keyword Hits',
        'Free article complete content': 'Full Text (PMC)',
        'pdf_total_keyword_hits':        'PDF Total Keyword Hits',
        'pdf_per_keyword_hits':          'PDF Hits Per Keyword',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def add_full_text_column(df, keywords=None):
    """
    Add full text column plus PDF keyword hit counts for each free PMC article.

    keywords: list of original search keywords — used to count hits in the PDF.
              If None, hit columns are skipped.
    """
    df = df.copy()
    content_col        = []
    pdf_total_col      = []
    pdf_per_kw_col     = []

    # Pre-compile per-keyword patterns once (reuse scraper helper via inline logic)
    kw_patterns = {}
    if keywords:
        for kw in keywords:
            # Strip PubMed syntax the same way _terms_from_keyword does
            cleaned = re.sub(r'\[\w+\]', '', kw)
            cleaned = re.sub(r'\b(AND|OR|NOT)\b', ' ', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'["\(\)]', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
            terms   = [t for t in cleaned.split() if len(t) > 1]
            if terms:
                kw_patterns[kw] = re.compile(
                    '|'.join(re.escape(t) for t in terms), re.IGNORECASE
                )

    for _, row in df.iterrows():
        if row.get('is_free_pmc') and row.get('pdf_url'):
            print(f"  Fetching PDF for PMID {row.get('pmid', '?')} ...")
            text = fetch_pdf_text(row['pdf_url'])
        else:
            text = ''

        content_col.append(text)

        # Count keyword hits in full text
        if text and kw_patterns:
            text_lower  = text.lower()
            total_hits  = 0
            per_kw_parts = []
            for kw, pat in kw_patterns.items():
                count = len(pat.findall(text_lower))
                total_hits += count
                if count > 0:
                    per_kw_parts.append(f"{kw}: {count}")
            pdf_total_col.append(total_hits)
            pdf_per_kw_col.append('; '.join(per_kw_parts) if per_kw_parts else '')
        else:
            pdf_total_col.append(0)
            pdf_per_kw_col.append('')

    df['Free article complete content'] = content_col
    if keywords:
        df['pdf_total_keyword_hits'] = pdf_total_col
        df['pdf_per_keyword_hits']   = pdf_per_kw_col

    # Drop internal-only columns not needed in exports
    drop_cols = [c for c in ['pub_type_label'] if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'change-me-in-production')

# ── User accounts ─────────────────────────────────────────────────────────────
# Simple in-memory user store. For production use a database.
# HOW TO ADD A USER:
#   from werkzeug.security import generate_password_hash
#   print(generate_password_hash("their_password"))
#   # paste the output as the password value below

USERS = {
    # email: hashed_password
    # Add your users here. Generate hash with: generate_password_hash("password")
    "admin@episcience.com": generate_password_hash("admin123"),
    "sreekanth.dabbara@gmail.com": generate_password_hash("epi2024"),
}

def login_required(f):
    """Decorator — redirects to login page if user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# ── NCBI credentials ──────────────────────────────────────────────────────────
# REQUIRED: change to your email
NCBI_EMAIL = "your.email@example.com"

# OPTIONAL but RECOMMENDED: free API key from https://www.ncbi.nlm.nih.gov/account/
# Adding a key raises the rate limit from 3 → 10 req/s and cuts search time ~3x
NCBI_API_KEY = None   # e.g. "abc123def456..."

# Default max articles fetched per keyword (user can override on results page)
DEFAULT_MAX_RESULTS = 500

scraper = MultiKeywordPubMedScraper(email=NCBI_EMAIL, api_key=NCBI_API_KEY)

recent_searches = []

# In-memory cache: search_id -> {keyword_summary, sorted_results_records}
# Keyed by a short hash so exports read the same data the user sees
import hashlib
_search_cache: dict = {}
CACHE_MAX = 20   # keep last 20 searches in memory


# ── Auth routes ──────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page."""
    if 'user_email' in session:
        return redirect(url_for('index'))   # already logged in

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        user_hash = USERS.get(email)
        if user_hash and check_password_hash(user_hash, password):
            session.permanent = bool(remember)
            session['user_email'] = email
            session['user_name']  = email.split('@')[0].title()
            return redirect(url_for('index'))
        else:
            return render_template('login.html',
                                   error="Invalid email or password. Please try again.",
                                   email=email)

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Simple self-registration — adds user to in-memory store."""
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not email or not password:
            return render_template('register.html', error="Email and password are required.")
        if password != confirm:
            return render_template('register.html', error="Passwords do not match.", email=email)
        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters.", email=email)
        if email in USERS:
            return render_template('register.html', error="An account with that email already exists.", email=email)

        USERS[email] = generate_password_hash(password)
        return render_template('login.html', message="Account created! You can now log in.")

    return render_template('register.html')


@app.route('/forgot-password')
def forgot_password():
    """Placeholder — implement email reset for production."""
    return render_template('login.html',
                           message="Password reset is not yet configured. Contact your administrator.")


# ── Main app routes (all protected by login_required) ────────────────────────

@app.route('/')
@login_required
def index():
    """Home page with search form"""
    return render_template('index_multi_with_logo.html', recent_searches=recent_searches[:10])


@app.route('/search', methods=['POST'])
@login_required
def search():
    """Handle multi-keyword search requests — fetches ALL results, filtering done on results page"""
    try:
        keywords_input = request.form.get('keywords', '').strip()

        if not keywords_input:
            return render_template('index_multi_with_logo.html',
                                 error="Please enter at least one keyword",
                                 recent_searches=recent_searches[:10])

        # Parse keywords — comma-separated or one per line
        if ',' in keywords_input:
            keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        else:
            keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]

        if not keywords:
            return render_template('index_multi_with_logo.html',
                                 error="No valid keywords found",
                                 recent_searches=recent_searches[:10])

        print(f"\nSearching for {len(keywords)} keywords (all results): {keywords}")

        # Respect user-selected fetch limit (defaults to DEFAULT_MAX_RESULTS)
        max_results = int(request.form.get('max_results', DEFAULT_MAX_RESULTS))
        max_results = max(1, min(max_results, 10000))  # clamp to safe range

        # Fetch up to max_results per keyword; user can limit display on results page
        all_results, ncbi_totals = scraper.search_multiple_keywords(keywords, max_results_per_keyword=max_results)

        # Compute cross-keyword match scores for every article
        all_results = scraper.compute_keyword_scores(all_results, keywords)

        # Default initial sort: ascending by article count
        sorted_results = scraper.sort_results_by_count(all_results, ascending=True)

        # Prepare full dataset for template
        keyword_summary = []
        total_articles = 0

        for keyword, df in sorted_results.items():
            count = len(df)
            total_articles += count

            # Pass records unsorted; JS handles all article-level sorting
            records = df.to_dict('records') if not df.empty else []
            free_count = sum(1 for r in records if r.get('is_free_pmc'))
            ncbi_total = ncbi_totals.get(keyword, count)

            keyword_summary.append({
                'keyword': keyword,
                'count': count,
                'ncbi_total': ncbi_total,          # real NCBI total for Load More
                'fetched': count,                   # how many we actually fetched
                'has_more': ncbi_total > count,     # whether Load More button shows
                'free_count': free_count,
                'results': records
            })

        # Store recent search record
        search_record = {
            'query': f"{len(keywords)} keyword(s): {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}",
            'count': total_articles,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        recent_searches.insert(0, search_record)
        if len(recent_searches) > 50:
            recent_searches.pop()

        total_free_articles  = sum(s['free_count'] for s in keyword_summary)
        total_ncbi_articles  = sum(s['ncbi_total'] for s in keyword_summary)
        keywords_str = ','.join(keywords)

        # ── Cache results so export doesn't need to re-search ────────────
        search_id = hashlib.md5(
            (keywords_str + str(max_results)).encode()
        ).hexdigest()[:12]
        _search_cache[search_id] = {
            'sorted_results': {kw: df for kw, df in sorted_results.items()},
            'keywords':       keywords,
            'sort_order':     'ascending',
            'max_results':    max_results,
        }
        # Keep cache bounded
        if len(_search_cache) > CACHE_MAX:
            oldest = next(iter(_search_cache))
            del _search_cache[oldest]
        # ─────────────────────────────────────────────────────────────────

        return render_template('results_multi.html',
                             keywords=keywords,
                             keywords_str=keywords_str,
                             search_id=search_id,
                             keyword_summary=keyword_summary,
                             total_articles=total_articles,
                             total_ncbi_articles=total_ncbi_articles,
                             total_free_articles=total_free_articles)

    except Exception as e:
        return render_template('index_multi_with_logo.html',
                             error=f"An error occurred: {str(e)}",
                             recent_searches=recent_searches[:10])


@app.route('/search_url', methods=['POST'])
@login_required
def search_url():
    """
    Handle PubMed URL-based search.
    Parses the URL, extracts the term + filters, converts them to a valid
    Entrez query, then runs the same pipeline as /search.
    """
    from urllib.parse import urlparse, parse_qs

    # ── PubMed filter code → Entrez query clause ─────────────────────────
    FILTER_MAP = {
        'datesearch.y_1':              '("last 1 year"[PDat])',
        'datesearch.y_5':              '("last 5 years"[PDat])',
        'datesearch.y_10':             '("last 10 years"[PDat])',
        'datesearch.y_20':             '("last 20 years"[PDat])',
        'lang.english':                '"english"[Language]',
        'lang.french':                 '"french"[Language]',
        'lang.german':                 '"german"[Language]',
        'lang.spanish':                '"spanish"[Language]',
        'lang.italian':                '"italian"[Language]',
        'lang.portuguese':             '"portuguese"[Language]',
        'lang.chinese':                '"chinese"[Language]',
        'lang.japanese':               '"japanese"[Language]',
        'hum_ani.humans':              '"humans"[MeSH Terms]',
        'hum_ani.animals':             '"animals"[MeSH Terms]',
        'ages.child':                  '"child"[MeSH Terms]',
        'ages.infant':                 '"infant"[MeSH Terms]',
        'ages.adult':                  '"adult"[MeSH Terms]',
        'ages.aged':                   '"aged"[MeSH Terms]',
        'ffrft.Y':                     '"full text"[Filter]',
        'simsearch2.ffrft':            '"free full text"[Filter]',
        'type.clinicaltrial':          '"Clinical Trial"[Publication Type]',
        'type.review':                 '"Review"[Publication Type]',
        'type.systematicreview':       '"Systematic Review"[Publication Type]',
        'type.randomizedcontrolledtrial': '"Randomized Controlled Trial"[Publication Type]',
        'type.metaanalysis':           '"Meta-Analysis"[Publication Type]',
        'type.casereports':            '"Case Reports"[Publication Type]',
        'type.observationalstudy':     '"Observational Study"[Publication Type]',
        'type.journal':                '"Journal Article"[Publication Type]',
        'sex.female':                  '"female"[MeSH Terms]',
        'sex.male':                    '"male"[MeSH Terms]',
    }

    try:
        pubmed_url  = request.form.get('pubmed_url', '').strip()
        max_results = int(request.form.get('max_results', DEFAULT_MAX_RESULTS))
        max_results = max(1, min(max_results, 10000))

        if not pubmed_url:
            return render_template('index_multi_with_logo.html',
                                 error="Please enter a PubMed URL",
                                 recent_searches=recent_searches[:10])

        # ── Parse URL ────────────────────────────────────────────────────
        parsed = urlparse(pubmed_url)

        # Accept both pubmed.ncbi.nlm.nih.gov and ncbi.nlm.nih.gov/pubmed
        if 'pubmed' not in parsed.netloc + parsed.path:
            return render_template('index_multi_with_logo.html',
                                 error="Please enter a valid PubMed URL "
                                       "(must contain pubmed.ncbi.nlm.nih.gov)",
                                 recent_searches=recent_searches[:10])

        params  = parse_qs(parsed.query, keep_blank_values=False)
        term    = params.get('term', [''])[0].strip()
        filters = params.get('filter', [])

        if not term:
            return render_template('index_multi_with_logo.html',
                                 error="No search term found in the URL. "
                                       "Make sure the URL includes a ?term= parameter.",
                                 recent_searches=recent_searches[:10])

        # ── Convert filters to Entrez clauses ────────────────────────────
        filter_clauses = []
        unknown_filters = []
        for f in filters:
            if f in FILTER_MAP:
                filter_clauses.append(FILTER_MAP[f])
            else:
                unknown_filters.append(f)

        if unknown_filters:
            print(f"  [search_url] unrecognised filters (ignored): {unknown_filters}")

        # Build the final Entrez query
        if filter_clauses:
            entrez_query = f"({term}) AND " + " AND ".join(filter_clauses)
        else:
            entrez_query = term

        # Use the term as the display label, filters as annotation
        filter_summary = "; ".join(filters) if filters else "none"
        display_label  = entrez_query   # shown in results page keyword card

        print(f"\n[search_url] Entrez query: {entrez_query}")
        print(f"[search_url] Filters applied: {filter_summary}")

        # ── Run same pipeline as /search ─────────────────────────────────
        keywords = [display_label]   # single "keyword" = the full entrez query

        all_results, ncbi_totals = scraper.search_multiple_keywords(
            keywords, max_results_per_keyword=max_results
        )
        all_results   = scraper.compute_keyword_scores(all_results, keywords)
        sorted_results = scraper.sort_results_by_count(all_results, ascending=True)

        keyword_summary = []
        total_articles  = 0

        for keyword, df in sorted_results.items():
            count = len(df)
            total_articles += count
            records    = df.to_dict('records') if not df.empty else []
            free_count = sum(1 for r in records if r.get('is_free_pmc'))
            ncbi_total = ncbi_totals.get(keyword, count)

            keyword_summary.append({
                'keyword':    keyword,
                'count':      count,
                'ncbi_total': ncbi_total,
                'fetched':    count,
                'has_more':   ncbi_total > count,
                'free_count': free_count,
                'results':    records,
            })

        search_record = {
            'query':     f"URL search: {term[:60]}{'…' if len(term) > 60 else ''}",
            'count':     total_articles,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        recent_searches.insert(0, search_record)
        if len(recent_searches) > 50:
            recent_searches.pop()

        total_free_articles = sum(s['free_count'] for s in keyword_summary)
        total_ncbi_articles = sum(s['ncbi_total'] for s in keyword_summary)
        keywords_str        = ','.join(keywords)

        search_id = hashlib.md5(
            (keywords_str + str(max_results)).encode()
        ).hexdigest()[:12]
        _search_cache[search_id] = {
            'sorted_results': {kw: df for kw, df in sorted_results.items()},
            'keywords':       keywords,
            'sort_order':     'ascending',
            'max_results':    max_results,
        }
        if len(_search_cache) > CACHE_MAX:
            del _search_cache[next(iter(_search_cache))]

        return render_template('results_multi.html',
                             keywords=keywords,
                             keywords_str=keywords_str,
                             search_id=search_id,
                             keyword_summary=keyword_summary,
                             total_articles=total_articles,
                             total_ncbi_articles=total_ncbi_articles,
                             total_free_articles=total_free_articles)

    except Exception as e:
        import traceback; traceback.print_exc()
        return render_template('index_multi_with_logo.html',
                             error=f"An error occurred: {str(e)}",
                             recent_searches=recent_searches[:10])



@app.route('/api/search/multi', methods=['POST'])
def api_search_multi():
    """API endpoint for multi-keyword searching"""
    try:
        data = request.get_json()
        
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        max_results = int(data.get('max_results_per_keyword', 20))
        sort_order = data.get('sort_order', 'ascending')
        
        if not keywords:
            return jsonify({'error': 'Keywords parameter is required'}), 400
        
        if max_results < 1 or max_results > 10000:
            return jsonify({'error': 'max_results must be between 1 and 10,000'}), 400
        
        # Search all keywords
        all_results, _ = scraper.search_multiple_keywords(keywords, max_results)
        
        # Sort by article count
        sorted_results = scraper.sort_results_by_count(all_results, ascending=(sort_order == 'ascending'))
        
        # Convert to JSON format
        response_data = {
            'total_keywords': len(keywords),
            'sort_order': sort_order,
            'results': []
        }
        
        for keyword, df in sorted_results.items():
            response_data['results'].append({
                'keyword': keyword,
                'count': len(df),
                'articles': df.to_dict('records') if not df.empty else []
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/load_more', methods=['POST'])
@login_required
def load_more():
    """
    Fetch the next batch of articles for a single keyword starting at an offset.
    Called by the results page 'Load More' button via AJAX.

    Request JSON:
        { "keyword": "lung cancer", "offset": 500, "batch": 500, "all_keywords": ["lung cancer", "breast cancer"] }

    Response JSON:
        { "keyword": "...", "articles": [...], "fetched": N, "offset": N, "has_more": bool, "ncbi_total": N }
    """
    try:
        data       = request.get_json()
        keyword    = data.get('keyword', '').strip()
        offset     = int(data.get('offset', 500))
        batch      = int(data.get('batch', 500))
        all_kws    = data.get('all_keywords', [keyword])

        if not keyword:
            return jsonify({'error': 'keyword is required'}), 400

        batch = max(1, min(batch, 500))   # cap at 500 per call

        # Fetch next batch
        articles = scraper.fetch_more(keyword, offset=offset, batch=batch)
        articles = [a for a in articles if a is not None]

        # Score the new batch against all keywords
        if articles:
            df_new = pd.DataFrame(articles)
            df_new['keyword'] = keyword

            # Lightweight scoring: keyword_match_count = 1 (single batch),
            # total hits computed via combined regex
            all_terms = list({
                term
                for kw in all_kws
                for term in scraper._terms_from_keyword(kw)
            })
            if all_terms:
                pattern = re.compile(
                    "|".join(re.escape(t) for t in all_terms), re.IGNORECASE
                )
                text_series = (
                    df_new['title'].fillna('') + ' ' + df_new['abstract'].fillna('')
                ).str.lower()
                df_new['keyword_total_hits']  = text_series.apply(
                    lambda t: len(pattern.findall(t))
                )
            else:
                df_new['keyword_total_hits'] = 0

            df_new['keyword_match_count'] = 1   # will update client-side if cross-match

            # Get real NCBI total to know if even more exist
            _, ncbi_total = scraper.search_pubmed(keyword, max_results=1)
            new_offset = offset + len(articles)

            return jsonify({
                'keyword':    keyword,
                'articles':   df_new.to_dict('records'),
                'fetched':    len(articles),
                'offset':     new_offset,
                'ncbi_total': ncbi_total,
                'has_more':   new_offset < ncbi_total,
            })
        else:
            _, ncbi_total = scraper.search_pubmed(keyword, max_results=1)
            return jsonify({
                'keyword':    keyword,
                'articles':   [],
                'fetched':    0,
                'offset':     offset,
                'ncbi_total': ncbi_total,
                'has_more':   False,
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _split_fulltext_across_cells(ws, wrap_align):
    """
    For every row in ws, find the 'Full Text (PMC)' column.
    If the content exceeds EXCEL_CELL_LIMIT chars, split the remainder
    into continuation columns: 'Full Text (PMC) - Part 2', '- Part 3', etc.
    All continuation header cells are added dynamically to the right of the
    existing last column.
    """
    # Find the Full Text column index from the header row
    ft_col_idx = None
    last_col    = ws.max_column

    for cell in ws[1]:
        if cell.value == 'Full Text (PMC)':
            ft_col_idx = cell.column
            break

    if ft_col_idx is None:
        return   # no full-text column on this sheet

    # First pass: split every cell value and track max parts needed
    row_chunks = {}   # row_number -> list of string chunks
    max_parts  = 1

    for row in ws.iter_rows(min_row=2):
        cell  = row[ft_col_idx - 1]
        value = cell.value
        if not value or not isinstance(value, str) or len(value) <= EXCEL_CELL_LIMIT:
            continue

        # Split at word boundaries where possible
        chunks = []
        remaining = value
        while remaining:
            if len(remaining) <= EXCEL_CELL_LIMIT:
                chunks.append(remaining)
                break
            # Try to split at last space/newline before the limit
            cut = remaining[:EXCEL_CELL_LIMIT].rfind(' ')
            if cut < EXCEL_CELL_LIMIT * 0.8:   # no good split point found
                cut = EXCEL_CELL_LIMIT
            chunks.append(remaining[:cut])
            remaining = remaining[cut:].lstrip()

        row_chunks[cell.row] = chunks
        if len(chunks) > max_parts:
            max_parts = len(chunks)

    if max_parts <= 1:
        return   # nothing needs splitting

    # Add continuation header columns (Part 2, Part 3, …)
    from openpyxl.styles import PatternFill, Font, Alignment
    hdr_fill = PatternFill(start_color='1A365D', end_color='1A365D', fill_type='solid')
    hdr_font = Font(color='FFFFFF', bold=True)

    part_col_map = {}   # part_number (2,3,...) -> column index
    for part in range(2, max_parts + 1):
        col_idx = last_col + (part - 1)
        part_col_map[part] = col_idx
        hdr_cell = ws.cell(row=1, column=col_idx,
                           value=f'Full Text (PMC) - Part {part}')
        hdr_cell.fill      = hdr_fill
        hdr_cell.font      = hdr_font
        hdr_cell.alignment = wrap_align
        ws.column_dimensions[
            __import__('openpyxl.utils', fromlist=['get_column_letter'])
            .get_column_letter(col_idx)
        ].width = 80

    # Second pass: write chunks back
    for row_num, chunks in row_chunks.items():
        # Part 1 — overwrite the original cell
        ws.cell(row=row_num, column=ft_col_idx).value = chunks[0]
        ws.cell(row=row_num, column=ft_col_idx).alignment = wrap_align

        # Parts 2+ — write into continuation columns
        for part, chunk in enumerate(chunks[1:], start=2):
            col_idx = part_col_map[part]
            c = ws.cell(row=row_num, column=col_idx, value=chunk)
            c.alignment = wrap_align

            # Match the green highlight of free PMC rows if the original row was green
            orig_fill = ws.cell(row=row_num, column=ft_col_idx).fill
            if orig_fill and orig_fill.fgColor and orig_fill.fgColor.rgb not in ('00000000', 'FF000000', ''):
                c.fill = orig_fill


@app.route('/export/multi/<format>')
@login_required
def export_multi(format):
    """Export results — reads from cache if available, else re-searches."""
    try:
        search_id    = request.args.get('search_id', '')
        keywords_str = request.args.get('keywords', '')
        max_results  = int(request.args.get('max_results', DEFAULT_MAX_RESULTS))
        sort_order   = request.args.get('sort_order', 'ascending')

        # ── Try cache first ──────────────────────────────────────────────
        if search_id and search_id in _search_cache:
            cached       = _search_cache[search_id]
            sorted_results = cached['sorted_results']
            keywords     = cached['keywords']
            print(f"  [export] using cached results for search_id={search_id}")
        else:
            # Fallback: re-search (e.g. cache expired or direct URL access)
            print(f"  [export] cache miss — re-searching...")
            if not keywords_str:
                return "No keywords provided", 400
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            all_results, _ = scraper.search_multiple_keywords(keywords, max_results)
            all_results    = scraper.compute_keyword_scores(all_results, keywords)
            sorted_results = scraper.sort_results_by_count(
                all_results, ascending=(sort_order == 'ascending')
            )

        # Apply max_results limit per keyword
        limited_results = {}
        for kw, df in sorted_results.items():
            limited_results[kw] = df.head(max_results) if not df.empty else df

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # ── CSV ──────────────────────────────────────────────────────────
        if format == 'csv':
            frames = []
            for kw, df in limited_results.items():
                if df.empty:
                    continue
                df_ft = add_full_text_column(df, keywords=keywords)
                df_ft = clean_for_export(df_ft)
                frames.append(df_ft)

            if not frames:
                return "No results to export", 404

            combined = pd.concat(frames, ignore_index=True)
            output = io.StringIO()
            combined.to_csv(output, index=False)
            output.seek(0)

            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'pubmed_{timestamp}.csv'
            )

        # ── JSON ─────────────────────────────────────────────────────────
        elif format == 'json':
            structured = {
                'search_date':    timestamp,
                'sort_order':     sort_order,
                'total_keywords': len(limited_results),
                'keywords':       []
            }
            for kw, df in limited_results.items():
                if not df.empty:
                    df_ft = add_full_text_column(df, keywords=keywords)
                    df_ft = clean_for_export(df_ft)
                else:
                    df_ft = df
                structured['keywords'].append({
                    'keyword':       kw,
                    'article_count': len(df_ft),
                    'articles':      df_ft.to_dict('records') if not df_ft.empty else []
                })

            return send_file(
                io.BytesIO(json.dumps(structured, indent=2).encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'pubmed_{timestamp}.json'
            )

        # ── Excel ────────────────────────────────────────────────────────
        elif format == 'excel':
            from openpyxl.styles import PatternFill, Font, Alignment
            from openpyxl.utils import get_column_letter

            output = io.BytesIO()
            print("📊 Building Excel workbook...")

            with pd.ExcelWriter(output, engine='openpyxl') as writer:

                # Define shared styles up front
                hdr_fill   = PatternFill(start_color='1A365D', end_color='1A365D', fill_type='solid')
                hdr_font   = Font(color='FFFFFF', bold=True)
                green_fill = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')
                wrap_align = Alignment(wrap_text=True, vertical='top')

                # Summary sheet
                summary_rows = []
                for kw, df in limited_results.items():
                    free_count = int(df['is_free_pmc'].sum()) if 'is_free_pmc' in df.columns else 0
                    summary_rows.append({
                        'Keyword':           kw,
                        'Articles Exported': len(df),
                        'Free PMC Articles': free_count,
                    })
                pd.DataFrame(summary_rows).to_excel(writer, sheet_name='Summary', index=False)

                all_frames = []

                for kw, df in limited_results.items():
                    if df.empty:
                        continue

                    # Free PMC first within sheet
                    if 'is_free_pmc' in df.columns:
                        df = df.sort_values('is_free_pmc', ascending=False)

                    df_ft = add_full_text_column(df, keywords=keywords)
                    df_clean = clean_for_export(df_ft)
                    all_frames.append(df_clean)

                    # Sheet name (max 31 chars, no special chars)
                    sheet_name = "".join(
                        c for c in kw if c.isalnum() or c in (' ', '-', '_')
                    )[:31]

                    df_clean.to_excel(writer, sheet_name=sheet_name, index=False)

                    # ── Split Full Text across continuation cells if > 32,767 chars ──
                    _split_fulltext_across_cells(writer.sheets[sheet_name], wrap_align)

                    # ── Styling ──────────────────────────────────────────
                    ws = writer.sheets[sheet_name]

                    for cell in ws[1]:
                        cell.fill      = hdr_fill
                        cell.font      = hdr_font
                        cell.alignment = wrap_align

                    # Find key column indices from header row
                    col_map      = {cell.value: cell.column for cell in ws[1]}
                    pmc_col      = col_map.get('PMC ID')
                    fulltext_col = col_map.get('Full Text (PMC)')

                    for row in ws.iter_rows(min_row=2):
                        is_free = bool(pmc_col and row[pmc_col - 1].value not in (None, 'N/A', ''))
                        if is_free:
                            for cell in row:
                                cell.fill = green_fill
                        if fulltext_col:
                            row[fulltext_col - 1].alignment = wrap_align

                    # Column widths
                    width_map = {
                        'Full Text (PMC)': 80,
                        'Abstract':        50,
                        'Affiliation':     40,
                        'Title':           50,
                        'Publication Type': 30,
                        'Authors':         35,
                        'Journal':         30,
                        'PubMed URL':      30,
                    }
                    for col_cells in ws.columns:
                        hdr = str(col_cells[0].value or '')
                        w   = width_map.get(hdr, 18)
                        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = w

                # All Results sheet
                if all_frames:
                    pd.concat(all_frames, ignore_index=True).to_excel(
                        writer, sheet_name='All Results', index=False
                    )
                    # ── Split Full Text across continuation cells if > 32,767 chars ──
                    _split_fulltext_across_cells(
                        writer.sheets['All Results'], wrap_align
                    )

            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'pubmed_{timestamp}.xlsx'
            )

        else:
            return "Invalid format", 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Export error: {str(e)}", 500

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/export/bulk_csv')
@login_required
def export_bulk_csv():
    """
    Streaming bulk CSV export — fetches articles from NCBI in batches of 500
    and writes rows directly to the response stream without loading everything
    into memory. Supports up to the full NCBI result count per keyword.

    Query params:
        keywords   — comma-separated keyword list
        target     — total articles to fetch per keyword (default 10000)
        already    — already-fetched count to skip (start offset, default 0)
    """
    from flask import Response, stream_with_context
    import csv

    keywords_str = request.args.get('keywords', '')
    target       = min(int(request.args.get('target', 10000)), 500000)
    already      = int(request.args.get('already', 0))

    if not keywords_str:
        return "No keywords provided", 400

    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

    # ── Column map: same order and friendly names as Excel export ───────
    BULK_RENAME = {
        'keyword':              'Keyword',
        'pmid':                 'PMID',
        'title':                'Title',
        'publication_type':     'Publication Type',
        'authors':              'Authors',
        'affiliation':          'Affiliation',
        'country':              'Country',
        'journal':              'Journal',
        'publication_date':     'Publication Date',
        'abstract':             'Abstract',
        'pmc_id':               'PMC ID',
        'url':                  'PubMed URL',
        'keyword_match_count':  'Keyword Match Count',
        'matched_keywords':     'Matched Keywords',
        'per_keyword_hits':     'Hits Per Keyword',
        'keyword_total_hits':   'Total Keyword Hits',
        'full_text':            'Full Text (PMC)',
        'pdf_per_keyword_hits': 'PDF Hits Per Keyword',
        'pdf_total_hits':       'PDF Total Keyword Hits',
    }
    BULK_INTERNAL_COLS = list(BULK_RENAME.keys())
    BULK_FRIENDLY_COLS = [BULK_RENAME[k] for k in BULK_INTERNAL_COLS]

    # Whether to include full text (always yes — free PMC articles are rare)
    include_fulltext = True

    def generate():
        """
        Generator: for each batch of articles —
          1. Score keyword hits in title+abstract
          2. If free PMC article, fetch full text via PMC XML API and
             score keyword hits in the PDF body too
          3. Write the row immediately to the stream
        Free PMC articles are typically only in the hundreds even for
        million-article searches, so the extra fetch time is small.
        """
        # Write CSV header
        buf = io.StringIO()
        csv.DictWriter(buf, fieldnames=BULK_FRIENDLY_COLS,
                       extrasaction='ignore',
                       lineterminator='\n').writeheader()
        yield buf.getvalue()

        # Pre-compile per-keyword patterns once
        kw_patterns = {}
        for kw in keywords:
            terms = scraper._terms_from_keyword(kw)
            if terms:
                kw_patterns[kw] = re.compile(
                    '|'.join(re.escape(t) for t in terms), re.IGNORECASE
                )

        for kw in keywords:
            fetched_so_far = already
            remaining      = target

            while remaining > 0:
                batch_size = min(500, remaining)
                articles   = scraper.fetch_more(kw, offset=fetched_so_far,
                                                batch=batch_size)
                articles   = [a for a in articles if a is not None]
                if not articles:
                    break

                for art in articles:
                    # ── Metadata scores (title + abstract) ───────────────
                    ab_text = (
                        str(art.get('title', '') or '') + ' ' +
                        str(art.get('abstract', '') or '')
                    ).lower()

                    art['keyword_match_count'] = 1
                    art['matched_keywords']    = kw
                    art['keyword']             = kw

                    per_parts  = []
                    total_hits = 0
                    for k, pat in kw_patterns.items():
                        c = len(pat.findall(ab_text))
                        total_hits += c
                        if c:
                            per_parts.append(f"{k}: {c}")
                    art['keyword_total_hits'] = total_hits
                    art['per_keyword_hits']   = '; '.join(per_parts)

                    # ── Full text for free PMC articles ───────────────────
                    art['full_text']            = ''
                    art['pdf_per_keyword_hits'] = ''
                    art['pdf_total_hits']       = 0

                    if include_fulltext and art.get('is_free_pmc')                             and art.get('pdf_url'):
                        print(f"  [bulk] fetching full text PMID "
                              f"{art.get('pmid','?')} ...")
                        ft = fetch_pdf_text(art['pdf_url'])
                        art['full_text'] = ft

                        if ft and not ft.startswith('Error')                                 and not ft.startswith('Could not')                                 and not ft.startswith('No text')                                 and not ft.startswith('pdfplumber'):
                            ft_lower      = ft.lower()
                            pdf_parts     = []
                            pdf_total     = 0
                            for k, pat in kw_patterns.items():
                                c = len(pat.findall(ft_lower))
                                pdf_total += c
                                if c:
                                    pdf_parts.append(f"{k}: {c}")
                            art['pdf_per_keyword_hits'] = '; '.join(pdf_parts)
                            art['pdf_total_hits']       = pdf_total

                    # ── Write row ─────────────────────────────────────────
                    friendly_row = {
                        BULK_RENAME[k]: art.get(k, '')
                        for k in BULK_INTERNAL_COLS
                    }
                    buf = io.StringIO()
                    csv.DictWriter(buf, fieldnames=BULK_FRIENDLY_COLS,
                                   extrasaction='ignore',
                                   lineterminator='\n').writerow(friendly_row)
                    yield buf.getvalue()

                fetched_so_far += len(articles)
                remaining      -= len(articles)
                if len(articles) < batch_size:
                    break   # NCBI has no more results

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        stream_with_context(generate()),
        mimetype='text/csv',
        headers={
            'Content-Disposition':
                f'attachment; filename="pubmed_bulk_{timestamp}.csv"'
        }
    )


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'email': NCBI_EMAIL,
        'features': ['multi-keyword-search', 'sorted-results'],
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🧬 PubMed Scraper - Multi-Keyword Search")
    print("=" * 60)
    print(f"Email configured: {NCBI_EMAIL}")
    if NCBI_EMAIL == "your.email@example.com":
        print("⚠️  WARNING: Please update your email in this file!")
        print("   Line 215: NCBI_EMAIL = 'your.email@example.com'")
    print("=" * 60)
    print("✨ Features:")
    print("  - Search multiple keywords at once")
    print("  - Results sorted by article count (ascending/descending)")
    print("  - Grouped display by keyword")
    print("  - Export to CSV, JSON, or Excel")
    print("=" * 60)
    print("Starting server at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
