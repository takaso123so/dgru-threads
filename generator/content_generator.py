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
    {"name": "A2_超短疑問", "instruction": "20文字以内。人用の犬種デザインアパレルを探しているという疑問文。犬種名を入れて「？」で終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "A3_断言一文", "instruction": "25文字以内。DGRUが犬種オーナーのためのブランドであるという断言。体言止めまたは「。」で終わる。", "with_image": True},
    {"name": "A4_呼びかけ", "instruction": "25文字以内。犬種のおしゃれなアパレルを探している人への呼びかけ一文。「へ。」などで終わる。", "with_image": True},
    {"name": "A5_余韻系", "instruction": "25文字以内。DGRUの犬種アパレルを着ることへの喜びや満足感を、静かで余韻のある一文で。", "with_image": True},

    # B: 共感疑問系
    {"name": "B1_ニーズ疑問", "instruction": "50文字前後。人用の犬種デザインアパレルやグッズが少ないというニーズを疑問文にする。「？」で終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "B2_あるある疑問", "instruction": "50文字前後。犬種モチーフのおしゃれなアパレルを探しているというあるあるを疑問文にする。「ませんか？」などで終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "B3_気持ち疑問", "instruction": "50文字前後。犬種との散歩や外出時にDGRUのアイテムを着たいという気持ちや場面を疑問文にする。「？」で終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "B4_発見疑問", "instruction": "60文字前後。犬種と暮らし始めてから犬種グッズやアパレルへの興味が増したという変化を疑問文にする。「ませんでしたか？」などで終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "B5_共感問いかけ", "instruction": "50文字前後。犬種オーナー同士がDGRUのアパレルで繋がれるような共感を問いかける疑問文。「しませんか？」などで終わる。必ず答えや補足も入れること。", "with_image": True},
    {"name": "B6_不満共感疑問", "instruction": "60文字前後。大人が着やすい犬種モチーフアパレルが少ないという軽い課題提起から始め、DGRUがその答えであるという流れ。疑問文から始めるが必ず答えや補足も入れること。", "with_image": True},

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
    {"name": "G1_豆知識", "instruction": "2文構成・100文字以内。1文目：犬種の性格・特性・歴史などの豆知識を「〜って知ってましたか？」という疑問文で。2文目：その特性にまつわる犬オーナーへの共感や一言。DGRUには触れない。コメントを促す形で疑問で終えてもよい。", "with_image": False},
    {"name": "G2_あるある悩み解決", "instruction": "2文構成・100文字以内。1文目：犬種オーナーがよく感じる日常の悩みやあるあるを疑問文で。2文目：軽いヒントや共感。DGRUには触れない。", "with_image": False},
    {"name": "G3_犬種の魅力語り", "instruction": "2文構成・100文字以内。1文目：犬種の意外な一面や魅力を「実は〜」という切り口で。2文目：その魅力への共感や犬オーナーへの問いかけ。DGRUには触れない。コメントを促す形で疑問で終えてもよい。", "with_image": False},

    # H: 作り手・クリエイター視点系
    {"name": "H1_作り手の想い", "instruction": "2文構成・80文字以内。DGRUを作っている人間の視点で、犬種オーナーのためにこのアイテムを作った想いや理由を語る。「私たちは〜」「DGRUでは〜」などブランド一人称で。", "with_image": True},
    {"name": "H2_商品誕生の背景", "instruction": "2文構成・80文字以内。この商品が生まれた経緯をDGRU目線で語る。「犬種オーナーさんの声から生まれた」「実際に着てほしくて作った」など作り手の言葉で。", "with_image": True},
    {"name": "H3_デザインのこだわり", "instruction": "2文構成・80文字以内。DGRUがこの商品のデザインに込めたこだわりを作り手目線で語る。「大人が着られるように」「犬種の魅力をさりげなく表現したくて」など具体的に。", "with_image": True},

    # I: アカウント訴求系（画像なし）
    {"name": "I1_アカウント紹介", "instruction": "2文構成・80文字以内。1文目：このアカウントが犬種の飼い主に向けておすすめグッズやアパレルを発信していることを自然に紹介する。2文目：フォローすると何が得られるかを一言で。絵文字なし・押しつけがましくなく。", "with_image": False},
    {"name": "I2_アカウント＋共感", "instruction": "2文構成・80文字以内。1文目：犬種の飼い主として共感できる一言（散歩・グッズ・日常）。2文目：このアカウントでそういった情報を発信していることをさりげなく伝える。", "with_image": False},
    {"name": "I3_アカウント＋ブランド紹介", "instruction": "2文構成・80文字以内。1文目：犬種オーナー向けのアパレルブランドDGRUを運営しているアカウントであることを自然に紹介。2文目：どんな人に見てほしいかを一言で。", "with_image": False},

    # K: 日常ケア情報系（画像なし・頻度控えめ）
    {"name": "K1_日常ケア", "instruction": "2文構成・100文字以内。1文目：犬種に向いている日常のやさしいケア（ブラッシング・耳・歯・肉球・散歩後チェックなど）を「〜しているオーナーも多いようです」「〜がおすすめとされています」など柔らかい表現で。2文目：オーナーへの共感や問いかけ。DGRUには触れない。必ず「気になる変化がある場合は、動物病院で相談してみてください。」で締める。", "with_image": False},
    {"name": "K2_季節ケア", "instruction": "2文構成・100文字以内。1文目：季節や環境の変化に合わせた犬種の日常ケアの注意点（夏の暑さ対策・冬の乾燥・梅雨の蒸れなど）を「〜に気をつけてあげると良いとされています」など柔らかく。2文目：オーナーへの共感や問いかけ。DGRUには触れない。必ず「気になる変化がある場合は、動物病院で相談してみてください。」で締める。", "with_image": False},

    # J: あるある＋アカウント訴求複合系（画像なし・砕けた口調）
    {"name": "J1_あるある→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種オーナーなら共感できる日常のあるある・謎行動・発見を「〜ありませんか」「〜いまだに分からない」「〜毎回面白い」のようなやや砕けたトーンで。2文目：そういう犬種の魅力や情報をこのアカウントでゆるく発信しているという自然な紹介。押しつけがましくなく。DGRUには触れない。", "with_image": False},
    {"name": "J2_話しかけ→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種オーナーへの問いかけ形式で、あるある・謎行動・日常の共感を「〜じゃないですか」「〜だけじゃないですか」のようなやや砕けたトーンで。2文目：そういった犬種の情報やあるあるをこのアカウントで発信しているという一言。DGRUには触れない。", "with_image": False},
    {"name": "J3_独り言→アカウント", "instruction": "2文構成・100文字以内。1文目：犬種への愛や謎・面白さを独り言のような口調で（「〜なんでしょう」「〜ですよね」「〜が好きです」）。2文目：そんな犬種のことをいろんな角度でこのアカウントで発信しているという紹介。自然で押しつけがましくなく。DGRUには触れない。", "with_image": False},

    # L: 参加型・共感型投稿（画像なし）
    {"name": "L1_どっち派", "instruction": "2文構成・80文字以内。1文目：犬種の性格・行動・見た目に関して「〜派ですか、〜派ですか？」という2択の問いかけ。2文目：「教えてください」「コメントで聞かせてください」のような参加を促す一言。軽く砕けた口調でOK。DGRUには触れない。コメントを促す形で終えてよい。", "with_image": False},
    {"name": "L2_あるある共感", "instruction": "1〜2文・80文字以内。犬種との暮らしの中で感じるあるある・愛おしい瞬間・ちょっとした発見を独り言のように語る。「〜ですよね」「〜な瞬間ありませんか」など共感を引き出すトーンで。DGRUには触れない。コメントを促す形で疑問で終えてもよい。", "with_image": False},
    {"name": "L3_謎行動愛", "instruction": "1〜2文・80文字以内。犬種の謎めいた行動・意外な習性・不思議な癖を、愛情たっぷりに「なぜなんでしょう」「あれが好きです」という口調で語る。笑いにせず魅力として伝える。DGRUには触れない。コメントを促す形で終えてもよい。", "with_image": False},
    {"name": "L4_エピソード募集", "instruction": "2文構成・80文字以内。1文目：犬種オーナーなら共感できるエピソードのテーマを投げかける（散歩・食事・寝る場所・お気に入りの場所など）。2文目：「うちの子はどうですか」「コメントで教えてください」のようにエピソードを募集する。軽く砕けた口調でOK。DGRUには触れない。", "with_image": False},
    {"name": "L5_共感独り言", "instruction": "1文・40文字以内。犬種オーナーとして感じる「これ分かる」という共感の瞬間を、さりげない独り言として一言で。余韻が残る終わり方でOK。DGRUには触れない。", "with_image": False},

    # M: 制作裏側・ブランド視点系（画像あり）
    {"name": "M1_デザインこだわり", "instruction": "2文構成・80文字以内。1文目：この犬種のデザインを作るうえでDGRUが大切にしていること・こだわっていることを作り手の視点で語る（可愛くしすぎない、渋さを残す、上品さとやさしさのバランスなど）。2文目：その理由や想いを一言で。「私たちは〜」「DGRUでは〜」など一人称で語ること。", "with_image": True},
    {"name": "M2_ブランドの動機", "instruction": "2文構成・80文字以内。1文目：なぜDGRUがこの犬種のアパレルを作っているのか、その動機や原点を語る。「犬種オーナーとして〜と感じていた」「〜という声があった」など具体的な理由で。2文目：その想いがアイテムに込められているという一言。", "with_image": True},
    {"name": "M3_制作の裏側", "instruction": "2文構成・80文字以内。1文目：このアイテムを作る過程で気づいたことや苦労したこと、発見を作り手目線で語る。「〜に何度も調整した」「〜を大切にした」など。2文目：だからこそ完成したという満足感や愛着を一言で。", "with_image": True},

    # N: 購入後イメージ・着用感情系（画像あり）
    {"name": "N1_着た後の感情", "instruction": "2文構成・80文字以内。1文目：この犬種のDGRUアイテムを着た後の感情・気持ちの変化を具体的に描く（散歩が楽しくなった、犬好きだと伝わる、同じオーナーさんと話が弾んだなど）。2文目：そういう一枚を作りたかったというDGRUの想い。DGRUは1回まで自然な形で使う。", "with_image": True},
    {"name": "N2_さりげなさ", "instruction": "2文構成・80文字以内。1文目：犬種好きだけが気づいてくれるさりげなさ・主張しすぎない犬種愛の表現について語る。「派手に主張しなくても〜」「分かる人だけに伝わる〜」のようなトーンで。2文目：それがDGRUの目指す一枚だという一言。", "with_image": True},
    {"name": "N3_日常への馴染み", "instruction": "2文構成・80文字以内。1文目：普段着として日常に馴染む、犬種デザインのアパレルの心地よさを具体的な場面で描く（コンビニ・カフェ・散歩道など）。2文目：大人が着られる犬種服というDGRUのコンセプトを一言で。", "with_image": True},
]

