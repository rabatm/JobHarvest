import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.helpers import safe_find_and_extract_next2,safe_find_and_extract_next,safe_extract_text_with_wait,safe_extract_text,clean_text, get_detail, get_job_info, waitloading, tryAndRetryClickXpath, tryAndRetryFillByXpath, getinnertextXpath, remove_tags
from utils.text_cleaning import extract_description_from_ld_json
from config.settings import HEADERS
from utils.getinfo_google import find_company_email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

base_url = 'https://www.jobup.ch/fr/emplois/'
job_url_jobup = 'https://www.jobup.ch'

def extract_city_name(text):
    # Supprimer les chiffres et les espaces insécables
    city_name = re.sub(r'\d+\xa0', '', text)
    return city_name

def generate_jobup_url(profession, location='France'):
    query_params = {
        'publication-date': 1,
        'term': profession,
    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url

def extract_city(soup):
    h3_tag = soup.find('h3', string='Lieu de travail :')
    if h3_tag:
        next_span = h3_tag.find_next_sibling('span', class_="Span-sc-1ybanni-0 Text__span-sc-1lu7urs-12 Text-sc-1lu7urs-13 gRaBYW")
        if next_span:
            return next_span.get_text(strip=True)
    return None

def get_jobup_job_details(job_link_scrap, job_info, driver):
    job_link = job_url_jobup + job_link_scrap
    try:
        driver.get(job_link)
        time.sleep(2)  # Considérer l'utilisation de Webdriver wait pour une approche plus robuste
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Utilisation de la fonction safe_extract_text pour extraire les informations de manière sûre
        job_title = safe_extract_text(soup, 'h1[data-cy="vacancy-title"]')
        company_name = safe_extract_text(soup, 'h2.Heading__H2-sc-uhbcp4-1.Text__h2-sc-1lu7urs-1.Span-sc-1ybanni-0.Text__span-sc-1lu7urs-12.Text-sc-1lu7urs-13.eWCVTP')
        contract_type = safe_extract_text(soup, 'span.VacancyInfo___StyledText-sc-1o72fha-1.gRaBYW')
        address_element = soup.select_one('a[data-cy="info-location-link"]')
        address = address_element.get_text(strip=True).split('<span')[0] if address_element else 'Adresse non trouvée'
        address_parts = address.split(',')
        cityDirty = address_parts[-1].strip() if len(address_parts) > 1 else 'Ville non trouvée'
        city = extract_city_name(cityDirty)
        if city == 'Ville non trouvée':
            city = extract_city(soup)
        job_description = safe_extract_text(soup, 'div.Div-sc-1cpunnt-0.ldfVbV')

        # Mise à jour du dictionnaire job_info avec les informations extraites
        job_info.update({
            'job_title': job_title,
            'company': company_name,
            'type': contract_type,
            'ville': city,
            'description': job_description,
            'salary': 'N/A',  # Assurez-vous que cette information est correctement gérée si elle est disponible
        })
        return job_info
    except Exception as e:
        print(f"Error occurred: {e}")
        return job_info

def scrape_jobup_job_details(categorie):
    # Installer le driver Chrome si nécessaire et initialiser le service
    url = generate_jobup_url(categorie)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    jobs_list = []
    try:
        # Accéder à l'URL spécifiée
        driver.get(url)

        # Attendre un moment pour que la page se charge complètement
        time.sleep(2)  # Attente pour que la page soit chargée (ajuster si nécessaire)

        # Extraire le contenu HTML de la page avec BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_info = {}
        job_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/fr/emplois/detail' in href:
                job_links.append(href)
        for job_link in job_links:
            job_info = get_jobup_job_details(job_link, job_info, driver)
            email, website_url = find_company_email(job_info.get('company'), driver)
            if email or email not in ["", None]:
                job_info['email'] = email
                job_info['website'] = website_url
                job_info['categorie'] = categorie
                jobs_list.append(job_info)
        dataframe = pd.DataFrame(jobs_list)
        return dataframe
            
    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Fermer le navigateur à la fin du scraping
        driver.quit()
