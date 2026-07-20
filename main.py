import requests
from bs4 import BeautifulSoup
import os
import json
import difflib

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SITES = {
    "ぽけらく(イベント)": "https://pokemongo-raku.com/postcategory/event",
    "フィールドリサーチ": "https://pokemongo-raku.com/post4966"
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


# 🔴 差分検出（神）
def fetch_diff(url, history):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # 不要部分削除
    for tag in soup(["script", "style"]):
        tag.decompose()

    content = soup.get_text(separator="\n").strip()

    old_content = history.get("diff_content", "")

    diff = difflib.unified_diff(
        old_content.splitlines(),
        content.splitlines(),
        lineterm=""
    )

    changes = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            changes.append(line[1:])

    # 更新保存
    history["diff_content"] = content

    return changes[:20], soup


def send_discord_event(name, articles):
    content = f"📢 **{name} 更新情報**\n\n"
    embeds = []

    for art in articles:
        content += f"🔹 {art['title']}\n{art['link']}\n\n"

        if art["img"]:
            embeds.append({"image": {"url": art["img"]}})

    data = {"content": content[:1800]}
    if embeds:
        data["embeds"] = embeds[:10]

    requests.post(WEBHOOK_URL, json=data)


def send_discord_diff(changes, soup):
    title = soup.select_one("h1").text.strip()

    img_tag = soup.select_one("img")
    img = img_tag.get("src") if img_tag else None

    content = "🆕 **フィールドリサーチ更新！**\n\n"

    for c in changes:
        if c.strip():
            content += f"＋ {c.strip()}\n"

    data = {"content": content[:1800]}

    if img:
        data["embeds"] = [{"image": {"url": img}}]

    requests.post(WEBHOOK_URL, json=data)


def main():
    print("===== START =====")

    history = load_history()

    # 🔵 イベント
    print("\n--- イベント ---")
    articles = fetch_list(SITES["ぽけらく(イベント)"])

    old_titles = history.get("events", [])
    new_articles = [a for a in articles if a["title"] not in old_titles]

    if new_articles:
        print("イベント更新あり")
        send_discord_event("イベント", new_articles)
        history["events"] = [a["title"] for a in articles]

    else:
        print("イベント更新なし")

    # 🔴 差分検出
    print("\n--- フィールドリサーチ ---")
    changes, soup = fetch_diff(SITES["フィールドリサーチ"], history)

    if changes:
        print(f"差分 {len(changes)}件")
        send_discord_diff(changes, soup)
    else:
        print("差分なし")

    save_history(history)

    print("===== END =====")


if __name__ == "__main__":
    main()
