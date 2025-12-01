from flask import Flask, jsonify, request
import requests
import subprocess
import os
from datetime import datetime
from lxml import etree

app = Flask(__name__)

# Configuration
OAI_PMH_CLI = 'C:/xampp82/htdocs/oai-pmh2/bin/cli'
TEMP_DIR = 'C:/xampp82/htdocs/oai-pmh2/temp'

# API Tokens (βάλε τα δικά σου)
ZENODO_TOKEN = 'vqIYhpJ4Xo0hWYJU4lC9SXlxQGuB3Nm63wZJxPCVET7F91F3uS43Q3LSjDS4'  # https://zenodo.org/account/settings/applications/tokens/new/
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN'   # Optional, για περισσότερα rate limits

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'version': '1.0',
        'endpoints': {
            '/sources': 'List all available data sources',
            '/sync/<source>': 'Sync data from a specific source',
            '/sync/<source>?limit=N': 'Sync with custom limit'
        },
        'available_sources': list(DATA_SOURCES.keys())
    })

@app.route('/sources')
def list_sources():
    """List all available data sources"""
    sources = []
    for name, config in DATA_SOURCES.items():
        sources.append({
            'name': name,
            'description': config.get('description', ''),
            'type': config['type'],
            'url': f'/sync/{name}'
        })
    return jsonify({'sources': sources})

@app.route('/sync/<source>')
def sync_data(source):
    """Sync data from specified source"""
    try:
        # Get optional parameters
        limit = request.args.get('limit', type=int)
        query = request.args.get('q', '')

        # Fetch data από external source
        data = fetch_from_external_source(source, limit=limit, query=query)

        if not data:
            return jsonify({
                'status': 'error',
                'message': f'No data found or unknown source: {source}'
            }), 404

        results = []
        success_count = 0

        # Προσθήκη κάθε record
        for record in data:
            xml_file = create_xml_file(record)

            result = subprocess.run([
                'php', OAI_PMH_CLI,
                'oai:add:record',
                record['identifier'],
                'oai_dc',
                xml_file,
                '--no-interaction'
            ], capture_output=True, text=True, cwd='C:/xampp82/htdocs/oai-pmh2')

            # Clean up temp file
            if os.path.exists(xml_file):
                os.remove(xml_file)

            status = 'success' if result.returncode == 0 else 'failed'
            if result.returncode == 0:
                success_count += 1

            results.append({
                'identifier': record['identifier'],
                'status': status,
                'title': record.get('title', '')[:50] + '...',
                'error': result.stderr.strip() if result.stderr else None
            })

        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': len(data),
            'successful': success_count,
            'failed': len(data) - success_count,
            'timestamp': datetime.now().isoformat(),
            'details': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'source': source
        }), 500

# ============================================================================
# DATA SOURCES CONFIGURATION
# ============================================================================

DATA_SOURCES = {
    'zenodo': {
        'type': 'rest_api',
        'description': 'Zenodo research repository',
        'api_url': 'https://zenodo.org/api/records'
    },
    'zenodo_sandbox': {
        'type': 'rest_api',
        'description': 'Zenodo sandbox for testing',
        'api_url': 'https://sandbox.zenodo.org/api/records'
    },
    'jsonplaceholder': {
        'type': 'rest_api',
        'description': 'JSONPlaceholder demo API',
        'api_url': 'https://jsonplaceholder.typicode.com/posts'
    },
    'github': {
        'type': 'rest_api',
        'description': 'GitHub repositories',
        'api_url': 'https://api.github.com'
    },
    'arxiv': {
        'type': 'rest_api',
        'description': 'arXiv preprint repository',
        'api_url': 'http://export.arxiv.org/api/query'
    }
}

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_from_external_source(source, limit=None, query=''):
    """Main router για data fetching"""

    if source not in DATA_SOURCES:
        return None

    # Default limit
    if limit is None:
        limit = 10

    # Route to appropriate handler
    if source == 'zenodo' or source == 'zenodo_sandbox':
        return fetch_from_zenodo(source, limit, query)

    elif source == 'jsonplaceholder':
        return fetch_from_jsonplaceholder(limit)

    elif source == 'github':
        return fetch_from_github(limit, query)

    elif source == 'arxiv':
        return fetch_from_arxiv(limit, query)

    else:
        return None

def fetch_from_zenodo(source, limit=10, query='open science'):
    """Fetch records από Zenodo"""

    api_url = DATA_SOURCES[source]['api_url']

    params = {
        'q': query if query else 'open science',
        'size': min(limit, 100),  # Zenodo max is 100 per page
        'page': 1,
        'sort': 'mostrecent'
    }

    headers = {}
    if ZENODO_TOKEN and ZENODO_TOKEN != 'YOUR_ZENODO_TOKEN':
        headers['Authorization'] = f'Bearer {ZENODO_TOKEN}'

    response = requests.get(api_url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"Zenodo API error: {response.status_code}")
        return []

    data = response.json()
    records = []

    for hit in data.get('hits', {}).get('hits', [])[:limit]:
        metadata = hit.get('metadata', {})

        # Get creators
        creators = metadata.get('creators', [])
        creator_names = [c.get('name', 'Unknown') for c in creators]

        # Get description
        description = metadata.get('description', 'No description')
        if len(description) > 500:
            description = description[:500] + '...'

        records.append({
            'identifier': f'zenodo:{hit.get("id")}',
            'datestamp': metadata.get('publication_date', datetime.now().strftime('%Y-%m-%d')),
            'title': metadata.get('title', 'Untitled'),
            'creator': '; '.join(creator_names) if creator_names else 'Unknown',
            'description': description,
            'doi': hit.get('doi', ''),
            'url': hit.get('links', {}).get('self_html', '')
        })

    return records

