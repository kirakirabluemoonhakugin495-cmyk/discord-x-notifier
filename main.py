import requests
import feedparser
import json
import os

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

print("Webhook:", WEBHOOK_URL[:30])

# テスト投稿（必ず1回送る）
res = requests.post(WEBHOOK_URL, json={
    "content": "✅ Bot起動確認"
})
print("Test Status:", res.status_code)

# フィード読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

for feed in feeds:
    name = feed["name"]
    url = feed["rss"]

    print(f"\n--- {name} ---")
    print("URL:", url)

    parsed = feedparser.parse(url)

    if not parsed.entries:
        print("❌ 記事なし")
        continue

    latest = parsed.entries[0]

    print("Title:", latest.title)

    embed = {
        "title": latest.title,
        "url": latest.link,
        "description": latest.summary,
        "color": 5814783,
        "footer": {
            "text": name
        }
    }

    data = {
        "embeds": [embed]
    }

    res = requests.post(WEBHOOK_URL, json=data)

    print("送信ステータス:", res.status_code)
