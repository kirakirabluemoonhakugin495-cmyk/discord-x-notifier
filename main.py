import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SITES = {
    "ポケマピ": "https://pokemongo-get.com/pokego02416/",
    "ポケらく": "https://pokemongo-raku.com/postcategory/event"
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


# 🔥 記事リスト取得（複数）
def fetch_articles(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []

    for a in soup.select("article")[:5]:  # 最大5件
        title_tag = a.select_one("h2, h3")
        link_tag = a.select_one("a")
        img_tag = a.select_one("img")

        if not title_tag or not link_tag:
            continue

        title = title_tag.text.strip()
        link = link_tag["href"]

        # 🔥 イベントのみ抽出
        if "イベント" not in title:
            continue

        img = None
        if img_tag and img_tag.get("src"):
            img = img_tag["src"]

        articles.append({
            "title": title,
            "link": link,
            "img": img
        })

    return articles


def send_discord_batch(name, new_articles):
    for art in new_articles:
        data = {
            "content": f"--- {name} ---\n{art['title']}\n{art['link']}"
        }

        if art["img"]:
            data["embeds"] = [{"image": {"url": art["img"]}}]

        res = requests.post(WEBHOOK_URL, json=data)
        print("送信:", res.status_code)


def main():
    print("===== START =====")

    history = load_history()

    for name, url in SITES.items():
        print(f"\n--- {name} ---")

        articles = fetch_articles(url)

        if not articles:
            print("取得失敗 or 記事なし")
            continue

        old_titles = history.get(name, [])
        new_articles = []

        for art in articles:
            if art["title"] not in old_titles:
                new_articles.append(art)

        if not new_articles:
            print("更新なし")
            continue

        print(f"{len(new_articles)}件の新規記事")

        send_discord_batch(name, new_articles)

        # 履歴更新（最大20件保持）
        history[name] = [a["title"] for a in articles][:20]

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
