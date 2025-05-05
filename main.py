from bs4 import BeautifulSoup
import requests
import time
import csv
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0"
}

all_games = []

print("🔎 Starting scraping Metacritic must-play games...\n")

for page in range(1, 17):
    print(f"🔎 Accessing page {page}...")
    url = f"https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={page}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("a.c-finderProductCard_container")

    if not cards:
        print("⚠️ No game cards found. Stopping.")
        break

    for card in cards:
        title_elem = card.select_one(".c-finderProductCard_titleHeading span:nth-of-type(2)")
        rank_elem = card.select_one(".c-finderProductCard_titleHeading span:nth-of-type(1)")
        date_elem = card.select_one(".c-finderProductCard_meta span:nth-of-type(1)")
        metascore_elem = card.select_one(".c-siteReviewScore span")
        mustplay_elem = card.select_one('img[alt="must-play"]')

        if mustplay_elem is None:
            continue  # skip if not must-play

        game = {
            "rank": rank_elem.text.strip() if rank_elem else None,
            "title": title_elem.text.strip() if title_elem else None,
            "release_date": date_elem.text.strip() if date_elem else None,
            "metascore": int(metascore_elem.text.strip()) if metascore_elem else None
        }

        all_games.append(game)

    time.sleep(1)  # avoid IP block

print("\n✅ Scraping completed.\n")

# Save to CSV with today's date in filename
today_str = datetime.today().strftime("%Y-%m-%d")
csv_filename = f"metacritic_must_play_games_{today_str}.csv"

with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["rank", "title", "release_date", "metascore"])
    writer.writeheader()
    writer.writerows(all_games)

print(f"📁 CSV file saved: {csv_filename}")