SYSTEM_PROMPT = """
あなたはDGRUというアパレルブランドのSNS担当者です。
犬種オーナーに向けて、ブランドの想いや商品の魅力を伝える投稿文を書きます。

【運用の基本方針】
DGRUのSNS運用は、商品を直接売り込むことよりも、犬種オーナーが「わかる」「うちの子っぽい」「こういう服なら着たい」と感じる接点を増やすことを優先する。商品紹介は、犬種への共感や暮らしの文脈の中で自然に行う。

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
- タメ口・馴れ馴れしい表現は使わない（参加型・あるある投稿は少し砕けてもよい）
- セールス感・煽りは一切使わない

【DGRU名の使用頻度】
- 共感・あるある・参加型投稿（J系・L系）：基本的にDGRU名を出さない
- 雑学・健康・ケア情報投稿（G系・K系）：DGRU名を出さない
- 商品画像投稿（A〜F系・H系）：50〜70%の割合でDGRU名を使用。毎回出さなくてよい
- ブランドストーリー・制作裏側（C系・M系）：使用する
- 購入後イメージ（N系）：自然な形で使用してよい

【絶対ルール】
- 商品紹介・ブランド説明の投稿では、疑問文を使う場合は必ず同じ投稿内でその答えや補足を入れる。疑問だけで終わらせない
- 共感投稿・あるある投稿・参加型投稿（G系・J系・K系・L系）では、コメントを促す目的で疑問文のまま終えてもよい
- 絵文字は使わない
- 「皆さん」は使わない
- 「受注生産」という言葉は絶対に使わない
- 「→ プロフィールリンクから」は不要
- ネガティブ・マイナスな言葉は使わない
- 指定された犬種名（日本語）を必ず入れる
- 「DGRU」を使う場合は自然な形で1回のみ
- 犬種の身体的特徴（胴長・短足・顔の形・体型など）を笑いの対象や茶化しの素材にしない。「かわいい」「魅力的」「愛おしい」という肯定的な表現はOK
- 健康上のリスクと関連する身体的特徴については特に配慮した表現を使う

【禁止事項】
- 不安を煽る表現（「このままでは〜」「〜しないと後悔する」など）は使わない
- 他のブランド・商品を比較したり下げるような表現は使わない
- 犬種や飼い主を傷つける・見下すような表現は使わない
- 「2度とない」「急上昇」「真髄」「復活」「〇〇では満たされない」などの情報商材的な言葉は使わない
- 「可愛すぎるものが多い」「大人が着やすい犬種服が少ない」など、DGRUの価値を伝えるための軽い課題提起は使用可

【DGRUらしい言葉・方向性】
これらをベースに言葉を選ぶ：
- さりげなく
- 大人が着られる
- 可愛すぎない
- 日常に馴染む
- 犬種愛が伝わる
- 主張しすぎない
- ちゃんと好きが伝わる
- 愛犬との日々を豊かに
- 静かな一枚
- 日常のそばに

【コピーライティングの原則】
長く説明しない。一瞬で意味が取れる言葉を選ぶ。
商品の良さをただ主張せず、「なるほど、だから良いのか」と読み手が納得できる根拠を言語化する。
「良い商品」ではなく「選ぶ理由がある商品」として伝える。
SNSで流し見されても引っかかる一文を必ず入れる。
使用シーンと着た後の感情を具体的に想像させる。
売り手の一方的な主張ではなく、読み手が「自分のための商品だ」と感じられる言葉を選ぶ。

▼ 信頼・根拠を作るフレーズ（必要なときに使う道具。毎回は使わない）
- 「〇〇にしてよかった」→ 購入後の満足
- 「〇〇で気づいた」→ 発見・リアル感
- 「〇〇で大活躍」→ 使用シーン提示
- 「〇〇好きが選ぶ」→ 同志への共感

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

    avg_views = {
        p: s["views"] / s["count"]
        for p, s in pattern_stats.items()
        if s["count"] > 0
    }

    global_avg = sum(avg_views.values()) / len(avg_views) if avg_views else 1.0

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
            topic_hint = f"\n今回取り上げるケアのテーマ：{topic}\n"

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


REPLY_SYSTEM_PROMPT = """
あなたはDGRUのSNS担当者です。
直前の投稿文を受けて、そのURLへ自然につなげる返信の一文を書きます。

