import requests
import feedparser
import json
import os
import re

print("===== START =====")

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# HTMLタグ除去
def clean_html(text):
    text = re.sub('<.*?>', '', text)
    text = text.replace('\n', '')
    return text.strip()

# 画像URL取得（あれば）
def get_image(entry):
    # media:content 対応
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    # summary内のimgタグ取得
    match = re.search(r'<img.*?src="(.*?)"', entry.summary)
    if match:
        return match.group(1)

    return None

# フィード読み込み
with open("feeds.json", "r", encoding="utf-8") as f:
    feeds = json.load(f)

# 送信済みデータ
try:
    with open("sent.json", "r", encoding="utf-8") as f:
        sent = json.load(f)
        print("sent.json 読み込みOK")
except:
    sent = {}
    print("sent.json 新規作成")

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

    print("タイトル:", latest.title)

    # 新着チェック
    if sent.get(name) != post_id:

        description = clean_html(latest.summary)
        image_url = get_image(latest)

        embed = {
            "title": latest.title,
            "url": latest.link,
            "description": description[:200],  # 長すぎ防止
            "color": 5814783,
            "footer": {
                "text": name
            }
        }

        # 画像があれば追加
        if image_url:
            embed["image"] = {"url": image_url}
            print("画像あり:", image_url)

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
        print("⏩ 新着なし")

# 保存
if updated:
    with open("sent.json", "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)
    print("💾 sent.json 更新")

print("===== END =====")
