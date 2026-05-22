import os
import random
from collections import defaultdict
from urllib.parse import urlparse

import requests


class QuotaExceededError(Exception):
    """Google CSE の無料クォータ超過"""

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")

PRODUCT_KEYWORDS = [
    "雑貨", "グッズ", "マグカップ", "ポーチ", "バッグ",
    "クッション", "タオル", "ステッカー", "キーホルダー",
    "スマホケース", "ぬいぐるみ", "置物", "フォトフレーム",
]


def search_breed_goods(breed_keywords: list[str], n: int = 20) -> list[dict]:
    """犬種グッズをGoogle Custom Search APIで画像検索する"""
    results = []
    attempts = 0
    max_attempts = 5

    while len(results) < n and attempts < max_attempts:
        attempts += 1
        keyword = random.choice(breed_keywords)
        product_kw = random.choice(PRODUCT_KEYWORDS)
        query = f"{keyword} {product_kw}"

        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "searchType": "image",
            "num": 10,
            "safe": "active",
            "imgType": "photo",
            "imgSize": "medium",
        }

        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10,
            )
            if resp.status_code == 429:
                raise QuotaExceededError("Google CSE 無料クォータ超過")
            data = resp.json()
            if "error" in data:
                reason = data["error"].get("status", "")
                if reason in ("RESOURCE_EXHAUSTED", "QUOTA_EXCEEDED"):
                    raise QuotaExceededError("Google CSE 無料クォータ超過")
            resp.raise_for_status()
            items = data.get("items", [])
            for item in items:
                image_url = item.get("link", "")
                source_url = item.get("image", {}).get("contextLink", "")
                if image_url and source_url:
                    results.append({
                        "image_url": image_url,
                        "source_url": source_url,
                        "title": item.get("title", ""),
                        "query": query,
                    })
            print(f"[INFO] Google検索 '{query}': {len(items)}件取得")
        except QuotaExceededError:
            raise
        except Exception as e:
            print(f"[WARN] Google検索失敗 ({query}): {e}")

    return results


def group_by_shop(candidates: list[dict]) -> dict[str, list[dict]]:
    """ソースURLのドメインでグループ化し、2件以上あるショップのみ返す"""
    groups = defaultdict(list)
    for c in candidates:
        domain = urlparse(c["source_url"]).netloc
        groups[domain].append(c)
    return {k: v for k, v in groups.items() if len(v) >= 2}
