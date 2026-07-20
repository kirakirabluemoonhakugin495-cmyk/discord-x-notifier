import requests
import feedparser
import json
import os
import re

print("===== START =====")

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

def clean_html(text):
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub('<.*?>', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    if "links" in entry:
        for link in entry.links:
            if link.get("type", "").startswith("image"):
                return link.get("href")

    match = re.search(r'<img.*?src="(.*?)"', entry.summary)
    if match:
        return match.group(1)

    return None

# フィード読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

# 送信履歴読み込み
try:
    with open("sent.json", "r", encoding="utf-8") as f:
        sent = json.load(f)
except:
    sent = {}

updated = False

for feed in feeds:
    name = feed["name"]
    url = feed["rss"]

    print(f"\n--- {name} ---")

    parsed = feedparser.parse(url)

    if not parsed.entries:
        print("記事なし")
        continue

    latest = parsed.entries[0]
    post_id = latest.link

    if sent.get(name) != post_id:
        description = clean_html(latest.summary)
        image_url = get_image(latest)

        embed = {
            "title": latest.title,
            "url": latest.link,
            "description": description[:200],
            "color": 5814783,
            "footer": {"text": name}
        }

        if image_url:
            embed["image"] = {"url": image_url}

        res = requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        print("送信:", res.status_code)

        if res.status_code == 204:
            sent[name] = post_id
            updated = True

# 保存
if updated:
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)

print("===== END =====")import requests
import feedparser
import json
import os
import re

print("===== START =====")

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# ✅ HTML整形（改行・URL除去）
def clean_html(text):
    # 改行タグを改行に変換
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)

    # HTMLタグ削除
    text = re.sub('<.*?>', '', text)

    # URL削除
    text = re.sub(r'http\S+', '', text)

    # 余計な空白整理
    text = re.sub(r'\n+', '\n', text)

    return text.strip()

# ✅ 画像取得（可能な限り）
def get_image(entry):
    # media:content
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    # enclosure
    if "links" in entry:
        for link in entry.links:
            if link.get("type", "").startswith("image"):
                return link.get("href")

    # HTML内img
    match = re.search(r'<img.*?src="(.*?)"', entry.summary)
    if match:
        return match.group(1)

    return None

# フィード読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

# 送信済み
try:
    with open("sent.json", "r", encoding="utf-8") as f:
        sent = json.load(f)
except:
    sent = {}

updated = False

for feed in feeds:
    name = feed["name"]
    url = feed["rss"]

    print(f"\n--- {name} ---")

    parsed = feedparser.parse(url)

    if not parsed.entries:
        print("❌ 記事なし")
        continue

    latest = parsed.entries[0]
    post_id = latest.link

    if sent.get(name) != post_id:

        description = clean_html(latest.summary)
        image_url = get_image(latest)

        # 👉 読みやすくする
        description = description[:200]

        embed = {
            "title": latest.title,
            "url": latest.link,
            "description": description,
            "color": 5814783,
            "footer": {
                "text": name
            }
        }

        # 画像があれば追加
        if image_url:
            embed["image"] = {"url": image_url}
            print("画像:", image_url)
        else:
            print("画像なし")

        res = requests.post(WEBHOOK_URL, json={
            "embeds": [embed]
        })

        print("送信:", res.status_code)

        if res.status_code == 204:
            sent[name] = post_id
            updated = True

# 保存
if updated:
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)

print("===== END =====")
