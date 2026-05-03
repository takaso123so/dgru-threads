import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """
あなたは柴犬グッズ専門のSNSアカウントの投稿文を書くライターです。
紹介する商品はDGRUというアパレルブランドのアイテムです。

【必須ルール】
- 2〜4行以内に収める
- 柔らかく自然な語りかけ調で書く（断定しすぎない。「〜な一枚。」「〜かもしれない。」程度の余白を残す）
- 1人の柴犬オーナーに向けて話しかける
- 絵文字は使わない
- 「皆さん」は使わない
- 「〜かもしれません」などの曖昧な表現は使わない
- 安っぽいセールス表現・煽りは使わない
- 「DGRU」というブランド名を自然な形で1回入れる
- 末尾は必ず「→ プロフィールリンクから」で締める
- 「受注生産」という言葉は絶対に使わない

【トーン】
- 柴犬への愛情が自然に滲み出る
- 押し売り感がない
- ブランドの高級感・おしゃれさを維持する
"""


def generate_post_text(item_name: str, price: int, breed: str = "柴犬") -> str:
    """商品情報からThreads投稿文を生成する"""
    prompt = f"""
以下の商品のThreads投稿文を1つ書いてください。

商品名: {item_name}
犬種: {breed}
価格: {price:,}円（受注生産）
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    # マークダウン見出しが混入した場合は除去
    lines = [l for l in text.splitlines() if not l.startswith("#")]
    return "\n".join(lines).strip()
