import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_FEEDS = [
    "https://www.nhk.or.jp/rss/news/cat0.xml",  # NHK 主要
    "https://www.nhk.or.jp/rss/news/cat4.xml",  # NHK 暮らし・食
    "https://www.nhk.or.jp/rss/news/cat6.xml",  # NHK 科学・文化
]

EXCLUDE_KEYWORDS = [
    "死亡", "死去", "訃報", "逮捕", "殺", "事件", "事故",
    "地震", "台風", "津波", "土砂", "災害", "洪水",
    "戦争", "紛争", "攻撃", "爆発", "爆撃", "侵攻",
    "火災", "犯罪", "裁判", "起訴", "捜査", "摘発",
    "選挙", "政府", "与党", "野党", "国会", "首相", "大臣", "議員",
    "差別", "虐待", "自殺", "テロ", "不審死",
    "感染", "死者", "重傷", "行方不明",
]


def _is_safe(title: str) -> bool:
    return not any(kw in title for kw in EXCLUDE_KEYWORDS)


def fetch_trend_topics(n: int = 5) -> str:
    """RSSから安全なニュース見出しをn件取得してテキストで返す。失敗時は季節の話題を返す。"""
    titles = []
    for url in RSS_FEEDS:
        if len(titles) >= n:
            break
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                tree = ET.parse(res)
            root = tree.getroot()
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is None or not title_el.text:
                    continue
                title = title_el.text.strip()
                if _is_safe(title) and title not in titles:
                    titles.append(title)
                if len(titles) >= n:
                    break
        except Exception as e:
            print(f"[WARN] RSS取得失敗 ({url}): {e}")

    if not titles:
        month = datetime.now().month
        return f"{month}月の季節の変わり目、気温や天気の話題"

    return "\n".join(f"・{t}" for t in titles)
