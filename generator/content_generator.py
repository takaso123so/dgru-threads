import csv
import os
import random
import time
from collections import defaultdict

import anthropic
from config import CLAUDE_API_KEY, BREEDS

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

INSIGHTS_PATH = "logs/insights.csv"
DEFAULT_WEIGHT = 1.0
MAX_WEIGHT = 3.0

PATTERNS = [
    # A: 超短文系
    {"name": "A1_体言止め", "instruction": "20文字以内。犬種デザインのアパレルやDGRUへの想いを体言止めで締める超短い一文。", "with_image": True},
    {"name": "A2_超短疑問", "instruction": "20文字以内。人用の犬種デザインアパレルを探しているという疑問文。犬種名を入れて「？」で終わる。", "with_image": True},
    {"name": "A3_断言一文", "instruction": "25文字以内。DGRUが犬種オーナーのためのブランドであるという断言。体言止めまたは「。」で終わる。", "with_image": True},
    {"name": "A4_呼びかけ", "instruction": "25文字以内。犬種のおしゃれなアパレルを探している人への呼びかけ一文。「へ。」などで終わる。", "with_image": True},
    {"name": "A5_余韻系", "instruction": "25文字以内。DGRUの犬種アパレルを着ることへの喜びや満足感を、静かで余韻のある一文で。", "with_image": True},

    # B: 共感疑問系
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
    {"name": "D2_散歩情景", "instruction": "2文構成・80文字以内。1文目：犬種との散歩にDGRUのアイテムを着ていきたいという共感。2文目：その時間を彩るDGRUのアイテム紹介。", "with_image": True},
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
    {"name": "G2_あるある悩み解決", "instruction": "2文構成・100文字以内。1文目：犬種オーナーがよく感じる日常の悩みやあるあるを疑問文で。2文目：軽いヒントや共感。DGRUには触れない。", "with_image": False},
    {"name": "G3_犬種の魅力語り", "instruction": "2文構成・100文字以内。1文目：犬種の意外な一面や魅力を「実は〜」という切り口で。2文目：その魅力への共感や犬オーナーへの問いかけ。DGRUには触れない。", "with_image": False},

    # H: 作り手・クリエイター視点系
    {"name": "H1_作り手の想い", "instruction": "2文構成・80文字以内。DGRUを作っている人間の視点で、犬種オーナーのためにこのアイテムを作った想いや理由を語る。「私たちは〜」「DGRUでは〜」などブランド一人称で。", "with_image": True},
    {"name": "H2_商品誕生の背景", "instruction": "2文構成・80文字以内。この商品が生まれた経緯をDGRU目線で語る。「犬種オーナーさんの声から生まれた」「実際に着てほしくて作った」など作り手の言葉で。", "with_image": True},
    {"name": "H3_デザインのこだわり", "instruction": "2文構成・80文字以内。DGRUがこの商品のデザインに込めたこだわりを作り手目線で語る。「大人が着られるように」「犬種の魅力をさりげなく表現したくて」など具体的に。", "with_image": True},

    # I: アカウント訴求系（画像なし）
    {"name": "I1_アカウント紹介", "instruction": "2文構成・80文字以内。1文目：このアカウントが犬種の飼い主に向けておすすめグッズやアパレルを発信していることを自然に紹介する。2文目：フォローすると何が得られるかを一言で。絵文字なし・押しつけがましくなく。", "with_image": False},
    {"name": "I2_アカウント＋共感", "instruction": "2文構成・80文字以内。1文目：犬種の飼い主として共感できる一言（散歩・グッズ・日常）。2文目：このアカウントでそういった情報を発信していることをさりげなく伝える。", "with_image": False},
    {"name": "I3_アカウント＋ブランド紹介", "instruction": "2文構成・80文字以内。1文目：犬種オーナー向けのアパレルブランドDGRUを運営しているアカウントであることを自然に紹介。2文目：どんな人に見てほしいかを一言で。", "with_image": False},

    # K: 健康・予防情報系（画像なし）
    {"name": "K1_病気啓発", "instruction": "2文構成・100文字以内。1文目：犬種がかかりやすいとされる病気やリスクを「〜と言われています」「〜の報告があります」など断定しない表現で紹介。2文目：早期発見や日常ケアのヒントを「〜かもしれません」「〜が助けになるとされています」など疑問形や柔らかい表現で。DGRUには触れない。", "with_image": False},
    {"name": "K2_予防ケア", "instruction": "2文構成・100文字以内。1文目：犬種に多いとされるトラブルや体の特徴から来るリスクを「〜しやすい傾向があるとされ」など柔らかく伝える。2文目：日常でできる予防・ケアを「〜が役立つとされています」「試してみたことはありますか？」などユーザーに問いかける形で。DGRUには触れない。", "with_image": False},
    {"name": "K3_対話型健康", "instruction": "2文構成・100文字以内。1文目：犬種オーナーが気になりやすい健康・体調の変化や症状を「〜が気になったことはありますか？」という問いかけで。2文目：その背景にある可能性や対処のヒントを「〜という声もあるようです」「獣医師に相談してみるのも一つかもしれません」など断定せず提示。DGRUには触れない。", "with_image": False},

    # J: あるある＋アカウント訴求複合系（画像なし・砕けた口調）
    {"name": "J1_あるある→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種オーナーなら共感できる日常のあるある・謎行動・発見を「〜ありませんか」「〜いまだに分からない」「〜毎回面白い」のようなやや砕けたトーンで。2文目：そういう犬種の魅力や情報をこのアカウントでゆるく発信しているという自然な紹介。押しつけがましくなく。DGRUには触れない。", "with_image": False},
    {"name": "J2_話しかけ→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種オーナーへの問いかけ形式で、あるある・謎行動・日常の共感を「〜じゃないですか」「〜だけじゃないですか」のようなやや砕けたトーンで。2文目：そういった犬種の情報やあるあるをこのアカウントで発信しているという一言。DGRUには触れない。", "with_image": False},
    {"name": "J3_独り言→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種への愛や謎・面白さを独り言のような口調で（「〜なんでしょう」「〜ですよね」「〜が好きです」）。2文目：そんな犬種のことをいろんな角度でこのアカウントで発信しているという紹介。自然で押しつけがましくなく。DGRUには触れない。", "with_image": False},
]

