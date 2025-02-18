from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import logging

# Configuration des logs
logging.basicConfig(level=logging.DEBUG, format="✅ [DEBUG] %(message)s")

# Initialisation de Flask
app = Flask(__name__)

# Fonction pour analyser une page web
def analyze_page(url):
    try:
        logging.debug(f"Analyse de la page : {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Détecter le type de page
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'
        else:
            page_type = 'Autre'

        # Récupérer la structure HN (H1 et H2)
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.text.strip() for tag in soup.find_all('h2')]

        # Nombre de mots
        word_count = len(soup.get_text().split())

        # Compter les liens internes et externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias présents
        media = {
            'images': len(soup.find_all('img')),
            'videos': len(soup.find_all('video')),
            'audios': len(soup.find_all('audio')),
            'embedded_videos': len(soup.find_all('iframe', src=lambda x: x and ('youtube' in x or 'vimeo' in x)))
        }

        return {
            'type': page_type,
            'headers': {'H1': h1, 'H2': h2s},
            'word_count': word_count,
            'internal_links': len(internal_links),
            'external_links': len(external_links),
            'media': media
        }

    except Exception as e:
        return {'error': str(e)}

# Route pour scraper Google
@app.route('/scrape', methods=['GET'])
def scrape_google():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir un paramètre 'query'"}), 400

    logging.debug(f"Lancement du scraping pour la requête : {query}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Pour éviter les blocages Google
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        logging.debug("Navigué sur Google.fr")
        driver.get("https://www.google.fr")

        # Pause pour éviter que Google détecte un bot
        time.sleep(3)

        # Accepter les cookies si pop-up
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_button.click()
            logging.debug("Pop-up cookies acceptée")
        except:
            logging.debug("Pas de pop-up cookies ou erreur")

        # Recherche Google
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.send_keys(query + Keys.RETURN)
        logging.debug(f"Recherche envoyée: {query}")

        # Pause après la recherche
        time.sleep(3)

        # Récupération des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]

        scraped_data = []

        for i, result in enumerate(results, 1):
            try:
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = link.split("/")[2]

                analysis = analyze_page(link)

                scraped_data.append({
                    "rank": i,
                    "domain": domain,
                    "link": link,
                    "type": analysis['type'],
                    "headers": analysis['headers'],
                    "word_count": analysis['word_count'],
                    "internal_links": analysis['internal_links'],
                    "external_links": analysis['external_links'],
                    "media": analysis['media']
                })
            except Exception as e:
                logging.debug(f"⚠️ Erreur sur un résultat : {e}")

        return jsonify(scraped_data)

    except Exception as e:
        logging.debug(f"❌ Erreur globale Selenium: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        logging.debug("Fermeture du navigateur.")
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
