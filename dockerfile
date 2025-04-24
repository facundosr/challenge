FROM python:3.8-slim

ENV PROJECT_ID=""
ENV DATASET=""
ENV TABLE=""
 
RUN apt-get update && apt-get install -y \
wget \
curl \
unzip \
libnss3 \
&& rm -rf /var/lib/apt/lists/*
 
ENV CHROMEDRIVER_VERSION=135.0.7049.5
 
### install chrome
RUN apt-get update && apt-get install -y wget && apt-get install -y zip
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
 
### install chromedriver
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip \
  && unzip chromedriver-linux64.zip && rm -dfr chromedriver_linux64.zip \
  && mv /chromedriver-linux64/chromedriver /usr/bin/chromedriver \
  && chmod +x /usr/bin/chromedriver
 
WORKDIR /app

COPY ./google-application-credentials.json /app/google-application-credentials.json
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/google-application-credentials.json"
 
COPY deployment/requirements.txt /app/requirements.txt
 
RUN pip install --no-cache-dir -r requirements.txt
 
COPY scraper /app/scraper
COPY models /app/models

EXPOSE 8080

CMD ["python3", "scraper/yogonet.py"]