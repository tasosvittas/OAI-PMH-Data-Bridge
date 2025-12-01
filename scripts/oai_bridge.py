from flask import Flask, jsonify, request, render_template_string
import requests
import subprocess
import os
from datetime import datetime
from lxml import etree

app = Flask(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

OAI_PMH_CLI = 'C:/xampp82/htdocs/oai-pmh2/bin/cli'
TEMP_DIR = 'C:/xampp82/htdocs/oai-pmh2/temp'

# API Tokens (προαιρετικά - βάλε τα δικά σου αν θέλεις)
ZENODO_TOKEN = 'YOUR_ZENODO_TOKEN'
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN'

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

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
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAI-PMH Data Bridge</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        
        .mode-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }
        .mode-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid transparent;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            text-align: center;
        }
        .mode-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .mode-btn:hover:not(.active) {
            border-color: #667eea;
        }
        
        .mode-content { display: none; }
        .mode-content.active { display: block; }
        
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        select, input[type="text"], input[type="number"], textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        select:focus, input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .source-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 14px;
            color: #666;
            display: none;
        }
        .source-info.active { display: block; }
        .example-box {
            background: #e7f3ff;
            padding: 12px;
            border-radius: 6px;
            margin-top: 8px;
            font-size: 13px;
            border-left: 3px solid #2196F3;
        }
        .example-box strong { color: #2196F3; }
        .example-box code {
            background: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:active { transform: translateY(0); }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .results {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .results.active { display: block; }
        .success { color: #28a745; font-weight: 600; }
        .error { color: #dc3545; font-weight: 600; }
        .record-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .record-title { font-weight: 600; color: #333; margin-bottom: 5px; }
        .record-id { font-size: 12px; color: #999; }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading.active { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .oai-link {
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
        }
        .oai-link a {
            color: #2196F3;
            word-break: break-all;
            text-decoration: none;
        }
        .oai-link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 OAI-PMH Data Bridge</h1>
            <p>Εύκολη συλλογή δεδομένων από διάφορες πηγές</p>
        </div>
        
        <div class="content">
            <!-- Mode Selector -->
            <div class="mode-selector">
                <div class="mode-btn active" onclick="switchMode('search')">
                    🔍 Αναζήτηση με Λέξεις-Κλειδιά
                </div>
                <div class="mode-btn" onclick="switchMode('specific')">
                    🎯 Συγκεκριμένο Record
                </div>
            </div>
            
            <!-- SEARCH MODE -->
            <div id="mode-search" class="mode-content active">
                <form id="searchForm">
                    <div class="form-group">
                        <label for="source">📚 Επιλέξτε Πηγή Δεδομένων:</label>
                        <select id="source" name="source" required>
                            <option value="">-- Επιλέξτε --</option>
                            <option value="zenodo">Zenodo - Ερευνητικά Δεδομένα</option>
                            <option value="github">GitHub - Repositories</option>
                            <option value="arxiv">arXiv - Επιστημονικά Papers</option>
                            <option value="jsonplaceholder">JSONPlaceholder - Demo</option>
                        </select>
                        
                        <div id="info-zenodo" class="source-info">
                            <strong>Zenodo:</strong> Ερευνητικά datasets, publications, software. 
                            Παράδειγμα αναζήτησης: "covid", "machine learning", "climate change"
                        </div>
                        <div id="info-github" class="source-info">
                            <strong>GitHub:</strong> Repositories με κώδικα.
                            Παράδειγμα αναζήτησης: "python machine learning", "react components"
                        </div>
                        <div id="info-arxiv" class="source-info">
                            <strong>arXiv:</strong> Preprint επιστημονικά papers.
                            Παράδειγμα αναζήτησης: "neural networks", "quantum computing"
                        </div>
                        <div id="info-jsonplaceholder" class="source-info">
                            <strong>JSONPlaceholder:</strong> Demo δεδομένα για δοκιμή.
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="query">🔍 Λέξεις Αναζήτησης:</label>
                        <input type="text" id="query" name="query" 
                               placeholder="π.χ. covid-19, machine learning, κτλ." 
                               value="machine learning">
                    </div>
                    
                    <div class="form-group">
                        <label for="limit">📊 Πόσα Αποτελέσματα:</label>
                        <input type="number" id="limit" name="limit" 
                               min="1" max="50" value="5">
                    </div>
                    
                    <button type="submit">🚀 Συλλογή Δεδομένων</button>
                </form>
            </div>
            
            <!-- SPECIFIC RECORD MODE -->
            <div id="mode-specific" class="mode-content">
                <form id="specificForm">
                    <div class="form-group">
                        <label for="specific-source">📚 Επιλέξτε Πηγή:</label>
                        <select id="specific-source" name="source" required>
                            <option value="">-- Επιλέξτε --</option>
                            <option value="zenodo">Zenodo</option>
                            <option value="github">GitHub</option>
                            <option value="arxiv">arXiv</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="specific-id">🎯 ID/DOI/URL του Record:</label>
                        <textarea id="specific-id" name="id" required 
                                  placeholder="Βάλτε ένα από τα παρακάτω..."></textarea>
                        
                        <div class="example-box">
                            <strong>Παραδείγματα:</strong><br><br>
                            
                            <strong>Zenodo:</strong><br>
                            • Record ID: <code>8186638</code><br>
                            • DOI: <code>10.5281/zenodo.8186638</code><br>
                            • URL: <code>https://zenodo.org/records/8186638</code><br><br>
                            
                            <strong>GitHub:</strong><br>
                            • Repository: <code>torvalds/linux</code><br>
                            • URL: <code>https://github.com/torvalds/linux</code><br><br>
                            
                            <strong>arXiv:</strong><br>
                            • arXiv ID: <code>2301.07041</code><br>
                            • URL: <code>https://arxiv.org/abs/2301.07041</code>
                        </div>
                    </div>
                    
                    <button type="submit">🎯 Λήψη Συγκεκριμένου Record</button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px;">Συλλογή δεδομένων σε εξέλιξη...</p>
            </div>
            
            <div class="results" id="results"></div>
        </div>
    </div>

    <script>
        const searchForm = document.getElementById('searchForm');
        const specificForm = document.getElementById('specificForm');
        const sourceSelect = document.getElementById('source');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        
        // Switch between modes
        function switchMode(mode) {
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.mode-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById('mode-' + mode).classList.add('active');
            
            // Clear results
            results.classList.remove('active');
        }
        
        // Show/hide source info
        sourceSelect.addEventListener('change', function() {
            document.querySelectorAll('.source-info').forEach(el => {
                el.classList.remove('active');
            });
            if (this.value) {
                document.getElementById('info-' + this.value).classList.add('active');
            }
        });
        
        // Handle search form
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const source = document.getElementById('source').value;
            const query = document.getElementById('query').value;
            const limit = document.getElementById('limit').value;
            
            const url = `/sync/${source}?q=${encodeURIComponent(query)}&limit=${limit}`;
            await fetchData(url);
        });
        
        // Handle specific record form
        specificForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const source = document.getElementById('specific-source').value;
            const id = document.getElementById('specific-id').value.trim();
            
            const url = `/sync/specific/${source}?id=${encodeURIComponent(id)}`;
            await fetchData(url);
        });
        
        async function fetchData(url) {
            loading.classList.add('active');
            results.classList.remove('active');
            
            // Disable buttons
            document.querySelectorAll('button[type="submit"]').forEach(btn => {
                btn.disabled = true;
            });
            
            try {
                const response = await fetch(url);
                const data = await response.json();
                
                loading.classList.remove('active');
                displayResults(data);
                
            } catch (error) {
                loading.classList.remove('active');
                results.innerHTML = `
                    <div class="error">
                        ❌ Σφάλμα: ${error.message}
                    </div>
                `;
                results.classList.add('active');
            } finally {
                // Re-enable buttons
                document.querySelectorAll('button[type="submit"]').forEach(btn => {
                    btn.disabled = false;
                });
            }
        }
        
        function displayResults(data) {
            let html = '';
            
            if (data.status === 'success') {
                html = `
                    <div class="success">
                        ✅ Επιτυχής συλλογή δεδομένων!
                    </div>
                    <p style="margin: 15px 0;">
                        <strong>Σύνολο:</strong> ${data.total_records} records<br>
                        <strong>Επιτυχημένα:</strong> ${data.successful}<br>
                        <strong>Αποτυχίες:</strong> ${data.failed}
                    </p>
                    
                    <div class="oai-link">
                        <strong>🔗 Δείτε τα δεδομένα στο OAI-PMH:</strong><br>
                        <a href="http://localhost/oai-pmh2/public/?verb=ListRecords&metadataPrefix=oai_dc" 
                           target="_blank">
                            http://localhost/oai-pmh2/public/?verb=ListRecords&metadataPrefix=oai_dc
                        </a>
                    </div>
                    
                    <h3 style="margin: 20px 0 10px 0;">📋 Records:</h3>
                `;
                
                data.details.forEach(record => {
                    const statusIcon = record.status === 'success' ? '✅' : '❌';
                    html += `
                        <div class="record-item">
                            <div class="record-title">${statusIcon} ${record.title}</div>
                            <div class="record-id">ID: ${record.identifier}</div>
                            ${record.error ? `<div class="error" style="margin-top: 5px; font-size: 12px;">${record.error}</div>` : ''}
                        </div>
                    `;
                });
            } else {
                html = `
                    <div class="error">
                        ❌ ${data.message}
                    </div>
                `;
            }
            
            results.innerHTML = html;
            results.classList.add('active');
        }
    </script>
</body>
</html>
'''

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Web interface για user-friendly access"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/sources')
def api_sources():
    """API endpoint για τις πηγές"""
    sources = []
    for name, config in DATA_SOURCES.items():
        sources.append({
            'name': name,
            'description': config.get('description', ''),
            'type': config['type']
        })
    return jsonify({'sources': sources})

@app.route('/sync/<source>')
def sync_data(source):
    """Sync data from specified source (search mode)"""
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
                'title': record.get('title', '')[:80] + ('...' if len(record.get('title', '')) > 80 else ''),
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

@app.route('/sync/specific/<source>')
def sync_specific(source):
    """Sync ένα συγκεκριμένο record με ID/DOI/URL"""
    try:
        record_id = request.args.get('id', '')
        
        if not record_id:
            return jsonify({
                'status': 'error',
                'message': 'Δεν δόθηκε ID/DOI/URL'
            }), 400
        
        # Fetch specific record
        data = fetch_specific_record(source, record_id)
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': f'Δεν βρέθηκε record με ID: {record_id}'
            }), 404
        
        # Import to OAI-PMH
        xml_file = create_xml_file(data)
        
        result = subprocess.run([
            'php', OAI_PMH_CLI,
            'oai:add:record',
            data['identifier'],
            'oai_dc',
            xml_file,
            '--no-interaction'
        ], capture_output=True, text=True, cwd='C:/xampp82/htdocs/oai-pmh2')
        
        if os.path.exists(xml_file):
            os.remove(xml_file)
        
        status = 'success' if result.returncode == 0 else 'failed'
        
        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': 1,
            'successful': 1 if status == 'success' else 0,
            'failed': 0 if status == 'success' else 1,
            'timestamp': datetime.now().isoformat(),
            'details': [{
                'identifier': data['identifier'],
                'status': status,
                'title': data.get('title', '')[:80] + ('...' if len(data.get('title', '')) > 80 else ''),
                'error': result.stderr.strip() if result.stderr else None
            }]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'source': source
        }), 500

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
        'size': min(limit, 100),
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
        
        creators = metadata.get('creators', [])
        creator_names = [c.get('name', 'Unknown') for c in creators]
        
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
        
        author_names = []
        for author in authors:
            name = author.find('atom:name', ns)
            if name is not None:
                author_names.append(name.text)
        
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
# SPECIFIC RECORD FETCHING
# ============================================================================

def fetch_specific_record(source, record_id):
    """Fetch ένα συγκεκριμένο record"""
    
    clean_id = parse_record_id(source, record_id)
    
    if source == 'zenodo':
        return fetch_zenodo_by_id(clean_id)
    
    elif source == 'github':
        return fetch_github_by_repo(clean_id)
    
    elif source == 'arxiv':
        return fetch_arxiv_by_id(clean_id)
    
    return None

def parse_record_id(source, record_id):
    """Parse ID από διάφορα formats"""
    
    record_id = record_id.strip()
    
    if source == 'zenodo':
        if 'zenodo.org' in record_id:
            return record_id.split('/')[-1]
        elif '10.5281/zenodo.' in record_id:
            return record_id.split('zenodo.')[-1]
        return record_id
    
    elif source == 'github':
        if 'github.com' in record_id:
            parts = record_id.split('github.com/')[-1].split('/')
            return f"{parts[0]}/{parts[1]}"
        return record_id
    
    elif source == 'arxiv':
        if 'arxiv.org' in record_id:
            return record_id.split('/abs/')[-1]
        return record_id
    
    return record_id

def fetch_zenodo_by_id(record_id):
    """Fetch συγκεκριμένο Zenodo record"""
    
    url = f'https://zenodo.org/api/records/{record_id}'
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    hit = response.json()
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

def fetch_github_by_repo(repo_path):
    """Fetch συγκεκριμένο GitHub repository"""
    
    url = f'https://api.github.com/repos/{repo_path}'
    
    headers = {}
    if GITHUB_TOKEN and GITHUB_TOKEN != 'YOUR_GITHUB_TOKEN':
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    repo = response.json()
    
    return {
        'identifier': f'github:repo:{repo["id"]}',
        'datestamp': repo['created_at'][:10],
        'title': repo['full_name'],
        'creator': repo['owner']['login'],
        'description': repo['description'] or 'No description',
        'url': repo['html_url'],
        'stars': repo['stargazers_count']
    }

def fetch_arxiv_by_id(arxiv_id):
    """Fetch συγκεκριμένο arXiv paper"""
    
    url = f'http://export.arxiv.org/api/query?id_list={arxiv_id}'
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    root = etree.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    entry = root.find('atom:entry', ns)
    if entry is None:
        return None
    
    title = entry.find('atom:title', ns)
    published = entry.find('atom:published', ns)
    summary = entry.find('atom:summary', ns)
    authors = entry.findall('atom:author', ns)
    
    author_names = []
    for author in authors:
        name = author.find('atom:name', ns)
        if name is not None:
            author_names.append(name.text)
    
    return {
        'identifier': f'arxiv:{arxiv_id}',
        'datestamp': published.text[:10] if published is not None else '',
        'title': title.text.strip() if title is not None else 'Untitled',
        'creator': '; '.join(author_names) if author_names else 'Unknown',
        'description': summary.text.strip()[:500] if summary is not None else '',
        'url': f'https://arxiv.org/abs/{arxiv_id}'
    }

# ============================================================================
# XML CREATION
# ============================================================================

def create_xml_file(record):
    """Create temporary XML file with proper OAI-DC format"""
    
    NSMAP = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    root = etree.Element(
        '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc',
        nsmap=NSMAP
    )
    
    root.set(
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
        'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
    )
    
    dc_ns = '{http://purl.org/dc/elements/1.1/}'
    
    if record.get('title'):
        etree.SubElement(root, dc_ns + 'title').text = record['title']
    
    if record.get('creator'):
        etree.SubElement(root, dc_ns + 'creator').text = record['creator']
    
    if record.get('description'):
        etree.SubElement(root, dc_ns + 'description').text = record['description']
    
    if record.get('datestamp'):
        etree.SubElement(root, dc_ns + 'date').text = record['datestamp']
    
    if record.get('doi'):
        etree.SubElement(root, dc_ns + 'identifier').text = f"DOI: {record['doi']}"
    
    if record.get('url'):
        etree.SubElement(root, dc_ns + 'identifier').text = record['url']
    
    if record.get('type'):
        etree.SubElement(root, dc_ns + 'type').text = record['type']
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    xml_file = os.path.join(TEMP_DIR, f'record_{timestamp}.xml')
    
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
    print("\nWeb Interface:")
    print("  http://localhost:5000/")
    print("\nAPI Endpoints:")
    print("  - http://localhost:5000/api/sources")
    print("  - http://localhost:5000/sync/<source>?q=query&limit=N")
    print("  - http://localhost:5000/sync/specific/<source>?id=ID")
    print("\nExamples:")
    print("  - http://localhost:5000/sync/zenodo?q=covid&limit=5")
    print("  - http://localhost:5000/sync/github?q=python&limit=10")
    print("  - http://localhost:5000/sync/specific/zenodo?id=8186638")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
