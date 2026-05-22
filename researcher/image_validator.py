from __future__ import annotations

import base64

import anthropic
import requests

from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def _fetch_image(url: str) -> tuple[str, str] | None:
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        if not content_type.startswith("image/"):
            return None
        return base64.standard_b64encode(resp.content).decode("utf-8"), content_type
    except Exception:
        return None


def validate_image(image_url: str, breed_ja: str) -> bool:
    """Claude Visionで画像を検証（犬種一致 かつ アパレルでない）"""
    fetched = _fetch_image(image_url)
    if not fetched:
        return False
    img_data, media_type = fetched

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"この画像を確認してください。\n"
                            f"条件1: {breed_ja}が描かれた、または{breed_ja}をモチーフにした商品である\n"
                            f"条件2: Tシャツ・パーカー・スウェットなど人間が着るアパレル商品ではない\n"
                            f"両方の条件を満たす場合のみ「OK」、それ以外は「NG」とだけ答えてください。"
                        ),
                    },
                ],
            }],
        )
        return msg.content[0].text.strip().upper().startswith("OK")
    except Exception as e:
        print(f"[WARN] 画像検証エラー: {e}")
        return False


def get_valid_images(candidates: list[dict], breed_ja: str, max_images: int = 4) -> list[dict]:
    """候補からバリデーション通過画像をmax_images枚返す"""
    valid = []
    for c in candidates:
        if len(valid) >= max_images:
            break
        print(f"[INFO] 検証中: {c['title'][:40]}...")
        if validate_image(c["image_url"], breed_ja):
            valid.append(c)
            print(f"[INFO] OK: {c['title'][:40]}")
        else:
            print(f"[INFO] NG: 除外")
    return valid
