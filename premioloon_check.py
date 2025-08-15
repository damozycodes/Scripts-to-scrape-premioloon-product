import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def search_premioloon(product_name):
    search_url = f"https://www.premioloon.com/suche?sSearch={product_name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Fehler beim Laden", None

        soup = BeautifulSoup(response.text, 'html.parser')
        first_result = soup.select_one(".product--title a")
        if not first_result:
            return "Nicht gefunden", None

        product_url = "https://www.premioloon.com" + first_result["href"]
        product_response = requests.get(product_url, headers=headers, timeout=10)
        product_soup = BeautifulSoup(product_response.text, "html.parser")

        stock_info = product_soup.select_one(".product--buybox .delivery--text")
        sku_info = product_soup.select_one(".product--ordernumber span")

        if stock_info:
            stock_text = stock_info.get_text(strip=True)
            if "nicht auf Lager" in stock_text.lower() or "ausverkauft" in stock_text.lower():
                status = "Ausverkauft"
            else:
                status = "Auf Lager"
        else:
            status = "Unbekannt"

        sku = sku_info.get_text(strip=True) if sku_info else None
        return status, sku

    except Exception as e:
        return f"Fehler: {e}", None

# CSV einlesen
input_file = "artikel.csv"
df = pd.read_csv(input_file)

# Neue Spalten initialisieren
df["premioloon_lager"] = ""
df["premioloon_artikelnummer"] = ""

# Alle Artikel prüfen
for index, row in df.iterrows():
    artikelname = row["artikel"]
    print(f"Prüfe: {artikelname}")
    status, sku = search_premioloon(artikelname)
    df.at[index, "premioloon_lager"] = status
    df.at[index, "premioloon_artikelnummer"] = sku
    time.sleep(1.5)  # höfliche Wartezeit

# Ergebnisse speichern
df.to_csv("ergebnis.csv", index=False, encoding="utf-8-sig")
print("Fertig! Datei 'ergebnis.csv' wurde erstellt.")
