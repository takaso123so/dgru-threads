import csv
import os
import sys
from datetime import datetime

from config import THREADS_ACCOUNTS
from fetcher.base_fetcher import get_random_product
from fetcher.image_fetcher import get_product_image_url
from generator.content_generator import generate_post_text
from poster.threads_poster import post_to_threads

LOG_PATH = "logs/post_log.csv"


def log_post(breed: str, item_name: str, url: str, post_id: str):
    """投稿履歴をCSVに記録する"""
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["posted_at", "breed", "item_name", "url", "post_id"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "posted_at": datetime.now().isoformat(),
            "breed": breed,
            "item_name": item_name,
            "url": url,
            "post_id": post_id
        })


def run(breed: str):
    account = THREADS_ACCOUNTS.get(breed)
    if not account:
        print(f"[ERROR] アカウント未設定: {breed}")
        return

    # 1. 商品をランダム取得
    product = get_random_product(breed, LOG_PATH)
    if not product:
        print("[ERROR] 投稿可能な商品がありません")
        return
    print(f"[INFO] 商品選定: {product['item_name']}")

    # 2. 画像URL取得
    image_url = get_product_image_url(product["url"])
    if not image_url:
        print(f"[ERROR] 画像取得失敗: {product['url']}")
        return
    print(f"[INFO] 画像URL取得: {image_url}")

    # 3. 投稿文生成
    text = generate_post_text(
        item_name=product["item_name"],
        price=int(product["price"]),
        breed=breed
    )
    print(f"[INFO] 生成された投稿文:\n{text}\n")

    # 4. Threadsに投稿
    post_id = post_to_threads(
        account_id=account["account_id"],
        access_token=account["access_token"],
        image_url=image_url,
        text=text,
        product_url=product.get("url", "")
    )
    print(f"[INFO] 投稿完了: post_id={post_id}")

    # 5. ログ記録
    log_post(breed, product["item_name"], product["url"], post_id)


if __name__ == "__main__":
    breed = sys.argv[1] if len(sys.argv) > 1 else "shiba"
    run(breed)
