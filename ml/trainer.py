import re
import joblib
import pandas as pd
from xgboost import XGBClassifier
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split


def clean_text(text):
    text = text.lower()
    text = re.sub(r'\W+', ' ', text)
    return text.strip()


df = pd.read_csv("csv/categorized_news.csv", delimiter=";")
df.drop_duplicates(inplace=True)
df.dropna(inplace=True)

df["Title"] = df["Title"].apply(clean_text)

# 📌 Convertir texto en números (vectorización)
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(df["Title"])
y = df["IsNews"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

xgb_model = XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=6)
xgb_model.fit(X_train, y_train)

accuracy = xgb_model.score(X_test, y_test)
print(f"XGBoost Accuracy: {accuracy:.2f}")

joblib.dump(xgb_model, "models/title_classifier1.pkl")
joblib.dump(vectorizer, "models/vectorizer1.pkl")

print("✅ Modelo guardado correctamente.")
