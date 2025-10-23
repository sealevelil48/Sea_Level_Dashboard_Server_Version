import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """Fetch IMS warnings from RSS feed"""
    try:
        # Fetch RSS feed
        url = "https://ims.gov.il/sites/default/files/ims_data/rss/alert/rssAlert_general_country_en.xml"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        warnings = []
        for item in root.findall('.//item')[:2]:  # Get up to 2 warnings
            title = item.find('title')
            description = item.find('description')
            pub_date = item.find('pubDate')
            
            if title is not None:
                warning = {
                    'title': title.text.strip(),
                    'description': description.text.strip() if description is not None else '',
                    'pub_date': pub_date.text.strip() if pub_date is not None else '',
                    'severity': get_warning_severity(title.text)
                }
                warnings.append(warning)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "warnings": warnings,
                "last_updated": datetime.now().isoformat(),
                "source": "IMS RSS Feed"
            })
        }
        
    except Exception as e:
        logger.error(f"Error fetching IMS warnings: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e), "warnings": []})
        }

def get_warning_severity(title_text):
    """Determine warning severity from title"""
    title_lower = title_text.lower()
    
    if any(word in title_lower for word in ['red', 'severe', 'extreme']):
        return 'red'
    elif any(word in title_lower for word in ['orange', 'significant']):
        return 'orange'  
    elif any(word in title_lower for word in ['yellow', 'heat', 'danger', 'high']):
        return 'yellow'
    else:
        return 'info'