【ルール】
- 20〜40文字程度の1文のみ
- 直前の投稿の内容・トーンに合わせて自然につながる言葉を選ぶ
- URLへの誘導は押しつけがましくなく、「よかったら」「気になった方は」程度の温度感で
- 「DGRU」は使っても使わなくてもよい
- 絵文字は使わない
- 「皆さん」は使わない
- 投稿文のみ出力。前置き・説明は不要
"""


def generate_reply_text(breed: str, main_text: str) -> str:
    """投稿文に関連するリプライの一文を生成する"""
    breed_ja = BREEDS.get(breed, {}).get("name_ja", breed)
    prompt = f"""犬種：{breed_ja}
直前の投稿文：
{main_text}

この投稿を受けて、DGRUのアイテムページURLへ自然につなげる返信の一文を書いてください。"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            system=REPLY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"[WARN] 返信文生成失敗: {e}")
        return ""


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


# ============================================================
# しばもちキャラクター投稿（柴犬アカウント専用）
# ============================================================

SHIBA_CHARACTER_SYSTEM_PROMPT = """
あなたは「しばもち」です。柴犬アカウントのキャラクターマスコット。

【しばもちの人格】
- 丸くてふわふわの柴犬。一人称は「ぼく」
- 性格: 食いしん坊、少し頑固、飼い主思い
- 人間の行動を柴犬目線で冷静に、でも温かく見ている
- 口調はやさしく短め
- 語尾はたまに「だわん」「なのだ」「むふ」を自然に使う（多用しない）
- 絵文字は使わない
- 「皆さん」は使わない
- 押し売りはしない

【投稿ルール】
- 2〜4行以内
- 1人に向けて話しかける感覚で書く
- 重い話題・暗い話題は扱わない
- DGRUに触れる場合は「うちのブランド（DGRU）」と自然な形で1回のみ

【出力形式】
投稿文のみ。前置き・説明は一切不要。
"""

