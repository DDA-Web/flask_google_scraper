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
import os
import time

# Initialisation de Flask
app = Flask(__name__)

# Fonction pour analyser une page web
def analyze_page(url):
    try:
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

        # Récupérer la structure HN (H1 et tous les H2)
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.text.strip() for tag in soup.find_all('h2')]

        headers = {
            'H1': h1,
            'H2': h2s
        }

        # Nombre de mots
        words = len(soup.get_text().split())

        # Liens internes et externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias (images, vidéos, audio, vidéos embed)
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: 'youtube' in x or 'vimeo' in x))

        return {
            'type': page_type,
            'headers': headers,
            'word_count': words,
            'internal_links': len(internal_links),
            'external_links': len(external_links),
            'media': {
                'images': images,
                'videos': videos,
                'audios': audios,
                'embedded_videos': embedded_videos
            }
        }

    except Exception as e:
        return {'error': str(e)}

# Route API pour scraper Google
@app.route('/scrape', methods=['GET'])
def scrape_google():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir un mot-clé."}), 400

    # Configurer Chrome pour Render
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--headless")  # Exécution sans interface graphique
    chrome_options.add_argument("--no-sandbox")  # Obligatoire pour Render
    chrome_options.add_argument("--disable-dev-shm-usage")  # Limiter l'utilisation mémoire
    chrome_options.add_argument("--remote-debugging-port=9222")  # Debugging mode
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://www.google.fr")

        # Accepter les cookies si nécessaire
        try:
            accept_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb")))
            accept_button.click()
        except:
            pass

        # Rechercher le mot-clé
        search_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "q")))
        search_box.send_keys(query + Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc")))
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]

        scraped_data = []

        for result in results:
            try:
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = link.split("/")[2]

                analysis = analyze_page(link)

                scraped_data.append({
                    "domain": domain,
                    "url": link,
                    "title": title,
                    "analysis": analysis
                })

            except Exception as e:
                print(f"⚠️ Erreur sur un résultat : {e}")

        return jsonify(scraped_data)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000, debug=True)
