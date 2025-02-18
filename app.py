from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import os

app = Flask(__name__)

def analyze_page(url):
    """
    Analyse la page : h1, h2, nombre de mots, liens internes/externes, etc.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Type de page (simple)
        page_type = "Autre"
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'

        # Récupérer H1 + tous les H2
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.text.strip() for tag in soup.find_all('h2')]

        # Compter le nombre de mots
        words = len(soup.get_text().split())

        # Liens internes / externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias (images, vidéos, audios, iframes embed)
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all(
            'iframe', 
            src=lambda x: x and ('youtube' in x or 'vimeo' in x)
        ))

        return {
            'type': page_type,
            'headers': {
                'H1': h1,
                'H2': h2s
            },
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

@app.route('/scrape', methods=['GET'])
def scrape_google():
    """
    Endpoint: GET /scrape?query=seo+freelance
    Récupère les 10 premiers résultats Google et analyse chaque page.
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir un mot-clé (query)."}), 400

    # Configuration de Selenium
    print("✅ [DEBUG] Configuration Selenium en cours...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")   # Ajout pour éviter certains crash

    # Forcer le chemin de chromedriver si nécessaire
    driver_path = "/usr/bin/chromedriver"  # Sur Debian/Ubuntu avec apt-get install chromium-driver
    service = Service(driver_path)

    print(f"✅ [DEBUG] On utilise chromedriver: {driver_path}")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ [DEBUG] ChromeDriver initialisé avec succès.")

    try:
        # Aller sur Google
        driver.get("https://www.google.fr")
        print("✅ [DEBUG] Navigué sur Google.fr")

        # Accepter cookies si pop-up
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_button.click()
            print("✅ [DEBUG] Bouton cookies cliqué.")
        except Exception as e:
            print(f"⚠️ [DEBUG] Pas de pop-up cookies ou erreur: {e}")

        # Rechercher le mot-clé
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.send_keys(query + Keys.RETURN)
        print(f"✅ [DEBUG] Recherche envoyée: {query}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        time.sleep(2)  # Laisser un petit délai

        # Récupérer les 10 premiers résultats
        blocks = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]
        scraped_data = []

        for block in blocks:
            try:
                title = block.find_element(By.CSS_SELECTOR, "h3").text
                link = block.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = link.split("/")[2]

                # Analyser la page
                analysis = analyze_page(link)

                scraped_data.append({
                    "domain": domain,
                    "url": link,
                    "title": title,
                    "analysis": analysis
                })

            except Exception as e:
                print(f"⚠️ [DEBUG] Erreur sur un bloc de résultats: {e}")

        return jsonify(scraped_data)

    except Exception as e:
        print(f"❌ [DEBUG] Erreur globale Selenium: {e}")
        return jsonify({"error": str(e)})

    finally:
        driver.quit()
        print("✅ [DEBUG] Fermeture du navigateur.")

# Sur Docker+Gunicorn, on ne lance pas app.run()
if __name__ == "__main__":
    # Pour test local si besoin :
    app.run(host="0.0.0.0", port=8000, debug=True)
    pass
