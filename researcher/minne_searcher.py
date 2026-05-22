import json
import random
import requests
from bs4 import BeautifulSoup

MINNE_SEARCH_URL = "https://minne.com/category/saleonly"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

PRODUCT_KEYWORDS = [
    "雑貨", "グッズ", "マグカップ", "ポーチ", "バッグ",
    "クッション", "タオル", "ステッカー", "キーホルダー",
    "スマホケース", "ぬいぐるみ", "置物", "フォトフレーム",
]


def search_breed_goods(breed_keywords: list[str], n: int = 20) -> list[dict]:
    """minneで犬種グッズを検索してスクレイピングする（JSON-LD使用）"""
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
                MINNE_SEARCH_URL,
                params={"q": query, "input_method": ""},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                except (json.JSONDecodeError, TypeError):
                    continue
                if data.get("@type") != "ItemList":
                    continue
                for item in data.get("itemListElement", []):
                    image_url = item.get("image", {}).get("contentUrl", "")
                    source_url = item.get("url", "")
                    title = item.get("name", "")
                    if not image_url or not source_url:
                        continue
                    results.append({
                        "image_url": image_url,
                        "source_url": source_url,
                        "title": title,
                        "query": query,
                    })

            print(f"[INFO] minne検索 '{query}': {len(results)}件累計")
        except Exception as e:
            print(f"[WARN] minne検索失敗 ({query}): {e}")

    return results
