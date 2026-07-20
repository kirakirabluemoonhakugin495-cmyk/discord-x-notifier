import requests
from bs4 import BeautifulSoup
import os
import hashlib

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

SITES = [
    ("ポケマピ", "https://nitter.net/search?f=tweets&q=%23ポケモンGO"),
    ("ポケらく", "https://nitter.net/pokelaku")
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# メモリ内重複防止（同一実行内）
seen_hashes = set()

# 🔧 画像URLを完全修正
def fix_image_url(url):
    if not url:
        return None

    if "nitter.net/pic/" in url:
        # デコード
        path = url.split("pic/")[1]
        path = path.replace("%2F", "/")

        # media/xxxx.jpg → pbs.twimg.com/media/xxxx.jpg
        return f"https://pbs.twimg.com/{path}"

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
        img = None

        if img_el and img_el.get("src"):
            raw_img = "https://nitter.net" + img_el["src"]
            img = fix_image_url(raw_img)

        # 重複判定用ハッシュ
        uid = hashlib.md5((text + link).encode()).hexdigest()

        posts.append({
            "text": text,
            "link": link,
            "img": img,
            "id": uid
        })

    return posts

# Discord送信
def send(post, site):
    content = f"【{site}】\n\n{post['text']}\n\n{post['link']}"

    data = {
        "content": content
    }

    # 画像が有効なときだけ付ける
    if post["img"] and "pbs.twimg.com" in post["img"]:
        data["embeds"] = [
            {"image": {"url": post["img"]}}
        ]

    res = requests.post(WEBHOOK_URL, json=data)
    print(f"送信: {res.status_code}")

# メイン
def main():
    print("===== START =====")

    global seen_hashes

    for name, url in SITES:
        print(f"\n--- {name} ---")
        posts = get_posts(url)

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
