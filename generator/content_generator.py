import random
import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

BREED_NAMES = {
    "shiba": "柴犬",
    "schnauzer": "シュナウザー",
}

PATTERNS = [
    # A: 超短文系
    {"name": "A1_体言止め", "instruction": "20文字以内の体言止めで終わる超短い一文。犬種名を入れる。"},
    {"name": "A2_超短疑問", "instruction": "20文字以内の短い疑問文。犬種名を入れて「？」で終わる。"},
    {"name": "A3_断言一文", "instruction": "25文字以内の断言する一文。犬種名を入れて体言止めまたは「。」で終わる。"},
    {"name": "A4_呼びかけ", "instruction": "25文字以内の犬種オーナーへの呼びかけ一文。「へ。」などで終わる。"},
    {"name": "A5_余韻系", "instruction": "25文字以内のほっとするような余韻のある一文。犬種名を入れる。"},

    # B: 共感疑問系
    {"name": "B1_ニーズ疑問", "instruction": "50文字前後。犬種オーナーが感じるニーズや不足感を疑問文にする。「？」で終わる。"},
    {"name": "B2_あるある疑問", "instruction": "50文字前後。犬種オーナーのあるあるを疑問文にする。「ませんか？」などで終わる。"},
    {"name": "B3_気持ち疑問", "instruction": "50文字前後。犬種との暮らしの中の気持ちや場面を疑問文にする。「？」で終わる。"},
    {"name": "B4_発見疑問", "instruction": "60文字前後。犬種と暮らし始めてからの変化や気づきを疑問文にする。「ませんでしたか？」などで終わる。"},
    {"name": "B5_共感問いかけ", "instruction": "50文字前後。犬種オーナー同士の共感を問いかける疑問文。「しませんか？」などで終わる。"},
    {"name": "B6_不満共感疑問", "instruction": "60文字前後。大人が着られる犬種モチーフアパレルが少ないという共感を疑問文にする。「ないですか？」などで終わる。"},

    # C: ブランドストーリー系
    {"name": "C1_誕生背景", "instruction": "80文字以内。犬種グッズの不足からDGRUが生まれた背景を語る。短い文を2〜3つつなげる。"},
    {"name": "C2_想い語り", "instruction": "80文字以内。犬種との暮らしへの想いとDGRUのものづくりをつなげて語る。"},
    {"name": "C3_こだわり", "instruction": "80文字以内。可愛すぎないおしゃれというDGRUのこだわりを語る。犬種名を入れる。"},
    {"name": "C4_ブランド宣言", "instruction": "50文字以内。犬種オーナーのためのアパレルであるというDGRUの宣言を一文で。"},
    {"name": "C5_価値観", "instruction": "80文字以内。犬への愛情を形にするというDGRUの価値観を語る。犬種名を入れる。"},

    # D: ライフスタイル系
    {"name": "D1_朝の情景", "instruction": "2文構成・80文字以内。1文目：犬種と過ごす朝の情景。2文目：そのそばにDGRUがいたいという想い。"},
    {"name": "D2_散歩情景", "instruction": "2文構成・80文字以内。1文目：犬種との散歩が好きという疑問または共感。2文目：その時間を彩るDGRUのアイテム。"},
    {"name": "D3_休日情景", "instruction": "2文構成・80文字以内。1文目：犬種と過ごす休日の豊かさ。2文目：その暮らしにDGRUがいたいという想い。"},
    {"name": "D4_愛犬との日常", "instruction": "2文構成・80文字以内。1文目：毎日そばにいることで深まる犬種への愛着。2文目：その気持ちを形にしたいDGRU。"},

    # E: 新作告知系
    {"name": "E1_シンプル告知", "instruction": "2文構成・60文字以内。1文目：犬種の新しいアイテムができたという告知。2文目：DGRUでゆっくり見てほしいという一言。"},
    {"name": "E2_季節告知", "instruction": "2文構成・60文字以内。1文目：この季節に着たくなる犬種アイテムが揃ったという告知。2文目：DGRUでチェックしてほしいという一言。"},

    # F: 一言＋ブランド系
    {"name": "F1_シンプルつなぎ", "instruction": "2文構成・60文字以内。1文目：犬種オーナーに届けたいものがあるという一言。2文目：それがDGRUというブランドだという宣言。"},
    {"name": "F2_問いかけ＋答え", "instruction": "2文構成・60文字以内。1文目：犬種オーナーのためのアパレルがあってもいいという疑問文。2文目：DGRUがそれをつくっているという答え。"},
]

SYSTEM_PROMPT = """
あなたは犬グッズ専門のSNSアカウントの投稿文を書くライターです。
紹介するのはDGRUというアパレルブランドのアイテムです。

【絶対ルール】
- 絵文字は使わない
- 「皆さん」は使わない
- 「受注生産」という言葉は絶対に使わない
- 「→ プロフィールリンクから」は不要
- 「ダサい」「イマイチ」などネガティブ・マイナスな言葉は使わない
- 安っぽいセールス表現・煽りは使わない
- 指定された犬種名（日本語）を必ず入れる
- 「DGRU」を使う場合は自然な形で1回のみ
- 友人に話しかけるような柔らかい口調
"""


def generate_post_text(breed: str = "柴犬") -> str:
    breed_ja = BREED_NAMES.get(breed, breed)
    pattern = random.choice(PATTERNS)

    prompt = f"""犬種：{breed_ja}
パターン：{pattern['name']}
指示：{pattern['instruction']}

上記の指示に従って、{breed_ja}オーナー向けのThreads投稿文を1つ書いてください。"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    lines = [l for l in text.splitlines() if not l.startswith("#")]
    return "\n".join(lines).strip()
