"""Generate quiz question data from extracted lesson JSON."""
import json
import sys
import random

sys.stdout.reconfigure(encoding='utf-8')

with open('c:/Users/user/elearnig/lesson_data_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

all_conclusions = [(l['num'], l['conclusion']) for l in data if l['conclusion']]
all_drills = [(l['num'], l['drill']) for l in data if l['drill']]

good_reasons = {
    1: '視聴者が自分ごと化でき、コメントが出やすくなるから',
    2: '視認性と音質が安定し、離脱を減らせるから',
    3: '0.8秒で続きを見る理由を提示し、滞在につながるから',
    4: '台本で構成が固定され、沈黙やブレが減るから',
    5: 'コメントが出ることで場の空気が温まり、滞在が伸びるから',
    6: '優先順位をつけることで効率的にコメントを拾えるから',
    7: '3層を同時に回すことで配信が途切れないから',
    8: '反復練習で同時処理が無意識にできるようになるから',
    9: '事前にNG表現を潰すことで事故リスクがゼロに近づくから',
    10: '手順があることでパニックにならず冷静に対処できるから',
    11: 'チェック表で毎回同じ品質を保てるから',
    12: '再現性があることで現場でも安定したパフォーマンスが出せるから',
    13: 'アルゴリズムの仕組みを理解し、反応を設計できるから',
    14: '構成で滞在率を設計し、偶然に頼らないから',
    15: 'サムネとタイトルで興味を引き、CTRを上げられるから',
    16: '3階層で初見から購買層まで対応できるから',
    17: '大量のフックを持つことで冒頭のバリエーションが増えるから',
    18: '3パターンを使い分けることで飽きさせないから',
    19: '信頼を先に構築することで購買への抵抗が減るから',
    20: 'ストーリーがあることで商品の価値が伝わりやすくなるから',
    21: 'FAQ準備で本番中の沈黙や詰まりがなくなるから',
    22: '使用シーンから逆算することで具体的な提案ができるから',
    23: '大量撮影で型が体に入り、本番で自然に出せるから',
    24: 'データに基づいた改善で効率的にPDCAが回るから',
    25: 'KPIを追跡することで改善の方向性が明確になるから',
    26: '1配信1改善で着実にレベルアップできるから',
    27: '変数を1つに絞ることで何が効いたか特定できるから',
    28: '設計→実演→改善が自走することで成長が止まらないから',
    29: '基準が明確だと目標に向けた努力の方向がブレないから',
    30: '構成で60分を管理することで体力勝負にならないから',
    31: '前半で滞在を固めることで後半の販売が安定するから',
    32: '後半で背中押しと満足を両立することでリピートにつながるから',
    33: 'KPIで品質を管理することで事故や品質低下を防げるから',
    34: '商品に役割を持たせることで導線が設計できるから',
    35: 'ショップ全体を設計することでライブ以外の売上も作れるから',
    36: '利益を見ることで持続可能な運営ができるから',
    37: '変数の掛け算で収入を最大化する戦略が立てられるから',
    38: '役割分担で一人の限界を超えられるから',
    39: '勝ち筋が固まってから拡張することで失敗リスクが減るから',
    40: '本番で再現できることが認定の本質だから',
}

ng_reasons = {
    1: '初見が自分ごと化できず、コメントも伸びにくい',
    2: '暗い画面や音割れで視聴者が即離脱する',
    3: '説明が長すぎて0.8秒で興味を引けず離脱される',
    4: '台本なしで沈黙やブレが発生し、視聴者が離れる',
    5: 'コメントを無視すると場の温度が下がり、離脱が増える',
    6: 'すべてのコメントを読もうとして進行が止まる',
    7: '1つの作業に集中しすぎて他の層が崩れる',
    8: '練習不足で本番中にパニックになる',
    9: '規約違反やNG表現で配信停止・アカウント凍結のリスク',
    10: 'トラブル時に手順がなくパニックで対応を誤る',
    11: 'ぶっつけ本番で服装や言い回しが原因の事故が起きる',
    12: '出来た気がするだけで次へ進み、現場で崩れる',
    13: 'アルゴリズムを無視して自分本位の配信をし、露出が減る',
    14: '構成なしで配信し、途中で視聴者が飽きて離脱する',
    15: 'サムネやタイトルが曖昧で、クリックされない',
    16: '全員に同じ話をして、初見も常連も満足しない',
    17: 'フックが1つしかなく、毎回同じ冒頭で飽きられる',
    18: '同じ話法の繰り返しで視聴者が飽きる',
    19: '信頼構築なしに売り込み、視聴者が離れる',
    20: 'スペック説明だけで商品の背景や物語が伝わらない',
    21: '質問に答えられず沈黙が続き、信頼を失う',
    22: '商品の表面的な特徴しか説明できず説得力に欠ける',
    23: '撮影本数が少なく型が身につかない',
    24: '感覚で改善しようとして同じ失敗を繰り返す',
    25: 'KPIを設定しても追跡しないため改善が進まない',
    26: '改善をまとめてやろうとして結局やらない',
    27: '複数の変数を同時に変えて何が効いたか分からない',
    28: '知識だけで満足し、実演が追いつかない',
    29: '基準が曖昧で自己判断に頼り、品質がブレる',
    30: '体力任せで60分を乗り切ろうとして後半が崩れる',
    31: '前半から売り込んで視聴者が離脱する',
    32: '後半で押しすぎて視聴者の満足度が下がる',
    33: '品質管理をせず事故や誤案内が増える',
    34: '全商品を同じ扱いにして導線が機能しない',
    35: 'ライブだけに依存しショップ全体の売上を逃す',
    36: '売上だけを見て利益が出ていない状態を見逃す',
    37: '1つの変数だけに依存して収入の天井にぶつかる',
    38: '全部一人でやろうとして限界に達する',
    39: '勝ち筋が固まる前に拡張して失敗する',
    40: '暗記だけで本番で再現できない',
}

kpi_wrong = {
    1: ['フォロワー数1万人以上を目指す', 'いいね数を最大化する', '配信時間を3時間以上にする'],
    2: ['フォロワー数を増やすことが最優先', 'トレンド商品を扱うことが最優先', 'コラボ配信を増やすことが最優先'],
    3: ['全項目で満点を取ることが目標', '視聴者数だけを追う', 'SNSフォロワー数を最優先にする'],
}

wrong_good_pool = [
    '視聴者数が多いほど売上が上がるから',
    'トレンドに乗ることが最も重要だから',
    '長時間配信するほど成果が出るから',
]
wrong_ng_pool = [
    '配信時間が短すぎることが最大の問題',
    '商品の価格設定が間違っている',
    'フォロワー数が少ないことが根本原因',
]

result = {}
for lesson in data:
    num = lesson['num']
    title_short = lesson['title'].split('\uff5c')[1] if '\uff5c' in lesson['title'] else lesson['title']
    conclusion = lesson['conclusion']
    drill = lesson['drill']
    kpi = lesson['kpi']
    stage = lesson['stage']

    questions = []

    # Q1: Conclusion
    other_conc = [c[1] for c in all_conclusions if c[0] != num]
    random.seed(num * 100 + 1)
    wc = random.sample(other_conc, 3)
    questions.append({
        'text': f'\u300c{title_short}\u300d\u306e\u7d50\u8ad6\u3068\u3057\u3066\u6700\u3082\u9069\u5207\u306a\u3082\u306e\u306f\u3069\u308c\u3067\u3059\u304b\uff1f',
        'explanation': f'\u3053\u306e\u56de\u306e\u7d50\u8ad6\u306f\u300c{conclusion}\u300d\u3067\u3059\u3002',
        'choices': [
            {'text': conclusion, 'is_correct': True},
            {'text': wc[0], 'is_correct': False},
            {'text': wc[1], 'is_correct': False},
            {'text': wc[2], 'is_correct': False},
        ]
    })

    # Q2: KPI
    wk = kpi_wrong.get(stage, kpi_wrong[1])
    questions.append({
        'text': '\u3053\u306e\u56de\u3067\u610f\u8b58\u3059\u308bKPI\u76ee\u5b89\u3068\u3057\u3066\u6b63\u3057\u3044\u3082\u306e\u306f\u3069\u308c\u3067\u3059\u304b\uff1f',
        'explanation': f'KPI\u76ee\u5b89\u306f\u300c{kpi}\u300d\u3067\u3059\u3002\u6570\u5b57\u306f\u7d50\u679c\u3067\u306f\u306a\u304f\u6539\u5584\u306e\u624b\u304c\u304b\u308a\u3068\u3057\u3066\u4f7f\u3044\u307e\u3059\u3002',
        'choices': [
            {'text': kpi, 'is_correct': True},
            {'text': wk[0], 'is_correct': False},
            {'text': wk[1], 'is_correct': False},
            {'text': wk[2], 'is_correct': False},
        ]
    })

    # Q3: GOOD reason
    gr = good_reasons.get(num, '\u578b\u901a\u308a\u306b\u5b9f\u8df5\u3059\u308b\u3053\u3068\u3067\u518d\u73fe\u6027\u304c\u751f\u307e\u308c\u308b\u304b\u3089')
    questions.append({
        'text': '\u3053\u306e\u56de\u306eGOOD\u4f8b\u304c\u52b9\u679c\u7684\u306a\u7406\u7531\u3068\u3057\u3066\u6700\u3082\u9069\u5207\u306a\u3082\u306e\u306f\u3069\u308c\u3067\u3059\u304b\uff1f',
        'explanation': f'GOOD\u4f8b\u306e\u30dd\u30a4\u30f3\u30c8\u306f\u300c{gr}\u300d\u3067\u3059\u3002',
        'choices': [
            {'text': gr, 'is_correct': True},
            {'text': wrong_good_pool[0], 'is_correct': False},
            {'text': wrong_good_pool[1], 'is_correct': False},
            {'text': wrong_good_pool[2], 'is_correct': False},
        ]
    })

    # Q4: NG reason
    nr = ng_reasons.get(num, 'NG\u4f8b\u306f\u578b\u3092\u7121\u8996\u3057\u305f\u884c\u52d5\u3067\u6210\u679c\u304c\u51fa\u306b\u304f\u3044')
    questions.append({
        'text': '\u3053\u306e\u56de\u306eNG\u4f8b\u304c\u554f\u984c\u3068\u306a\u308b\u6700\u5927\u306e\u7406\u7531\u306f\u3069\u308c\u3067\u3059\u304b\uff1f',
        'explanation': f'NG\u4f8b\u306e\u554f\u984c\u70b9\u306f\u300c{nr}\u300d\u3067\u3059\u3002',
        'choices': [
            {'text': nr, 'is_correct': True},
            {'text': wrong_ng_pool[0], 'is_correct': False},
            {'text': wrong_ng_pool[1], 'is_correct': False},
            {'text': wrong_ng_pool[2], 'is_correct': False},
        ]
    })

    # Q5: Drill
    other_dr = [d[1] for d in all_drills if d[0] != num]
    random.seed(num * 100 + 5)
    wd = random.sample(other_dr, 3)
    questions.append({
        'text': '\u3053\u306e\u56de\u306e\u30df\u30cb\u30c9\u30ea\u30eb\u3067\u4f5c\u6210\u3059\u308b\u6210\u679c\u7269\u3068\u3057\u3066\u6b63\u3057\u3044\u3082\u306e\u306f\u3069\u308c\u3067\u3059\u304b\uff1f',
        'explanation': f'\u3053\u306e\u56de\u306e\u30c9\u30ea\u30eb\u306f\u300c{drill}\u300d\u3067\u3059\u3002',
        'choices': [
            {'text': drill, 'is_correct': True},
            {'text': wd[0], 'is_correct': False},
            {'text': wd[1], 'is_correct': False},
            {'text': wd[2], 'is_correct': False},
        ]
    })

    result[num] = questions

with open('c:/Users/user/elearnig/quiz_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

total_q = sum(len(qs) for qs in result.values())
total_c = sum(len(q['choices']) for qs in result.values() for q in qs)
print(f'Total questions: {total_q}')
print(f'Total choices: {total_c}')
print(f'Lessons: {len(result)}')

for q in result[1]:
    print(f'  Q: {q["text"][:60]}')
    for c in q['choices']:
        mark = 'O' if c['is_correct'] else 'X'
        print(f'    [{mark}] {c["text"][:60]}')
