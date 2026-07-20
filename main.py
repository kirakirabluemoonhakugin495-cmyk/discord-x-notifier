import requests
from bs4 import BeautifulSoup
import os
import hashlib

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

SITES = [
    ("ポケマピ", "https://nitter.poast.org/search?f=tweets&q=%23ポケモンGO"),
    ("ポケらく", "https://nitter.poast.org/pokelaku")
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

seen_hashes = set()

# 画像URL修正（確実に表示できる形に）
def fix_image_url(url):
    if not url:
        return None

    if "nitter" in url and "/pic/" in url:
        path = url.split("/pic/")[1]
        path = path.replace("%2F", "/")
        return f"https://pbs.twimg.com/{path}"

    return url

# 投稿取得（安定版）
def get_posts(url):
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print("取得失敗:", res.status_code)
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    items = soup.select("div.timeline-item")

    posts = []

    for item in items[:5]:
        text_el = item.select_one(".tweet-content")
        link_el = item.select_one("a.tweet-link")
        img_el = item.select_one("img[src*='media']")

        text = text_el.text.strip() if text_el else ""
        link = "https://nitter.poast.org" + link_el["href"] if link_el else ""
        img = None

        if img_el and img_el.get("src"):
            raw = "https://nitter.poast.org" + img_el["src"]
            img = fix_image_url(raw)

        if not text:
            continue

        uid = hashlib.md5((text + link).encode()).hexdigest()

        posts.append({
            "id": uid,
            "text": text,
            "link": link,
            "img": img
        })

    return posts

# Discord送信
def send(post, site):
    content = f"【{site}】\n\n{post['text']}\n\n{post['link']}"

    data = {
        "content": content
    }

    # 画像が有効なときだけ送る
    if post["img"] and "pbs.twimg.com" in post["img"]:
        data["embeds"] = [
            {
                "image": {"url": post["img"]}
            }
        ]

    res = requests.post(WEBHOOK_URL, json=data)
    print("送信:", res.status_code)

# メイン処理
def main():
    print("===== START =====")

    global seen_hashes

    for name, url in SITES:
        print(f"\n--- {name} ---")

        posts = get_posts(url)

        if not posts:
            print("投稿なし")
            continue

        for post in posts:
            if post["id"] in seen_hashes:
                continue

            print("投稿:", post["text"][:30])
            print("画像:", post["img"])

            send(post, name)

            seen_hashes.add(post["id"])

    print("===== END =====")


if __name__ == "__main__":
    main()
