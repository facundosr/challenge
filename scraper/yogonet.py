import os
import re
import time
import platform
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
from pyvirtualdisplay.display import Display
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
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.url = 'https://www.yogonet.com/international/'

        self.driver = None
        if platform.system() == 'Linux':
            self.display = Display(visible=0, size=(1366, 768))
            self.display.start()

    def run(self):
        logging.info("Inicio del scraping")
        with webdriver.Chrome(options=Options()) as driver:
            self.driver = driver
            self.driver.get(self.url)
            self.scroll_down()
            html_content = self.driver.page_source
            soup = BS(html_content, 'lxml')
            raw_news = soup.find_all('div', attrs={'class': REGEX['news']})
            all_news = [self.build_payload(raw_new) for raw_new in raw_news]
            return pd.DataFrame(filter(None, all_news))  # Filtra `None`

    def process_data(self, df):
        """Agrega métricas adicionales a los datos."""
        df["WordsCount"] = df["Title"].apply(lambda x: len(x.split()))
        df["CharCount"] = df["Title"].apply(lambda x: len(x.replace(' ', '')))
        df["CapitalizedWords"] = df["Title"].apply(lambda x: [word for word in x.split() if word.istitle()])
        return df

    def build_payload(self, raw_new):
        title = self.get_text_or_none(raw_new, 'h2', REGEX['title'])
        kicker = self.get_text_or_none(raw_new, 'div', REGEX['kicker'])
        img = self.get_img(raw_new)
        link = self.get_url(raw_new)
        return {"Title": title, "Kicker": kicker, "Img": img, "Link": link} if title and kicker else None

    @staticmethod
    def get_text_or_none(soup, tag, regex):
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

@app.route('/', methods=['GET'])
def run_app():
    start_time = time.time()

    scraper = Scraper()
    scraped_data = scraper.run()
    processed_data = scraper.process_data(scraped_data)

    scraper.insert_into_bigquery(processed_data)

    data_dict = processed_data.head().to_dict(orient='records')
    time_elapsed = time.time() - start_time

    logging.info(f"Script ejecutado en {time_elapsed:.2f} segundos.")
    return {"message": "Scraping completed", "time_elapsed": time_elapsed, "data_sample": data_dict}

if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 8080)), host='0.0.0.0', debug=True)
