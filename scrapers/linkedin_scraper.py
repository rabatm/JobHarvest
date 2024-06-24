import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.helpers import clean_text, get_detail, get_job_info, waitloading, tryAndRetryClickXpath, tryAndRetryFillByXpath, getinnertextXpath, remove_tags
from utils.text_cleaning import extract_description_from_ld_json
from config.settings import HEADERS
from utils.getinfo_google import find_company_email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

base_url = 'https://fr.linkedin.com/jobs/linkedin-emplois'

def generate_linkedin_url(profession, location='France'):
    query_params = {
        'keywords': profession,
        'location': "France",
        'geoId': 105015875,
        'f_TPR': 'r86400',

    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url

def get_linkedin_job_details(job_link, job_info, driver):
    try :
        driver.get(job_link)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Safe extraction function
        # Extract job title
        job_title = soup.select_one('h1.top-card-layout__title').text.strip()

        # Extract company name
        company_name = soup.select_one('span.topcard__flavor a.topcard__org-name-link').text.strip()

        # Extract contract type, location, and other details
        contract_type = 'N/A'
        location_element = soup.find('span', class_='topcard__flavor topcard__flavor--bullet')
        location = location_element.text.strip()

        # Extract job description
        job_description = soup.find('div', class_='description__text description__text--rich').text.strip()

        # Create job info dictionary
        job_info = {
            'job_title': job_title,
            'company': company_name,
            'type': contract_type,
            'ville': location,
            'description': job_description,
            'salary': 'N/A',
        }
        return job_info
    except Exception as e:
        print(f"Error occurred: {e}")
        return job_info

def scrape_linkedin_job_details(categorie):
    # Installer le driver Chrome si nécessaire et initialiser le service
    url = generate_linkedin_url(categorie)
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
            if 'fr.linkedin.com/jobs/view' in href:
                job_links.append(href)
        for job_link in job_links:
            job_info = get_linkedin_job_details(job_link, job_info, driver)
            email, website_url = find_company_email(job_info.get('company'), driver)
            if email or email not in ["", None]:
                job_info['email'] = email
                job_info['website'] = website_url
                job_info['categorie'] = categorie
                jobs_list.append(job_info)

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Fermer le navigateur à la fin du scraping
        dataframe = pd.DataFrame(jobs_list)
        return dataframe
        driver.quit()
