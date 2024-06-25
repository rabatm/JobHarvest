import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.helpers import safe_find_next,safe_find_and_extract, safe_extract,clean_text, get_detail, get_job_info, waitloading, tryAndRetryClickXpath, tryAndRetryFillByXpath, getinnertextXpath, remove_tags
from utils.text_cleaning import extract_description_from_ld_json
from config.settings import HEADERS
from utils.getinfo_google import find_company_email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

base_url = 'https://www.hellowork.com/fr-fr/emploi/recherche.html'
job_url_hello = 'https://www.hellowork.com/fr-fr/emplois/'

def generate_hellowork_url(profession, location='France'):
    query_params = {
        'k': profession,
        'd': 'h'
    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url


def extract_hellowork_job_id(url):
    # Expression régulière pour capturer l'identifiant après "idOffre="
    match = re.search(r'/emplois/(\d+)\.html', url)
    if match:
        return match.group(1)
    else:
        return None

def get_hellowork_job_details(job_id, job_info, driver):
    try :
        job_url = job_url_hello + job_id + '.html'
        driver.get(job_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Safe extraction function
        # Extract job title
        job_title = soup.select_one('h1 span.tw-block').text.strip()

        # Extract company name
        company_name = soup.select_one('div.tw-inline-flex a').text.strip()

        # Extract contract type, location, and other details
        details = soup.select('ul.tw-flex.tw-flex-wrap.tw-gap-3 li.tw-tag-contract-s.tw-readonly')
        location = details[0].text.strip()
        contract_type = details[1].text.strip()

        # Extract job description
        job_description = soup.select_one('section p.tw-typo-long-m')
        if job_description:
           job_description = str(job_description)

        # Create job info dictionary
        job_info = {
            'job_title': job_title,
            'company': company_name,
            'type':contract_type,
            'ville': location,
            'description': job_description,
            'salary': safe_extract(soup.find, "span", {"property": "product:price:amount"}, default="$0"),
            'start_date': safe_extract(soup.find, "span", {"property": "validThrough"}, default="Now"),
            'experience': safe_extract(soup.find, "dd", {"class": "item experienceLevel"}),
            'role': safe_extract(soup.find, "dd", {"class": "item mainFunction"}),
            'status': safe_extract(soup.find, "dd", {"class": "item employmentType"}),
            'travel_zone': safe_extract(soup.find, "dd", {"class": "item travelScope"}),
            'sector': safe_extract(soup.find, "dd", {"class": "item businessArea"}),
            'profile': safe_find_and_extract(soup, ("h4", {"text": "Profil recherché"}), "p"),
            'skills': {
                'languages': [],
                'know_how': [],
                'knowledge': []
            }
        }
        return job_info
    except Exception as e:
        print(f"Error occurred: {e}")
        return job_info

def scrape_hellowork_job_details(categorie):
    # Installer le driver Chrome si nécessaire et initialiser le service
    url = generate_hellowork_url(categorie)

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
        job_ids = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'fr-fr/emplois' in href:
                job_ids.append(extract_hellowork_job_id(href))
        for job_id in job_ids:
            job_info = get_hellowork_job_details(job_id, job_info, driver)
            email, website_url = find_company_email(job_info.get('company'), driver)
            if email or email not in ["", None]:
                job_info['email'] = email
                job_info['website'] = website_url
                job_info['categorie'] = categorie
                jobs_list.append(job_info)
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        dataframe = pd.DataFrame(jobs_list)
        driver.quit()
        return dataframe