SYSTEM_PROMPT = """
あなたはDGRUというアパレルブランドのSNS担当者です。
犬種オーナーに向けて、ブランドの想いや商品の魅力を伝える投稿文を書きます。

【ブランドの本質・絶対に間違えないこと】
DGRUは「犬好きの人間が着るアパレルブランド」です。
- 販売しているのは人間用の服（Tシャツ・スウェット・パーカーなど）
- 服には犬種のデザイン・プリントが入っている
- 着るのは飼い主（人間）であり、犬ではない
- 「犬に着せる服」「ペットウェア」「ドッグウェア」とは全く別物
- 「愛犬と一緒に着る」「ペアルック」などの表現も不可（人間だけが着る）

【口調・トーン】
- 丁寧語（です・ます調）を基本とする
- 堅すぎず、温かみと誠実さのある言葉を選ぶ
- 作り手・ブランドとして語る場面では「私たちは」「DGRUでは」などの一人称を使う
- タメ口・馴れ馴れしい表現は使わない
- セールス感・煽りは一切使わない

【絶対ルール】
- 絵文字は使わない
- 「皆さん」は使わない
- 「受注生産」という言葉は絶対に使わない
- 「→ プロフィールリンクから」は不要
- ネガティブ・マイナスな言葉は使わない
- 指定された犬種名（日本語）を必ず入れる
- 「DGRU」を使う場合は自然な形で1回のみ
- 犬種の身体的特徴（胴長・短足・顔の形・体型など）を笑いの対象や茶化しの素材にしない。「かわいい」「魅力的」「愛おしい」という肯定的な表現はOK
- 健康上のリスクと関連する身体的特徴については特に配慮した表現を使う（例：ダックスフンドの胴長を笑いにするのはNG、「あの胴長がたまらなく好きです」はOK）

【コピーライティングの原則】
長く説明しない。一瞬で意味が取れる言葉を選ぶ。
商品の良さをただ主張せず、「なるほど、だから良いのか」と読み手が納得できる根拠を言語化する。
説明ではなく、欲望・承認欲求・快楽を刺激し、購入後の感情を売ることを意識する。
SNSで流し見されても引っかかる一文を必ず入れる。

▼ 感情を動かすキーワード（状況に応じて自然に組み込む）
- 「〇〇では満たされない」→ 問題提起（例：普通の犬グッズでは満たされない人へ）
- 「〇〇へ導く」→ 変身願望（例：愛犬との毎日をもっと楽しい時間へ導く一枚）
- 「〇〇と褒められたい」→ 承認欲求（例：犬好きなのにおしゃれだね、と褒められたいあなたへ）
- 「2度とない」→ 希少性（例：愛犬との今を楽しむ、2度とない一枚）
- 「〇〇度急上昇」→ 変化の期待（例：犬好き度急上昇。ドッグカフェでの注目度急上昇）
- 「〇〇のままでいて」→ 理想化（例：犬が好きなあなたには、ずっとそのままでいてほしい）
- 「無限大」→ 自由度・可能性（例：犬好きコーデの楽しみ方は無限大）
- 「余すところなく」→ こだわりの本気度（例：犬種の魅力を余すところなく表現したデザイン）
- 「真髄」→ 本質・品格（例：犬好きファッションの真髄を、日常に）
- 「復活」→ 懐かしさ・取り戻したい感（例：犬を飼い始めた頃のワクワクが復活する一枚）

▼ 信頼・根拠を作るフレーズ（売り手の主張ではなく第三者視点で）
- 「〇〇も注目する」→ 権威・話題性（例：犬好きクリエイターも注目する犬種別アパレル）
- 「〇〇で分かった」→ 調査・リサーチ感（例：犬好きの声で分かった、普段着に馴染む犬服の条件）
- 「〇〇にしてよかった」→ 購入後の満足（例：DGRUにしてよかった。うちの子愛をちゃんとファッションにできたから）
- 「〇〇こそ、本物の証」→ こだわりの証明（例：犬種ごとに描き分けるこだわりこそ、本物の証）
- 「〇〇で大活躍」→ 使用シーン提示（例：ドッグカフェで大活躍。休日の散歩で大活躍）

▼ 投稿設計の方針
- 商品紹介だけでなく、情報・共感・応援・制作の裏側・犬種への愛を混ぜる
- 使用シーンと購入後の感情を具体的に想像させる
- 「良い商品」ではなく「選ぶ理由がある商品」として伝える
- 売り手の一方的な主張ではなく、読み手が「自分のための商品だ」と感じられる言葉を選ぶ

▼ キーワード・フレーズの使い方
これらは毎回使うべきルールではなく、必要なときに使う道具です。
パターンの指示と文字数制限を最優先してください。
無理に組み込もうとするとトーンが崩れます。使わない投稿があって構いません。

【出力形式】
- 投稿文のみを出力する
- 前置き・説明・文字数カウント・構成メモは一切不要
- 「---」などの区切り線も不要
"""


