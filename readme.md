# 📝 **README - Deploy del Proyecto Scraper**  

¡Bienvenido! Este archivo explica cómo desplegar el proyecto **Scraper** utilizando 🐳 Docker y ☁️ **Google Cloud Run** de forma eficiente. 

## 📝 **Descripción del Proyecto**

## **Desarrollado por: Facundo Sosa Ruveda**

        Previa ejecución del dinamc scraper por primerva vez, se necesitan tener los modelos entrenados y guardados en la carpeta models
        - paso 1: obtener el html raw de las noticias de yogonet con la ejecución del script ml/get_raw_elements.py y
            categorizar las noticias con 0 y 1 en el categorized_news.csv
        - paso 2: entrenar el modelo con el script ml/trainer.py que guardará los modelos en la carpeta models

Este proyecto es un **scraper** que utiliza **Google Cloud Run** para realizar tareas de:  
1. 🌐 **Scraping web** de noticias con `Python` y `Selenium`.  
2. ⚙️ **Procesamiento de datos** con `pandas`.  
3. 📊 **Almacenamiento** en una tabla de **BigQuery**.
4. 📊 **Ejecución** deploy de la imagen y ejecución del job **Cloud Run**. 

### 🌍 **Sitio web objetivo**  
El scraper extrae las noticias de la portada del siguiente portal:  
[🔗 Yogonet International](https://www.yogonet.com/international/)  

### 📦 **Datos extraídos**  
Del sitio web se obtienen los siguientes datos:  
- 📰 **Title**: Título de la noticia.  
- 📢 **Kicker**: Subtítulo o categoría.  
- 🖼 **Image**: URL de la imagen asociada.  
- 🔗 **Link**: Enlace directo a la noticia.  

---

### 🔄 **Post-procesamiento de Datos**  
Con la ayuda de `pandas`, se calculan las siguientes métricas adicionales:  
- ✍️ **Recuento de palabras en el título**: Total de palabras en cada título.  
- 🔤 **Recuento de caracteres en el título**: Total de caracteres excluyendo espacios.  
- 🔠 **Palabras capitalizadas**: Lista de palabras que comienzan con mayúscula en el título.  

---

### 📂 **Almacenamiento: Integración con BigQuery**  
Una vez procesados, los datos se insertan en una tabla de **BigQuery** para un análisis más avanzado o almacenamiento a largo plazo.  


---

## 🚀 **Requisitos previos**
Antes de comenzar, asegúrate de tener todo lo siguiente configurado:  

1. ✅ **Cuenta de Google Cloud** con un proyecto habilitado.
2. ✅ **Credenciales** google-application-credentials.json con las credenciales para trabajar con BigQuery.  
3. ✅ Instaladas las herramientas necesarias:  
   - 🛠️ [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)  
   - 🛠️ [Docker](https://docs.docker.com/get-docker/)  

---

## 📦 **Estructura del Proyecto**
```
📁 challenge/
├── 📄 dockerfile
├── 📄 readme.md
└── 📁 csv/
    ├── 📄 categorized_news.csv
    ├── 📄 raw_elements.csv
└── 📁 ml/
    ├── 📄 get_raw_elements.py
    └── 📄 trainer.py
└── 📁 models/
    ├── 📄 title_classifier.pkl
    └── 📄 vectorizer.pkl
└── 📁 deployment/
    ├── 📄 deploy.sh
    └── 📄 requirements.txt
└── 📁 scraper/
    └── 📄 yogonet.py
```
---

## 🛠️ **Configuración Inicial**

1. **Clonar el repositorio** en tu máquina local:     
   ```bash
   git clone https://github.com/facundosr/challenge.git
   cd challenge/

## Pasos para el Despliegue

### 1. Obtener csv con elementos crudos del html
   - Ejectuar ml/get_raw_elements.py, creará un csv en la carpeta csv con el nombre categorized_news.csv
   - Clasificar con 1 aquellas filas que son noticias

### 2. Entrenar el modelo de identificación de noticias
   - Ejectuar ml/trainer.py, entrenará los modelos y los guardará en la carpeta models

### 3. Pegar credenciales para google aplicattions
< Antes que nada debés pegar en la raíz del proyecto el archivo `google-application-credentials.json` >

### 4. Insertar valores en las variables
1. En el archivo dockerfile que está en la raíz del proyecto completar los valores de las variables:
   - `PROJECT_ID`: ID del proyecto de google cloud
   - `DATASET`: nombre del dataset o conjunto de datos de bigquery
   - `TABLE`: nombre de la tabla del dataset

2. En el archivo deploy.sh que se encuentra dentro de la carpeta deployment, completar:
   - `PROJECT_ID`: ID del proyecto de google cloud
   - `REGION`: región en la que quiere ejecutarse el servicio Cloud Run

### 5. Construcción de la Imagen Docker

El `Dockerfile` instala todas las dependencias necesarias para la aplicación, incluido ChromeDriver y Google Chrome para la ejecución del scraper. Sigue estos pasos:

1. Dirigirse al directorio raíz del proyecto.
2. Construí la imagen Docker:
   ```docker build -t yogonet-scrapper-app .```

### 6. Ejecución del Script de Despliegue

El script `deploy.sh` configura el proyecto, habilita las APIs necesarias y despliega la aplicación en Cloud Run.

1. Ejecutar el script:
   ```bash ./deployment/deploy.sh```

2. Copiar y pegar la url en el explorador. Esto ejecutará el servicio en cloud run. Si todo es exitoso se puede ver un diccionario similar a este:

    ```{
    "data_sample": [
        {
            "CapitalizedWords": [
                "Senate"
            ],
            "CharCount": 51,
            "Img": "https://imagenesyogonet.b-cdn.net/data/imagenes/2024/12/12/70840/1734008878-us-congress-united-states-capitol-washington-dc-capitolio-estados-unidos-usa-03.jpg",
            "Kicker": "December 17",
            "Link": "https://www.yogonet.com/international/news/2024/12/12/88336-us-senate-committee-to-hold-sports-betting-hearing-next-week",
            "Title": "US Senate committee to hold sports betting hearing next week",
            "WordsCount": 10
        }],
         "message": "Scraping completed",
         "time_elapsed": 14.446839332580566
      } 

### Configuración de Google Cloud Run

El script realiza las siguientes acciones:

1. **Habilitar servicios necesarios:**

   - `containerregistry.googleapis.com`
   - `artifactregistry.googleapis.com`
   - `run.googleapis.com`

2. **Construir y subir la imagen:**

   - Configura Docker para trabajar con Google Cloud.
   - Subir la imagen al Container Registry del proyecto.

3. **Despliegue en Cloud Run:**

   - Despliega el servicio con 1GB de memoria y puerto 8080.
   - Permite acceso no autenticado para pruebas públicas.

4. **Obtener la URL del servicio:**

   - La URL del servicio será mostrada al final del despliegue.


---

## Ejecución Local

Para probar la aplicación localmente:

1. Construye y ejecuta el contenedor:
   ```
   docker run -p 8080:8080 yogonet-scrapper-app
   ```
2. Accede a la aplicación en: [http://localhost:8080](http://localhost:8080)

---

## Recursos

- [Google Cloud Run](https://cloud.google.com/run)
- [Google Container Registry](https://cloud.google.com/container-registry)
- [Docker Documentation](https://docs.docker.com/)


