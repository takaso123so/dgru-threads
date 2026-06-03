"""
汎用キャラクターアカウント投稿生成モジュール。
breeds.json の character ブロックを読み込み、どの犬種でも動く。
toypoodle 以降の犬種はこちらを使う。
"""
import random
import time

import anthropic
from config import CLAUDE_API_KEY, BREEDS

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def _build_system_prompt(breed: str) -> str:
    """breeds.json の character ブロックからシステムプロンプトを組み立てる"""
    ch = BREEDS[breed]["character"]
    name = ch["name"]
    first_person = ch["first_person"]
    personality = ch["personality"]
    tone = ch["tone"]
    catchphrases = "、".join(ch.get("catchphrases", []))
    sub_catchphrases = "、".join(ch.get("sub_catchphrases", []))

    return f"""あなたは「{name}」です。{breed}アカウントのキャラクターマスコット。

【{name}の人格】
- 一人称は「{first_person}」
- 性格: {personality}
- 口調: {tone}
- 口癖（たまに自然に使う）: {catchphrases}
- サブ口癖（必要なときだけ）: {sub_catchphrases}

【投稿ルール】
- 2〜4行以内
- 1人に向けて話しかける感覚で書く
- 重い話題・暗い話題は扱わない
- 絵文字は使わない
- 「皆さん」は使わない
- DGRUに触れる場合は「うちのブランド（DGRU）」と自然な形で1回のみ

【出力形式】
投稿文のみ。前置き・説明は一切不要。
"""


def _call_claude(system_prompt: str, prompt: str, max_tokens: int = 200) -> str:
    """リトライ付きClaude呼び出し"""
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"[WARN] API過負荷、{wait}秒後にリトライ ({attempt+1}/3)")
                time.sleep(wait)
            else:
                raise
    return ""


def generate_character_trend_text(breed: str, topic_text: str) -> str:
    """トレンド・ニュースに対してキャラクターが反応する投稿文を生成"""
    system = _build_system_prompt(breed)
    ch = BREEDS[breed]["character"]
    name = ch["name"]
    prompt = f"""今日のニュース・話題（見出しリスト）：
{topic_text}

この中の1つの話題に対して、{name}がキャラクターらしい目線で軽くコメントする投稿文を書いてください。
2〜4行以内。重い話題は避けて、日常・生活・季節・おもしろ系の話題を優先してください。"""
    return _call_claude(system, prompt)


def generate_character_casual_text(breed: str) -> str:
    """キャラクターの日常ひとコマ投稿文を生成"""
    system = _build_system_prompt(breed)
    ch = BREEDS[breed]["character"]
    name = ch["name"]
    scenes = ch.get("casual_scenes", [])
    scene = random.choice(scenes) if scenes else "飼い主さんと過ごしているとき"
    prompt = f"""シーン：{scene}

このシーンで{name}が感じていることや思っていることを、短い投稿文にしてください。
2〜4行以内。{name}らしく。"""
    return _call_claude(system, prompt)


def generate_character_comic_prompt(breed: str) -> str:
    """コマ漫画のDALL-E 3用英語プロンプトをClaudeで生成する"""
    ch = BREEDS[breed]["character"]
    appearance_en = ch.get("appearance_en", "")
    comic_scenes_en = ch.get("comic_scenes_en", [])
    scene = random.choice(comic_scenes_en) if comic_scenes_en else "sitting and looking cute"

    system = f"""You generate DALL-E 3 image prompts for a Japanese-style single-panel comic (1-koma manga).

Character description (follow exactly, do NOT change):
{appearance_en}

Art style (follow exactly):
- Hand-drawn single-panel sketch
- Rough pencil or pen outlines, slightly wobbly lines
- Light cross-hatching
- Soft watercolor or colored-pencil wash
- Simple background that shows the situation without being too detailed
- Warm, cozy, slightly humorous feel
- NO text, NO speech bubbles, NO logos, NO captions, NO writing of any kind

Output: One English DALL-E 3 prompt only. No explanations. No Japanese."""

    prompt = f"Scene: The character is {scene}. Write a DALL-E 3 prompt for this scene."

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                time.sleep(30 * (attempt + 1))
            else:
                raise
    return ""


def generate_character_product_text(breed: str, products: list) -> tuple[str, str]:
    """商品紹介投稿文をキャラクター口調で生成。戻り値: (text, pattern_name)"""
    system = _build_system_prompt(breed)
    ch = BREEDS[breed]["character"]
    name = ch["name"]
    product_angle = ch.get("product_angle", "")
    item_names = "、".join(p["item_name"] for p in products[:2])

    prompt = f"""紹介する商品：{item_names}

{name}がDGRUの商品を飼い主さんへ紹介する投稿文を書いてください。
訴求の方向性: {product_angle}
商品URLは本文に書かない（返信に貼るので不要）。
2〜4行以内。{name}らしく。"""

    text = _call_claude(system, prompt)
    return text, f"{breed.upper()}_PRODUCT_INTRO"
