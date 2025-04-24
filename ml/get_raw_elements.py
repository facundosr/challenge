from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as BS
import pandas as pd
import logging

class GetRawElements:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.url = "https://www.yogonet.com/international/"
        self.driver = None

    def run(self):
        logging.info("Iniciando el scraping...")
        with webdriver.Chrome(options=self.options) as driver:
            self.driver = driver
            self.driver.get(self.url)
            soup = self.get_soup()

        news_articles = self.get_all_news(soup)
        return pd.DataFrame(news_articles)

    def get_soup(self):
        html_content = self.driver.page_source
        return BS(html_content, "lxml")

    def get_all_news(self, soup):
        """🔹 Encuentra todos los contenedores de noticias de forma dinámica"""
        news_articles = []

        # Buscamos secciones que tengan múltiples <h2> o <h3> con enlaces
        for article in soup.find_all(["article", "div"], recursive=True):
            title = self.get_title(article)
            kicker = self.get_kicker(article)
            link = self.get_url(article)
            img = self.get_img(article)

            if title and link:
                news_articles.append({
                    "Title": title,
                    "Kicker": kicker,
                    "Link": link,
                    "Img": img,
                    "IsNews":0
                })

        return news_articles

    def get_title(self, article):
        """🔹 Encuentra el título de la noticia dinámicamente"""
        title_tag = article.find(["h1", "h2", "h3", "a"])
        return title_tag.get_text(strip=True) if title_tag else None

    def get_kicker(self, article):
        """🔹 Encuentra el kicker (subtítulo o etiqueta de la noticia)"""
        kicker_tag = article.find(["h4", "h5", "span", "strong"])
        return kicker_tag.get_text(strip=True) if kicker_tag else None

    def get_url(self, article):
        """🔹 Encuentra la URL de la noticia"""
        link_tag = article.find("a", href=True)
        return link_tag["href"] if link_tag else None
        
    def get_img(self, article):
        """🔹 Encuentra la imagen de la noticia"""
        img_tag = article.find("img", src=True)
        return img_tag["src"] if img_tag else None
    
if __name__ == "__main__":
    dinamic_scraper = GetRawElements()
    df = dinamic_scraper.run()

    df = df.dropna(subset=["Title"])
    df = df.drop_duplicates(subset=["Title"], keep="first")
    df.to_csv("csv/raw_elements.csv", sep=";",  index=False)

    print(f"✅ Noticias filtradas guardadas. Total: {len(df)}")
