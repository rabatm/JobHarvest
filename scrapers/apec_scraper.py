import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.helpers import safe_find_and_extract_next,safe_find_and_extract_sibling,safe_find_and_extract,clean_text, get_detail, get_job_info, waitloading, tryAndRetryClickXpath, tryAndRetryFillByXpath, getinnertextXpath, remove_tags
from utils.text_cleaning import extract_description_from_ld_json
from config.settings import HEADERS
from utils.getinfo_google import find_company_email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse

def find_apec_description_after_empty_p(soup, header_text):
    """
    Trouve le texte de description qui suit un <h4> avec un texte spécifique, sautant un <p> vide.

    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup à utiliser pour la recherche.
        header_text (str): Le texte à rechercher dans le <h4>.

    Returns:
        str: Le texte de la description ou "Description non trouvée" si non trouvé.
    """
    header_tag = soup.find('h4', string=header_text)
    if header_tag:
        # Trouver le premier <p> après <h4>
        first_p = header_tag.find_next_sibling('p')
        if first_p:
            # Trouver le deuxième <p> qui contient la description
            second_p = first_p.find_next_sibling('p')
            if second_p:
                return first_p.text.strip()
    return "Description non trouvée"

def generate_apec_url(profession, location='France'):
    base_url = 'https://www.apec.fr/candidat/recherche-emploi.html'
    query_params = {
        'keywords': profession,
        'location': location
    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url


def extract_job_id(url):
    # Expression régulière pour capturer l'identifiant unique qui peut contenir lettres et chiffres
    match = re.search(r'detail-offre/([a-zA-Z0-9]+)[?]', url)
    if match:
        return match.group(1)
    else:
        return None

def get_apec_job_details(job_id, job_info, driver):
    job_url = 'https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/' + job_id
    driver.get(job_url)
    time.sleep(5) 
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Safe extraction function
    def safe_extract(callable, *args, **kwargs):
        try:
            result = callable(*args, **kwargs)
            if result:
                return result.text.strip()
            else:
                return "Not found"
        except AttributeError:
            return "Not found"

    job_info = {}
    # Safe extraction for lists with fixed expected lengths
    details = [li.get_text().strip() if hasattr(li, 'get_text') else '' for li in soup.select('ul.details-offer-list > li')]
    if len(details) == 3:
        entreprise, contrat, localisation = details
    else:
        entreprise, contrat, localisation = "Not found", "Not found", "Not found"
    description = find_apec_description_after_empty_p(soup, "Descriptif du poste")
    header_tag = soup.find('h4', string="Descriptif du poste")
    if header_tag:
        # Trouver le premier <p> après <h4>
        first_p = header_tag.find_next_sibling('p')
        if first_p:
            description = first_p.text.strip()
            # Trouver le deuxième <p> qui contient la description
            second_p = first_p.find_next_sibling('p')
            if second_p:
                profile =  first_p.text.strip()
    salaire_title = soup.find('h4', text='Salaire')
    salaire_span = salaire_title.find_next('span').text
    
    job_info = {
        'job_title': safe_extract(soup.find, 'h1', text=True),
        # Assuming entreprise, contrat, localisation are extracted correctly
        'company': entreprise,
        'type': contrat,
        'ville': localisation,
        "salary": safe_find_and_extract_next(soup, 'h4', next_tag='span', text='Salaire'),
        "start_date": safe_find_and_extract_sibling(soup, ("h4", {"text": "Prise de poste"}), "span"),
        "experience": safe_find_and_extract_next(soup, 'h4', next_tag='span', text='Expérience'),
        "role": safe_find_and_extract_sibling(soup, ("h4", {"text": "Métier"}), "span"),
        "status": safe_find_and_extract_sibling(soup, ("h4", {"text": "Statut du poste"}), "span"),
        "travel_zone": safe_find_and_extract_sibling(soup, ("h4", {"text": "Zone de déplacement"}), "span"),
        "sector": safe_find_and_extract_sibling(soup, ("h4", {"text": "Secteur d’activité du poste"}), "span"),
        "description": description,
        "profile": profile,
        "skills": {
            "languages": [lang.text for lang in soup.select(".added-skills-language .infos_skills p")],
            "know_how": [skill.text for skill in soup.select(".added-skills-manager__knowhow p")],
            "knowledge": [knowledge.text for knowledge in soup.select(".added-skills-manager__knowledge .infos_skills p")]
        }
    }
    return job_info

def scrape_apec_job_details( categorie):
    url = generate_apec_url(categorie)
    # Installer le driver Chrome si nécessaire et initialiser le service
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
        job_ids = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'emploi/detail-offre' in href:
                job_ids.append(extract_job_id(href))

        for job_id in job_ids:
            job_info = get_apec_job_details(job_id, job_info, driver)
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
