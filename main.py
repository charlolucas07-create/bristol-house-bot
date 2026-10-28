import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_properties.txt"

TARGET_URLS = [
    "https://www.rightmove.co.uk/student-accommodation/find.html?searchType=STUDENT&locationIdentifier=REGION%5E93859&minBedrooms=6&maxBedrooms=6&propertyTypes=house",
    "https://www.onthemarket.com/to-rent/student-properties/6-bed-houses/redland-bristol/"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9"
}

# Matches /properties/12345678 and /details/12345678 however the link ends
ID_PATTERN = re.compile(r"/(?:properties|details)/(\d{6,})")


def send_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram send error:", e)


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()


def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(sorted(seen_ids)))


def check_properties():
    first_run = not os.path.exists(SEEN_FILE)
    seen_ids = load_seen()
    new_count = 0

    for url in TARGET_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            print(f"{url[:60]}... -> status {response.status_code}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                match = ID_PATTERN.search(link["href"])
                if not match:
                    continue

                clean_id = match.group(1)
                if clean_id in seen_ids:
                    continue

                full_url = urljoin(url, link["href"]).split("#")[0]
                seen_ids.add(clean_id)
                new_count += 1

                # First run just records what's already listed, no alert spam
                if not first_run:
                    message = f"🚨 *NEW 6-BED STUDENT HOUSE FOUND!*\n\n🔗 [View Listing]({full_url})"
                    send_alert(message)
                    print(f"Alert sent for property ID: {clean_id}")

        except Exception as e:
            print(f"Error checking page {url}: {e}")

    # Always write the file so the workflow has something to commit
    save_seen(seen_ids)
    print(f"Done. {new_count} new listings, {len(seen_ids)} tracked in total.")


if __name__ == "__main__":
    check_properties()
