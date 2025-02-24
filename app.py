from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import logging
import traceback

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_driver():
    """Configuration optimisée avec timeout ajusté"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(45)  # Augmentation du timeout
    return driver

def analyze_page(url):
    """Analyse SEO avec gestion d'erreur améliorée"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Vérifie le statut HTTP
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Détection type de page
        page_type = "Autre"
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'

        # Extraction HN
        h1 = soup.find('h1').get_text().strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.get_text().strip() for tag in soup.find_all('h2')]

        # Comptage mots
        word_count = len(soup.get_text(strip=True).split())

        # Analyse liens
        links = soup.find_all('a', href=True)
        base_url = url.split('//')[-1].split('/')[0]
        internal_links = [link['href'] for link in links if base_url in link['href']]
        external_links = [link['href'] for link in links if base_url not in link['href']]

        # Détection médias
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: x and any(s in x for s in ['youtube', 'vimeo'])))

        return {
            "type": page_type,
            "headers": {"H1": h1, "H2": h2s},
            "word_count": word_count,
            "internal_links": len(internal_links),
            "external_links": len(external_links),
            "media": {
                "images": images,
                "videos": videos,
                "audios": audios,
                "embedded_videos": embedded_videos
            }
        }

    except Exception as e:
        logging.error(f"Erreur analyse {url}: {str(e)}")
        return {"error": str(e)}

@app.route('/scrape', methods=['GET'])
def scrape_and_analyze():
    """Nouvelle implémentation robuste"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.fr/search?q={query}&gl=fr")

        # Gestion cookies améliorée
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(., 'Tout accepter')]]"))
            ).click()
            time.sleep(1)
        except Exception:
            logging.info("Pas de pop-up cookies")

        # Nouveaux sélecteurs Google
        WebDriverWait(driver, 25).until(  # Augmentation du timeout
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )

        # Récupération résultats
        results = driver.find_elements(By.CSS_SELECTOR, "div.g, div[data-header-feature]")[:10]
        
        data = []
        for element in results:
            try:
                link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                analysis = analyze_page(link)
                
                data.append({
                    "title": element.find_element(By.CSS_SELECTOR, "h3, span[role='heading']").text,
                    "link": link,
                    "analysis": analysis
                })
            except Exception as e:
                logging.warning(f"Erreur résultat: {str(e)}")
                continue

        return jsonify({"query": query, "results": data})

    except Exception as e:
        logging.error(f"ERREUR: {traceback.format_exc()}")
        return jsonify({
            "error": "Service indisponible - Veuillez réessayer plus tard",
            "code": 503
        }), 503

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)