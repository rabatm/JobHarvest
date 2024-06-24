from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
import re
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def clean_text(text):
    replacements = {
        '√©': 'é',
        '√®': 'è',
        '√¥': 'à',
        '√¢': 'â',
        '√ª': 'ê',
        '√´': 'ô',
        '√∫': 'ù',
        '√ç': 'ç',
        '‚Äô': "'",
        '‚Äî': "—",
        '‚Ä¶': "…",
        '√¨': 'è'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def get_detail(soup, selector, attribute, index=None):
    element = soup.find('div', class_=selector)
    if element and index is not None:
        element = element.find_all('div')[index]
    if element:
        text = element.get_text().strip()
        return text.replace("\n", " ") if text else "N/A"
    else:
        return "N/A"

def get_job_info(post, selector, attribute):
    element = post.select_one(selector)
    if element:
        text = clean_text(element.get_text().strip())
        return text.replace("\n", " ") if text else "N/A"
    else:
        return "N/A"

def get_soup(url, headers=None, retries=3):
    session = requests.Session()
    print(f"Requesting {url}")
    for _ in range(retries):
        try:
            resp = session.get(url, headers=headers)
            resp.raise_for_status()  # Raises an exception if the status is 4xx or 5xx
            return BeautifulSoup(resp.content, 'html.parser')
        except HTTPError as e:
            print(f"HTTPError occurred: {e.response.status_code} - {e.response.reason}")
        except ConnectionError:
            print("ConnectionError occurred")
        except Timeout:
            print("Timeout occurred")
    return None

def waitloading(driver, timeout=10):
    """Wait for a page to finish loading within a given timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except TimeoutException:
        print("Page load timed out but continuing with the script.")

def tryAndRetryClickXpath(driver, xPath):
    try : 
        waitBeforeClickOnXpath(driver, xPath)
    except NoSuchElementException:
        print("the element needs to be charged:           "+str(xPath))
        time.sleep(10)
        waitBeforeClickOnXpath(driver, xPath)

def tryAndRetryFillByXpath(driver, xpath, value):
    try:
        fillByXpath(driver, xpath, value)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(5)
        tryAndRetryFillByXpath(driver, xpath, value)

def getinnertextXpath(driver, xPath):
    try:
        result = ""
        result = driver.find_element(By.XPATH, xPath)
        result = (result.get_attribute('innerText'))
    except NoSuchElementException:  #spelling error making this code not work as expected
        result = " "
        pass
    if result == " ":
        time.sleep(2)
        try:
            result = ""
            result = driver.find_element(By.XPATH, xPath)
            result = (result.get_attribute('innerText'))
        except NoSuchElementException:  #spelling error making this code not work as expected
            result = " "
            pass
    return str(result)

TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(description):
    return TAG_RE.sub(' ', description)

def safe_extract(callable, *args, **kwargs):
    try:
        result = callable(*args, **kwargs)
        if result:
            return result.text.strip()
        else:
            return "Not found"
    except AttributeError:
        return "Not found"

def safe_find_next(element, tag):
    """Tente de trouver le prochain élément spécifié à partir d'un élément BeautifulSoup donné.
    
    Args:
        element: L'élément BeautifulSoup à partir duquel effectuer la recherche.
        tag: Le nom de la balise à rechercher.
    
    Returns:
        Le prochain élément trouvé, ou None si l'élément initial est None ou si aucun élément suivant n'est trouvé.
    """
    if element is not None:
        return element.find_next(tag)
    return None

def safe_find_and_extract(soup, initial_selector, next_tag, default_text="N/A"):
    """
    Trouve un élément dans le document BeautifulSoup, navigue au prochain élément spécifié,
    et extrait le texte de manière sûre.

    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup à utiliser pour la recherche.
        initial_selector (str or tuple): Le sélecteur pour trouver le tag initial. Peut être une chaîne pour 'find'
                                         ou un tuple pour 'find' avec des attributs (tag, {"attribute": "value"}).
        next_tag (str): Le nom du tag à trouver ensuite avec find_next.
        default_text (str, optional): Le texte par défaut si l'élément n'est pas trouvé. Defaults to "Not provided".

    Returns:
        str: Le texte extrait de l'élément trouvé ou le texte par défaut.
    """
    # Trouver le tag initial en fonction du type de sélecteur fourni
    if isinstance(initial_selector, tuple):
        initial_tag = soup.find(*initial_selector)
    else:
        initial_tag = soup.find(initial_selector)

    # Utiliser find_next pour trouver le tag suivant, si le tag initial est trouvé
    next_tag_found = initial_tag.find_next(next_tag) if initial_tag else None

    # Extraire et retourner le texte, ou retourner le texte par défaut
    return next_tag_found.text.strip() if next_tag_found else default_text

def safe_find_and_extract_sibling(soup, initial_selector, next_tag, default_text="N/A"):
    """
    Trouve un élément dans le document BeautifulSoup, navigue au prochain élément frère spécifié,
    et extrait le texte de manière sûre.

    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup à utiliser pour la recherche.
        initial_selector (str or tuple): Le sélecteur pour trouver le tag initial. Peut être une chaîne pour 'find'
                                         ou un tuple pour 'find' avec des attributs (tag, {"attribute": "value"}).
        next_tag (str): Le nom du tag frère à trouver ensuite avec find_next_sibling.
        default_text (str, optional): Le texte par défaut si l'élément n'est pas trouvé. Defaults to "Not provided".

    Returns:
        str: Le texte extrait de l'élément trouvé ou le texte par défaut.
    """
    # Trouver le tag initial en fonction du type de sélecteur fourni
    if isinstance(initial_selector, tuple):
        initial_tag = soup.find(*initial_selector)
    else:
        initial_tag = soup.find(initial_selector)

    # Utiliser find_next_sibling pour trouver le tag frère suivant, si le tag initial est trouvé
    next_sibling_found = initial_tag.find_next_sibling(next_tag) if initial_tag else None

    # Extraire et retourner le texte, ou retourner le texte par défaut
    return next_sibling_found.text.strip() if next_sibling_found else default_text

def safe_find_and_extract_next(soup, tag_name, next_tag='span', default_text="N/A", **kwargs):
    """
    Trouve un élément dans le document BeautifulSoup en utilisant un nom de tag et des attributs optionnels,
    puis extrait le texte du prochain élément spécifié.
    """
    # Trouver le tag initial en utilisant le nom du tag et les attributs de recherche fournis via kwargs
    initial_tag = soup.find(tag_name, **kwargs)
    
    # Si le tag initial est trouvé, chercher le tag suivant dans le même parent
    if initial_tag:
        parent = initial_tag.parent
        next_tag_found = parent.find(next_tag)
        
        # Extraire et retourner le texte, ou retourner le texte par défaut
        return next_tag_found.text.strip() if next_tag_found else default_text
    else:
        return default_text

def safe_extract_text(soup, selector, attribute=None):
    """
    Tente de trouver un élément avec un sélecteur CSS donné et extrait son texte.
    Si l'élément n'est pas trouvé, retourne 'N/A'.
    Si un attribut est spécifié, retourne la valeur de cet attribut au lieu du texte.
    """
    element = soup.select_one(selector)
    if element:
        return element.get(attribute).strip() if attribute else element.text.strip()
    return 'N/A'

def safe_extract_text_with_wait(driver, css_selector, wait_time=10):
    """
    Attend que l'élément soit visible et extrait son texte.
    Si l'élément n'est pas trouvé ou n'est pas visible dans le délai imparti, retourne 'N/A'.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element.text.strip()
    except:
        return 'N/A'
    
def safe_find_and_extract_next2(soup, parent_tag_name, tag_name, next_tag='span', default_text="N/A", **kwargs):
    """
    Trouve un élément dans le document BeautifulSoup en utilisant un nom de tag et des attributs optionnels,
    navigue au prochain élément spécifié, et extrait le texte de manière sûre.

    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup à utiliser pour la recherche.
        parent_tag_name (str): Le nom du parent tag à trouver.
        tag_name (str): Le nom du tag à trouver.
        next_tag (str, optional): Le nom du tag à trouver ensuite avec find_next. Defaults to 'span'.
        default_text (str, optional): Le texte par défaut si l'élément n'est pas trouvé. Defaults to "N/A".
        **kwargs: Arguments clés-valeurs supplémentaires pour la recherche, comme 'text' ou {'class': 'my-class'}.

    Returns:
        str: Le texte extrait de l'élément trouvé ou le texte par défaut.
    """
    # Trouver le parent tag initial en utilisant le nom du tag et les attributs de recherche fournis via kwargs
    parent_tag = soup.find(parent_tag_name, **kwargs)

    if parent_tag:
        # Chercher le tag enfant dans le parent tag
        tag = parent_tag.find(tag_name, text=lambda text: text.strip() == 'Lieu de travail :')

        # Si le tag enfant est trouvé, utiliser find_next pour trouver le tag suivant
        if tag:
            next_tag_found = tag.find_next(next_tag)
            # Extraire et retourner le texte, ou retourner le texte par défaut
            return next_tag_found.text.strip() if next_tag_found else default_text

    return default_text