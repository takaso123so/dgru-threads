import csv
import os
import sys
from datetime import datetime

from config import BREEDS, THREADS_ACCOUNTS
from fetcher.base_fetcher import get_random_products
from fetcher.image_fetcher import get_product_image_url
from generator.content_generator import generate_post_text
from poster.threads_poster import post_to_threads, post_text_only

LOG_PATH = "logs/post_log.csv"


def log_post(breed: str, products: list, post_id: str, pattern_name: str = "", with_image: bool = True):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["posted_at", "breed", "pattern_name", "with_image", "post_id", "item_names"])
        if not file_exists:
            writer.writeheader()
        item_names = ",".join(p["item_name"] for p in products) if products else ""
        writer.writerow({
            "posted_at": datetime.now().isoformat(),
            "breed": breed,
            "pattern_name": pattern_name,
            "with_image": with_image,
            "post_id": post_id,
            "item_names": item_names,
        })


def run(breed: str):
    account = THREADS_ACCOUNTS.get(breed)
    if not account:
        print(f"[ERROR] アカウント未設定: {breed}")
        return

    breed_info = BREEDS[breed]
    category_url = breed_info["category_url"]
    topic_tag = breed_info["topic_tag"]

    # 1. 投稿文生成（画像の要否を先に判定）
    text, with_image, pattern_name = generate_post_text(breed=breed)
    print(f"[INFO] 生成された投稿文:\n{text}\n")
    print(f"[INFO] パターン: {pattern_name} / 画像添付: {with_image}")

    # 2. 商品・画像取得（画像が必要な場合は多めに候補を取得して4枚確保）
    image_urls = []
    products = []
    if with_image:
        candidates = get_random_products(breed, n=8, log_path=LOG_PATH)
        if not candidates:
            print("[ERROR] 投稿可能な商品がありません")
            return
        for p in candidates:
            url = get_product_image_url(p["url"])
            if url:
                image_urls.append(url)
                products.append(p)
                print(f"[INFO] 画像取得: {url}")
                if len(image_urls) == 4:
                    break
            else:
                print(f"[WARN] 画像取得失敗: {p['url']}")

        if len(image_urls) < 2:
            print("[ERROR] 画像が2枚未満のため投稿をスキップ")
            return
        print(f"[INFO] 商品選定: {[p['item_name'] for p in products]}")
    else:
        products = get_random_products(breed, n=4, log_path=LOG_PATH)
        if not products:
            print("[ERROR] 投稿可能な商品がありません")
            return

    # 3. 投稿（画像あり or テキストのみ）
    if with_image:
        post_id = post_to_threads(
            account_id=account["account_id"],
            access_token=account["access_token"],
            image_urls=image_urls,
            text=text,
            reply_text=category_url,
            topic_tag=topic_tag,
        )
    else:
        print("[INFO] テキストのみ投稿")
        post_id = post_text_only(
            account_id=account["account_id"],
            access_token=account["access_token"],
            text=text,
        )

    # 4. ログ記録
    if post_id:
        log_post(breed, products, post_id, pattern_name, with_image)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    breeds_to_run = list(BREEDS.keys()) if target == "all" else [target]
    for b in breeds_to_run:
        print(f"\n===== {b} =====")
        run(b)
