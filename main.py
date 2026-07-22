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
# JST取得
# -----------------------
def get_jst():
    return datetime.utcnow() + timedelta(hours=9)


# -----------------------
# 10時台のみ実行
# -----------------------
def is_target_hour():
    return get_jst().hour == 10


# -----------------------
# 本日送信済みチェック
# -----------------------
def already_sent_today(history):
    today = get_jst().strftime("%Y-%m-%d")
    return history.get("last_sent_date") == today


# -----------------------
# history読み書き
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
# 記事ページから画像取得
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
# 記事一覧取得
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
        "content": f"📢 **{name} 最新情報（本日まとめ）**",
        "embeds": embeds[:10]
    }

    res = requests.post(WEBHOOK_URL, json=data)
    print("Discord:", res.status_code)


# -----------------------
# メイン処理
# -----------------------
def main():

    print("===== START =====")

    history = load_history()

    # 10時台以外は終了
    if not is_target_hour():
        print("10時台以外のためスキップ")
        return

    # すでに送信済みなら終了
    if already_sent_today(history):
        print("今日はすでに送信済み")
        return

    any_sent = False

    for name, url in SITE.items():

        print("\n---", name, "---")

        articles = get_articles(url)

        if not articles:
            print("記事なし")
            continue

        old = history.get(name, [])

        new_articles = [
            a for a in articles
            if a["url"] not in old
        ]

        if new_articles:
            print(len(new_articles), "件送信")
            send_discord(name, new_articles)
            any_sent = True
        else:
            print("新規なし")

        history[name] = [a["url"] for a in articles]

    # 送信した日にちを記録
    if any_sent:
        history["last_sent_date"] = get_jst().strftime("%Y-%m-%d")

    save_history(history)

    print("===== END =====")


# -----------------------
# エントリーポイント（★ここ重要）
# -----------------------
if __name__ == "__main__":
    main()
