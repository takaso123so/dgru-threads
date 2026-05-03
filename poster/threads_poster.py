import time
import requests
from typing import Optional, List

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def _create_carousel_item(account_id: str, access_token: str, image_url: str) -> Optional[str]:
    """カルーセル用の子コンテナを作成してIDを返す"""
    res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads",
        params={
            "media_type": "IMAGE",
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": access_token,
        }
    )
    res.raise_for_status()
    return res.json()["id"]


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


def post_carousel_to_threads(
    account_id: str,
    access_token: str,
    image_urls: List[str],
    text: str,
    reply_text: str = ""
) -> Optional[str]:
    """4枚カルーセル投稿し、リプライにURLを追加する"""

    # 1. 各画像の子コンテナを作成
    children = []
    for url in image_urls:
        item_id = _create_carousel_item(account_id, access_token, url)
        children.append(item_id)
        print(f"[INFO] カルーセルアイテム作成: {item_id}")

    # アイテムの処理完了を待つ
    time.sleep(15)

    # 2. カルーセルコンテナを作成
    carousel_res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "text": text,
            "access_token": access_token,
        }
    )
    carousel_res.raise_for_status()
    carousel_id = carousel_res.json()["id"]
    print(f"[INFO] カルーセルコンテナ作成: {carousel_id}")

    # 3. 公開
    post_id = _publish(account_id, access_token, carousel_id)
    print(f"[INFO] 投稿完了: post_id={post_id}")

    # 4. リプライ追加
    if reply_text and post_id:
        time.sleep(5)
        _post_reply(account_id, access_token, post_id, reply_text)

    return post_id
