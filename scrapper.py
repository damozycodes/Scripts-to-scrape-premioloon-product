import time
from datetime import datetime
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=chrome_options)


def scrape_premioloon_product(driver, url):
    try:
        driver.get(url)
        time.sleep(6)  

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract product name
        name_tag = soup.find("h1", class_="product--title")
        name = name_tag.get_text(strip=True) if name_tag else None

        # Extract price
        price_tag = soup.find("span", class_="price--content")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        # Extract weight
        weight_tag = soup.find("span", {"class": "entry--content", "itemprop": "weight"})
        weight = weight_tag.get_text(strip=True) if weight_tag else None

        # Extract article number
        article_tag = soup.find("span", {"class": "entry--content", "itemprop": "sku"})
        article_number = article_tag.get_text(strip=True) if article_tag else None

        # Extract stock / availability
        availability_tag = soup.find("span", itemprop="availability")
        if availability_tag and availability_tag.has_attr("href"):
            availability = availability_tag["href"].split("/")[-1]  # "InStock"
        else:
            availability = "SOLD_OUT/NOT_AVAILABLE"

        return {
            "URL": url,
            "Name": name,
            "Price": price,
            "Weight": weight,
            "Article Number": article_number,
            "Stock Status": availability
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def main():
    file_path = "Ballon_Inventar_Aktualisiert.csv"
    df = pd.read_csv(file_path)

    print(f"Available Column names: {df.columns}")
    product_names = df['artikel'].dropna().tolist()

    if not product_names:
        print("No product names found in CSV.")
        return

    # Generate URLs
    product_urls = []
    for product in product_names:
        if product.strip():  # ensure product name is not empty
            slug = product.lower().replace(" ", "-")
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            url = f"https://www.premioloon.com/{slug}"
            product_urls.append(url)

    driver = init_driver()
    results = []
    for url in product_urls:
        product_data = scrape_premioloon_product(driver, url)
        if product_data and product_data["Name"]:  # only add if product name exists
            product_data["Scrape Date"] = datetime.now().strftime("%Y-%m-%d")
            results.append(product_data)

    driver.quit()

    if results:
        results_df = pd.DataFrame(results)
        scrape_date = datetime.now().strftime("%Y-%m-%d")
        results_df.to_csv(f"premioloon_products_{scrape_date}.csv", index=False)
        print(f"Scraping complete. Data saved to premioloon_products_{scrape_date}.csv")
    else:
        print("No valid products found to save.")


if __name__ == "__main__":
    main()