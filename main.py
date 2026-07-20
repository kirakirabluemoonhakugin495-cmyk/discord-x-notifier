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


# -----------------------
# 履歴
# -----------------------

def load_history():

    if os.path.exists(HISTORY_FILE):
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    return {}



def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )



# -----------------------
# 画像取得
# -----------------------

def get_image(img_tag):

    if not img_tag:
        return None

    img = (
        img_tag.get("src")
        or img_tag.get("data-src")
        or img_tag.get("data-original")
    )


    if not img:
        return None


    if img.startswith("//"):
        img = "https:" + img


    if not img.startswith("http"):
        return None


    return img



# -----------------------
# ぽけらく一覧取得
# -----------------------

def fetch_event_articles(url):

    res = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )


    articles = []


    for item in soup.select("article")[:10]:

        title_tag = item.select_one(
            "h2,h3"
        )

        link_tag = item.select_one(
            "a"
        )


        if not title_tag or not link_tag:
            continue


        title = title_tag.text.strip()

        link = link_tag.get(
            "href"
        )


        if not link:
            continue


        img = get_image(
            item.select_one("img")
        )


        articles.append(
            {
                "title": title,
                "link": link,
                "img": img
            }
        )


    return articles



# -----------------------
# フィールドリサーチ差分
# -----------------------

def fetch_page_diff(url, history):

    res = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )


    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )


    # 不要部分削除
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer"
        ]
    ):
        tag.decompose()



    text = soup.get_text(
        "\n"
    )


    text = "\n".join(
        x.strip()
        for x in text.splitlines()
        if x.strip()
    )


    old = history.get(
        "field_text",
        ""
    )


    diff = difflib.unified_diff(
        old.splitlines(),
        text.splitlines(),
        lineterm=""
    )


    changes = []


    for line in diff:

        if (
            line.startswith("+")
            and not line.startswith("+++")
        ):
            changes.append(
                line[1:]
            )


    history["field_text"] = text


    img = get_image(
        soup.select_one("img")
    )


    return changes, img



# -----------------------
# Discord送信
# -----------------------

def send_article_embed(
        name,
        articles
):

    embeds = []


    for art in articles:

        embed = {
            "title": art["title"],
            "url": art["link"],
            "color": 5814783
        }


        if art.get("img"):

            embed["image"] = {
                "url": art["img"]
            }


        embeds.append(
            embed
        )


    data = {
        "content":
            f"📢 **{name} 更新情報**"
    }


    if embeds:

        data["embeds"] = embeds[:10]


    res = requests.post(
        WEBHOOK_URL,
        json=data
    )


    print(
        "送信:",
        res.status_code
    )



def send_diff_embed(
        changes,
        img
):

    if not changes:
        return


    description = ""


    for c in changes[:20]:

        description += (
            f"＋ {c}\n"
        )


    embed = {

        "title":
            "🆕 フィールドリサーチ更新",

        "description":
            description[:4000],

        "color":
            65280
    }


    if img:

        embed["image"] = {
            "url": img
        }


    data = {
        "embeds":[
            embed
        ]
    }


    res = requests.post(
        WEBHOOK_URL,
        json=data
    )


    print(
        "差分送信:",
        res.status_code
    )



# -----------------------
# メイン
# -----------------------

def main():

    print(
        "===== START ====="
    )


    history = load_history()



    # イベント
    print(
        "\n--- ぽけらくイベント ---"
    )


    articles = fetch_event_articles(
        SITES["ぽけらく(イベント)"]
    )


    old = history.get(
        "events",
        []
    )


    new_articles = [

        a for a in articles

        if a["title"] not in old

    ]


    if new_articles:

        print(
            len(new_articles),
            "件更新"
        )


        send_article_embed(
            "ぽけらく(イベント)",
            new_articles
        )


    else:

        print(
            "更新なし"
        )


    history["events"] = [
        a["title"]
        for a in articles[:20]
    ]



    # フィールドリサーチ

    print(
        "\n--- フィールドリサーチ ---"
    )


    changes, img = fetch_page_diff(
        SITES["フィールドリサーチ"],
        history
    )


    if changes:

        print(
            "差分あり:",
            len(changes)
        )


        send_diff_embed(
            changes,
            img
        )


    else:

        print(
            "変更なし"
        )



    save_history(
        history
    )


    print(
        "===== END ====="
    )



if __name__ == "__main__":

    main()
