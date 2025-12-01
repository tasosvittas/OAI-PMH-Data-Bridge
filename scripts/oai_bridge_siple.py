from flask import Flask, jsonify, request, render_template_string
import requests
import subprocess
import os
from datetime import datetime
from lxml import etree

# ============================================================================
# CONFIGURATION - ΑΛΛΑΞΕ ΜΟΝΟ ΑΥΤΟ
# ============================================================================

OAI_PMH_CLI = 'C:/xampp82/htdocs/oai-pmh2/bin/cli'  # ← ΤΟ ΜΟΝΟ ΠΟΥ ΠΡΕΠΕΙ ΝΑ ΑΛΛΑΞΕΙΣ
TEMP_DIR = 'C:/xampp82/htdocs/oai-pmh2/temp'

# API Tokens (προαιρετικά)
ZENODO_TOKEN = ''
GITHUB_TOKEN = ''

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)

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
        .mode-btn:hover:not(.active) { border-color: #667eea; }
        
        .mode-content { display: none; }
        .mode-content.active { display: block; }
        
        .form-group { margin-bottom: 25px; }
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
        textarea { min-height: 100px; resize: vertical; }
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
        .oai-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 OAI-PMH Data Bridge</h1>
            <p>Εύκολη συλλογή δεδομένων από διάφορες πηγές</p>
        </div>
        
        <div class="content">
            <div class="mode-selector">
                <div class="mode-btn active" onclick="switchMode('search')">
                    🔍 Αναζήτηση
                </div>
                <div class="mode-btn" onclick="switchMode('specific')">
                    🎯 Συγκεκριμένο Record
                </div>
            </div>
            
            <!-- SEARCH MODE -->
            <div id="mode-search" class="mode-content active">
                <form id="searchForm">
                    <div class="form-group">
                        <label for="source">📚 Πηγή:</label>
                        <select id="source" name="source" required>
                            <option value="">-- Επιλέξτε --</option>
                            <option value="zenodo">Zenodo</option>
                            <option value="github">GitHub</option>
                            <option value="arxiv">arXiv</option>
                            <option value="jsonplaceholder">Demo</option>
                        </select>
                        
                        <div id="info-zenodo" class="source-info">
                            <strong>Zenodo:</strong> Ερευνητικά datasets
                        </div>
                        <div id="info-github" class="source-info">
                            <strong>GitHub:</strong> Repositories
                        </div>
                        <div id="info-arxiv" class="source-info">
                            <strong>arXiv:</strong> Papers
                        </div>
                        <div id="info-jsonplaceholder" class="source-info">
                            <strong>Demo:</strong> Test data
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="query">🔍 Αναζήτηση:</label>
                        <input type="text" id="query" name="query" 
                               placeholder="π.χ. covid-19" 
                               value="machine learning">
                    </div>
                    
                    <div class="form-group">
                        <label for="limit">📊 Αριθμός:</label>
                        <input type="number" id="limit" name="limit" 
                               min="1" max="50" value="5">
                    </div>
                    
                    <button type="submit">🚀 Συλλογή</button>
                </form>
            </div>
            
            <!-- SPECIFIC MODE -->
            <div id="mode-specific" class="mode-content">
                <form id="specificForm">
                    <div class="form-group">
                        <label for="specific-source">📚 Πηγή:</label>
                        <select id="specific-source" required>
                            <option value="">-- Επιλέξτε --</option>
                            <option value="zenodo">Zenodo</option>
                            <option value="github">GitHub</option>
                            <option value="arxiv">arXiv</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="specific-id">🎯 ID/DOI/URL:</label>
                        <textarea id="specific-id" required></textarea>
                        
                        <div class="example-box">
                            <strong>Zenodo:</strong> <code>8186638</code> ή <code>10.5281/zenodo.8186638</code><br>
                            <strong>GitHub:</strong> <code>torvalds/linux</code><br>
                            <strong>arXiv:</strong> <code>2301.07041</code>
                        </div>
                    </div>
                    
                    <button type="submit">🎯 Λήψη</button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px;">Συλλογή...</p>
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
        
        function switchMode(mode) {
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.mode-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('mode-' + mode).classList.add('active');
            results.classList.remove('active');
        }
        
        sourceSelect.addEventListener('change', function() {
            document.querySelectorAll('.source-info').forEach(el => el.classList.remove('active'));
            if (this.value) {
                document.getElementById('info-' + this.value).classList.add('active');
            }
        });
        
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const source = document.getElementById('source').value;
            const query = document.getElementById('query').value;
            const limit = document.getElementById('limit').value;
            const url = `/sync/${source}?q=${encodeURIComponent(query)}&limit=${limit}`;
            await fetchData(url);
        });
        
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
            
            try {
                const response = await fetch(url);
                const data = await response.json();
                loading.classList.remove('active');
                displayResults(data);
            } catch (error) {
                loading.classList.remove('active');
                results.innerHTML = `<div class="error">❌ Σφάλμα: ${error.message}</div>`;
                results.classList.add('active');
            }
        }
        
        function displayResults(data) {
            let html = '';
            
            if (data.status === 'success') {
                html = `
                    <div class="success">✅ Επιτυχία!</div>
                    <p style="margin: 15px 0;">
                        <strong>Σύνολο:</strong> ${data.total_records}<br>
                        <strong>Επιτυχημένα:</strong> ${data.successful}<br>
                        <strong>Αποτυχίες:</strong> ${data.failed}
                    </p>
                    <div class="oai-link">
                        <strong>🔗 OAI-PMH:</strong><br>
                        <a href="http://localhost/oai-pmh2/public/?verb=ListRecords&metadataPrefix=oai_dc" target="_blank">
                            Δείτε τα records
                        </a>
                    </div>
                    <h3 style="margin: 20px 0 10px 0;">📋 Records:</h3>
                `;
                
                data.details.forEach(record => {
                    const icon = record.status === 'success' ? '✅' : '❌';
                    html += `
                        <div class="record-item">
                            <div class="record-title">${icon} ${record.title}</div>
                            <div class="record-id">ID: ${record.identifier}</div>
                        </div>
                    `;
                });
            } else {
                html = `<div class="error">❌ ${data.message}</div>`;
            }
            
            results.innerHTML = html;
            results.classList.add('active');
        }
    </script>
