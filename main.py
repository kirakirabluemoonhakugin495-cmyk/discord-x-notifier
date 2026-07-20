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
    "ぽけまぴ(フィールドリサーチ)": "https://pokemongo-get.com/research_fi/"
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


def fetch_articles(url):
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print("取得失敗:", res.status_code)
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    articles = []

    # サイトごとの対応
    items = soup.select("article")

    for item in items[:5]:
        title_tag = item.select_one("h2, h3")
        link_tag = item.select_one("a")
        img_tag = item.select_one("img")

        if not title_tag or not link_tag:
            continue

        title = title_tag.text.strip()
        link = link_tag["href"]

        # 相対URL対策
        if link.startswith("/"):
            base = "/".join(url.split("/")[:3])
            link = base + link

        img = None
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src")

            # 画像URL補正
            if img and img.startswith("//"):
                img = "https:" + img

        articles.append({
            "title": title,
            "link": link,
            "img": img
        })

    return articles


def send_discord(name, new_articles):
    content = f"📢 **{name} 更新情報**\n\n"

    embeds = []

    for art in new_articles:
        content += f"🔹 {art['title']}\n{art['link']}\n\n"

        if art["img"]:
            embeds.append({
                "image": {"url": art["img"]}
            })

    data = {
        "content": content[:1800]  # 長すぎ防止
    }

    if embeds:
        data["embeds"] = embeds[:10]

    res = requests.post(WEBHOOK_URL, json=data)
    print("送信:", res.status_code)


def main():
    print("===== START =====")

    history = load_history()

    for name, url in SITES.items():
        print(f"\n--- {name} ---")

        articles = fetch_articles(url)

        if not articles:
            print("記事取得失敗")
            continue

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

        history[name] = [a["title"] for a in articles][:20]

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
