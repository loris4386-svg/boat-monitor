import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def load_seen():
    if not os.path.exists("seen.json"):
        return {}
    with open("seen.json", "r") as f:
        return json.load(f)

def save_seen(seen):
    with open("seen.json", "w") as f:
        json.dump(seen, f, indent=2)

def parse_listings(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    listings = []

    for item in soup.select(".search-result"):
        link_tag = item.select_one("a")
        if not link_tag:
            continue

        url = link_tag["href"]
        if "boats.com" not in url:
            url = "https://www.boats.com" + url

        listing_id = url.rstrip("/").split("-")[-1]

        title = item.select_one(".search-result-title")
        price = item.select_one(".price")
        location = item.select_one(".search-result-location")

        listings.append({
            "id": listing_id,
            "url": url,
            "title": title.get_text(strip=True) if title else "N/A",
            "price": price.get_text(strip=True) if price else "N/A",
            "location": location.get_text(strip=True) if location else "N/A"
        })

    return listings

def extract_price(price_str):
    price_str = price_str.replace("€", "").replace(",", "").replace(".", "").strip()
    if price_str.isdigit():
        return int(price_str)
    return None

def main():
    seen = load_seen()

    url_italy = "https://www.boats.com/boats-for-sale/?class=power-motor-yachts&price=100000-500000&country=italy&seller=private"
    url_world = "https://www.boats.com/boats-for-sale/?class=power-motor-yachts&price=500000-*&seller=private"

    listings = parse_listings(url_italy) + parse_listings(url_world)

    for l in listings:
        if l["id"] in seen:
            continue

        price = extract_price(l["price"])
        if not price:
            continue

        location = l["location"].lower()

        if price <= 500000:
            if "italy" not in location:
                continue
        else:
            if "united states" in location or "usa" in location:
                continue

        message = (
            f"🚤 <b>Nuovo Motor Yacht da privato</b>\n\n"
            f"<b>Modello:</b> {l['title']}\n"
            f"<b>Prezzo:</b> {l['price']}\n"
            f"<b>Località:</b> {l['location']}\n\n"
            f"🔗 {l['url']}"
        )

        send_telegram(message)
        seen[l["id"]] = datetime.utcnow().isoformat()

    save_seen(seen)

if __name__ == "__main__":
    main()
