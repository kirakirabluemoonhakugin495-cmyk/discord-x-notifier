import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime, timedelta


WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SITE = {
    "ぽけらく(イベント)":
        "https://pokemongo-raku.com/postcategory/event",

    "フィールドリサーチ":
        "https://pokemongo-raku.com/post4966"
}

HISTORY_FILE = "history.json"


# -----------------------
# 時間制御（最重要）
# -----------------------
def is_morning_10():
    jst = datetime.utcnow() + timedelta(hours=9)
    return jst.hour == 10


# -----------------------
# history
# -----------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------
# 画像取得
# -----------------------
def get_image(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        og = soup.select_one('meta[property="og:image"]')
        if og:
            return og.get("content")

    except:
        pass

    return None


# -----------------------
# 記事取得
# -----------------------
def get_articles(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
    except:
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    result = []

    for article in soup.select("article")[:5]:

        title = article.select_one("h2,h3")
        link = article.select_one("a")

        if not title or not link:
            continue

        href = link.get("href")

        # 空URLや広告除外
        if not href or "javascript" in href:
            continue

        result.append({
            "title": title.text.strip(),
            "url": href,
            "image": get_image(href)
        })

    return result


# -----------------------
# Discord送信
# -----------------------
def send_discord(name, articles):

    embeds = []

    for a in articles:

        embed = {
            "title": a["title"],
            "url": a["url"],
            "color": 5814783
        }

        if a["image"]:
            embed["image"] = {"url": a["image"]}

        embeds.append(embed)

    data = {
        "content": f"📢 **{name} 最新情報（10時更新）**",
        "embeds": embeds[:10]
    }

    res = requests.post(WEBHOOK_URL, json=data)

    print("Discord:", res.status_code)


# -----------------------
# main
# -----------------------
def main():

    print("===== START =====")

    # ★ 最重要：10時以外は絶対止める
    if not is_morning_10():
        print("10時以外のためスキップ")
        return

    history = load_history()

    for name, url in SITE.items():

        print("\n---", name, "---")

        articles = get_articles(url)

        if not articles:
            print("記事なし")
            continue

        old = history.get(name, [])

        # 新しい記事のみ
        new_articles = [
            a for a in articles
            if a["url"] not in old
        ]

        if new_articles:
            print(len(new_articles), "件送信")
            send_discord(name, new_articles)
        else:
            print("新規なし")

        # 最新状態保存
        history[name] = [
            a["url"] for a in articles
        ]

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
