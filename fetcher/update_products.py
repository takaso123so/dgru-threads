"""
BASEカテゴリページから商品リストを更新するスクリプト
使い方: python fetcher/update_products.py
"""

import csv
import re
import time
import os
import sys

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BREEDS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_products_from_category(category_url: str) -> list[dict]:
    all_seen_urls = set()
    products = []
    page = 1

    while True:
        url = f"{category_url}?page={page}"
        print(f"  取得中: {url}")
        res = requests.get(url, headers=HEADERS, timeout=30)
        if not res.ok:
            print(f"  [WARN] {res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")

        # BASEの商品リストコンテナを絞り込む（カテゴリ本文のみ）
        # item-list-item や .item-detail などBASEのクラスを優先して探す
        containers = (
            soup.select(".item-list-item")
            or soup.select(".item-wrap")
            or soup.select("li.item")
        )

        new_on_page = []
        if containers:
            for container in containers:
                a = container.find("a", href=re.compile(r"/items/\d+"))
                if not a:
                    continue
                href = a.get("href", "")
                if href.startswith("/"):
                    item_url = "https://dgru.base.shop" + href.split("?")[0]
                else:
                    item_url = href.split("?")[0]

                if item_url in all_seen_urls:
                    continue

                # SOLD OUT除外
                container_text = container.get_text()
                if "SOLD OUT" in container_text or "売り切れ" in container_text:
                    continue

                img = a.find("img")
                raw_name = (img.get("alt", "") if img else "") or a.get_text(strip=True)
                # 価格・改行・説明文を除去して商品名のみ抽出
                name = re.split(r"¥|[\d,]+円|\n", raw_name.strip())[0].strip()
                if not name or len(name) < 2:
                    continue

                price = ""
                price_el = container.find(string=re.compile(r"[\d,]+円|¥[\d,]+"))
                if price_el:
                    price = re.sub(r"[^\d]", "", str(price_el))

                all_seen_urls.add(item_url)
                new_on_page.append({"item_name": name, "url": item_url, "price": price})
        else:
            # フォールバック: /items/数字 のリンクをページ全体から探すが、
            # 既に取得済みURLのみのページなら終了
            for a in soup.select("a[href*='/items/']"):
                href = a.get("href", "")
                if not re.search(r"/items/\d+", href):
                    continue
                if href.startswith("/"):
                    item_url = "https://dgru.base.shop" + href.split("?")[0]
                else:
                    item_url = href.split("?")[0]

                if item_url in all_seen_urls:
                    continue

                # SOLD OUT除外
                parent = a.parent
                parent_text = parent.get_text() if parent else ""
                if "SOLD OUT" in parent_text or "売り切れ" in parent_text:
                    continue

                img = a.find("img")
                raw_name = (img.get("alt", "") if img else "") or a.get_text(strip=True)
                name = re.split(r"¥|[\d,]+円|\n", raw_name.strip())[0].strip()
                if not name or len(name) < 2:
                    continue

                price = ""
                if parent:
                    price_el = parent.find(string=re.compile(r"[\d,]+円|¥[\d,]+"))
                    if price_el:
                        price = re.sub(r"[^\d]", "", str(price_el))

                all_seen_urls.add(item_url)
                new_on_page.append({"item_name": name, "url": item_url, "price": price})

        if not new_on_page:
            print(f"  → ページ{page}で新規商品なし、終了")
            break

        print(f"  → ページ{page}: {len(new_on_page)}件")
        products.extend(new_on_page)
        page += 1
        time.sleep(2)

    return products


def update_csv(breed: str, products: list[dict]):
    csv_path = f"data/products_{breed}.csv"
    os.makedirs("data", exist_ok=True)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["item_name", "url", "price"])
        writer.writeheader()
        writer.writerows(products)

    print(f"  → {csv_path} に {len(products)} 件を保存")


def main():
    target_breeds = sys.argv[1:] if len(sys.argv) > 1 else list(BREEDS.keys())

    for breed in target_breeds:
        if breed not in BREEDS:
            print(f"[ERROR] 未対応の犬種: {breed}")
            continue

        category_url = BREEDS[breed]["category_url"]
        print(f"\n[{breed}] 商品リスト取得中...")
        products = fetch_products_from_category(category_url)
        print(f"  取得件数: {len(products)} 件")

        if not products:
            print(f"  [WARN] 商品が取得できませんでした。CSVは更新しません")
            continue

        for p in products:
            print(f"    - {p['item_name']} ({p['price']}円) {p['url']}")

        update_csv(breed, products)

    print("\n完了")


if __name__ == "__main__":
    main()
