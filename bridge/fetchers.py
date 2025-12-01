"""Data fetching from external sources"""
import requests
from datetime import datetime
from lxml import etree
from config import ZENODO_TOKEN, GITHUB_TOKEN


def fetch_from_source(source, limit, query):
    """Route to appropriate fetcher based on source"""
    fetchers = {
        'zenodo': fetch_zenodo,
        'github': fetch_github,
        'arxiv': fetch_arxiv,
        'jsonplaceholder': fetch_jsonplaceholder
    }
    
    fetcher = fetchers.get(source)
    if fetcher:
        return fetcher(limit, query)
    return None


def fetch_specific(source, record_id):
    """Fetch specific record by ID"""
    record_id = record_id.strip()
    
    if source == 'zenodo':
        return fetch_zenodo_by_id(record_id)
    elif source == 'github':
        return fetch_github_by_id(record_id)
    elif source == 'arxiv':
        return fetch_arxiv_by_id(record_id)
    
    return None


# Zenodo
def fetch_zenodo(limit, query):
    """Fetch records from Zenodo"""
    params = {
        'q': query or 'open science',
        'size': min(limit, 100),
        'sort': 'mostrecent'
    }
    
    headers = {}
    if ZENODO_TOKEN:
        headers['Authorization'] = f'Bearer {ZENODO_TOKEN}'
    
    try:
        response = requests.get(
            'https://zenodo.org/api/records',
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        records = []
        for hit in data.get('hits', {}).get('hits', [])[:limit]:
            records.append(_transform_zenodo_record(hit))
        
        return records
    except Exception as e:
        print(f"Zenodo fetch error: {e}")
        return []


def fetch_zenodo_by_id(record_id):
    """Fetch specific Zenodo record"""
    # Parse ID from different formats
    if 'zenodo.org' in record_id:
        record_id = record_id.split('/')[-1]
    elif '10.5281/zenodo.' in record_id:
        record_id = record_id.split('zenodo.')[-1]
    
    try:
        response = requests.get(
            f'https://zenodo.org/api/records/{record_id}',
            timeout=30
        )
        response.raise_for_status()
        return _transform_zenodo_record(response.json())
    except Exception as e:
        print(f"Zenodo specific fetch error: {e}")
        return None


def _transform_zenodo_record(hit):
    """Transform Zenodo record to standard format"""
    metadata = hit.get('metadata', {})
    
    creators = metadata.get('creators', [])
    creator_names = [c.get('name', 'Unknown') for c in creators]
    
    description = metadata.get('description', 'No description')
    if len(description) > 500:
        description = description[:500] + '...'
    
    return {
        'identifier': f'zenodo:{hit.get("id")}',
        'datestamp': metadata.get('publication_date', datetime.now().strftime('%Y-%m-%d')),
        'title': metadata.get('title', 'Untitled'),
        'creator': '; '.join(creator_names) if creator_names else 'Unknown',
        'description': description,
        'doi': hit.get('doi', ''),
        'url': hit.get('links', {}).get('self_html', '')
    }


# GitHub
def fetch_github(limit, query):
    """Fetch repositories from GitHub"""
    params = {
        'q': query or 'machine learning',
        'sort': 'stars',
        'per_page': min(limit, 100)
    }
    
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        response = requests.get(
            'https://api.github.com/search/repositories',
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        records = []
        for repo in data.get('items', [])[:limit]:
            records.append(_transform_github_record(repo))
        
        return records
    except Exception as e:
        print(f"GitHub fetch error: {e}")
        return []


def fetch_github_by_id(repo_path):
    """Fetch specific GitHub repository"""
    # Parse repo path from URL
    if 'github.com' in repo_path:
        parts = repo_path.split('github.com/')[-1].split('/')
        repo_path = f"{parts[0]}/{parts[1]}"
    
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        response = requests.get(
            f'https://api.github.com/repos/{repo_path}',
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return _transform_github_record(response.json())
    except Exception as e:
        print(f"GitHub specific fetch error: {e}")
        return None


def _transform_github_record(repo):
    """Transform GitHub record to standard format"""
    return {
        'identifier': f'github:repo:{repo["id"]}',
        'datestamp': repo['created_at'][:10],
        'title': repo['full_name'],
        'creator': repo['owner']['login'],
        'description': repo['description'] or 'No description',
        'url': repo['html_url']
    }


# arXiv
def fetch_arxiv(limit, query):
    """Fetch papers from arXiv"""
    params = {
        'search_query': f'all:{query}' if query else 'all:machine learning',
        'start': 0,
        'max_results': min(limit, 100)
    }
    
    try:
        response = requests.get(
            'http://export.arxiv.org/api/query',
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        root = etree.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        records = []
        for entry in root.findall('atom:entry', ns)[:limit]:
            records.append(_transform_arxiv_record(entry, ns))
        
        return records
    except Exception as e:
        print(f"arXiv fetch error: {e}")
        return []


def fetch_arxiv_by_id(arxiv_id):
    """Fetch specific arXiv paper"""
    # Parse ID from URL
    if 'arxiv.org' in arxiv_id:
        arxiv_id = arxiv_id.split('/abs/')[-1]
    
    try:
        response = requests.get(
            f'http://export.arxiv.org/api/query?id_list={arxiv_id}',
            timeout=30
        )
        response.raise_for_status()
        
        root = etree.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entry = root.find('atom:entry', ns)
        if entry is not None:
            return _transform_arxiv_record(entry, ns)
        return None
    except Exception as e:
        print(f"arXiv specific fetch error: {e}")
        return None


def _transform_arxiv_record(entry, ns):
    """Transform arXiv record to standard format"""
    title = entry.find('atom:title', ns)
    published = entry.find('atom:published', ns)
    summary = entry.find('atom:summary', ns)
    authors = entry.findall('atom:author', ns)
    arxiv_id = entry.find('atom:id', ns)
    
    author_names = []
    for author in authors:
        name = author.find('atom:name', ns)
        if name is not None:
            author_names.append(name.text)
    
    id_text = arxiv_id.text if arxiv_id is not None else ''
    arxiv_num = id_text.split('/abs/')[-1] if '/abs/' in id_text else ''
    
    return {
        'identifier': f'arxiv:{arxiv_num}',
        'datestamp': published.text[:10] if published is not None else '',
        'title': title.text.strip() if title is not None else 'Untitled',
        'creator': '; '.join(author_names) if author_names else 'Unknown',
        'description': summary.text.strip()[:500] if summary is not None else '',
        'url': id_text
    }


# JSONPlaceholder (Demo)
def fetch_jsonplaceholder(limit, query=''):
    """Fetch demo data from JSONPlaceholder"""
    try:
        response = requests.get(
            'https://jsonplaceholder.typicode.com/posts',
            timeout=30
        )
        response.raise_for_status()
        posts = response.json()
        
        records = []
        for post in posts[:limit]:
            records.append({
                'identifier': f'jsonplaceholder:post:{post["id"]}',
                'datestamp': datetime.now().strftime('%Y-%m-%d'),
                'title': post['title'],
                'creator': f'User {post["userId"]}',
                'description': post['body']
            })
        
        return records
    except Exception as e:
        print(f"JSONPlaceholder fetch error: {e}")
        return []
