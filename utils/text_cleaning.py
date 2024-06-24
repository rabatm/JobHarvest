import json
from bs4 import BeautifulSoup
import re

def extract_description_from_ld_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', type='application/ld+json')
    if script_tag:
        json_data = json.loads(script_tag.string)
        if 'description' in json_data:
            description_html = json_data['description']
            description_soup = BeautifulSoup(description_html, 'html.parser')
            description_text = description_soup.get_text()
            return description_text
    return None

def clean_title(title):
# Remplacer tous les caractères non alphanumériques par des espaces
    cleaned_title = re.sub(r'\W+', '', title)
    return cleaned_title