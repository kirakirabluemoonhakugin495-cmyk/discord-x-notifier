import requests
import feedparser
import json
import os

print("===== START =====")

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
print("Webhook OK")

# フィード読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

# 送信済みデータ読み込み
try:
    with open("sent.json", "r", encoding="utf-8") as f:
        sent = json.load(f)
        print("sent.json 読み込みOK")
except:
    sent = {}
    print("sent.json なし（新規作成）")

updated = False

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
    post_id = latest.link

    print("タイトル:", latest.title)

    # 初回でも投稿するように修正
    if sent.get(name) != post_id:

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

        if res.status_code == 204:
            sent[name] = post_id
            updated = True
            print("✅ 投稿成功")
        else:
            print("❌ 投稿失敗:", res.text)

    else:
        print("⏩ 新着なし（スキップ）")

# 保存
if updated:
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)
    print("💾 sent.json 更新")

print("===== END =====")