def load_pattern_weights(breed: str) -> dict[str, float]:
    """犬種ごとのinsightsデータからパターン別重みを計算する"""
    if not os.path.exists(INSIGHTS_PATH):
        return {}

    pattern_stats = defaultdict(lambda: {"views": 0, "count": 0})
    try:
        with open(INSIGHTS_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("breed", "").strip() != breed:
                    continue
                p = row.get("pattern_name", "").strip()
                if not p:
                    continue
                pattern_stats[p]["views"] += int(row.get("views") or 0)
                pattern_stats[p]["count"] += 1
    except Exception:
        return {}

    if not pattern_stats:
        return {}

    # 全パターンのavg viewsを計算
    avg_views = {
        p: s["views"] / s["count"]
        for p, s in pattern_stats.items()
        if s["count"] > 0
    }

    global_avg = sum(avg_views.values()) / len(avg_views) if avg_views else 1.0

    # 重みを計算（グローバル平均を1.0として正規化、上限3.0）
    weights = {}
    for p, avg in avg_views.items():
        weights[p] = min(avg / global_avg, MAX_WEIGHT)

    return weights


def weighted_choice(patterns: list[dict], weights: dict[str, float]) -> dict:
    """重み付きでパターンを選択する"""
    if not weights:
        return random.choice(patterns)

    pattern_weights = [weights.get(p["name"], DEFAULT_WEIGHT) for p in patterns]
    return random.choices(patterns, weights=pattern_weights, k=1)[0]


def generate_post_text(breed: str = "shiba", force_image: bool | None = None) -> tuple:
    """投稿文・画像フラグ・パターン名を返す。戻り値: (text, with_image, pattern_name)
    force_image=True  → 画像ありパターンのみ選択
    force_image=False → 画像なしパターンのみ選択
    force_image=None  → ランダム（従来通り）
    """
    breed_ja = BREEDS.get(breed, {}).get("name_ja", breed)

    if force_image is True:
        available = [p for p in PATTERNS if p["with_image"]]
    elif force_image is False:
        available = [p for p in PATTERNS if not p["with_image"]]
    else:
        available = PATTERNS

    weights = load_pattern_weights(breed)
    pattern = weighted_choice(available, weights)

    if weights:
        top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"[INFO] パターン重み上位3: {top}")

    # G系・K系はトピックをランダムで指定して内容の多様性を確保
    topic_hint = ""
    if pattern["name"].startswith("G"):
        topics = BREEDS.get(breed, {}).get("knowledge_topics", [])
        if topics:
            topic = random.choice(topics)
            topic_hint = f"\n今回取り上げる知識のテーマ：{topic}\n"
    elif pattern["name"].startswith("K"):
        topics = BREEDS.get(breed, {}).get("health_topics", [])
        if topics:
            topic = random.choice(topics)
            topic_hint = f"\n今回取り上げる健康トピック：{topic}\n"

    prompt = f"""犬種：{breed_ja}
パターン：{pattern['name']}
指示：{pattern['instruction']}
{topic_hint}
【必須確認】DGRUは飼い主（人間）が着る犬種デザインのアパレルブランドです。犬に着せる服・ドッグウェアではありません。投稿文に「〇〇に似合う」「〇〇が着る」のような犬を主語にした表現を絶対に使わないでください。あくまで「飼い主が着る服」として書いてください。

上記の指示に従って、{breed_ja}オーナー向けのThreads投稿文を1つ書いてください。"""

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"[WARN] API過負荷、{wait}秒後にリトライ ({attempt+1}/3)")
                time.sleep(wait)
            else:
                raise

    text = message.content[0].text.strip()
    lines = [
        l for l in text.splitlines()
        if not l.startswith("#")
        and not l.startswith("---")
        and not l.startswith("【")
        and "投稿文" not in l
        and "文字数" not in l
        and "構成" not in l
    ]
    return "\n".join(lines).strip(), pattern["with_image"], pattern["name"]


