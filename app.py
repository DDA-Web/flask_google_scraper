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
    """Configuration du navigateur headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def analyze_page(url):
    """Analyse SEO d'une page web"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Détection du type de page
        page_type = "Autre"
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'

        # Extraction des en-têtes
        h1 = soup.find('h1').get_text().strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.get_text().strip() for tag in soup.find_all('h2')]

        # Comptage des mots
        word_count = len(soup.get_text().split())

        # Analyse des liens
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Détection des médias
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: x and ('youtube' in x or 'vimeo' in x)))

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
        logging.error(f"Erreur d'analyse pour {url}: {str(e)}")
        return {"error": str(e)}

@app.route('/scrape', methods=['GET'])
def scrape_and_analyze():
    """Endpoint complet avec scraping Google + analyse SEO"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.fr/search?q={query}&gl=fr")

        # Récupération des résultats Google
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
        results = driver.find_elements(By.CSS_SELECTOR, "div.g")[:10]

        data = []
        for element in results:
            try:
                # Extraction lien
                link_element = element.find_element(By.CSS_SELECTOR, "a")
                url = link_element.get_attribute("href")
                
                # Analyse SEO
                analysis = analyze_page(url)

                data.append({
                    "title": element.find_element(By.CSS_SELECTOR, "h3").text,
                    "link": url,
                    "analysis": analysis
                })
            except Exception as e:
                logging.warning(f"Erreur sur un résultat: {str(e)}")
                continue

        return jsonify({"query": query, "results": data})

    except Exception as e:
        logging.error(f"ERREUR: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Échec du traitement"}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)