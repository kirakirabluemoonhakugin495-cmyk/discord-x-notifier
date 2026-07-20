import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# チェック対象サイト
SITES = [
    ("ポケモンGO攻略情報＠ポケマピ", "https://nitter.net/search?f=tweets&q=%23ポケモンGO"),
    ("ポケらく＠ポケモンアプリ情報", "https://nitter.net/pokelaku")
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEEN_FILE = "seen.json"

# 既読データ読み込み
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

# 既読データ保存
def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

# Nitter画像URL → Twitter CDNに変換
def fix_image_url(url):
    if url and "nitter.net/pic/" in url:
        url = url.replace("https://nitter.net/pic/", "")
        url = url.replace("%2F", "/")
        return f"https://pbs.twimg.com/{url}"
    return url

# 投稿取得
def get_posts(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select(".timeline-item")
    
    posts = []
    for item in items[:5]:
        text_el = item.select_one(".tweet-content")
        link_el = item.select_one("a.tweet-link")
        img_el = item.select_one("img")

        text = text_el.text.strip() if text_el else ""
        link = "https://nitter.net" + link_el["href"] if link_el else ""
        img = img_el["src"] if img_el else None

        if img:
            img = "https://nitter.net" + img

        img = fix_image_url(img)

        posts.append({
            "text": text,
            "link": link,
            "img": img
        })

    return posts

# Discord送信
def send(post, site_name):
    content = f"【{site_name}】\n{post['text']}\n{post['link']}"

    data = {
        "content": content
    }

    # 画像がある場合はembedで送る
    if post["img"]:
        data["embeds"] = [
            {
                "image": {"url": post["img"]}
            }
        ]

    res = requests.post(WEBHOOK_URL, json=data)
    print(f"送信: {res.status_code}")

# メイン処理
def main():
    print("===== START =====")

    seen = load_seen()
    new_seen = set(seen)

    for name, url in SITES:
        print(f"\n--- {name} ---")
        posts = get_posts(url)

        for post in posts:
            if post["link"] in seen:
                continue

            print(post["text"])
            send(post, name)

            new_seen.add(post["link"])

    save_seen(new_seen)

    print("===== END =====")


if __name__ == "__main__":
    main()
