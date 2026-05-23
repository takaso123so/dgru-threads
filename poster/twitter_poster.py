import os
from io import BytesIO
from typing import Optional

import requests
import tweepy

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")


def _get_clients(access_token: str, access_token_secret: str) -> tuple:
    """v1.1 API（メディアアップロード用）とv2 Client（ツイート投稿用）を返す"""
    auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return api_v1, client_v2


def _upload_media(api_v1: tweepy.API, image_url: str) -> Optional[int]:
    """画像URLからTwitterにメディアアップロードしてmedia_idを返す"""
    try:
        resp = requests.get(image_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        media = api_v1.media_upload(filename="image.jpg", file=BytesIO(resp.content))
        return media.media_id
    except Exception as e:
        print(f"[WARN] Twitter メディアアップロード失敗: {e}")
        return None


def post_to_twitter(
    access_token: str,
    access_token_secret: str,
    image_urls: list[str],
    text: str,
    reply_text: str = "",
) -> Optional[str]:
    """画像付きツイートを投稿し、返信にURLを添える"""
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        print("[ERROR] TWITTER_API_KEY / TWITTER_API_SECRET が未設定")
        return None

    api_v1, client_v2 = _get_clients(access_token, access_token_secret)

    # メディアアップロード（最大4枚）
    media_ids = []
    for url in image_urls[:4]:
        mid = _upload_media(api_v1, url)
        if mid:
            media_ids.append(mid)
            print(f"[INFO] Twitter メディアアップロード完了: {mid}")

    # ツイート投稿
    try:
        resp = client_v2.create_tweet(
            text=text,
            media_ids=media_ids if media_ids else None,
        )
        tweet_id = str(resp.data["id"])
        print(f"[INFO] Twitter 投稿完了: tweet_id={tweet_id}")
    except Exception as e:
        print(f"[ERROR] Twitter 投稿失敗: {e}")
        return None

    # 返信にURL
    if reply_text and tweet_id:
        try:
            client_v2.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            print(f"[INFO] Twitter 返信投稿完了")
        except Exception as e:
            print(f"[WARN] Twitter 返信失敗: {e}")

    return tweet_id
