import json
from urllib.parse import urljoin, urlparse

import requests
import re
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, ConnectionError, Timeout

from utils.helpers import get_soup  # Assuming this is your utility function

file_path = "db/companies.json"

def url_to_email(url):
    """Constructs a generic 'contact@...' email based on the URL domain."""
    domain = ".".join(urlparse(url).netloc.split(".")[-2:]) 
    return f"contact@{domain}"

def get_company_website(job_info, max_retries=3):
    """Searches Bing for the company's official website with retry logic."""
    company_name = job_info.get("company")
    compagny_ville = job_info.get("ville")
    if not company_name:
        return None

    headers = {'User-Agent': 'Mozilla/5.0'}
    excluded_keywords = ["wikipedia", "bing", "microsoft", "societe.com", "linkedin", "facebook", "twitter", "youtube", "instagram"]
    search_url = f"https://www.bing.com/search?q={company_name}+{ville}"

    retries = 0
    while retries < max_retries:
        try:
            soup = get_soup(search_url, headers=headers)
            if not soup:
                return None

            for result in soup.find_all(class_="b_algo"):
                if company_name.lower() in result.get_text().lower():
                    href = result.find("a").get("href")
                    if href and ("http" in href or "https" in href) and all(exclude not in href for exclude in excluded_keywords):
                        return href
            return None  # No suitable website found
        except (HTTPError, ConnectionError, Timeout):
            retries += 1
    print("Failed to get company website after retries.")
    return None  # Failed after retries

def search_for_email(soup):
    """Finds an email address within HTML content."""
    for link in soup.select("a[href^=mailto]"):
        return link["href"].replace("mailto:", "")

    email_pattern = r"[\w\.-]+@[\w\.-]+"
    match = re.search(email_pattern, soup.text)
    return match.group(0) if match else None

def get_contact_email(website_url, max_retries=3):
    """Gets contact email from website by crawling important pages with retry logic."""
    soup = get_soup(website_url)
    if not soup:
        return None

    email = search_for_email(soup)
    if email:
        return email

    important_pages = ["contact", "about", "impressum", "team", "support", "services", "connect", "info"]
    for page in important_pages:
        retries = 0
        while retries < max_retries:
            try:
                full_url = urljoin(website_url, page)
                soup = get_soup(full_url)
                if soup:
                    email = search_for_email(soup)
                    if email:
                        return email
            except (HTTPError, ConnectionError, Timeout):
                retries += 1
    return None  # No email found after retries

def get_contact_info_and_logo(website):
    """Extracts contact email and logo from the website."""
    soup = get_soup(website)
    if not soup:
        return {"contact_email": None, "logo": None}

    email = get_contact_email(website) or url_to_email(website)
    logo = None

    for img in soup.find_all("img"):
        if "logo" in (img.get("alt", "").lower() or img.get("src", "").lower()):
            logo = img.get("src")
            if logo.startswith("/"):  # Make relative URLs absolute
                logo = urljoin(website, logo)
            break  # Stop after finding the first logo

    return {"contact_email": email, "logo": logo}

def find_company_json(company_name, job_info):
    # Convertir la chaîne JSON en liste Python
    with open(file_path, 'r') as file:
        companies_list = json.load(file)
    
    # Parcourir chaque compagnie dans la liste
    for company in companies_list:
        # Vérifier si le nom de la compagnie correspond
        if company['company'].lower() == company_name.lower():
            # Retourner un dictionnaire avec les informations de contact et le site web
            job_info['contact_email'] = company['contact']
            job_info['website'] = company['website']
            return job_info
    # Si aucune compagnie correspondante n'est trouvée, retourner None
    return None

def add_contact_info_and_logo(job_info):
    website = get_company_website(job_info)
    if website:
        info = get_contact_info_and_logo(website)
        #job_info['contact_email'] = info.get('contact_email')
        #job_info['logo'] = info.get('logo')
    else:
        job_info['contact_email'] = None
        job_info['logo'] = None
    return job_info

def add_contact_info(job_info):
    print(job_info)
    if find_company_json(job_info['company'], job_info):
        return job_info
    website = get_company_website(job_info)
    if website:
        job_info['contact_email'] = get_contact_email(website) or url_to_email(website)
        job_info['website'] = website
    else:
        job_info['contact_email'] = None
        job_info['website'] = None
    return job_info
