import requests
import feedparser
import json
import os

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

print("Webhook:", WEBHOOK_URL[:30])  # 確認用（全部出さない）

res = requests.post(WEBHOOK_URL, json={
    "content": "テスト投稿"
})

print("Status:", res.status_code)
print("Response:", res.text)

# 監視対象読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

# 送信済みデータ読み込み
try:
    with open("sent.json", "r", encoding="utf-8") as f:
        sent = json.load(f)
except:
    sent = {}

updated = False

for feed in feeds:
    name = feed["name"]
    url = feed["rss"]

    parsed = feedparser.parse(url)

    if not parsed.entries:
        continue

    latest = parsed.entries[0]
    post_id = latest.link  # 一意IDとして使う

    # 初回登録
    if name not in sent:
        sent[name] = post_id
        updated = True
        continue

    # 新しい投稿のみ送信
    if sent[name] != post_id:
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

        print(f"送信: {name}")
        sent[name] = post_id
        updated = True

# 保存
if updated:
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)
