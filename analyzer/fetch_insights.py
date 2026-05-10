"""
Threads Insights取得スクリプト
- logs/post_log.csv から投稿済みレコードを読み込む
- 投稿から24時間以上経過したものを対象にThreads Insights APIを叩く
- 結果を logs/insights.csv に保存
- パターン別パフォーマンスサマリーを出力
"""

import csv
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import THREADS_ACCOUNTS

POST_LOG_PATH = "logs/post_log.csv"
INSIGHTS_PATH = "logs/insights.csv"
THREADS_API_BASE = "https://graph.threads.net/v1.0"
METRICS = "views,likes,replies,reposts,quotes"
MIN_AGE_HOURS = 24


def load_post_log() -> list[dict]:
    if not os.path.exists(POST_LOG_PATH):
        print(f"[INFO] {POST_LOG_PATH} が存在しません")
        return []
    with open(POST_LOG_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_fetched_ids() -> set[str]:
    if not os.path.exists(INSIGHTS_PATH):
        return set()
    with open(INSIGHTS_PATH, encoding="utf-8") as f:
        return {row["post_id"] for row in csv.DictReader(f)}


def save_insight(row: dict):
    os.makedirs(os.path.dirname(INSIGHTS_PATH), exist_ok=True)
    file_exists = os.path.exists(INSIGHTS_PATH)
    with open(INSIGHTS_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "fetched_at", "breed", "pattern_name", "with_image",
            "views", "likes", "replies", "reposts", "quotes",
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def fetch_insights_for_post(post_id: str, access_token: str) -> dict | None:
    url = f"{THREADS_API_BASE}/{post_id}/insights"
    res = requests.get(url, params={"metric": METRICS, "access_token": access_token})
    if not res.ok:
        print(f"[WARN] insights取得失敗 post_id={post_id}: {res.status_code}")
        return None

    data = res.json().get("data", [])
    result = {}
    for item in data:
        name = item.get("name")
        values = item.get("values", [])
        result[name] = values[0]["value"] if values else item.get("total_value", {}).get("value", 0)
    return result


def print_summary(insights_rows: list[dict]):
    if not insights_rows:
        print("\n[INFO] インサイトデータがまだありません")
        return

    pattern_stats = defaultdict(lambda: {"views": 0, "likes": 0, "replies": 0, "count": 0})
    for row in insights_rows:
        p = row["pattern_name"]
        pattern_stats[p]["views"] += int(row.get("views") or 0)
        pattern_stats[p]["likes"] += int(row.get("likes") or 0)
        pattern_stats[p]["replies"] += int(row.get("replies") or 0)
        pattern_stats[p]["count"] += 1

    print("\n" + "=" * 60)
    print("パターン別パフォーマンス（累計）")
    print("=" * 60)
    sorted_patterns = sorted(
        pattern_stats.items(),
        key=lambda x: x[1]["views"] / max(x[1]["count"], 1),
        reverse=True,
    )
    print(f"{'パターン':<20} {'投稿数':>5} {'総views':>8} {'avg views':>10} {'likes':>7} {'replies':>8}")
    print("-" * 60)
    for pattern, stats in sorted_patterns:
        avg_views = stats["views"] / max(stats["count"], 1)
        print(f"{pattern:<20} {stats['count']:>5} {stats['views']:>8} {avg_views:>10.1f} {stats['likes']:>7} {stats['replies']:>8}")
    print("=" * 60)


def main():
    posts = load_post_log()
    fetched_ids = load_fetched_ids()
    now = datetime.now(timezone.utc)
    new_count = 0

    for post in posts:
        post_id = post.get("post_id", "").strip()
        breed = post.get("breed", "").strip()
        pattern_name = post.get("pattern_name", "").strip()
        with_image = post.get("with_image", "").strip()
        posted_at_str = post.get("posted_at", "").strip()

        if not post_id or post_id in fetched_ids:
            continue

        try:
            posted_at = datetime.fromisoformat(posted_at_str)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"[WARN] 日付パース失敗: {posted_at_str}")
            continue

        age_hours = (now - posted_at).total_seconds() / 3600
        if age_hours < MIN_AGE_HOURS:
            print(f"[SKIP] {post_id} — まだ{MIN_AGE_HOURS}時間経過していません ({age_hours:.1f}h)")
            continue

        account = THREADS_ACCOUNTS.get(breed)
        if not account:
            print(f"[WARN] アカウント未設定: breed={breed}")
            continue

        print(f"[INFO] インサイト取得中: {post_id} (breed={breed}, pattern={pattern_name})")
        metrics = fetch_insights_for_post(post_id, account["access_token"])
        if metrics is None:
            continue

        save_insight({
            "post_id": post_id,
            "fetched_at": now.isoformat(),
            "breed": breed,
            "pattern_name": pattern_name,
            "with_image": with_image,
            "views": metrics.get("views", 0),
            "likes": metrics.get("likes", 0),
            "replies": metrics.get("replies", 0),
            "reposts": metrics.get("reposts", 0),
            "quotes": metrics.get("quotes", 0),
        })
        fetched_ids.add(post_id)
        new_count += 1
        time.sleep(1)

    print(f"\n[INFO] 新規取得: {new_count}件")

    # 全データ読み込んでサマリー表示
    if os.path.exists(INSIGHTS_PATH):
        with open(INSIGHTS_PATH, encoding="utf-8") as f:
            all_insights = list(csv.DictReader(f))
        print_summary(all_insights)


if __name__ == "__main__":
    main()
