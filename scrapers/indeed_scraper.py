import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
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
import undetected_chromedriver as uc 
import time
import urllib.parse

def extraire_indee_ville(text):
    # Regex ajustée pour ignorer les chiffres et l'espace au début
    match = re.search(r"^\d*\s*(.*?)(?: \(\d+\)|$)", text)
    if match:
        return match.group(1)
    else:
        return None

def find_indeed_description_title(soup, phrase):
    try:
        return soup.find('h2', string=lambda text: text and phrase in text)
    except Exception as e:
        print(f"Error finding description title: {e}")
        return None

def find_indeed_description_div(description_title):
    try:
        return description_title.find_next('div', {'class': 'jobsearch-jobDescriptionText'})
    except Exception as e:
        print(f"Error finding description div: {e}")
        return None

def get_indeed_content_after_phrase(soup, phrase):
    description_title = find_indeed_description_title(soup, phrase)
    if description_title is None:
        return None
    description_div = find_indeed_description_div(description_title)
    if description_div is None:
        return None
    return description_div.get_text().strip()

def get_indeed_job_details(job_url, job_info, driver):
    if not job_url.startswith('http'):
        job_url = 'https://fr.indeed.com' + job_url
    driver.get(job_url)
    time.sleep(5) 
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    #job_info['description'] = extract_description_from_ld_json(job_resp.content)
    job_info['salary'] = get_detail(soup, 'salary-snippet-container', 'salary')
    job_info['type'] = get_detail(soup, 'jobsearch-JobInfoHeader-subtitle', 'type', 1)
    job_description_div = soup.find(id="jobDescriptionText")
    
    if job_description_div:
        job_description_html = str(job_description_div)
        job_info['description'] = str(job_description_div)
    return job_info

def scrape_indeed_job_details(categorie):
    url = generate_indeed_url(categorie)
    options = uc.ChromeOptions() 
    options.headless = False 
    driver = uc.Chrome(use_subprocess=True, options=options)
    driver.get(url)
    driver.maximize_window() 
    time.sleep(2) 
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    jobs_list = []
    for post in soup.select('.job_seen_beacon'):
        job_info = {}
        try:
            job_info['categorie'] = categorie
            job_link_tag = post.select_one('a[id^="sj_"]')
            job_link = job_link_tag['href'] if job_link_tag else None
            
            job_info['company'] = get_job_info(post, '[data-testid="company-name"]', 'company')
            email, website_url = find_company_email(job_info.get('company'), driver)
            if email or email not in ["", None]:
                job_info['email'] = email
                job_info['website'] = website_url
            else:
                continue
            job_info = get_indeed_job_details(job_link, job_info, driver)
            company = post.select_one('[data-testid="company-name"]')
            if not company:
                continue
            job_info['job_title'] = get_job_info(post, '.jobTitle span', 'job_title')
            job_info['company'] = get_job_info(post, '[data-testid="company-name"]', 'company')
            job_info['ville'] = extraire_indee_ville(get_job_info(post, '[data-testid="text-location"]', 'location'))
            time.sleep(50)
            job_info['date'] = get_job_info(post, '[data-testid="myJobsStateDate"]', 'date')
            job_info['job_link'] = job_link.replace("\n", " ") if job_link else None
            jobs_list.append(job_info)
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            # Fermer le navigateur à la fin du scraping
            dataframe = pd.DataFrame(jobs_list)
            driver.quit()
            return dataframe

def generate_indeed_url(job_title, location='France'):
    base_url = 'https://fr.indeed.com/jobs'
    query_params = {
        'q': job_title,
        'l': location,
        'from': 'searchOnHP'
    }
    url = base_url + '?' + urllib.parse.urlencode(query_params)
    return url
