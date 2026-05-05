import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """
あなたは犬グッズ専門のSNSアカウントの投稿文を書くライターです。
紹介するのはDGRUというアパレルブランドのアイテムです。

【必須ルール】
- 必ず2行で書く
- 1行目：犬オーナーが共感する「あるある」や「悩み」を疑問文にする。必ず「？」で終わる
- 2行目：1行目の課題・共感に対して、DGRUがその答えであることを自然につなげる
- 特定の商品説明はしない
- 柔らかく、友人に話しかけるような口調で書く
- 犬種名を必ず入れる
- 絵文字は使わない
- 「皆さん」は使わない
- 安っぽいセールス表現・煽りは使わない
- 「DGRU」というブランド名を2行目に自然な形で1回入れる
- 末尾に「→ プロフィールリンクから」は不要
- 「受注生産」という言葉は絶対に使わない

【文例イメージ】
- 人用の柴犬デザインの服って、なかなかないと思いませんか？
  そんな柴犬オーナーのために、DGRUがあります。

- 犬の服はたくさんあるけど、自分が着たい柴犬グッズが見つからないと感じたことありませんか？
  DGRUは、柴犬と暮らす人のためのアパレルブランドです。

- シュナウザーのデザインって、可愛すぎるかダサいかの二択じゃないですか？
  ちょうどいいおしゃれを、DGRUで作っています。

【トーン】
- 犬への愛情が自然に滲み出る
- 押し売り感がない
- 読んで「わかる」と思わず頷けるような文章
"""


BREED_NAMES = {
    "shiba": "柴犬",
    "schnauzer": "シュナウザー",
}


def generate_post_text(breed: str = "柴犬") -> str:
    """ブランド・ライフスタイル訴求のThreads投稿文を生成する"""
    breed_ja = BREED_NAMES.get(breed, breed)
    prompt = f"犬種：{breed_ja}のオーナーに向けたThreads投稿文を1つ書いてください。必ず「{breed_ja}」という言葉を投稿文中に入れてください。"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    lines = [l for l in text.splitlines() if not l.startswith("#")]
    return "\n".join(lines).strip()
