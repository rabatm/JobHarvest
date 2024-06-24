import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.helpers import safe_extract, clean_text, get_detail, get_job_info, waitloading, tryAndRetryClickXpath, tryAndRetryFillByXpath, getinnertextXpath, remove_tags
from utils.text_cleaning import extract_description_from_ld_json
from config.settings import HEADERS
from utils.getinfo_google import find_company_email 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

base_url = 'https://candidat.francetravail.fr/offres/recherche'
job_url_pole = 'https://candidat.francetravail.fr'

def generate_pole_url(profession, location='France'):
    query_params = {
        'emission': 1,
        'motsCles': profession
    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url

def safe_extract(selector_func, selector, attr=None, default=None):
    try:
        element = selector_func(selector)
        if element:
            if attr:
                return element.get(attr)
            else:
                return element.text.strip()
    except AttributeError:
        pass
    return default

def get_pole_job_details(job_id, job_info, driver):

    print(f"Scraping job details for {job_url_pole + job_id}")
    job_url = job_url_pole + job_id
    driver.get(job_url)
    time.sleep(5) 
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    job_info = {}
    # Safe extraction for lists with fixed expected lengths
    details = [li.get_text().strip() if hasattr(li, 'get_text') else '' for li in soup.select('ul.details-offer-list > li')]
    if len(details) == 3:
        entreprise, contrat, localisation = details
    else:
        entreprise, contrat, localisation = "Not found", "Not found", "Not found"

    description_element = soup.find("h4", text="Descriptif du poste")
    description = description_element.find_next("p").text if description_element else "Description not found"
    job_info = {
        # Assuming entreprise, contrat, localisation are extracted correctly
        'job_title': safe_extract(soup.select_one, '#labelPopinDetailsOffre span[itemprop="title"]'),
        'company': safe_extract(soup.select_one, 'div.media-body h3.t4.title'),
        'type': safe_extract(soup.select_one, 'dl.icon-group dt:contains("Type de contrat") + dd'),
        'ville': safe_extract(soup.select_one, 'span[itemprop="name"]').split(' - ')[-1] if safe_extract(soup.select_one, 'span[itemprop="name"]') else None,
        "salary": safe_extract(soup.select_one, 'dl.icon-group dd ul li:contains("Salaire brut :")'),
        "start_date": safe_extract(soup.select_one, 'span[itemprop="datePosted"]'),
        "experience": safe_extract(soup.select_one, 'span[itemprop="experienceRequirements"]'),
        "role": safe_extract(soup.select_one, 'span[itemprop="title"]'),
        "status": safe_extract(soup.select_one, 'li:contains("Qualification :")'),
        "travel_zone": None,  # Not present in the provided HTML
        "sector": safe_extract(soup.select_one, 'li:contains("Secteur d\'activité :")'),
        "description": safe_extract(soup.select_one, 'div[itemprop="description"]'),
        "profile": safe_extract(soup.select_one, 'h2.t5.subtitle:contains("Profil souhaité") + div'),
        "skills": {
            "languages": [safe_extract(lang, '.skill-name') for lang in soup.select('.skill-list .skill-competence')],
            "know_how": [safe_extract(skill, '.skill-name') for skill in soup.select('.skill-list .skill-savoir')],
            "knowledge": []  # Not present in the provided HTML
        }
    }
    return job_info

def scrape_pole_job_details(categorie):
    # Installer le driver Chrome si nécessaire et initialiser le service
    url = generate_pole_url(categorie)
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    jobs_list = []
    try:
        # Accéder à l'URL spécifiée
        driver.get(url)

        # Attendre un moment pour que la page se charge complètement
        time.sleep(5)  # Attente pour que la page soit chargée (ajuster si nécessaire)

        # Extraire le contenu HTML de la page avec BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_info = {}
        job_hrefs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'offres/recherche/detail/' in href:
                job_hrefs.append(href)

        for job_href in job_hrefs:
            job_info = get_pole_job_details(job_href, job_info, driver)
            email, website_url = find_company_email(job_info.get('company'), driver)
            if email or email not in ["", None]:
                job_info['email'] = email
                job_info['website'] = website_url
                job_info['categorie'] = categorie
                jobs_list.append(job_info)
            else:
                print(f"No email found for {job_info.get('company')}")
    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Fermer le navigateur à la fin du scraping
        dataframe = pd.DataFrame(jobs_list)
        driver.quit()
        return dataframe
