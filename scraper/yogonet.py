import time
import os
import logging
import joblib
import pandas as pd
from selenium import webdriver
from flask import Flask
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as BS
from google.cloud import bigquery

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

model = joblib.load("models/title_classifier.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

def is_valid_title(title):
    vectorized = vectorizer.transform([title])
    prediction = model.predict(vectorized)[0]
    return prediction == 1


class DinamicScraper:
    """
        Realiza el scraping de la página de noticias de Yogonet y filtra las noticias con un modelo entrnado para identificar noticias.
        Previa ejecución del dinamc scraper por primerva vez, se necesitan tener los modelos entrenados y guardados en la carpeta models
        - paso 1: obtener el html raw de las noticias de yogonet con la ejecución del script ml/get_raw_elements.py y
            categorizar las noticias con 0 y 1 en el categorized_news.csv
        - paso 2: entrenar el modelo con el script ml/trainer.py que guardará los modelos en la carpeta models
    """
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.url = 'https://www.yogonet.com/international/'

    def run(self):
        """Ejecuta el scraper y devuelve un DataFrame con noticias válidas"""
        logging.info("Inicio del scraping")
        with webdriver.Chrome(options=self.options) as driver:
            driver.get(self.url)
            soup = self.get_soup(driver)
        
        all_news = self.get_all_news(soup)
        return pd.DataFrame(filter(None, all_news))

    def get_soup(self, driver):
        """Obtiene el HTML con BeautifulSoup"""
        try:
            html_content = driver.page_source
            return BS(html_content, 'lxml')
        except Exception as e:
            logging.exception("Error al obtener el soup del html")
            raise

    def get_all_news(self, soup):
        """Extrae todas las noticias del HTML"""
        try:
            raw_news = soup.find_all('div', class_="noticia")
            return [self.process_news(raw_new) for raw_new in raw_news]
        except Exception as e:
            logging.exception("Error al obtener las noticias")
            raise

    def process_news(self, raw_new):
        """Extrae título, kicker, imagen y enlace, y filtra con IA"""
        try:
            title = self.get_text(raw_new, "h2")
            kicker = self.get_text(raw_new, "div", "volanta")
            img = self.get_img(raw_new)
            link = self.get_url(raw_new)

            # Verificar con si el título es una noticia real
            have_keys = [title!=None, link!=None, "https" in link, "news" in link ]
            if title and is_valid_title(title) or all(have_keys):
                return {"Title": title, "Kicker": kicker, "Img": img, "Link": link}
            return None
        except Exception as e:
            logging.error(f"Error al procesar la noticia: {e}")
            return None

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

    @staticmethod
    def get_text(soup, tag, class_name=None):
        """Obtiene texto limpio de un tag"""
        element = soup.find(tag, class_=class_name) if class_name else soup.find(tag)
        return element.text.strip() if element else None

    @staticmethod
    def get_img(raw_new):
        """Extrae la URL de la imagen"""
        img_container = raw_new.find('img')
        return img_container['src'] if img_container else None

    @staticmethod
    def get_url(raw_new):
        """Extrae el enlace de la noticia"""
        url_container = raw_new.find('a')
        return url_container['href'] if url_container else None

@app.route('/', methods=['GET'])
def run_app():
    try:
        start_time = time.time()

        scraper = DinamicScraper()
        scraped_data = scraper.run()
        processed_data = scraper.process_data(scraped_data)
        print(scraped_data.head())
        processed_data.to_csv("processed_data.csv", index=False)
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
