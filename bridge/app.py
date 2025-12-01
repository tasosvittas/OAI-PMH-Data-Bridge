"""Flask application for OAI-PMH data bridge"""
from flask import Flask, jsonify, request, render_template
from config import OAI_PMH_BASE_URL
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import config AFTER loading .env
from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, 
    OAI_PMH_CLI, TEMP_DIR
)
from fetchers import fetch_from_source, fetch_specific
from oai_handler import import_records

app = Flask(__name__)


# @app.route('/')
# def index():
#     """Main web interface"""
#     return render_template('index.html')
@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html', oai_base_url=OAI_PMH_BASE_URL)

@app.route('/sync/<source>')
def sync_data(source):
    """Sync data from specified source"""
    try:
        limit = request.args.get('limit', type=int, default=5)
        query = request.args.get('q', '')
        
        # Fetch data from external source
        data = fetch_from_source(source, limit, query)
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': f'Unknown source or no data: {source}'
            }), 404
        
        # Import to OAI-PMH
        results = import_records(data)
        
        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': results['total'],
            'successful': results['successful'],
            'failed': results['failed'],
            'details': results['details']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'source': source
        }), 500


@app.route('/sync/specific/<source>')
def sync_specific_record(source):
    """Sync specific record by ID/DOI/URL"""
    try:
        record_id = request.args.get('id', '')
        
        if not record_id:
            return jsonify({
                'status': 'error',
                'message': 'No ID provided'
            }), 400
        
        # Fetch specific record
        data = fetch_specific(source, record_id)
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': f'Record not found: {record_id}'
            }), 404
        
        # Import to OAI-PMH
        results = import_records([data])
        
        return jsonify({
            'status': 'success',
            'source': source,
            'total_records': 1,
            'successful': results['successful'],
            'failed': results['failed'],
            'details': results['details']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'source': source
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'cli_path': OAI_PMH_CLI,
        'temp_dir': TEMP_DIR
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("OAI-PMH Data Bridge")
    print("="*60)
    print(f"\nCLI Path: {OAI_PMH_CLI}")
    print(f"Temp Dir: {TEMP_DIR}")
    print(f"\nWeb Interface: http://localhost:{FLASK_PORT}/")
    print(f"Health Check: http://localhost:{FLASK_PORT}/health")
    print("="*60 + "\n")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )




# """Flask application for OAI-PMH data bridge"""
# from flask import Flask, jsonify, request, render_template
# from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, OAI_PMH_CLI, TEMP_DIR
# from fetchers import fetch_from_source, fetch_specific
# from oai_handler import import_records

# app = Flask(__name__)


# @app.route('/')
# def index():
#     """Main web interface"""
#     return render_template('index.html')

# # ... existing imports ..


# @app.route('/sync/<source>')
# def sync_data(source):
#     """Sync data from specified source"""
#     try:
#         limit = request.args.get('limit', type=int, default=5)
#         query = request.args.get('q', '')
        
#         # Fetch data from external source
#         data = fetch_from_source(source, limit, query)
        
#         if not data:
#             return jsonify({
#                 'status': 'error',
#                 'message': f'Unknown source or no data: {source}'
#             }), 404
        
#         # Import to OAI-PMH
#         results = import_records(data)
        
#         return jsonify({
#             'status': 'success',
#             'source': source,
#             'total_records': results['total'],
#             'successful': results['successful'],
#             'failed': results['failed'],
#             'details': results['details']
#         })
        
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e),
#             'source': source
#         }), 500


# @app.route('/sync/specific/<source>')
# def sync_specific_record(source):
#     """Sync specific record by ID/DOI/URL"""
#     try:
#         record_id = request.args.get('id', '')
        
#         if not record_id:
#             return jsonify({
#                 'status': 'error',
#                 'message': 'No ID provided'
#             }), 400
        
#         # Fetch specific record
#         data = fetch_specific(source, record_id)
        
#         if not data:
#             return jsonify({
#                 'status': 'error',
#                 'message': f'Record not found: {record_id}'
#             }), 404
        
#         # Import to OAI-PMH
#         results = import_records([data])
        
#         return jsonify({
#             'status': 'success',
#             'source': source,
#             'total_records': 1,
#             'successful': results['successful'],
#             'failed': results['failed'],
#             'details': results['details']
#         })
        
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e),
#             'source': source
#         }), 500


# @app.route('/health')
# def health():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'cli_path': OAI_PMH_CLI,
#         'temp_dir': TEMP_DIR
#     })


# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("OAI-PMH Data Bridge")
#     print("="*60)
#     print(f"\nCLI Path: {OAI_PMH_CLI}")
#     print(f"Temp Dir: {TEMP_DIR}")
#     print(f"\nWeb Interface: http://localhost:{FLASK_PORT}/")
#     print(f"Health Check: http://localhost:{FLASK_PORT}/health")
#     print("="*60 + "\n")
    
#     app.run(
#         host=FLASK_HOST,
#         port=FLASK_PORT,
#         debug=FLASK_DEBUG
#     )
