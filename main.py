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



# =========================
# 履歴
# =========================

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



# =========================
# 画像取得
# =========================

def get_article_image(url):

    try:

        res = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )


        soup = BeautifulSoup(
            res.text,
            "html.parser"
        )


        # OGP画像
        og = soup.select_one(
            'meta[property="og:image"]'
        )


        if og and og.get("content"):

            img = og["content"]


            if img.startswith("//"):
                img = "https:" + img


            if img.startswith("http"):
                return img



        # Twitterカード画像
        tw = soup.select_one(
            'meta[name="twitter:image"]'
        )


        if tw and tw.get("content"):

            img = tw["content"]


            if img.startswith("//"):
                img = "https:" + img


            if img.startswith("http"):
                return img



    except Exception as e:

        print(
            "画像取得失敗:",
            e
        )


    return None




# =========================
# イベント記事取得
# =========================

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



        img = get_article_image(
            link
        )



        articles.append(
            {
                "title": title,
                "link": link,
                "img": img
            }
        )


    return articles




# =========================
# 差分取得
# =========================

def fetch_field_diff(
        url,
        history
):

    res = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )


    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )


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


    img = get_article_image(
        url
    )


    return changes, img




# =========================
# Discord送信
# =========================

def send_articles(
        name,
        articles
):

    embeds = []


    for art in articles:


        embed = {

            "title":
                art["title"],

            "url":
                art["link"],

            "color":
                5814783
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




def send_field_update(
        changes,
        img
):

    description = ""


    for c in changes[:30]:

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



    res = requests.post(
        WEBHOOK_URL,
        json={
            "embeds":[embed]
        }
    )


    print(
        "差分送信:",
        res.status_code
    )



# =========================
# メイン
# =========================

def main():

    print(
        "===== START ====="
    )


    history = load_history()



    # -----------------
    # イベント
    # -----------------

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


        send_articles(
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





    # -----------------
    # フィールド
    # -----------------

    print(
        "\n--- フィールドリサーチ ---"
    )


    changes, img = fetch_field_diff(
        SITES["フィールドリサーチ"],
        history
    )



    if changes:

        print(
            "差分あり:",
            len(changes)
        )


        send_field_update(
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
