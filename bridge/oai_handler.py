"""OAI-PMH operations via HTTP API"""
import os
import requests
from datetime import datetime
from lxml import etree
from config import TEMP_DIR, IS_DOCKER

def import_records(records):
    """Import records via HTTP API"""
    
    # CORRECT URL - Use Docker service name
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
            
            # Build URL with correct hostname
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


