# """OAI-PMH operations"""
# import os
# import subprocess
# from datetime import datetime
# from lxml import etree
# from config import OAI_PMH_CLI, TEMP_DIR


# def import_records(records):
#     """Import records to OAI-PMH repository"""
#     results = {
#         'total': len(records),
#         'successful': 0,
#         'failed': 0,
#         'details': []
#     }
    
#     for record in records:
#         try:
#             # Create XML file
#             xml_file = create_xml(record)
            
#             # Import via PHP CLI
#             result = subprocess.run([
#                 'php',
#                 OAI_PMH_CLI,
#                 'oai:add:record',
#                 record['identifier'],
#                 'oai_dc',
#                 xml_file,
#                 '--no-interaction'
#             ],
#             capture_output=True,
#             text=True,
#             cwd='C:/xampp82/htdocs/oai-pmh2',
#             timeout=60
#             )
            
#             # Clean up temp file
#             if os.path.exists(xml_file):
#                 os.remove(xml_file)
            
#             # Process result
#             status = 'success' if result.returncode == 0 else 'failed'
            
#             if status == 'success':
#                 results['successful'] += 1
#             else:
#                 results['failed'] += 1
            
#             results['details'].append({
#                 'identifier': record['identifier'],
#                 'status': status,
#                 'title': record.get('title', '')[:80],
#                 'error': result.stderr if result.returncode != 0 else None
#             })
            
#         except Exception as e:
#             results['failed'] += 1
#             results['details'].append({
#                 'identifier': record.get('identifier', 'unknown'),
#                 'status': 'failed',
#                 'title': record.get('title', '')[:80],
#                 'error': str(e)
#             })
    
#     return results


# def create_xml(record):
#     """Create Dublin Core XML file"""
#     NSMAP = {
#         'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
#         'dc': 'http://purl.org/dc/elements/1.1/',
#         'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
#     }
    
#     # Create root element
#     root = etree.Element(
#         '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc',
#         nsmap=NSMAP
#     )
    
#     root.set(
#         '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
#         'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
#     )
    
#     # Add Dublin Core elements
#     dc_ns = '{http://purl.org/dc/elements/1.1/}'
    
#     if record.get('title'):
#         etree.SubElement(root, dc_ns + 'title').text = record['title']
    
#     if record.get('creator'):
#         etree.SubElement(root, dc_ns + 'creator').text = record['creator']
    
#     if record.get('description'):
#         etree.SubElement(root, dc_ns + 'description').text = record['description']
    
#     if record.get('datestamp'):
#         etree.SubElement(root, dc_ns + 'date').text = record['datestamp']
    
#     if record.get('doi'):
#         etree.SubElement(root, dc_ns + 'identifier').text = f"DOI: {record['doi']}"
    
#     if record.get('url'):
#         etree.SubElement(root, dc_ns + 'identifier').text = record['url']
    
#     # Create temporary file
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
#     xml_file = os.path.join(TEMP_DIR, f'record_{timestamp}.xml')
    
#     # Write to file
#     tree = etree.ElementTree(root)
#     tree.write(
#         xml_file,
#         pretty_print=True,
#         xml_declaration=True,
#         encoding='UTF-8'
#     )
    
#     return xml_file
"""OAI-PMH operations via HTTP API"""
import os
import requests
from datetime import datetime
from lxml import etree
from config import TEMP_DIR, IS_DOCKER

def import_records(records):
    """Import records via HTTP API"""
    
    # ✅ CORRECT URL - Use Docker service name
    if IS_DOCKER:
        base_url = 'http://oai-pmh'
    else:
        base_url = 'http://localhost'
    
    results = {
        'total': len(records),
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    for record in records:
        try:
            xml_content = create_xml_string(record)
            
            # ✅ Build URL with correct hostname
            url = base_url + '/import-record.php'
            
            print(f"[OAI] Calling: {url}")
            
            response = requests.post(
                url,
                data={
                    'identifier': record['identifier'],
                    'metadataPrefix': 'oai_dc',
                    'content': xml_content
                },
                timeout=60
            )
            
            if response.status_code == 200:
                results['successful'] += 1
                print(f"[OAI] ✓ Success: {record['identifier']}")
                status = 'success'
                error = None
            else:
                results['failed'] += 1
                print(f"[OAI] ✗ Failed: {record['identifier']}")
                print(f"[OAI] Response: {response.text}")
                status = 'failed'
                error = response.text
            
            results['details'].append({
                'identifier': record['identifier'],
                'status': status,
                'title': record.get('title', '')[:80],
                'error': error
            })
            
        except Exception as e:
            print(f"[OAI] Exception: {str(e)}")
            results['failed'] += 1
            results['details'].append({
                'identifier': record.get('identifier', 'unknown'),
                'status': 'failed',
                'title': record.get('title', '')[:80],
                'error': str(e)
            })
    
    return results


def create_xml_string(record):
    """Create Dublin Core XML as string"""
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
    
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')


