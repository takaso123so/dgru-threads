import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional


def get_product_image_url(product_url: str, retries: int = 3) -> Optional[str]:
    """BASE商品ページからog:image URLを取得する（クエリパラメータを除去）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for attempt in range(retries):
        try:
            response = requests.get(product_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            og_image = soup.find("meta", property="og:image")

            if og_image and og_image.get("content"):
                parsed = urlparse(og_image["content"])
                return parsed._replace(query="", fragment="").geturl()

            return None

        except requests.exceptions.Timeout:
            print(f"[WARN] タイムアウト（{attempt + 1}/{retries}）: {product_url}")
            if attempt < retries - 1:
                time.sleep(5)
        except Exception as e:
            print(f"[WARN] 画像取得エラー: {e}")
            return None

    print(f"[ERROR] 画像取得失敗（リトライ上限）: {product_url}")
    return None
