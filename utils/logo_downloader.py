import os
import requests
import base64
import io
from PIL import Image
from urllib.parse import urlparse, urlunparse
from os import makedirs
from os.path import join, exists, basename

def apec_logo_get(soup):
    """
    Télécharge le logo de l'entreprise à partir de l'objet BeautifulSoup d'une page APEC et le sauvegarde dans le répertoire 'img'.
    
    :param soup: BeautifulSoup object de la page de détail de l'offre d'emploi
    """
    # Trouver l'URL du logo
    figure_element = soup.find('figure')
    if figure_element:
        img_element = figure_element.find('img')
        print(img_element)
        if img_element and 'src' in img_element.attrs:
            img_src = img_element['src']
            # Construire l'URL complète si nécessaire
            if not img_src.startswith('http'):
                img_src = 'https://www.apec.fr/' + img_src
            # Vérifier si le répertoire 'img' existe, sinon le créer
            img_dir = join(os.getcwd(), 'img')
            if not exists(img_dir):
                makedirs(img_dir)
            # Télécharger le logo
            try:
                response = requests.get(img_src)
                print(img_src)
                if response.status_code == 200:
                    # Construire le chemin complet du fichier
                    file_path = join(img_dir, basename(img_src))
                    # Sauvegarder le logo localement
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Logo saved as {file_path}")
                    return basename(img_src)
                else:
                    print("Failed to download the logo.")
            except Exception as e:
                print(f"An error occurred while downloading the logo: {e}")
        else:
            print("Logo source not found")
    else:
        print("Figure element not found")

def download_logo(job_info):
    default_logo_url = "chemin/vers/logo/par_defaut.png"
    logo_url = job_info.get('logo', default_logo_url)

    if not os.path.exists('assets'):
        os.makedirs('assets')

    company_name = job_info.get('company', 'default_company')
    file_path = f"img/{company_name}"

    try:
        if logo_url.startswith('data:image'):
            format, imgstr = logo_url.split(';base64,')
            ext = format.split('/')[-1]

            image_data = base64.b64decode(imgstr)
            image = Image.open(io.BytesIO(image_data))
            image.save(f"{file_path}.png")
            job_info['logo'] = company_name
        else:
            parsed_url = urlparse(logo_url)
            cleaned_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path.lstrip('/'), parsed_url.params, parsed_url.query, parsed_url.fragment))

            if cleaned_url.startswith(('http', 'https')):
                response = requests.get(cleaned_url, stream=True)
                response.raise_for_status()
                with open(f"{file_path}.png", 'wb') as f:
                    f.write(response.content)
                job_info['logo'] = company_name
            else:
                raise ValueError("Invalid URL")
    except Exception as e:
        print(f"Error downloading or saving logo: {e}. Using default logo.")
        job_info['logo'] = "default"
