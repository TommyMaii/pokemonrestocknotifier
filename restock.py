# restock.py
import requests
from bs4 import BeautifulSoup
import json
import time
import csv
import os

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "restock_state.json"
CSV_FILE = "restock_log.csv"

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def log_csv(product, shop, url):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not exists:
            writer.writerow(["timestamp", "shop", "product", "url"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), shop, product, url])

def notify(product, shop, url):
    body = f"{product} is back in stock at {shop}!\n\n{url}"
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": body})
    except Exception as e:
        print(f"Discord error: {e}")
    log_csv(product, shop, url)

# Insert all `check_*` functions here (from your script)
def check_cardcenter_collection_boxes():
    url = "https://cardcenter.no/collections/collection-bokser"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    results = {}
    for item in soup.select(".product-item"):
        name = item.select_one(".product-title").text.strip()
        sold_out = item.select_one(".badge--sold-out")
        results[name] = not bool(sold_out)
    return results

def check_cardcenter_mystery():
    url = "https://cardcenter.no/products/pokemon-japansk-mystery-box"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    name = "Pokemon Japansk Mystery Box"
    sold_out = "Utsolgt" in soup.get_text()
    return {name: not sold_out}

def check_collectible_boxes():
    url = "https://www.collectible.no/pokemon-collector-trainer-boxes/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    results = {}
    for item in soup.select(".product"):
        name_tag = item.select_one(".woocommerce-loop-product__title")
        name = name_tag.text.strip() if name_tag else "Unknown"
        sold_out = item.select_one(".out-of-stock")
        results[name] = not bool(sold_out)
    return results

def check_pokestore_prismatic():
    url = "https://pokestore.no/products/pokemon-prismatic-evolutions-elite-trainer-box"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    name = "Pokemon Prismatic Evolutions Elite Trainer Box"
    sold_out = "Utsolgt" in soup.get_text()
    return {name: not sold_out}

def check_pokelageret_mystery():
    urls = [
        "https://pokelageret.no/produkt/alt-pokemon/mystery-box/mystery-booster-box",
        "https://pokelageret.no/produkt/alt-pokemon/mystery-box/graded-mystery-booster-bundle",
        "https://pokelageret.no/produkt/alt-pokemon/mystery-box/vintage-mystery-booster-box",
        "https://pokelageret.no/produkt/alt-pokemon/mystery-box/mystery-booster-bundle-emerald"
    ]
    results = {}
    for url in urls:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        title = soup.select_one("h1")
        name = title.text.strip() if title else url
        sold_out = "Utsolgt" in soup.get_text()
        results[name] = not sold_out
    return results

# ========== MAIN MONITOR ==========

def monitor():
    previous = load_state()
    current = {}

    shops = {
        "Pokemadness": (check_pokemadness, "https://www.pokemadness.no/22-pokemon"),
        "Kidsa": (check_kidsa, "https://kidsa.no/pokemon.html"),
        "Poke4Dayz": (check_poke4dayz, "https://www.poke4dayz.no/sealed-1"),
        "Pokelageret": (check_pokelageret, "https://pokelageret.no/butikk/alt-pokemon/booster-bokser-1"),
        "PokiHeaven": (check_pokiheaven, "https://www.poki-heaven.no/butikk/pokemon-tcg/collection-etb-tin-battle-deck"),
        "PokeShop Booster": (check_pokeshop_boosters, "https://poke-shop.no/butikk/alle-produkter/boosterbokser-1"),
        "PokeShop ETB": (check_pokeshop_etb, "https://poke-shop.no/butikk/alle-produkter/elite-trainer-box"),
        "Gamezone": (check_gamezone, "https://gamezone.no/samlekort/pokemon?pageID=3"),
        "Cardcenter": (check_cardcenter, "https://cardcenter.no/collections/pokemon"),
        "Cardcenter Collection Boxes": (check_cardcenter_collection_boxes, "https://cardcenter.no/collections/collection-bokser"),
        "Cardcenter Mystery Box": (check_cardcenter_mystery, "https://cardcenter.no/products/pokemon-japansk-mystery-box"),
        "MaxGaming": (check_maxgaming, "https://www.maxgaming.no/no/hjem-fritid/samlekortspill/pokemon"),
        "Pokestore": (check_pokestore, "https://pokestore.no/collections/pokemon-booster-bokser"),
        "Pokestore Prismatic": (check_pokestore_prismatic, "https://pokestore.no/products/pokemon-prismatic-evolutions-elite-trainer-box"),
        "Collectible": (check_collectible, "https://www.collectible.no/pokemon-boosters/"),
        "Collectible Boxes": (check_collectible_boxes, "https://www.collectible.no/pokemon-collector-trainer-boxes/"),
        "Outland": (check_outland, "https://www.outland.no/brands/pokemon?p=1"),
        "Pokelageret Mystery Boxes": (check_pokelageret_mystery, "https://pokelageret.no")
    }

    for shop, (func, url) in shops.items():
        try:
            stock = func()
            current[shop] = stock
            old = previous.get(shop, {})
            for product, in_stock in stock.items():
                if in_stock and not old.get(product, False):
                    notify(product, shop, url)
        except Exception as e:
            print(f"Error checking {shop}: {e}")

    save_state(current)


if __name__ == "__main__":
    while True:
        monitor()
        time.sleep(1800)  # every 30 min
