import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import dns.resolver # Pour la validation DNS
from utils.helpers import get_soup

def get_company_website(company_name, driver, max_retries=3):
    if not company_name:
        return None
    headers = {'User-Agent': 'Mozilla/5.0'}
    excluded_keywords = ["wikipedia", "bing", "microsoft", "societe.com", "linkedin", "facebook", "twitter", "youtube", "instagram"]
    search_url = f"https://www.bing.com/search?q={company_name}"

    driver.get(search_url)

    retries = 0
    while retries < max_retries:
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            if not soup:
                retries += 1
                continue

            for result in soup.find_all(class_="b_algo"):
                if company_name.lower() in result.get_text().lower():
                    href = result.find("a").get("href")
                    if href and ("http" in href or "https" in href) and all(exclude not in href for exclude in excluded_keywords):
                        return href
            return None  # No suitable website found
        except (HTTPError, ConnectionError, Timeout):
            retries += 1
    return None

def search_google_for_email(company_name, driver, query_terms=["contact", "recrutement"]):
    """Recherche des emails sur Google en utilisant différents termes de recherche."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    for term in query_terms:
        search_url = f"https://www.google.com/search?q={company_name}+email+{term}"
        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        email_pattern = r"[\w\.-]+@[\w\.-]+"
        for result in soup.find_all('div', class_='g'):
            match = re.search(email_pattern, result.text)
            if match and is_valid_email(match.group(0)) and "webmaster" not in match.group(0):
                return match.group(0)
    return None

def search_contact_page_for_email(website_url, driver):
    """Recherche des emails sur la page "Contact" du site web."""
    contact_url = urljoin(website_url, "contact")
    driver.get(contact_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    if soup:
        return search_for_email(soup)
    return None

def search_for_email(soup):
    """Extrait les adresses email d'une soupe BeautifulSoup."""
    email_pattern = r"[\w\.-]+@[\w\.-]+"
    matches = re.findall(email_pattern, soup.text)
    for email in matches:
        if is_valid_email(email):
            return email
    return None

def is_valid_email(email):
    """Vérifie la validité d'une adresse email en utilisant la validation DNS MX."""
    print(f"Validation de l'email {email}...")
    if not email or email in ["", None] :
        return False
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        return True  # MX records found, email is valid
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return False  # No MX records found, email is invalid

def url_to_email(url):
    """Constructs a generic 'contact@...' email based on the URL domain."""
    domain = ".".join(urlparse(url).netloc.split(".")[-2:]) 
    return f"contact@{domain}"

def find_company_email(company_name, driver):
    """Essaie différentes méthodes pour trouver l'email de contact et le site web de l'entreprise."""
    email = None  # Initialisation de l'email à None

    website_url = get_company_website(company_name, driver)
    if not website_url:
        print("Aucun site web trouvé pour", company_name)
        return None, None
    print("Site web trouvé :", website_url)
    if website_url:  # Si un site web a été trouvé
        email_temp = search_contact_page_for_email(website_url, driver)
        if is_valid_email(email_temp):
            email = email_temp
    if not email or email in ["", None] :  # Si aucun email n'a été trouvé sur la page contact
        email_temp = search_google_for_email(company_name, driver)  or url_to_email(website_url)
        print(email)
        print("Email trouvé :", email_temp)
        if is_valid_email(email_temp):
            email = email_temp
    if not email:
        print("Email trouvé :", email)
    return email, website_url

