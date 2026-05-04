import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """
あなたは犬グッズ専門のSNSアカウントの投稿文を書くライターです。
紹介するのはDGRUというアパレルブランドのアイテムです。

【必須ルール】
- 3行以内に収める
- 「新作できました」「新しいアイテムが揃いました」などの柔らかい告知、またはブランドの想いや価値観を語る一文から始める
- 特定の商品説明はしない。ブランドのスタンスや犬との暮らしへの想いを語る
- 「可愛すぎない、ちょうどいいおしゃれ」「普段着として着たくなる」というブランドの世界観を自然に入れる
- 柔らかく、友人に話しかけるような口調で書く
- 犬種名を自然に入れる
- 絵文字は使わない
- 「皆さん」は使わない
- 安っぽいセールス表現・煽りは使わない
- 「DGRU」というブランド名を自然な形で1回入れる
- 末尾に「→ プロフィールリンクから」は不要
- 「受注生産」という言葉は絶対に使わない

【文例イメージ】
- 柴犬グッズの新作できました。可愛すぎず、でも一緒に暮らす子のことをちゃんと想って作っています。
- おしゃれなのに、ちゃんと柴犬愛がある。そんなアイテムをDGRUで揃えています。
- 柴犬と暮らすって、毎日がちょっと特別。その気持ちをそっと形にしたくて、DGRUは生まれました。

【トーン】
- 犬への愛情が自然に滲み出る
- 押し売り感がない
- ブランドの想いや価値観が伝わる、読んでほっとするような文章
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
