import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

ACCOUNTS = {
    "ポケマピ": "https://nitter.net/pokemapi",
    "ポケらく": "https://nitter.net/pokeraku_app"
}

HISTORY_FILE = "history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def fetch_latest(account, url):
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"取得失敗: {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        tweet = soup.select_one(".timeline-item")

        if not tweet:
            return None

        text = tweet.select_one(".tweet-content").text.strip()
        img_tag = tweet.select_one("img")

        img_url = None
        if img_tag:
            img_url = "https://nitter.net" + img_tag["src"]

        return text, img_url

    except Exception as e:
        print("エラー:", e)
        return None


def send_discord(title, text, img):
    data = {
        "content": f"--- {title} ---\n{text}"
    }

    if img:
        data["embeds"] = [{"image": {"url": img}}]

    res = requests.post(WEBHOOK_URL, json=data)
    print("送信:", res.status_code)


def main():
    print("===== START =====")

    history = load_history()

    for name, url in ACCOUNTS.items():
        print(f"\n--- {name} ---")

        result = fetch_latest(name, url)

        if not result:
            print("投稿なし")
            continue

        text, img = result

        # 🔥 重複チェック
        if history.get(name) == text:
            print("重複のためスキップ")
            continue

        print("新規投稿:", text[:30])

        send_discord(name, text, img)

        history[name] = text

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
