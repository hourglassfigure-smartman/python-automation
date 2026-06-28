# -*- coding: utf-8 -*-
"""
パレオな男（yuchrszk.blogspot.com）スクレイパー

仕様:
  - 収集対象 : https://yuchrszk.blogspot.com/ の最新記事（既定で5件）
  - 取得情報 : コラム要約 / 参考文献 / アクションプラン
  - 出力形式 : Markdown にまとめて books_<日付>.md として保存
  - エラー処理: 接続エラーはログに出力して終了
  - robots.txt を読み込み、禁止パスにはアクセスしない
  - リクエスト間に 1〜3 秒のランダム待機を挿入

備考:
  このブログのテーマは本文を JavaScript で描画するため、HTML を直接 GET しても
  本文が取れない。そのため Blogger が公開している JSON フィード
  （/feeds/posts/default。robots.txt で許可されている）を取得し、その中の
  本文 HTML を BeautifulSoup で解析して各項目を抽出する。

  なお、この個人ブログは Dラボのような「要約／参考文献／アクションプラン」という
  固定ラベルを持たないため、各項目は以下のヒューリスティックで抽出する:
    - コラム要約     : 本文冒頭の導入文（最初の段落群）
    - 参考文献       : 本文中の外部参照リンク（PubMed / DOI / 学術サイト等）
    - アクションプラン: 「まとめ」「ポイント」「実践」等の節に続くテキスト
  抽出できない項目は「（該当箇所が見つかりませんでした）」と明記する。
"""

from __future__ import annotations

import logging
import random
import re
import sys
import time
from datetime import date
from urllib.parse import urljoin, urlparse, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------------
BASE_URL = "https://yuchrszk.blogspot.com/"
FEED_URL = urljoin(BASE_URL, "feeds/posts/default")
MAX_POSTS = 5                      # 取得する最新記事数
USER_AGENT = "PaleoBlogScraper/1.0 (+educational use; contact: local)"
REQUEST_TIMEOUT = 20               # 秒
MIN_DELAY, MAX_DELAY = 1.0, 3.0    # リクエスト間のランダム待機（秒）

# アクションプランとみなす節見出しのキーワード
ACTION_KEYWORDS = ("まとめ", "ポイント", "実践", "結論", "対策", "コツ", "教訓", "要点")

# 実践的アドバイスを含む文を見分けるためのキーワード（見出しが無い場合のフォールバック）
ACTION_PHRASES = (
    "実践", "しよう", "したほうが", "した方が", "するとよ", "するといい",
    "おすすめ", "オススメ", "置き換え", "心がけ", "意識し", "取り入れ",
    "避け", "減らし", "増やし", "心掛け", "べきでしょう", "がよさげ", "が良さげ",
)

# 画像など参考文献に含めたくない外部ホスト／拡張子
IMAGE_HOST_HINTS = ("googleusercontent.com", "blogger.com/img")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp")

