"""LLM分析層: トランスクリプト+定量メトリクスをICF PCCマーカーに照合する。"""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from .models import Segment, format_transcript

DEFAULT_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
あなたはICF(国際コーチング連盟)のMCC(マスター認定コーチ)資格を持つ経験豊富なメンターコーチです。
コーチングセッションのトランスクリプトと定量メトリクスをもとに、コーチの成長を支援する
建設的なフィードバックを日本語で提供します。

評価の枠組みはICF PCCマーカー(2020年改訂版)に準拠します。対象コンピテンシー:
- 2. 倫理に基づいた行動 / 3. 合意の締結と維持 / 4. 信頼と安全を育む
- 5. プレゼンスを維持する / 6. 積極的に傾聴する / 7. 気づきを引き起こす
- 8. クライアントの成長を促進する

重要な原則:
- 感情の断定はしない。話速・沈黙などのシグナルは「変化の候補」として提示し、
  確認はコーチ自身の記憶とクライアントとの対話に委ねる。
- 良かった点を具体的な発言引用とともに先に示し、改善点は「次の機会にどう試すか」の形で提案する。
- 各指摘には必ずタイムスタンプと発言の引用を添える(根拠のない一般論は書かない)。
- これは人間のメンターコーチングの代替ではなく、その準備・補完である旨をわきまえる。
"""

USER_TEMPLATE = """\
以下はコーチングセッションのトランスクリプトと、自動計算した定量メトリクスです。

# トランスクリプト
{transcript}

# 定量メトリクス (JSON)
{metrics_json}

以下の構成でメンターコーチとしての分析レポートをMarkdownで作成してください:

## 1. セッション概観
セッションの流れとテーマの3〜5行の要約。

## 2. 強力だった質問
特に効果的だったコーチの質問を最大5つ、タイムスタンプ・引用・PCCマーカーとの対応・
なぜ効果的だったかの分析とともに。

## 3. PCCマーカー照合
各コンピテンシー(4〜8)について、観察されたマーカー(発言引用つき)と観察されなかった
重要マーカーを整理。

## 4. 注目すべきシグナル
定量メトリクス(沈黙・話速変化・話題ループ・割り込み・発話比率)から、コーチが
振り返るべきポイントを解釈。感情は断定せず「〜の可能性を確認したい」の形で。

## 5. 見逃した可能性のあるテーマ
クライアントの発言に含まれていたが深掘りされなかったテーマの候補。

## 6. 次のセッションへの実験提案
コーチが次に試せる具体的な行動を3つ以内で。
"""


def analyze_session(
    segments: list[Segment],
    metrics: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> str:
    """セッションを分析し、Markdownのメンターレポート本文を返す。"""
    client = Anthropic()
    prompt = USER_TEMPLATE.format(
        transcript=format_transcript(segments),
        metrics_json=json.dumps(metrics, ensure_ascii=False, indent=1),
    )
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    return "".join(b.text for b in message.content if b.type == "text")
