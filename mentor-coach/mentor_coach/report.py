"""メトリクス+LLM分析をMarkdownレポートに整形する。"""

from __future__ import annotations

from typing import Any


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def metrics_markdown(metrics: dict[str, Any]) -> str:
    """定量メトリクスのMarkdownセクション(LLM不要・オフラインで生成可能)。"""
    lines: list[str] = ["## 定量メトリクス", ""]

    ratio = metrics.get("talk_ratio", {})
    if ratio:
        lines.append("### 発話比率")
        for speaker, r in sorted(ratio.items()):
            lines.append(f"- {speaker}: {r * 100:.0f}%")
        lines.append("")

    q = metrics.get("coach_questions", {})
    if q:
        lines.append("### コーチの質問")
        lines.append(
            f"- 質問数: {q['total']} (開かれた質問 {q['open']} / 閉じた質問 {q['closed']})"
        )
        if q.get("open_ratio") is not None:
            lines.append(f"- 開かれた質問の比率: {q['open_ratio'] * 100:.0f}%")
        lines.append("")

    silences = metrics.get("silences", [])
    lines.append(f"### 沈黙 (4秒以上): {len(silences)}回")
    for s in silences[:10]:
        lines.append(
            f"- {_fmt_time(s['start'])} から {s['duration']}秒 "
            f"({s['after_speaker']} の発話後、{s['broken_by']} が破った)"
        )
    lines.append("")

    inter = metrics.get("interruptions", [])
    if inter:
        lines.append(f"### 割り込み: {len(inter)}回")
        for i in inter[:10]:
            lines.append(
                f"- {_fmt_time(i['time'])} {i['interrupter']} が {i['interrupted']} に"
                f"重ねて発話 ({i['overlap']}秒)"
            )
        lines.append("")

    shifts = metrics.get("speech_rate_shifts", [])
    if shifts:
        lines.append("### 話速の急変 (感情変化の確認候補)")
        for p in shifts[:10]:
            arrow = "加速" if p["direction"] == "faster" else "減速"
            lines.append(f"- {_fmt_time(p['time'])} {p['speaker']} が{arrow} (×{p['ratio']})")
        lines.append("")

    topic = metrics.get("topic_shifts", [])
    loops = metrics.get("loops", [])
    if topic:
        lines.append(
            "### 話題転換候補: " + ", ".join(_fmt_time(t["time"]) for t in topic[:10])
        )
    if loops:
        lines.append("### 話題ループ候補")
        for lp in loops[:5]:
            lines.append(
                f"- {_fmt_time(lp['returned_at'])} に {_fmt_time(lp['similar_to'])} 付近の"
                f"話題へ回帰 (類似度 {lp['similarity']})"
            )
    lines.append("")
    return "\n".join(lines)


def build_report(metrics: dict[str, Any], analysis_md: str | None = None) -> str:
    parts = [
        "# コーチングセッション分析レポート",
        "",
        "> 本レポートはAIによる分析です。ICF倫理規程に基づき、セッションの録音・分析には"
        "クライアントの同意が必要です。感情に関する記述はすべて「確認すべき候補」であり断定ではありません。",
        "",
        metrics_markdown(metrics),
    ]
    if analysis_md:
        parts += ["---", "", analysis_md]
    return "\n".join(parts)
