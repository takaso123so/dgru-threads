import os
from typing import Optional

import tweepy

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")


def _get_client(access_token: str, access_token_secret: str) -> tweepy.Client:
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )


def post_to_twitter(
    access_token: str,
    access_token_secret: str,
    image_urls: list[str],
    text: str,
    reply_text: str = "",
) -> Optional[str]:
    """テキストのみツイートを投稿し、返信にURLを添える（画像は現在未対応）"""
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        print("[ERROR] TWITTER_API_KEY / TWITTER_API_SECRET が未設定")
        return None

    client = _get_client(access_token, access_token_secret)

    # ツイート投稿（テキストのみ）
    try:
        resp = client.create_tweet(text=text)
        tweet_id = str(resp.data["id"])
        print(f"[INFO] Twitter 投稿完了: tweet_id={tweet_id}")
    except Exception as e:
        print(f"[ERROR] Twitter 投稿失敗: {e}")
        return None

    # 返信にURL
    if reply_text and tweet_id:
        try:
            client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            print(f"[INFO] Twitter 返信投稿完了")
        except Exception as e:
            print(f"[WARN] Twitter 返信失敗: {e}")

    return tweet_id
