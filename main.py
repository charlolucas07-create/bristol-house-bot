import os
import requests
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
        f.write("\n".join(seen_ids))

def check_properties():
    seen_ids = load_seen()
    new_found = False

    for url in TARGET_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = soup.find_all("a", href=True)
            for link in links:
                href = link['href']
                
                # Strict URL path check to ignore navigation, footer, and menu links
                if ("/properties/" in href or "/details/" in href) and not href.startswith("#"):
                    
                    # Ensure numeric property ID
                    clean_id = href.split("/")[-1].split(".")[0].split("?")[0]
                    
                    if clean_id.isdigit() and len(clean_id) >= 6 and clean_id not in seen_ids:
                        full_url = href if href.startswith("http") else "https://www.rightmove.co.uk" + href
                        
                        seen_ids.add(clean_id)
                        new_found = True
                        
                        message = f"🚨 *NEW 6-BED STUDENT HOUSE FOUND!*\n\n🔗 [View Listing]({full_url})"
                        send_alert(message)
                        print(f"Alert sent for property ID: {clean_id}")

        except Exception as e:
            print(f"Error checking page {url}: {e}")

    if new_found:
        save_seen(seen_ids)
    else:
        print("Checked portals — no new listings right now.")

if __name__ == "__main__":
    check_properties()