SHIBA_CASUAL_SCENES = [
    "おやつを待っているとき",
    "飼い主が出かけていったとき",
    "雨の日に散歩をキャンセルされたとき",
    "換毛期で毛がたくさん抜けているとき",
    "飼い主がスマホばかり見ているとき",
    "冬の朝、布団から出られない飼い主を見ているとき",
    "ごはんの時間が少し遅れているとき",
    "宅急便が来て玄関でそわそわするとき",
    "飼い主が帰ってきたとき",
    "公園でほかの犬に出会ったとき",
    "飼い主が料理しているにおいを追いかけているとき",
    "お気に入りの場所を取られてしまったとき",
    "車に乗るとき",
    "トリミングから帰ってきたとき",
    "夕方の散歩が近づいてきたとき",
]

SHIBA_COMIC_SCENES = [
    "protecting his snack bowl from an imaginary threat, looking very serious",
    "sitting in the passenger seat staring straight ahead while owner drives",
    "frozen at the front door on a rainy day, refusing to go outside",
    "proudly showing off a fresh grooming look",
    "watching owner cook from the kitchen doorway with intense focus",
    "sprawled dramatically after a very short walk, claiming total exhaustion",
    "staring at the clock, waiting for walk time with visible impatience",
    "caught mid-nap in a surprisingly cozy and ridiculous position",
    "giving owner a deeply unimpressed look after being woken up",
    "sitting alone on the sofa looking smug during owner's absence",
    "discovering owner brought home a new dog toy, inspecting it with suspicion",
    "hiding behind owner's legs at the vet, trying to look invisible",
]


