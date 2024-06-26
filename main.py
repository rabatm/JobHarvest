# -*- coding: utf-8 -*-
import json
import pandas as pd
import os
from scrapers.indeed_scraper import scrape_indeed_job_details, generate_indeed_url
from utils.text_cleaning import clean_title
from utils.getinfo import add_contact_info_and_logo
from scrapers.apec_scraper import scrape_apec_job_details, generate_apec_url
from scrapers.hellowork_scraper import scrape_hellowork_job_details, generate_hellowork_url
from scrapers.linkedin_scraper import scrape_linkedin_job_details, generate_linkedin_url
from scrapers.jobup_scraper import scrape_jobup_job_details, generate_jobup_url
from scrapers.pole_scraper import scrape_pole_job_details
from scrapers.indeed_scraper import scrape_indeed_job_details, generate_indeed_url
import concurrent.futures
import datetime

directory_json = "json"

def fetch_data(title, scraper, source):
    if not os.path.exists(directory_json):
        os.makedirs(directory_json)

    job_data = scraper(title)

    if isinstance(job_data, pd.DataFrame):
        if not job_data.empty:
            today = datetime.date.today().strftime("%Y-%m-%d")
            filename = f"{source}_{clean_title(title)}_{today}.json"
            filename_with_path = os.path.join(directory_json, filename)
            job_data.to_json(filename_with_path, orient='records', lines=True)
            print(f"Les données pour {title} ont été enregistrées dans {filename_with_path}.")
    else:
        print(f"Aucune donnée n'a été récupérée pour {title} {source}.")



# Ensure the 'json' directory exists
if not os.path.exists('json'):
    os.makedirs('json')

with open('db/categorie.json', 'r', encoding='utf-8') as f:
    categories = json.load(f)

for category, subcategories in categories.items():
    for subcategory in subcategories:
        try :
            #fetch_data(subcategory, scrape_hellowork_job_details, 'hello')
            #fetch_data(subcategory, scrape_pole_job_details, 'pole')
            #fetch_data(subcategory, scrape_linkedin_job_details, 'linkedin')
            #fetch_data(subcategory, scrape_jobup_job_details, 'jobup')
            #fetch_data(subcategory, scrape_apec_job_details, 'apec')
            fetch_data(subcategory, scrape_indeed_job_details, 'indeed')
        except Exception as e:
            print(f"Error occurred: {e}")
            continue
        finally:
            print(f"Scraping terminé pour {subcategory}.")

## site a scpper 
# indee ok
# apec ok
# https://www.hellowork.com/fr-fr ok
#https://fr.linkedin.com/jobs/search  ok
# https://www.jobup.ch/fr/emplois/ ok
# https://candidat.pole-emploi.fr/offres/emploi" ok