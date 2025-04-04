import os
import re
import time
import logging
import pandas as pd
from flask import Flask
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as BS
from google.cloud import bigquery

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REGEX = {
    'title': re.compile(r'^titulo fuente_roboto_slab*'),
    'kicker': re.compile(r'^volanta fuente_roboto_slab*'),
    'news': re.compile(r'^slot slot_\d+ noticia*')
}

class Scraper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.url = 'https://www.yogonet.com/international/'
        self.driver = None

    def run(self):
        logging.info("Inicio del scraping")
        with webdriver.Chrome(options=self.options) as driver:
            self.driver = driver
            self.driver.get(self.url)
            self.scroll_down()
            soup = self.get_soup()
        all_news = self.get_all_news(soup)
        return pd.DataFrame(filter(None, all_news))
        
    def get_soup(self):
        try:
            html_content = self.driver.page_source
            return BS(html_content, 'lxml')
        except Exception as e:
            logging.exception("Error al obtener el soup del html")
            raise
    
    def get_all_news(self, soup):
        try:
            raw_news = soup.find_all('div', attrs={'class': REGEX['news']})
            return [self.build_payload(raw_new) for raw_new in raw_news]
        except Exception as e:
            logging.exception("Error al obtener las noticias")
            raise

    def process_data(self, df):
        """Agrega métricas adicionales a los datos."""
        try:
            df["WordsCount"] = df["Title"].apply(lambda x: len(x.split()))
            df["CharCount"] = df["Title"].apply(lambda x: len(x.replace(' ', '')))
            df["CapitalizedWords"] = df["Title"].apply(lambda x: [word for word in x.split() if word.istitle()])
            return df
        except Exception as e:
            logging.exception("Error al agregar métricas adicionales")
            raise

    def build_payload(self, raw_new):
        try:
            title = self.get_text(raw_new, 'h2', REGEX['title'])
            kicker = self.get_text(raw_new, 'div', REGEX['kicker'])
            img = self.get_img(raw_new)
            link = self.get_url(raw_new)
            return {"Title": title, "Kicker": kicker, "Img": img, "Link": link} if title and kicker else None
        except Exception as e:
            logging.error(f"Error al construir el payload: {e}")
            return None

    @staticmethod
    def get_text(soup, tag, regex):
        element = soup.find(tag, attrs={'class': regex})
        return element.text.strip() if element else None

    @staticmethod
    def get_img(raw_new):
        img_container = raw_new.find('div', class_='imagen')
        return img_container.img['src'] if img_container and img_container.img else None

    @staticmethod
    def get_url(raw_new):
        url_container = raw_new.find('h2', attrs={'class': REGEX['title']})
        return url_container.a['href'] if url_container and url_container.a else None

    def scroll_down(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            footer = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'footer')))
            
            scroll_origin = ScrollOrigin.from_element(footer, 0, -50)
            ActionChains(self.driver).scroll_from_origin(scroll_origin, 0, 200).perform()
        except Exception as e:
            logging.warning(f"No se pudo hacer scroll: {e}")

    def insert_into_bigquery(self, df):
        if df.empty:
            logging.warning("No hay datos para insertar en BigQuery")
            return

        try:
            project_id = os.getenv("PROJECT_ID")
            dataset = os.getenv("DATASET")
            table = os.getenv("TABLE")

            if not all([project_id, dataset, table]):
                logging.error("Variables de entorno de BigQuery no configuradas correctamente")
                return

            table_id = f"{project_id}.{dataset}.{table}"
            client = bigquery.Client()
            client.load_table_from_dataframe(df, table_id).result()
            logging.info("Datos insertados correctamente en BigQuery")
        except Exception as e:
            logging.error(f"Error al insertar en BigQuery: {e}")
            raise


@app.route('/', methods=['GET'])
def run_app():
    try:
        start_time = time.time()

        scraper = Scraper()
        scraped_data = scraper.run()
        processed_data = scraper.process_data(scraped_data)

        scraper.insert_into_bigquery(processed_data)

        data_dict = processed_data.head().to_dict(orient='records')
        time_elapsed = time.time() - start_time

        logging.info(f"Script ejecutado en {time_elapsed:.2f} segundos.")
        return {"message": "Scraping completed", "time_elapsed": time_elapsed, "sample": data_dict}
    except Exception as e:
        logging.error(f"Error en `run_app()`: {e}")
        return {"error": "Ocurrió un error en el servidor"}

if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 8080)), host='0.0.0.0', debug=True)
