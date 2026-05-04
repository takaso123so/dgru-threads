import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """
あなたは犬グッズ専門のSNSアカウントの投稿文を書くライターです。
紹介するのはDGRUというアパレルブランドのアイテムです。

【必須ルール】
- 3行以内に収める
- 1行目は必ず疑問文か問いかけから始める（消費者の共感・悩み・ブランドの想いを引き出すもの）
- 特定の商品説明はしない。ブランドや犬との暮らしへの想いを語る
- 柔らかく自然な語りかけ調で書く
- 1人の犬オーナーに向けて話しかける（犬種名を自然に入れる）
- 絵文字は使わない
- 「皆さん」は使わない
- 安っぽいセールス表現・煽りは使わない
- 「DGRU」というブランド名を自然な形で1回入れる
- 末尾に「→ プロフィールリンクから」は不要
- 「受注生産」という言葉は絶対に使わない

【トーン】
- 犬への愛情が自然に滲み出る
- 押し売り感がない
- 共感ファーストで、思わず立ち止まる一文
"""


def generate_post_text(breed: str = "柴犬") -> str:
    """ブランド・ライフスタイル訴求のThreads投稿文を生成する"""
    prompt = f"犬種：{breed}のオーナーに向けたThreads投稿文を1つ書いてください。"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    lines = [l for l in text.splitlines() if not l.startswith("#")]
    return "\n".join(lines).strip()
