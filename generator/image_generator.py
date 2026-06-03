import datetime
import os

import requests

COMICS_DIR = "comics"
GITHUB_PAGES_BASE = "https://takaso123so.github.io/dgru-threads"


def is_comic_day() -> bool:
    return datetime.date.today().day % 2 == 0


def get_today_comic_path(breed: str = "shiba") -> str:
    today = datetime.date.today().isoformat()
    return os.path.join(COMICS_DIR, f"{today}-{breed}.png")


def get_today_comic_url(breed: str = "shiba") -> str:
    today = datetime.date.today().isoformat()
    return f"{GITHUB_PAGES_BASE}/comics/{today}-{breed}.png"


def generate_and_save_comic_panel(dalle_prompt: str, breed: str = "shiba") -> str | None:
    """DALL-E 3で画像を生成してcomics/に保存。成功したらパスを返す。"""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY が未設定")
        return None

    client = openai.OpenAI(api_key=api_key)
    os.makedirs(COMICS_DIR, exist_ok=True)
    path = get_today_comic_path(breed)

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url, timeout=30).content
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"[INFO] コマ漫画保存: {path}")
        return path
    except Exception as e:
        print(f"[ERROR] 画像生成失敗: {e}")
        return None
