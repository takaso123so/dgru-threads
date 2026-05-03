import csv
import random
import os
from datetime import datetime, timedelta
from typing import Optional


def get_random_product(breed: str, log_path: str = "logs/post_log.csv") -> Optional[dict]:
    """指定犬種の商品をランダムに1件取得（直近7日間の重複を避ける）"""
    csv_path = f"data/products_{breed}.csv"

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"商品リストが見つかりません: {csv_path}")

    with open(csv_path, encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    if not products:
        return None

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

    # 全商品が投稿済みならリセット
    if not available:
        available = products

    return random.choice(available)