</body>
</html>
'''

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/sync/<source>')
def sync_data(source):
    try:
        limit = request.args.get('limit', type=int, default=5)
        query = request.args.get('q', '')
        
        data = fetch_from_source(source, limit, query)
        
        if not data:
            return jsonify({'status': 'error', 'message': f'Unknown source: {source}'}), 404
        
        results = import_to_oai(data)
        
        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': results['total'],
            'successful': results['successful'],
            'failed': results['failed'],
            'details': results['details']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sync/specific/<source>')
def sync_specific(source):
    try:
        record_id = request.args.get('id', '')
        if not record_id:
            return jsonify({'status': 'error', 'message': 'No ID provided'}), 400
        
        data = fetch_specific(source, record_id)
        if not data:
            return jsonify({'status': 'error', 'message': 'Record not found'}), 404
        
        results = import_to_oai([data])
        
        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': 1,
            'successful': results['successful'],
            'failed': results['failed'],
            'details': results['details']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_from_source(source, limit, query):
    if source == 'zenodo':
        return fetch_zenodo(limit, query)
    elif source == 'github':
        return fetch_github(limit, query)
    elif source == 'arxiv':
        return fetch_arxiv(limit, query)
    elif source == 'jsonplaceholder':
        return fetch_jsonplaceholder(limit)
    return None

def fetch_zenodo(limit, query):
    params = {'q': query or 'open science', 'size': min(limit, 100), 'sort': 'mostrecent'}
    headers = {}
    if ZENODO_TOKEN:
        headers['Authorization'] = f'Bearer {ZENODO_TOKEN}'
    
    try:
        response = requests.get('https://zenodo.org/api/records', params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        records = []
        for hit in data.get('hits', {}).get('hits', [])[:limit]:
            metadata = hit.get('metadata', {})
            creators = metadata.get('creators', [])
            creator_names = [c.get('name', 'Unknown') for c in creators]
            description = metadata.get('description', 'No description')[:500]
            
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
    except:
        return []

def fetch_github(limit, query):
    params = {'q': query or 'machine learning', 'sort': 'stars', 'per_page': min(limit, 100)}
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        response = requests.get('https://api.github.com/search/repositories', params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        records = []
        for repo in data.get('items', [])[:limit]:
            records.append({
                'identifier': f'github:repo:{repo["id"]}',
                'datestamp': repo['created_at'][:10],
                'title': repo['full_name'],
                'creator': repo['owner']['login'],
                'description': repo['description'] or 'No description',
                'url': repo['html_url']
            })
        return records
    except:
        return []

def fetch_arxiv(limit, query):
    params = {
        'search_query': f'all:{query}' if query else 'all:machine learning',
        'start': 0,
        'max_results': min(limit, 100)
    }
    
    try:
        response = requests.get('http://export.arxiv.org/api/query', params=params, timeout=30)
        response.raise_for_status()
        
        root = etree.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        records = []
        for entry in root.findall('atom:entry', ns)[:limit]:
            title = entry.find('atom:title', ns)
            published = entry.find('atom:published', ns)
            summary = entry.find('atom:summary', ns)
            authors = entry.findall('atom:author', ns)
            arxiv_id = entry.find('atom:id', ns)
            
            author_names = [author.find('atom:name', ns).text for author in authors if author.find('atom:name', ns) is not None]
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
    except:
        return []

def fetch_jsonplaceholder(limit):
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/posts', timeout=30)
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
    except:
        return []

def fetch_specific(source, record_id):
    record_id = record_id.strip()
    
    if source == 'zenodo':
        if 'zenodo.org' in record_id:
            record_id = record_id.split('/')[-1]
        elif '10.5281/zenodo.' in record_id:
            record_id = record_id.split('zenodo.')[-1]
        
        try:
            response = requests.get(f'https://zenodo.org/api/records/{record_id}', timeout=30)
            response.raise_for_status()
            hit = response.json()
            metadata = hit.get('metadata', {})
            creators = metadata.get('creators', [])
            creator_names = [c.get('name', 'Unknown') for c in creators]
            
            return {
                'identifier': f'zenodo:{hit.get("id")}',
                'datestamp': metadata.get('publication_date', datetime.now().strftime('%Y-%m-%d')),
                'title': metadata.get('title', 'Untitled'),
                'creator': '; '.join(creator_names),
                'description': metadata.get('description', '')[:500],
                'doi': hit.get('doi', ''),
                'url': hit.get('links', {}).get('self_html', '')
            }
        except:
            return None
    
    elif source == 'github':
        if 'github.com' in record_id:
            parts = record_id.split('github.com/')[-1].split('/')
            record_id = f"{parts[0]}/{parts[1]}"
        
        try:
            response = requests.get(f'https://api.github.com/repos/{record_id}', timeout=30)
            response.raise_for_status()
            repo = response.json()
            
            return {
                'identifier': f'github:repo:{repo["id"]}',
                'datestamp': repo['created_at'][:10],
                'title': repo['full_name'],
                'creator': repo['owner']['login'],
                'description': repo['description'] or 'No description',
                'url': repo['html_url']
            }
        except:
            return None
    
    elif source == 'arxiv':
        if 'arxiv.org' in record_id:
            record_id = record_id.split('/abs/')[-1]
        
        try:
            response = requests.get(f'http://export.arxiv.org/api/query?id_list={record_id}', timeout=30)
            response.raise_for_status()
            
            root = etree.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            
            if entry is None:
                return None
            
            title = entry.find('atom:title', ns)
            published = entry.find('atom:published', ns)
            summary = entry.find('atom:summary', ns)
            authors = entry.findall('atom:author', ns)
            
            author_names = [author.find('atom:name', ns).text for author in authors if author.find('atom:name', ns) is not None]
            
            return {
                'identifier': f'arxiv:{record_id}',
                'datestamp': published.text[:10] if published is not None else '',
                'title': title.text.strip() if title is not None else 'Untitled',
                'creator': '; '.join(author_names),
                'description': summary.text.strip()[:500] if summary is not None else '',
                'url': f'https://arxiv.org/abs/{record_id}'
            }
        except:
            return None
    
    return None

# ============================================================================
# OAI-PMH IMPORT
# ============================================================================

def import_to_oai(records):
    results = {'total': len(records), 'successful': 0, 'failed': 0, 'details': []}
    
    for record in records:
        try:
            xml_file = create_xml(record)
            
            result = subprocess.run([
                'php', OAI_PMH_CLI,
                'oai:add:record',
                record['identifier'],
                'oai_dc',
                xml_file,
                '--no-interaction'
            ], capture_output=True, text=True, cwd='C:/xampp82/htdocs/oai-pmh2', timeout=60)
            
            if os.path.exists(xml_file):
                os.remove(xml_file)
            
            status = 'success' if result.returncode == 0 else 'failed'
            if status == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'identifier': record['identifier'],
                'status': status,
                'title': record.get('title', '')[:80],
                'error': result.stderr if result.returncode != 0 else None
            })
        except Exception as e:
            results['failed'] += 1
            results['details'].append({
                'identifier': record.get('identifier', 'unknown'),
                'status': 'failed',
                'title': record.get('title', '')[:80],
                'error': str(e)
            })
    
    return results

def create_xml(record):
    NSMAP = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    root = etree.Element('{http://www.openarchives.org/OAI/2.0/oai_dc/}dc', nsmap=NSMAP)
    root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
             'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd')
    
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
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    xml_file = os.path.join(TEMP_DIR, f'record_{timestamp}.xml')
    
    tree = etree.ElementTree(root)
    tree.write(xml_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    return xml_file

# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 OAI-PMH Data Bridge")
    print("="*60)
    print(f"\n✓ CLI Path: {OAI_PMH_CLI}")
    print(f"✓ Temp Dir: {TEMP_DIR}")
    print(f"\n🌐 Web: http://localhost:5000/")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
