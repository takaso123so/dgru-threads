import random
import requests
from bs4 import BeautifulSoup

BASE_SEARCH_URL = "https://base.shop/search"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

PRODUCT_KEYWORDS = [
    "雑貨", "グッズ", "マグカップ", "ポーチ", "バッグ",
    "クッション", "タオル", "ステッカー", "キーホルダー",
    "スマホケース", "ぬいぐるみ", "置物", "フォトフレーム",
]


def search_breed_goods(breed_keywords: list[str], n: int = 30) -> list[dict]:
    """BASEで犬種グッズを検索してスクレイピングする"""
    results = []
    attempts = 0
    max_attempts = 5

    while len(results) < n and attempts < max_attempts:
        attempts += 1
        keyword = random.choice(breed_keywords)
        product_kw = random.choice(PRODUCT_KEYWORDS)
        query = f"{keyword} {product_kw}"

        try:
            resp = requests.get(
                BASE_SEARCH_URL,
                params={"keyword": query},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "base.shop" not in href and "thebase.in" not in href:
                    continue

                img = a.find("img")
                if not img:
                    continue

                image_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src", "")
                if not image_url or image_url.startswith("data:"):
                    continue

                results.append({
                    "image_url": image_url,
                    "source_url": href,
                    "title": img.get("alt", ""),
                    "query": query,
                })

            print(f"[INFO] BASE検索 '{query}': {len(results)}件累計")
        except Exception as e:
            print(f"[WARN] BASE検索失敗 ({query}): {e}")

    return results
