import csv
import os
import sys
from datetime import datetime

from config import BREEDS, THREADS_ACCOUNTS
from fetcher.base_fetcher import get_random_products
from fetcher.image_fetcher import get_product_image_url
from generator.content_generator import generate_post_text, generate_curation_text
from poster.threads_poster import post_to_threads, post_text_only

LOG_PATH = "logs/post_log.csv"
CURATION_LOG_PATH = "logs/curation_log.csv"


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


def log_curation_post(breed: str, images: list, post_id: str, pattern_name: str):
    os.makedirs(os.path.dirname(CURATION_LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(CURATION_LOG_PATH)
    with open(CURATION_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["posted_at", "breed", "pattern_name", "post_id", "queries", "source_url"])
        if not file_exists:
            writer.writeheader()
        queries = ",".join(dict.fromkeys(img.get("query", "") for img in images))
        source_url = images[0].get("source_url", "") if images else ""
        writer.writerow({
            "posted_at": datetime.now().isoformat(),
            "breed": breed,
            "pattern_name": pattern_name,
            "post_id": post_id,
            "queries": queries,
            "source_url": source_url,
        })



def _is_japanese(s: str) -> bool:
    return any("぀" <= c <= "鿿" for c in s)


def run(breed: str):
    """DGRU商品の投稿（既存フロー）"""
    account = THREADS_ACCOUNTS.get(breed)
    if not account:
        print(f"[ERROR] アカウント未設定: {breed}")
        return

    breed_info = BREEDS[breed]
    category_url = breed_info["category_url"]
    topic_tag = breed_info["topic_tag"]

    text, with_image, pattern_name = generate_post_text(breed=breed)
    print(f"[INFO] 生成された投稿文:\n{text}\n")
    print(f"[INFO] パターン: {pattern_name} / 画像添付: {with_image}")

    image_urls = []
    products = []
    if with_image:
        try:
            candidates = get_random_products(breed, n=8, log_path=LOG_PATH)
        except FileNotFoundError as e:
            print(f"[ERROR] 商品CSVが見つかりません（update_products.ymlを実行してください）: {e}")
            return
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

    if post_id:
        log_post(breed, products, post_id, pattern_name, with_image)


def run_curation(breed: str):
    """キュレーション投稿（BASE/minne/Creema スクレイピング + Claude Vision検証）"""
    account = THREADS_ACCOUNTS.get(breed)
    if not account:
        print(f"[ERROR] アカウント未設定: {breed}")
        return

    breed_info = BREEDS[breed]
    breed_ja = breed_info["name_ja"]
    topic_tag = breed_info["topic_tag"]
    breed_keywords = [kw for kw in breed_info["keywords"] if _is_japanese(kw)]

    if not breed_keywords:
        print(f"[ERROR] 日本語キーワードが見つかりません: {breed}")
        return

    from researcher.base_searcher import search_breed_goods as base_search
    from researcher.minne_searcher import search_breed_goods as minne_search
    from researcher.creema_searcher import search_breed_goods as creema_search
    from researcher.google_searcher import group_by_shop
    from researcher.image_validator import get_valid_images

    # 1. BASE・minne・Creema から並行して候補画像を収集
    candidates = []
    for name, fn in [("BASE", base_search), ("minne", minne_search), ("Creema", creema_search)]:
        try:
            items = fn(breed_keywords, n=15)
            print(f"[INFO] {name}検索完了: {len(items)}件")
            candidates.extend(items)
        except Exception as e:
            print(f"[WARN] {name}検索失敗: {e}")

    print(f"[INFO] 候補合計: {len(candidates)}件")
    if not candidates:
        print("[ERROR] 候補画像が取得できませんでした")
        return

    # 2. ショップ単位でグループ化
    shop_groups = group_by_shop(candidates)
    print(f"[INFO] ショップ数（2件以上）: {len(shop_groups)}")
    if not shop_groups:
        print("[ERROR] 2件以上の画像を持つショップが見つかりませんでした")
        return

    # 3. 画像数の多いショップから順にバリデーション → 2枚以上通過したショップを採用
    valid_images = []
    shop_url = ""
    for domain, group in sorted(shop_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"[INFO] ショップ検証中: {domain} ({len(group)}件)")
        validated = get_valid_images(group, breed_ja, max_images=4)
        if len(validated) >= 2:
            valid_images = validated
            shop_url = valid_images[0]["source_url"]
            print(f"[INFO] ショップ採用: {domain} / 有効画像: {len(valid_images)}枚")
            break

    if len(valid_images) < 2:
        print("[ERROR] 条件を満たすショップが見つかりませんでした")
        return

    image_urls = [img["image_url"] for img in valid_images]
    print(f"[INFO] 返信URL: {shop_url}")

    # 4. 投稿文生成
    text, pattern_name = generate_curation_text(breed=breed)
    print(f"[INFO] キュレーション投稿文:\n{text}\n")
    print(f"[INFO] パターン: {pattern_name}")

    # 5. 投稿
    post_id = post_to_threads(
        account_id=account["account_id"],
        access_token=account["access_token"],
        image_urls=image_urls,
        text=text,
        reply_text=shop_url,
        topic_tag=topic_tag,
    )

    # 6. ログ記録
    if post_id:
        log_curation_post(breed, valid_images, post_id, pattern_name)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    post_type = sys.argv[2] if len(sys.argv) > 2 else "all"

    breeds_to_run = list(BREEDS.keys()) if target == "all" else [target]
    for b in breeds_to_run:
        print(f"\n===== {b} ({post_type}) =====")
        if post_type in ("dgru", "all"):
            print(f"--- DGRU投稿 ---")
            run(b)
        if post_type in ("curation", "all"):
            print(f"--- キュレーション投稿 ---")
            run_curation(b)