CURATION_SYSTEM_PROMPT = """
あなたは犬好きのためのグッズキュレーターです。
特定の犬種の飼い主や犬好きに向けて、見つけた可愛いグッズへの共感や驚きを自然な言葉で伝えます。

【口調・トーン】
- 特定のブランド名・ショップ名は出さない
- 発見・共感・驚きを素直に表現する
- 押しつけがましくない、自然な一言
- 丁寧すぎず、かといって馴れ馴れしくもない

【絶対ルール】
- 絵文字は使わない
- 「皆さん」は使わない
- 購入を促す表現・セールス感は使わない
- 指定された犬種名（日本語）を必ず入れる
- ブランド名・DGRUは一切出さない

【コピーの原則】
長く説明しない。一瞬で意味が取れる言葉を選ぶ。
SNSで流し見されても引っかかる一文を必ず入れる。
これらは毎回使うべきルールではなく、必要なときに使う道具です。
パターンの指示と文字数制限を最優先してください。

【出力形式】
投稿文のみを出力する。前置き・説明は一切不要。
"""

CURATION_PATTERNS = [
    {"name": "CUR1_発見", "instruction": "60文字以内。この犬種グッズを見つけた驚きや喜びを「可愛すぎませんか」「見つけてしまいました」のようなトーンで。"},
    {"name": "CUR2_共感", "instruction": "70文字以内。この犬種が好きな人なら絶対分かるという共感から始め、グッズへの気持ちを一言で。"},
    {"name": "CUR3_問いかけ", "instruction": "60文字以内。この犬種好きへの問いかけ形式。「〇〇好きって、こういうの好きじゃないですか？」のようなトーンで。"},
    {"name": "CUR4_一言", "instruction": "30文字以内。この犬種グッズへの率直な一言。体言止めか短い感嘆で。"},
    {"name": "CUR5_紹介", "instruction": "80文字以内。この犬種好きに向けて、今回見つけたグッズをさりげなく紹介する2文。"},
    {"name": "CUR6_不満共感", "instruction": "70文字以内。この犬種のグッズってなかなか見つからないという不満に共感してから、見つけた喜びを表現。"},
    {"name": "CUR7_断言", "instruction": "40文字以内。この犬種好きなら絶対気になると断言する一文。体言止めか「はず。」で終わる。"},
]


def generate_curation_text(breed: str = "shiba") -> tuple[str, str]:
    """キュレーション投稿文を生成。戻り値: (text, pattern_name)"""
    breed_ja = BREEDS.get(breed, {}).get("name_ja", breed)
    pattern = random.choice(CURATION_PATTERNS)

    prompt = f"""犬種：{breed_ja}
パターン：{pattern['name']}
指示：{pattern['instruction']}

{breed_ja}好きに向けたグッズキュレーション投稿文を書いてください。"""

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                system=CURATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"[WARN] API過負荷、{wait}秒後にリトライ ({attempt+1}/3)")
                time.sleep(wait)
            else:
                raise

    text = message.content[0].text.strip()
    lines = [
        l for l in text.splitlines()
        if not l.startswith("#")
        and not l.startswith("---")
        and not l.startswith("【")
        and "投稿文" not in l
        and "文字数" not in l
    ]
    return "\n".join(lines).strip(), pattern["name"]