def fetch_from_jsonplaceholder(limit=10):
    """Fetch από JSONPlaceholder"""

    response = requests.get('https://jsonplaceholder.typicode.com/posts')
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

def fetch_from_github(limit=10, query='machine learning'):
    """Fetch repositories από GitHub"""

    headers = {}
    if GITHUB_TOKEN and GITHUB_TOKEN != 'YOUR_GITHUB_TOKEN':
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    params = {
        'q': query if query else 'machine learning',
        'sort': 'stars',
        'order': 'desc',
        'per_page': min(limit, 100)
    }

    response = requests.get(
        'https://api.github.com/search/repositories',
        params=params,
        headers=headers
    )

    if response.status_code != 200:
        print(f"GitHub API error: {response.status_code}")
        return []

    data = response.json()
    records = []

    for repo in data.get('items', [])[:limit]:
        records.append({
            'identifier': f'github:repo:{repo["id"]}',
            'datestamp': repo['created_at'][:10],
            'title': repo['full_name'],
            'creator': repo['owner']['login'],
            'description': repo['description'] or 'No description',
            'url': repo['html_url'],
            'stars': repo['stargazers_count']
        })

    return records

def fetch_from_arxiv(limit=10, query='machine learning'):
    """Fetch papers από arXiv"""

    params = {
        'search_query': f'all:{query}' if query else 'all:machine learning',
        'start': 0,
        'max_results': min(limit, 100),
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }

    response = requests.get(
        'http://export.arxiv.org/api/query',
        params=params
    )

    if response.status_code != 200:
        return []

    # Parse XML response
    root = etree.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    records = []
    for entry in root.findall('atom:entry', ns)[:limit]:
        title = entry.find('atom:title', ns)
        published = entry.find('atom:published', ns)
        summary = entry.find('atom:summary', ns)
        authors = entry.findall('atom:author', ns)
        arxiv_id = entry.find('atom:id', ns)

        # Get author names
        author_names = []
        for author in authors:
            name = author.find('atom:name', ns)
            if name is not None:
                author_names.append(name.text)

        # Extract arXiv ID from URL
        id_text = arxiv_id.text if arxiv_id is not None else ''
        arxiv_num = id_text.split('/abs/')[-1] if '/abs/' in id_text else ''

        records.append({
            'identifier': f'arxiv:{arxiv_num}',
            'datestamp': published.text[:10] if published is not None else '',
            'title': title.text.strip() if title is not None else 'Untitled',
            'creator': '; '.join(author_names) if author_names else 'Unknown',
            'description': summary.text.strip()[:500] if summary is not None else '',
            'url': id_text
        })

    return records

# ============================================================================
# XML CREATION
# ============================================================================

def create_xml_file(record):
    """Create temporary XML file with proper OAI-DC format"""

    # Define namespaces
    NSMAP = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

    # Create root element
    root = etree.Element(
        '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc',
        nsmap=NSMAP
    )

    # Add schemaLocation
    root.set(
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
        'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
    )

    # Add DC elements
    dc_ns = '{http://purl.org/dc/elements/1.1/}'

    if record.get('title'):
        etree.SubElement(root, dc_ns + 'title').text = record['title']

    if record.get('creator'):
        etree.SubElement(root, dc_ns + 'creator').text = record['creator']

    if record.get('description'):
        etree.SubElement(root, dc_ns + 'description').text = record['description']

    if record.get('datestamp'):
        etree.SubElement(root, dc_ns + 'date').text = record['datestamp']

    # Additional fields
    if record.get('doi'):
        etree.SubElement(root, dc_ns + 'identifier').text = f"DOI: {record['doi']}"

    if record.get('url'):
        etree.SubElement(root, dc_ns + 'identifier').text = record['url']

    if record.get('type'):
        etree.SubElement(root, dc_ns + 'type').text = record['type']

    # Create temporary file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    xml_file = os.path.join(TEMP_DIR, f'record_{timestamp}.xml')

    # Write to file
    tree = etree.ElementTree(root)
    tree.write(
        xml_file,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8'
    )

    return xml_file

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("OAI-PMH Bridge Server")
    print("="*60)
    print("\nAvailable sources:")
    for name, config in DATA_SOURCES.items():
        print(f"  - {name}: {config['description']}")
    print("\nEndpoints:")
    print("  - http://localhost:5000/")
    print("  - http://localhost:5000/sources")
    print("  - http://localhost:5000/sync/<source>")
    print("\nExamples:")
    print("  - http://localhost:5000/sync/zenodo?q=covid&limit=5")
    print("  - http://localhost:5000/sync/github?q=python&limit=10")
    print("  - http://localhost:5000/sync/arxiv?q=neural+networks&limit=5")
    print("="*60 + "\n")

    app.run(debug=True, port=5000, host='0.0.0.0')
