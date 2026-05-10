import csv
import random
import os
from datetime import datetime, timedelta
from typing import List

REPOST_INTERVAL_DAYS = 2


def get_random_products(breed: str, n: int = 4, log_path: str = "logs/post_log.csv") -> List[dict]:
    """指定犬種の商品をランダムにn件取得（直近2日間の重複を避ける）"""
    csv_path = f"data/products_{breed}.csv"

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"商品リストが見つかりません: {csv_path}")

    with open(csv_path, encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    if not products:
        return []

    # 直近の投稿済み商品名を取得して重複回避
    recent_names = set()
    if os.path.exists(log_path):
        cutoff = datetime.now() - timedelta(days=REPOST_INTERVAL_DAYS)
        with open(log_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("breed") != breed:
                    continue
                try:
                    posted_at = datetime.fromisoformat(row["posted_at"])
                except (KeyError, ValueError):
                    continue
                if posted_at > cutoff:
                    for name in row.get("item_names", "").split(","):
                        if name.strip():
                            recent_names.add(name.strip())

    available = [p for p in products if p["item_name"] not in recent_names]

    # 未投稿商品がn件未満ならリセット
    if len(available) < n:
        available = products

    return random.sample(available, min(n, len(available)))