# 参考文献として扱う外部ドメインのヒント（学術・論文系を優先表示）
REFERENCE_HINTS = (
    "pubmed", "ncbi.nlm.nih.gov", "doi.org", "sciencedirect", "springer",
    "nature.com", "wiley", "tandfonline", "frontiersin", "biorxiv",
    "medrxiv", "researchgate", "jamanetwork", "bmj.com", "cell.com",
    "academic.oup.com", "sagepub", "mdpi.com", "plos",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scraper")


# ----------------------------------------------------------------------------
# robots.txt
# ----------------------------------------------------------------------------
def load_robots(base_url: str) -> RobotFileParser:
    """robots.txt を読み込んで RobotFileParser を返す。"""
    robots_url = urljoin(base_url, "/robots.txt")
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        logger.info("robots.txt を読み込みました: %s", robots_url)
    except Exception as exc:  # robots が読めない場合は安全側に倒して終了
        logger.error("robots.txt の読み込みに失敗しました: %s", exc)
        raise
    return rp


def can_fetch(rp: RobotFileParser, url: str) -> bool:
    allowed = rp.can_fetch(USER_AGENT, url)
    if not allowed:
        logger.warning("robots.txt により禁止されたパスです。スキップ: %s", url)
    return allowed


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------
def polite_sleep() -> None:
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    logger.info("待機 %.2f 秒", delay)
    time.sleep(delay)


def get_json(session: requests.Session, url: str) -> dict:
    """指定 URL を GET して JSON を返す。接続エラーはログ出力して終了。"""
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("接続エラーが発生しました（%s）: %s", url, exc)
        logger.error("処理を中断して終了します。")
        sys.exit(1)


# ----------------------------------------------------------------------------
# フィード解析
# ----------------------------------------------------------------------------
def list_recent_posts(session: requests.Session, rp: RobotFileParser,
                      limit: int) -> list[dict]:
    """一覧フィードから最新記事の (id, title, url) を取得する。"""
    list_url = f"{FEED_URL}?alt=json&max-results={limit}"
    if not can_fetch(rp, list_url):
        logger.error("一覧フィードへのアクセスが robots.txt で禁止されています。終了します。")
        sys.exit(1)

    logger.info("記事一覧フィードを取得します: %s", list_url)
    data = get_json(session, list_url)
    entries = data.get("feed", {}).get("entry", [])

    posts = []
    for e in entries:
        post_id = e["id"]["$t"].rsplit(".post-", 1)[-1]
        alt = next((l["href"] for l in e.get("link", [])
                    if l.get("rel") == "alternate"), BASE_URL)
        posts.append({
            "id": post_id,
            "title": e["title"]["$t"],
            "url": alt,
            "published": e.get("published", {}).get("$t", "")[:10],
        })
    logger.info("最新 %d 件の記事を取得対象とします。", len(posts))
    return posts


def fetch_post_content(session: requests.Session, rp: RobotFileParser,
                       post_id: str) -> str:
    """記事 ID から per-post フィードを取得し本文 HTML を返す。"""
    url = f"{FEED_URL}/{post_id}?alt=json"
    if not can_fetch(rp, url):
        return ""
    data = get_json(session, url)
    return data.get("entry", {}).get("content", {}).get("$t", "")


# ----------------------------------------------------------------------------
# 本文 HTML からの項目抽出（BeautifulSoup）
# ----------------------------------------------------------------------------
def extract_summary(soup: BeautifulSoup, max_chars: int = 320) -> str:
    """本文冒頭の導入文を要約として抽出する。"""
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) >= 30:  # 画像のみ等の空段落を飛ばす
            return text[:max_chars] + ("…" if len(text) > max_chars else "")
    # 段落が無ければ全文の先頭を使う
    text = soup.get_text(" ", strip=True)
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def extract_references(soup: BeautifulSoup) -> list[str]:
    """外部参照リンク（論文・学術サイトを優先）を抽出する。"""
    internal_host = urlparse(BASE_URL).netloc.replace("www.", "")
    refs: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        host = urlsplit(href).netloc.lower()
        if not host:
            continue
        # 内部リンク（ブログ自身）は除外
        if internal_host in host or "blogspot." in host:
            continue
        # 画像リンクは参考文献ではないので除外
        if any(h in href for h in IMAGE_HOST_HINTS):
            continue
        if urlsplit(href).path.lower().endswith(IMAGE_EXTS):
            continue
        if href in seen:
            continue
        seen.add(href)
        label = a.get_text(" ", strip=True) or "(リンク)"
        is_academic = any(h in host for h in REFERENCE_HINTS)
        refs.append((is_academic, label, href))

    # 学術系を先に、その後その他の外部リンク
    refs.sort(key=lambda r: (not r[0]))
    return [f"[{label}]({href})" for _, label, href in refs]


