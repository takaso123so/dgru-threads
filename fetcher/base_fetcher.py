import csv
import random
import os
from datetime import datetime, timedelta
from typing import List


def get_random_products(breed: str, n: int = 4, log_path: str = "logs/post_log.csv") -> List[dict]:
    """指定犬種の商品をランダムにn件取得（直近7日間の重複を避ける）"""
    csv_path = f"data/products_{breed}.csv"

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"商品リストが見つかりません: {csv_path}")

    with open(csv_path, encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    if not products:
        return []

    # 直近の投稿済みURLを取得
    recent_urls = set()
    if os.path.exists(log_path):
        cutoff = datetime.now() - timedelta(days=7)
        with open(log_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["breed"] == breed:
                    posted_at = datetime.fromisoformat(row["posted_at"])
                    if posted_at > cutoff:
                        recent_urls.add(row["url"])

    available = [p for p in products if p["url"] not in recent_urls]

    # 未投稿商品がn件未満ならリセット
    if len(available) < n:
        available = products

    return random.sample(available, min(n, len(available)))
