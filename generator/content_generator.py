import random
import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

BREED_NAMES = {
    "shiba": "柴犬",
    "schnauzer": "シュナウザー",
}

PATTERNS = [
    # A: 超短文系（DGRUアパレルに紐づく）
    {"name": "A1_体言止め", "instruction": "20文字以内。犬種デザインのアパレルやDGRUへの想いを体言止めで締める超短い一文。", "with_image": True},
    {"name": "A2_超短疑問", "instruction": "20文字以内。人用の犬種デザインアパレルを探しているという疑問文。犬種名を入れて「？」で終わる。", "with_image": True},
    {"name": "A3_断言一文", "instruction": "25文字以内。DGRUが犬種オーナーのためのブランドであるという断言。体言止めまたは「。」で終わる。", "with_image": True},
    {"name": "A4_呼びかけ", "instruction": "25文字以内。犬種のおしゃれなアパレルを探している人への呼びかけ一文。「へ。」などで終わる。", "with_image": True},
    {"name": "A5_余韻系", "instruction": "25文字以内。DGRUの犬種アパレルを着ることへの喜びや満足感をほっとするような一文で。", "with_image": True},

    # B: 共感疑問系（ファッション・グッズ関連）
    {"name": "B1_ニーズ疑問", "instruction": "50文字前後。人用の犬種デザインアパレルやグッズが少ないというニーズを疑問文にする。「？」で終わる。", "with_image": True},
    {"name": "B2_あるある疑問", "instruction": "50文字前後。犬種モチーフのおしゃれなアパレルを探しているというあるあるを疑問文にする。「ませんか？」などで終わる。", "with_image": True},
    {"name": "B3_気持ち疑問", "instruction": "50文字前後。犬種との散歩や外出時にDGRUのアイテムを着たいという気持ちや場面を疑問文にする。「？」で終わる。", "with_image": True},
    {"name": "B4_発見疑問", "instruction": "60文字前後。犬種と暮らし始めてから犬種グッズやアパレルへの興味が増したという変化を疑問文にする。「ませんでしたか？」などで終わる。", "with_image": True},
    {"name": "B5_共感問いかけ", "instruction": "50文字前後。犬種オーナー同士がDGRUのアパレルで繋がれるような共感を問いかける疑問文。「しませんか？」などで終わる。", "with_image": True},
    {"name": "B6_不満共感疑問", "instruction": "60文字前後。大人が着られる犬種モチーフアパレルが少ないという悩みに共感し、DGRUがその答えであるという流れ。疑問文から始める。", "with_image": True},

    # C: ブランドストーリー系
    {"name": "C1_誕生背景", "instruction": "80文字以内。犬種グッズの不足からDGRUが生まれた背景を語る。短い文を2〜3つつなげる。", "with_image": True},
    {"name": "C2_想い語り", "instruction": "80文字以内。犬種との暮らしへの想いとDGRUのものづくりをつなげて語る。", "with_image": True},
    {"name": "C3_こだわり", "instruction": "80文字以内。可愛すぎないおしゃれというDGRUのこだわりを語る。犬種名を入れる。", "with_image": True},
    {"name": "C4_ブランド宣言", "instruction": "50文字以内。犬種オーナーのためのアパレルであるというDGRUの宣言を一文で。", "with_image": True},
    {"name": "C5_価値観", "instruction": "80文字以内。犬への愛情をDGRUのアパレルという形にするという価値観を語る。犬種名を入れる。", "with_image": True},

    # D: ライフスタイル×DGRUアパレル系
    {"name": "D1_朝の情景", "instruction": "2文構成・80文字以内。1文目：犬種と過ごす朝にDGRUのアイテムを着るという情景。2文目：そういう日常をDGRUと一緒に。", "with_image": True},
    {"name": "D2_散歩情景", "instruction": "2文構成・80文字以内。1文目：犬種との散歩にDGRUのアイテムを着ていきたいという疑問または共感。2文目：その時間を彩るDGRUのアイテム紹介。", "with_image": True},
    {"name": "D3_休日情景", "instruction": "2文構成・80文字以内。1文目：犬種と過ごす休日にDGRUのアイテムを着るという豊かさ。2文目：その暮らしにDGRUがいたいという想い。", "with_image": True},
    {"name": "D4_愛犬との外出", "instruction": "2文構成・80文字以内。1文目：犬種と外出する時に着たい服がなかったという悩み。2文目：DGRUはそのために作られたというつなぎ。", "with_image": True},

    # E: 新作告知系
    {"name": "E1_シンプル告知", "instruction": "2文構成・60文字以内。1文目：犬種の新しいDGRUアイテムができたという告知。2文目：ゆっくり見てほしいという一言。", "with_image": True},
    {"name": "E2_季節告知", "instruction": "2文構成・60文字以内。1文目：この季節に着たくなる犬種のDGRUアイテムが揃ったという告知。2文目：チェックしてほしいという一言。", "with_image": True},

    # F: 一言＋ブランド系
    {"name": "F1_シンプルつなぎ", "instruction": "2文構成・60文字以内。1文目：犬種オーナーに届けたいものがあるという一言。2文目：それがDGRUというブランドだという宣言。", "with_image": True},
    {"name": "F2_問いかけ＋答え", "instruction": "2文構成・60文字以内。1文目：犬種オーナーのためのアパレルがあってもいいという疑問文。2文目：DGRUがそれをつくっているという答え。", "with_image": True},

    # G: 豆知識・雑学系（画像なし）
    {"name": "G1_豆知識", "instruction": "2文構成・100文字以内。1文目：犬種の性格・特性・歴史などの豆知識を「〜って知ってましたか？」という疑問文で。2文目：その特性にまつわる犬オーナーへの共感や一言。DGRUには触れない。", "with_image": False},
    {"name": "G2_あるある悩み解決", "instruction": "2文構成・100文字以内。1文目：犬種オーナーがよく感じる日常の悩みやあるあるを疑問文で。2文目：「こうするといいみたいです」「こういう方法があります」という軽いヒントや共感。DGRUには触れない。", "with_image": False},
    {"name": "G3_犬種の魅力語り", "instruction": "2文構成・100文字以内。1文目：犬種の意外な一面や魅力を「実は〜」という切り口で。2文目：その魅力への共感や犬オーナーへの問いかけ。DGRUには触れない。", "with_image": False},
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


def generate_post_text(breed: str = "柴犬") -> tuple:
    """投稿文と画像添付フラグを返す。戻り値: (text, with_image)"""
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
    return "\n".join(lines).strip(), pattern["with_image"]
