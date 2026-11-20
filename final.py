import sqlite3
import time
import requests
from bs4 import BeautifulSoup

# 1. データベースとテーブルの準備
db_name = "google_repos.db"
conn = sqlite3.connect(db_name)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS repositories")
cur.execute("""
    CREATE TABLE repositories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        language TEXT,
        stars TEXT
    )
""")
conn.commit()

# 2. スクレイピングの準備
base_url = "https://github.com/orgs/google/repositories"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

page = 1

# 3. 全ページ分のループ処理
while True:
    url = f"{base_url}?page={page}"
    print(f"{page}ページ目を取得中...")

    res = requests.get(url, headers=headers)
    time.sleep(1)  # 必須ルール：アクセスごとに1秒待機

    if res.status_code != 200:
        print("ページの取得に失敗しました。")
        break

    soup = BeautifulSoup(res.text, "html.parser")

    # リポジトリ名へのリンク（/google/リポジトリ名）をすべて探す
    repo_links = []
    for a in soup.select("a[href^='/google/']"):
        href = a.get("href", "")
        parts = href.split("/")
        if len(parts) == 3 and a.text.strip():
            repo_links.append(a)

    # リポジトリが1件も見つからなければ終了
    if not repo_links:
        print("全ページの取得が完了しました。")
        break

    # 1件ずつ情報を抜き出してDBに保存
    for link in repo_links:
        name = link.text.strip()

        # スター数のリンクを取得
        star_tag = soup.select_one(f"a[href='/google/{name}/stargazers']")
        stars = star_tag.text.strip() if star_tag else "0"

        # 主要な言語の取得（先ほど成功した「スターリンクから親ブロックを辿る」方法）
        lang = "None"
        if star_tag:
            block = star_tag.find_parent("li") or star_tag.find_parent(
                "div"
            ).find_parent("div")
            if block:
                lang_tag = block.select_one("span[class^='PrimaryLanguageName']")
                if lang_tag:
                    lang = lang_tag.text.strip()

        # DBへデータを挿入
        cur.execute(
            "INSERT INTO repositories (name, language, stars) VALUES (?, ?, ?)",
            (name, lang, stars),
        )

    conn.commit()
    page += 1

# 4. 保存したデータをSELECT文で表示
print("\n--- データベースに保存されたデータ（最初の20件） ---")
cur.execute("SELECT * FROM repositories LIMIT 20")
for row in cur.fetchall():
    print(row)

cur.execute("SELECT COUNT(*) FROM repositories")
total = cur.fetchone()[0]
print(f"\n合計保存件数: {total}件")

conn.close()