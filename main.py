import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SITES = {
    "ぽけらく(イベント)": "https://pokemongo-raku.com/postcategory/event",
    "ぽけらく(フィールドリサーチ)": "https://pokemongo-raku.com/post4966"
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


# 🔵 イベント一覧
def fetch_list(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []

    for item in soup.select("article")[:5]:
        title = item.select_one("h2, h3").text.strip()
        link = item.select_one("a")["href"]

        img_tag = item.select_one("img")
        img = img_tag.get("src") if img_tag else None

        articles.append({
            "title": title,
            "link": link,
            "img": img
        })

    return articles


# 🔴 固定ページ（更新検知）
def fetch_single(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    title = soup.select_one("h1").text.strip()

    img_tag = soup.select_one("img")
    img = img_tag.get("src") if img_tag else None

    return [{
        "title": title,
        "link": url,
        "img": img
    }]


def send_discord(name, new_articles):
    content = f"📢 **{name} 更新情報**\n\n"
    embeds = []

    for art in new_articles:
        content += f"🔹 {art['title']}\n{art['link']}\n\n"

        if art["img"]:
            embeds.append({
                "image": {"url": art["img"]}
            })

    data = {"content": content[:1800]}

    if embeds:
        data["embeds"] = embeds[:10]

    res = requests.post(WEBHOOK_URL, json=data)
    print("送信:", res.status_code)


def main():
    print("===== START =====")

    history = load_history()

    for name, url in SITES.items():
        print(f"\n--- {name} ---")

        if "フィールドリサーチ" in name:
            articles = fetch_single(url)
        else:
            articles = fetch_list(url)

        old_titles = history.get(name, [])
        new_articles = []

        for art in articles:
            if art["title"] not in old_titles:
                new_articles.append(art)

        if not new_articles:
            print("更新なし")
            continue

        print(f"{len(new_articles)}件の更新")

        send_discord(name, new_articles)

        history[name] = [a["title"] for a in articles]

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
