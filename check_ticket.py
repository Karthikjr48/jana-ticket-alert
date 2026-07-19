import os
import json
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

URLS = {
    "district": "https://www.district.in/movies/seven-screen-s-cinemas-kilambakkam-chennai-in-chennai-CD1102122",
    "ticketnew": "https://ticketnew.com/movies/chennai/seven-screen-s-cinemas-kilambakkam-chennai-c/1102122",
    "bookmyshow": "https://in.bookmyshow.com/explore/movies-chennai"
}


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=20
    )


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)

    return {
        "started": False,
        "alerted": False
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


state = load_state()

if not state["started"]:
    send("🟡 Monitoring Started\nCurrent Status : NOT OPEN")
    state["started"] = True
    save_state(state)

print("Monitor initialized successfully.")
