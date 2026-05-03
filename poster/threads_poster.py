import time
import requests
from typing import Optional

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def _create_and_publish(account_id: str, access_token: str, params: dict) -> Optional[str]:
    """コンテナ作成 → 公開の共通処理。投稿IDを返す。"""
    container_res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads",
        params={**params, "access_token": access_token}
    )
    container_res.raise_for_status()
    creation_id = container_res.json()["id"]

    time.sleep(30)

    publish_res = requests.post(
        f"{THREADS_API_BASE}/{account_id}/threads_publish",
        params={"creation_id": creation_id, "access_token": access_token}
    )
    publish_res.raise_for_status()
    return publish_res.json().get("id")


def post_to_threads(account_id: str, access_token: str, image_url: str, text: str, product_url: str = "") -> Optional[str]:
    """画像+テキストで投稿し、商品URLをリプライとして追加する。"""

    # メイン投稿
    post_id = _create_and_publish(account_id, access_token, {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": text,
    })

    # 商品URLをリプライで追加
    if product_url and post_id:
        time.sleep(5)
        _create_and_publish(account_id, access_token, {
            "media_type": "TEXT",
            "text": product_url,
            "reply_to_id": post_id,
        })

    return post_id
