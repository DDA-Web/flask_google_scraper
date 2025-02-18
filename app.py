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

app = Flask(__name__)

def analyze_page(url):
    """
    Analyse le contenu d'une page : h1, h2, etc.
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

        # Nombre de mots
        words = len(soup.get_text().split())

        # Liens internes vs externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: x and ('youtube' in x or 'vimeo' in x)))

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
    Exemple d'appel :
    GET /scrape?query=seo+freelance
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir un mot-clé."}), 400

    # Configurer Selenium / Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")      # Mode sans interface
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.google.fr")

        # Accepter cookies (si pop-up)
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_button.click()
        except:
            pass

        # Recherche
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.send_keys(query + Keys.RETURN)

        # Attendre l'apparition des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        time.sleep(2)

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
                print(f"⚠️ Erreur sur un bloc: {e}")

        return jsonify(scraped_data)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

# Pas besoin de app.run() si on utilise Gunicorn + Docker
if __name__ == "__main__":
    # app.run(debug=True, port=8000)
    pass