def extract_action_plan(soup: BeautifulSoup, max_chars: int = 400) -> str:
    """アクションプランを抽出する。

    1) 「まとめ／ポイント／実践」等を含む見出し（b/strong/h*）があればその節を採用。
    2) 見出しが無い場合は、実践的アドバイスを含む文を本文から拾うフォールバック。
    """
    # --- 1) 見出しベース ---
    for tag in soup.find_all(["b", "strong", "h1", "h2", "h3", "h4", "h5", "h6"]):
        heading = tag.get_text(" ", strip=True)
        if heading and any(kw in heading for kw in ACTION_KEYWORDS):
            collected: list[str] = []
            for sib in tag.find_all_next(string=True):
                txt = sib.strip()
                if txt and txt != heading:
                    collected.append(txt)
                if sum(len(x) for x in collected) >= max_chars:
                    break
            body = " ".join(collected)[:max_chars].strip()
            if body:
                return f"**{heading}**\n\n{body}…"

    # --- 2) フォールバック: 実践的な文を抽出 ---
    full_text = soup.get_text(" ", strip=True)
    # 句点で文に分割し、実践フレーズを含む文を採用
    sentences = re.split(r"(?<=[。！？])\s*", full_text)
    picked: list[str] = []
    for s in sentences:
        s = s.strip()
        if len(s) < 12:
            continue
        if any(p in s for p in ACTION_PHRASES):
            picked.append(s)
        if sum(len(x) for x in picked) >= max_chars:
            break
    if picked:
        body = "".join(picked)[:max_chars].strip()
        return f"（本文中の実践的記述を抽出）\n\n{body}…"
    return ""


def html_to_sections(content_html: str) -> dict:
    soup = BeautifulSoup(content_html, "lxml")
    return {
        "summary": extract_summary(soup),
        "references": extract_references(soup),
        "action_plan": extract_action_plan(soup),
    }


# ----------------------------------------------------------------------------
# Markdown 出力
# ----------------------------------------------------------------------------
NOT_FOUND = "（該当箇所が見つかりませんでした）"


def build_markdown(posts: list[dict]) -> str:
    today = date.today().isoformat()
    lines = [
        f"# パレオな男 記事まとめ（{today}）",
        "",
        f"- 収集元: {BASE_URL}",
        f"- 取得件数: {len(posts)} 件",
        f"- 生成日時: {today}",
        "",
        "---",
        "",
    ]
    for i, p in enumerate(posts, 1):
        lines.append(f"## {i}. {p['title']}")
        lines.append("")
        lines.append(f"- 公開日: {p.get('published', '不明')}")
        lines.append(f"- URL: {p['url']}")
        lines.append("")

        lines.append("### コラム要約")
        lines.append(p["summary"] or NOT_FOUND)
        lines.append("")

        lines.append("### 参考文献")
        if p["references"]:
            lines.extend(f"- {r}" for r in p["references"])
        else:
            lines.append(NOT_FOUND)
        lines.append("")

        lines.append("### アクションプラン")
        lines.append(p["action_plan"] or NOT_FOUND)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ----------------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------------
def main() -> None:
    logger.info("スクレイピングを開始します。対象: %s", BASE_URL)

    rp = load_robots(BASE_URL)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    posts = list_recent_posts(session, rp, MAX_POSTS)

    results: list[dict] = []
    for idx, post in enumerate(posts):
        polite_sleep()  # リクエスト間に 1〜3 秒待機
        logger.info("[%d/%d] 取得中: %s", idx + 1, len(posts), post["title"])
        content_html = fetch_post_content(session, rp, post["id"])
        if not content_html:
            logger.warning("本文を取得できませんでした。スキップ: %s", post["url"])
            continue
        sections = html_to_sections(content_html)
        post.update(sections)
        results.append(post)

    if not results:
        logger.error("有効な記事を取得できませんでした。終了します。")
        sys.exit(1)

    markdown = build_markdown(results)
    out_path = f"books_{date.today().isoformat()}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info("完了: %s に %d 件を書き出しました。", out_path, len(results))


if __name__ == "__main__":
    main()
