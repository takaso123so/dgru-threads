import requests
from bs4 import BeautifulSoup
from typing import Optional


def get_product_image_url(product_url: str) -> Optional[str]:
    """BASE商品ページからog:image URLを取得する"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(product_url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    og_image = soup.find("meta", property="og:image")

    if og_image and og_image.get("content"):
        return og_image["content"]

    return None
