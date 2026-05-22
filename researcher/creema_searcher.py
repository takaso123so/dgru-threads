import json
import random
import re
import requests

CREEMA_SEARCH_URL = "https://www.creema.jp/listing"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

PRODUCT_KEYWORDS = [
    "雑貨", "グッズ", "マグカップ", "ポーチ", "バッグ",
    "クッション", "タオル", "ステッカー", "キーホルダー",
    "スマホケース", "ぬいぐるみ", "置物", "フォトフレーム",
]


def search_breed_goods(breed_keywords: list[str], n: int = 20) -> list[dict]:
    """Creemaで犬種グッズを検索してスクレイピングする（JavaScript埋め込みデータ使用）"""
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
                CREEMA_SEARCH_URL,
                params={"q": query},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()

            # Extract items array from embedded JS: Creema.data.SearchResult = { items: [...] }
            match = re.search(r'items:\s*(\[.*?\])(?=,\s*\n)', resp.text, re.DOTALL)
            if not match:
                print(f"[WARN] Creema: items配列が見つかりません ({query})")
                continue

            items = json.loads(match.group(1))
            for item in items:
                image_url = item.get("image", "")
                item_id = item.get("item_id")
                title = item.get("title", "")
                if not image_url or not item_id:
                    continue
                results.append({
                    "image_url": image_url,
                    "source_url": f"https://www.creema.jp/item/{item_id}",
                    "title": title,
                    "query": query,
                })

            print(f"[INFO] Creema検索 '{query}': {len(results)}件累計")
        except Exception as e:
            print(f"[WARN] Creema検索失敗 ({query}): {e}")

    return results
