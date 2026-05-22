"""
キュレーション投稿のドライランテスト（Threadsへの投稿なし）
使い方:
  GOOGLE_API_KEY=xxx GOOGLE_CSE_ID=xxx CLAUDE_API_KEY=xxx python3 test_curation.py shiba
"""

import sys

from config import BREEDS
from researcher.google_searcher import search_breed_goods, group_by_shop, QuotaExceededError
from researcher.base_searcher import search_breed_goods as base_search
from researcher.image_validator import get_valid_images
from generator.content_generator import generate_curation_text


def _is_japanese(s: str) -> bool:
    return any("぀" <= c <= "鿿" for c in s)


def test(breed: str = "shiba"):
    breed_info = BREEDS.get(breed)
    if not breed_info:
        print(f"[ERROR] 未定義の犬種: {breed}")
        print(f"利用可能: {list(BREEDS.keys())}")
        return

    breed_ja = breed_info["name_ja"]
    breed_keywords = [kw for kw in breed_info["keywords"] if _is_japanese(kw)]
    print(f"\n=== テスト開始: {breed_ja} ===")
    print(f"検索キーワード: {breed_keywords}\n")

    # 1. 画像検索
    print("--- Step 1: 画像検索 ---")
    try:
        candidates = search_breed_goods(breed_keywords, n=30)
        print(f"Google検索結果: {len(candidates)}件\n")
    except QuotaExceededError:
        print("[WARN] Google CSEクォータ超過 → BASEにフォールバック")
        candidates = base_search(breed_keywords, n=30)
        print(f"BASE検索結果: {len(candidates)}件\n")

    if not candidates:
        print("[ERROR] 候補が0件でした")
        return

    # 2. ショップごとにグループ化
    print("--- Step 2: ショップグループ化 ---")
    shop_groups = group_by_shop(candidates)
    print(f"2件以上のショップ数: {len(shop_groups)}")
    for domain, items in sorted(shop_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {domain}: {len(items)}件")
    print()

    if not shop_groups:
        print("[ERROR] グループ化できるショップがありませんでした")
        return

    # 3. Claude Vision で画像検証
    print("--- Step 3: Claude Vision 画像検証 ---")
    valid_images = []
    selected_domain = ""
    for domain, group in sorted(shop_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\nショップ検証中: {domain}")
        validated = get_valid_images(group, breed_ja, max_images=4)
        if len(validated) >= 2:
            valid_images = validated
            selected_domain = domain
            break

    if len(valid_images) < 2:
        print("\n[ERROR] 条件を満たすショップが見つかりませんでした")
        return

    print(f"\n採用ショップ: {selected_domain}")
    print(f"有効画像数: {len(valid_images)}枚")
    for i, img in enumerate(valid_images, 1):
        print(f"  [{i}] {img['title'][:50]}")
        print(f"       画像URL: {img['image_url'][:80]}")
        print(f"       ソース:  {img['source_url'][:80]}")

    # 4. 投稿文生成
    print("\n--- Step 4: 投稿文生成 ---")
    text, pattern_name = generate_curation_text(breed=breed)
    print(f"パターン: {pattern_name}")
    print(f"投稿文:\n{text}")
    print("\n=== テスト完了（Threadsへの投稿なし） ===")


if __name__ == "__main__":
    breed = sys.argv[1] if len(sys.argv) > 1 else "shiba"
    test(breed)
