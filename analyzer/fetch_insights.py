"""
Threads Insights取得スクリプト
- Threads APIから直接最近の投稿を取得（post_log.csvがなくても動作）
- 投稿から24時間以上経過したものを対象にInsights APIを叩く
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
from config import BREEDS, THREADS_ACCOUNTS

POST_LOG_PATH = "logs/post_log.csv"
INSIGHTS_PATH = "logs/insights.csv"
THREADS_API_BASE = "https://graph.threads.net/v1.0"
METRICS = "views,likes,replies,reposts,quotes"
MIN_AGE_HOURS = 24
FETCH_LIMIT = 50  # 各アカウントから取得する最近の投稿数


def fetch_recent_posts(account_id: str, access_token: str, breed: str) -> list[dict]:
    """Threads APIから直接最近の投稿一覧を取得する"""
    res = requests.get(
        f"{THREADS_API_BASE}/{account_id}/threads",
        params={
            "fields": "id,timestamp,media_type",
            "limit": FETCH_LIMIT,
            "access_token": access_token,
        }
    )
    if not res.ok:
        print(f"[WARN] 投稿一覧取得失敗 breed={breed}: {res.status_code}")
        return []

    posts = []
    for item in res.json().get("data", []):
        posts.append({
            "post_id": item["id"],
            "posted_at": item.get("timestamp", ""),
            "breed": breed,
            "pattern_name": "",
            "with_image": item.get("media_type", "") != "TEXT",
        })
    print(f"[INFO] {breed}: {len(posts)}件の投稿を取得")
    return posts


def load_post_log() -> list[dict]:
    if not os.path.exists(POST_LOG_PATH):
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

    # 犬種別サマリー
    breed_stats = defaultdict(lambda: {"views": 0, "likes": 0, "replies": 0, "count": 0})
    pattern_stats = defaultdict(lambda: {"views": 0, "likes": 0, "replies": 0, "count": 0})

    for row in insights_rows:
        b = row["breed"]
        breed_stats[b]["views"] += int(row.get("views") or 0)
        breed_stats[b]["likes"] += int(row.get("likes") or 0)
        breed_stats[b]["replies"] += int(row.get("replies") or 0)
        breed_stats[b]["count"] += 1

        p = row.get("pattern_name", "")
        if p:
            pattern_stats[p]["views"] += int(row.get("views") or 0)
            pattern_stats[p]["likes"] += int(row.get("likes") or 0)
            pattern_stats[p]["replies"] += int(row.get("replies") or 0)
            pattern_stats[p]["count"] += 1

    print("\n" + "=" * 60)
    print("犬種別パフォーマンス")
    print("=" * 60)
    print(f"{'犬種':<15} {'投稿数':>6} {'総views':>8} {'avg views':>10} {'likes':>7}")
    print("-" * 60)
    for breed, s in sorted(breed_stats.items(), key=lambda x: x[1]["views"] / max(x[1]["count"], 1), reverse=True):
        avg = s["views"] / max(s["count"], 1)
        print(f"{breed:<15} {s['count']:>6} {s['views']:>8} {avg:>10.1f} {s['likes']:>7}")

    if pattern_stats:
        print("\n" + "=" * 60)
        print("パターン別パフォーマンス（avg views降順）")
        print("=" * 60)
        print(f"{'パターン':<20} {'投稿数':>5} {'avg views':>10} {'likes':>7} {'replies':>8}")
        print("-" * 60)
        for pattern, s in sorted(pattern_stats.items(), key=lambda x: x[1]["views"] / max(x[1]["count"], 1), reverse=True):
            avg = s["views"] / max(s["count"], 1)
            print(f"{pattern:<20} {s['count']:>5} {avg:>10.1f} {s['likes']:>7} {s['replies']:>8}")
    print("=" * 60)


def main():
    now = datetime.now(timezone.utc)
    fetched_ids = load_fetched_ids()
    new_count = 0

    # post_log.csv からの投稿 + Threads APIから直接取得した投稿をマージ
    log_posts = load_post_log()
    log_post_ids = {p["post_id"] for p in log_posts}

    all_posts = list(log_posts)

    # 各犬種のアカウントから直接投稿一覧を取得（ログにないものを補完）
    for breed, account in THREADS_ACCOUNTS.items():
        if not account["access_token"]:
            continue
        recent = fetch_recent_posts(account["account_id"], account["access_token"], breed)
        for p in recent:
            if p["post_id"] not in log_post_ids:
                all_posts.append(p)
                log_post_ids.add(p["post_id"])
        time.sleep(1)

    print(f"\n[INFO] 対象投稿総数: {len(all_posts)}件")

    for post in all_posts:
        post_id = post.get("post_id", "").strip()
        breed = post.get("breed", "").strip()

        if not post_id or post_id in fetched_ids:
            continue

        account = THREADS_ACCOUNTS.get(breed)
        if not account:
            continue

        # 投稿時刻を確認（24時間以上経過しているか）
        posted_at_str = post.get("posted_at", "").strip()
        if posted_at_str:
            try:
                posted_at = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                age_hours = (now - posted_at).total_seconds() / 3600
                if age_hours < MIN_AGE_HOURS:
                    print(f"[SKIP] {post_id} — まだ{MIN_AGE_HOURS}時間未満 ({age_hours:.1f}h)")
                    continue
            except ValueError:
                pass

        print(f"[INFO] インサイト取得中: {post_id} (breed={breed})")
        metrics = fetch_insights_for_post(post_id, account["access_token"])
        if metrics is None:
            continue

        save_insight({
            "post_id": post_id,
            "fetched_at": now.isoformat(),
            "breed": breed,
            "pattern_name": post.get("pattern_name", ""),
            "with_image": post.get("with_image", ""),
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

    if os.path.exists(INSIGHTS_PATH):
        with open(INSIGHTS_PATH, encoding="utf-8") as f:
            all_insights = list(csv.DictReader(f))
        print_summary(all_insights)


if __name__ == "__main__":
    main()