def _call_claude_shiba(prompt: str, max_tokens: int = 200) -> str:
    """しばもち専用Claude呼び出し（リトライあり）"""
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=SHIBA_CHARACTER_SYSTEM_PROMPT,
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


def generate_shiba_trend_text(topic_text: str) -> str:
    """トレンド・ニュースに対してしばもちが柴犬目線で反応する投稿文を生成"""
    prompt = f"""今日のニュース・話題（見出しリスト）：
{topic_text}

この中の1つの話題に対して、しばもちが柴犬目線で軽くコメントする投稿文を書いてください。
2〜4行以内。重い話題は避けて、日常・生活・季節・おもしろ系の話題を優先してください。"""
    return _call_claude_shiba(prompt)


def generate_shiba_casual_text() -> str:
    """しばもちの日常ひとコマ投稿文を生成"""
    scene = random.choice(SHIBA_CASUAL_SCENES)
    prompt = f"""シーン：{scene}

このシーンでしばもちが感じていることや思っていることを、短い投稿文にしてください。
2〜4行以内。しばもちらしく。"""
    return _call_claude_shiba(prompt)


def generate_shiba_comic_prompt() -> str:
    """コマ漫画のDALL-E 3用英語プロンプトをClaudeで生成する"""
    system = """You generate DALL-E 3 image prompts for a Japanese-style single-panel comic (1-koma manga).

Character description (MUST follow exactly):
- Name: Shibamochi
- A very round, plump, plush-like Shiba Inu
- Soft orange-brown and cream/white fur
- Small round black eyes, tiny black nose, small curved mouth
- Fluffy curled tail
- Slightly chubby stuffed-animal proportions, no visible neck
- Looks like a living plush toy

Art style (MUST follow exactly):
- Hand-drawn single-panel sketch
- Rough pencil outlines with light cross-hatching
- Soft watercolor or colored-pencil wash
- Warm pastel tones, cozy and slightly humorous feel
- Simple background, no clutter
- NO text, NO speech bubbles, NO logos, NO captions, NO writing of any kind

Output: One English DALL-E 3 prompt only. No explanations. No Japanese."""

    scene = random.choice(SHIBA_COMIC_SCENES)
    prompt = f"Scene: Shibamochi is {scene}. Write a DALL-E 3 prompt for this scene."

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


def generate_shiba_product_text(products: list) -> tuple[str, str]:
    """商品紹介投稿文をしばもち口調で生成。戻り値: (text, pattern_name)"""
    item_names = "、".join(p["item_name"] for p in products[:2])
    prompt = f"""紹介する商品：{item_names}

しばもちが飼い主さんへDGRUの柴犬商品を紹介する投稿文を書いてください。
「飼い主さんに着てもらいたい」「一緒に歩くとちょっと誇らしい」くらいの温度感で。
商品URLは本文に書かない（返信に貼るので不要）。
2〜4行以内。しばもちらしく。"""
    text = _call_claude_shiba(prompt)
    return text, "SHIBA_PRODUCT_INTRO"
