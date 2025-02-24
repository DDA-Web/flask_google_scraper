from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import logging
from selenium.webdriver.remote.remote_connection import LOGGER

app = Flask(__name__)

# Configuration du logging
LOGGER.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

def analyze_page(url):
    """Analyse une page web et retourne ses métriques SEO"""
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

        # Extraction des headers
        h1 = soup.find('h1').get_text().strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.get_text().strip() for tag in soup.find_all('h2')]

        # Comptage des mots
        word_count = len(soup.get_text().split())

        # Liens
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias
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
        logging.error(f"Erreur d'analyse: {str(e)}")
        return {"error": str(e)}

@app.route('/scrape', methods=['GET'])
def scrape_google():
    """Endpoint pour scraper les résultats Google"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' manquant"}), 400

    driver = None
    try:
        # Configuration de Chrome pour Docker
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.binary_location = "/usr/bin/chromium-browser"

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        # Accès à Google
        driver.get("https://www.google.fr")
        time.sleep(2)

        # Gestion des cookies
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            accept_btn.click()
        except Exception as e:
            logging.info("Pas de pop-up cookies trouvé")

        # Recherche
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query + Keys.RETURN)
        time.sleep(3)

        # Extraction des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]
        
        data = []
        for block in results:
            try:
                title = block.find_element(By.CSS_SELECTOR, "h3").text
                link = block.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                data.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Erreur sur un résultat: {str(e)}")
                continue

        return jsonify({"query": query, "results": data})

    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)