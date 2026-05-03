import time
import requests
from typing import Optional, List

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def _publish(account_id: str, access_token: str, creation_id: str) -> Optional[str]:
    """コンテナを公開して投稿IDを返す"""
    time.sleep(30)
    res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads_publish",
        params={"creation_id": creation_id, "access_token": access_token}
    )
    res.raise_for_status()
    return res.json().get("id")


def _post_reply(account_id: str, access_token: str, reply_to_id: str, text: str) -> Optional[str]:
    """テキストリプライを投稿する"""
    container_res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": reply_to_id,
            "access_token": access_token,
        }
    )
    container_res.raise_for_status()
    creation_id = container_res.json()["id"]
    time.sleep(5)
    res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads_publish",
        params={"creation_id": creation_id, "access_token": access_token}
    )
    res.raise_for_status()
    return res.json().get("id")


def _try_carousel(account_id: str, access_token: str, image_urls: List[str], text: str) -> Optional[str]:
    """カルーセル投稿を試みる。失敗したらNoneを返す"""
    try:
        children = []
        for url in image_urls:
            res = requests.post(
                f"{THREADS_API_BASE}/{account_id}/threads",
                params={
                    "media_type": "IMAGE",
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": access_token,
                }
            )
            if not res.ok:
                print(f"[WARN] カルーセルアイテム作成失敗: {res.status_code} {res.text}")
                return None
            children.append(res.json()["id"])
            print(f"[INFO] カルーセルアイテム作成: {children[-1]}")

        time.sleep(15)

        carousel_res = requests.post(
            f"{THREADS_API_BASE}/{account_id}/threads",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children),
                "text": text,
                "access_token": access_token,
            }
        )
        if not carousel_res.ok:
            print(f"[WARN] カルーセルコンテナ作成失敗: {carousel_res.status_code} {carousel_res.text}")
            return None

        carousel_id = carousel_res.json()["id"]
        print(f"[INFO] カルーセルコンテナ作成: {carousel_id}")
        return _publish(account_id, access_token, carousel_id)

    except Exception as e:
        print(f"[WARN] カルーセル投稿エラー: {e}")
        return None


def _post_single_image(account_id: str, access_token: str, image_url: str, text: str) -> Optional[str]:
    """単画像投稿"""
    res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads",
        params={
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": access_token,
        }
    )
    res.raise_for_status()
    creation_id = res.json()["id"]
    return _publish(account_id, access_token, creation_id)


def post_to_threads(
    account_id: str,
    access_token: str,
    image_urls: List[str],
    text: str,
    reply_text: str = ""
) -> Optional[str]:
    """カルーセル投稿を試み、失敗したら単画像にフォールバックする"""

    # カルーセル投稿を試みる
    post_id = _try_carousel(account_id, access_token, image_urls, text)

    # 失敗したら1枚目の画像で単画像投稿
    if not post_id:
        print("[INFO] 単画像投稿にフォールバック")
        post_id = _post_single_image(account_id, access_token, image_urls[0], text)
        print(f"[INFO] 投稿完了: post_id={post_id}")

    # リプライ追加
    if reply_text and post_id:
        time.sleep(5)
        _post_reply(account_id, access_token, post_id, reply_text)

    return post_id
