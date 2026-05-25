import os
from io import BytesIO
from typing import Optional

import requests
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


def _get_api(access_token: str, access_token_secret: str) -> tweepy.API:
    auth = tweepy.OAuth1UserHandler(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return tweepy.API(auth)


def _upload_images(api: tweepy.API, image_urls: list[str]) -> list[str]:
    media_ids = []
    for url in image_urls[:4]:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            media = api.media_upload(filename="image.jpg", file=BytesIO(resp.content))
            media_ids.append(str(media.media_id))
            print(f"[INFO] 画像アップロード完了: media_id={media.media_id}")
        except Exception as e:
            print(f"[WARN] 画像アップロード失敗: {url}: {e}")
    return media_ids


def post_to_twitter(
    access_token: str,
    access_token_secret: str,
    image_urls: list[str],
    text: str,
    reply_text: str = "",
) -> Optional[str]:
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        print("[ERROR] TWITTER_API_KEY / TWITTER_API_SECRET が未設定")
        return None

    client = _get_client(access_token, access_token_secret)

    # 画像アップロード
    media_ids = []
    if image_urls:
        api = _get_api(access_token, access_token_secret)
        media_ids = _upload_images(api, image_urls)

    # ツイート投稿
    try:
        kwargs = {"text": text}
        if media_ids:
            kwargs["media_ids"] = media_ids
        resp = client.create_tweet(**kwargs)
        tweet_id = str(resp.data["id"])
        print(f"[INFO] Twitter 投稿完了: tweet_id={tweet_id}")
    except tweepy.errors.Unauthorized as e:
        print(f"[ERROR] Twitter 認証エラー (401): {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Twitter 投稿失敗: {type(e).__name__}: {e}")
        return None

    # 返信にURL
    if reply_text and tweet_id:
        try:
            client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            print(f"[INFO] Twitter 返信投稿完了")
        except Exception as e:
            print(f"[WARN] Twitter 返信失敗: {e}")

    return tweet_id
