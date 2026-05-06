import csv
import os
import sys
from datetime import datetime

from config import THREADS_ACCOUNTS
from fetcher.base_fetcher import get_random_products
from fetcher.image_fetcher import get_product_image_url
from generator.content_generator import generate_post_text
from poster.threads_poster import post_to_threads, post_text_only

LOG_PATH = "logs/post_log.csv"
CATEGORY_URLS = {
    "shiba": "https://dgru.base.shop/categories/7018493",
    "schnauzer": "https://dgru.base.shop/categories/6987466",
}
TOPIC_TAGS = {
    "shiba": "柴犬",
    "schnauzer": "シュナウザー",
}


def log_post(breed: str, products: list, post_id: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["posted_at", "breed", "item_name", "url", "post_id"])
        if not file_exists:
            writer.writeheader()
        for p in products:
            writer.writerow({
                "posted_at": datetime.now().isoformat(),
                "breed": breed,
                "item_name": p["item_name"],
                "url": p["url"],
                "post_id": post_id,
            })


def run(breed: str):
    account = THREADS_ACCOUNTS.get(breed)
    if not account:
        print(f"[ERROR] アカウント未設定: {breed}")
        return

    # 1. 商品を4件ランダム取得
    products = get_random_products(breed, n=4, log_path=LOG_PATH)
    if not products:
        print("[ERROR] 投稿可能な商品がありません")
        return
    print(f"[INFO] 商品選定: {[p['item_name'] for p in products]}")

    # 2. 投稿文生成（画像の要否を先に判定）
    text, with_image = generate_post_text(breed=breed)
    print(f"[INFO] 生成された投稿文:\n{text}\n")
    print(f"[INFO] 画像添付: {with_image}")

    # 3. 画像が必要な場合のみ取得
    image_urls = []
    if with_image:
        for p in products:
            url = get_product_image_url(p["url"])
            if url:
                image_urls.append(url)
                print(f"[INFO] 画像取得: {url}")
            else:
                print(f"[WARN] 画像取得失敗: {p['url']}")

        if len(image_urls) < 2:
            print("[ERROR] 画像が2枚未満のため投稿をスキップ")
            return

    # 4. 投稿（画像あり or テキストのみ）
    if with_image:
        post_id = post_to_threads(
            account_id=account["account_id"],
            access_token=account["access_token"],
            image_urls=image_urls,
            text=text,
            reply_text=CATEGORY_URLS.get(breed, ""),
            topic_tag=TOPIC_TAGS.get(breed, ""),
        )
    else:
        print("[INFO] テキストのみ投稿")
        post_id = post_text_only(
            account_id=account["account_id"],
            access_token=account["access_token"],
            text=text,
        )

    # 5. ログ記録
    if post_id:
        log_post(breed, products, post_id)


if __name__ == "__main__":
    breed = sys.argv[1] if len(sys.argv) > 1 else "shiba"
    run(breed)
