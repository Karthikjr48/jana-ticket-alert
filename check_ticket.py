import os
import json
import time
import logging
from datetime import datetime
import requests
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- UNGA DETAILS ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MOVIE_NAME = "Jana Nayagan"

URLS = {
    "district": "https://www.district.in/movies/seven-screen-s-cinemas-kilambakkam-chennai-in-chennai-CD1102122",
    "ticketnew": "https://ticketnew.com/movies/chennai/seven-screen-s-cinemas-kilambakkam-chennai-c/1102122",
    "bookmyshow_search": "https://in.bookmyshow.com/explore/movies-chennai",
    "pvr": "https://www.pvrcinemas.com/nowshowing/Chennai"
}

STATE_FILE = "state.json"
# ---------------------

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state: {e}")
    return {"started": False, "alerted": False}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving state: {e}")

def send_alert(messages):
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram credentials not configured. Skipping alert.")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for msg in messages:
        try:
            resp = requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }, timeout=15)
            resp.raise_for_status()
            logger.info("Alert sent successfully.")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

def check_district(page):
    logger.info("Checking District...")
    try:
        page.goto(URLS["district"], wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        content = page.inner_text("body").lower().replace("'", "")
        movie = MOVIE_NAME.lower()
        
        if movie in content:
            if "no shows" not in content and "no movies" not in content:
                if "am" in content or "pm" in content or "book" in content or "tickets" in content:
                    return True
    except Exception as e:
        logger.error(f"District check failed: {e}")
    return False

def check_ticketnew(page):
    logger.info("Checking TicketNew...")
    try:
        page.goto(URLS["ticketnew"], wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        content = page.inner_text("body").lower().replace("'", "")
        movie = MOVIE_NAME.lower()
        
        if movie in content:
            if "currently no shows" not in content and "no movies available" not in content:
                if "am" in content or "pm" in content or "book" in content or "tickets" in content:
                    return True
    except Exception as e:
        logger.error(f"TicketNew check failed: {e}")
    return False

def check_bookmyshow(page):
    logger.info("Checking BookMyShow...")
    try:
        page.goto(URLS["bookmyshow_search"], wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        content = page.inner_text("body").lower().replace("'", "")
        movie = MOVIE_NAME.lower()
        theatre = "seven screens cinemas"
        
        if movie in content:
            page.goto("https://in.bookmyshow.com/chennai/cinemas", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            cinema_content = page.inner_text("body").lower().replace("'", "")
            if theatre in cinema_content:
                if "am" in cinema_content or "pm" in cinema_content or "book" in cinema_content:
                    return True
    except Exception as e:
        logger.error(f"BookMyShow check failed: {e}")
    return False

def check_pvr(page):
    logger.info("Checking PVR INOX...")
    try:
        page.goto(URLS["pvr"], wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        content = page.inner_text("body").lower().replace("'", "")
        movie = MOVIE_NAME.lower()
        
        if movie in content:
            if "am" in content or "pm" in content or "book" in content or "tickets" in content:
                return True
    except Exception as e:
        logger.error(f"PVR INOX check failed: {e}")
    return False

def main():
    state = load_state()
    
    if not state.get("started", False):
        send_alert(["🟡 Monitoring Started\nCurrent Status : NOT OPEN"])
        state["started"] = True
        save_state(state)
        
    if state.get("alerted", False):
        logger.info("Already alerted. Exiting.")
        return

    opened_sites = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            if check_district(page):
                opened_sites.append(("District (Seven Screen's)", URLS["district"]))
                
            if check_ticketnew(page):
                opened_sites.append(("TicketNew (Seven Screen's)", URLS["ticketnew"]))
                
            if check_bookmyshow(page):
                opened_sites.append(("BookMyShow (Seven Screen's)", "https://in.bookmyshow.com/chennai"))
                
            if check_pvr(page):
                opened_sites.append(("PVR INOX", URLS["pvr"]))
                
            browser.close()
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        
    if opened_sites:
        logger.info("BOOKING OPENED!")
        current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        alerts = []
        for i in range(1, 4):
            site_info = "\n".join([f"✅ <a href='{site[1]}'>{site[0]}</a>" for site in opened_sites])
            alert_msg = f"🚨 ALERT {i}\n\n🎬 <b>Movie</b>: {MOVIE_NAME}\n\n<b>Which websites opened</b>:\n{site_info}\n\n🕒 <b>Time</b>: {current_time}"
            alerts.append(alert_msg)
            
        send_alert(alerts)
        state["alerted"] = True
        save_state(state)
    else:
        logger.info("Booking not open yet. Sending not open message.")
        current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        send_alert([f"ℹ️ Status Check\n\n🎬 <b>Movie</b>: {MOVIE_NAME}\n\n❌ <b>Booking is NOT OPEN yet (Checked Seven Screen's & PVR INOX).</b>\n🕒 Checked at: {current_time}"])

if __name__ == "__main__":
    main()
