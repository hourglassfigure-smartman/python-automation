"""定量メトリクス層: トランスクリプトから科学的に堅牢な指標を抽出する。

感情推定は行わない。ここで扱うのは測定可能な客観指標のみ:
発話比率 / 沈黙 / 話速 / 割り込み / 質問分類 / 話題転換・ループ候補。
"""

from __future__ import annotations

import re
from typing import Any

from .models import COACH, Segment

# --- 質問検出 ---------------------------------------------------------------

# 開かれた質問(open question)を示す疑問詞
_OPEN_MARKERS = (
    "なぜ", "どうして", "どのよう", "どんな", "どういう", "どう",
    "何が", "何を", "何と", "何に", "なにが", "なにを",
    "いかが", "どこ", "誰", "だれ", "いつ", "どちら", "どれ",
)

_QUESTION_ENDINGS = re.compile(
    r"(か[。．\s]*$|か[?？]$|[?？]$|でしょう[。．]?$|ますか|ですか|のかな[。．]?$)"
)


def is_question(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    return bool(_QUESTION_ENDINGS.search(text)) or text.endswith(("?", "？"))


def classify_question(text: str) -> str:
    """"open"(開かれた質問) / "closed"(閉じた質問) を返す。"""
    return "open" if any(m in text for m in _OPEN_MARKERS) else "closed"


def question_stats(segments: list[Segment], coach_speaker: str = COACH) -> dict[str, Any]:
    questions = []
    for s in segments:
        if s.speaker == coach_speaker and is_question(s.text):
            questions.append(
                {"time": s.start, "text": s.text, "type": classify_question(s.text)}
            )
    n_open = sum(1 for q in questions if q["type"] == "open")
    return {
        "questions": questions,
        "total": len(questions),
        "open": n_open,
        "closed": len(questions) - n_open,
        "open_ratio": round(n_open / len(questions), 2) if questions else None,
    }


# --- 発話比率 / 沈黙 / 話速 / 割り込み --------------------------------------


def talk_ratio(segments: list[Segment]) -> dict[str, float]:
    """話者ごとの発話時間比率。"""
    totals: dict[str, float] = {}
    for s in segments:
        totals[s.speaker] = totals.get(s.speaker, 0.0) + s.duration
    grand = sum(totals.values())
    if grand <= 0:
        return {k: 0.0 for k in totals}
    return {k: round(v / grand, 3) for k, v in totals.items()}


def detect_silences(segments: list[Segment], min_gap: float = 4.0) -> list[dict[str, Any]]:
    """min_gap 秒以上の沈黙。コーチングでは沈黙は考慮すべきシグナル(悪ではない)。"""
    ordered = sorted(segments, key=lambda s: s.start)
    silences = []
    for prev, nxt in zip(ordered, ordered[1:]):
        gap = nxt.start - prev.end
        if gap >= min_gap:
            silences.append(
                {
                    "start": round(prev.end, 1),
                    "duration": round(gap, 1),
                    "after_speaker": prev.speaker,
                    "broken_by": nxt.speaker,
                }
            )
    return silences


def speech_rate_series(segments: list[Segment]) -> list[dict[str, Any]]:
    """セグメントごとの話速(文字/秒)。急な増減は感情変化の候補シグナル。"""
    series = []
    for s in segments:
        if s.duration >= 1.0 and s.char_count > 0:
            series.append(
                {
                    "time": round(s.start, 1),
                    "speaker": s.speaker,
                    "cps": round(s.char_count / s.duration, 2),
                }
            )
    return series


def speech_rate_shifts(
    segments: list[Segment], threshold: float = 1.5
) -> list[dict[str, Any]]:
    """同一話者の直前発話と比べ話速が threshold 倍以上変化した点を抽出。"""
    series = speech_rate_series(segments)
    last: dict[str, float] = {}
    shifts = []
    for p in series:
        prev = last.get(p["speaker"])
        if prev and prev > 0:
            ratio = p["cps"] / prev
            if ratio >= threshold or ratio <= 1 / threshold:
                shifts.append(
                    {
                        "time": p["time"],
                        "speaker": p["speaker"],
                        "direction": "faster" if ratio > 1 else "slower",
                        "ratio": round(ratio, 2),
                    }
                )
        last[p["speaker"]] = p["cps"]
    return shifts


def detect_interruptions(
    segments: list[Segment], min_overlap: float = 0.5
) -> list[dict[str, Any]]:
    """他話者の発話終了前に min_overlap 秒以上重なって話し始めた箇所。"""
    ordered = sorted(segments, key=lambda s: s.start)
    hits = []
    for prev, nxt in zip(ordered, ordered[1:]):
        overlap = prev.end - nxt.start
        if nxt.speaker != prev.speaker and overlap >= min_overlap:
            hits.append(
                {
                    "time": round(nxt.start, 1),
                    "interrupter": nxt.speaker,
                    "interrupted": prev.speaker,
                    "overlap": round(overlap, 1),
                }
            )
    return hits


# --- 話題転換・ループ検知 (字句類似度ベースの簡易実装) -----------------------


def _char_bigrams(text: str) -> set[str]:
    chars = "".join(text.split())
    return {chars[i : i + 2] for i in range(len(chars) - 1)}


def _similarity(a: str, b: str) -> float:
    """文字バイグラムのJaccard類似度 (0.0-1.0)。"""
    ga, gb = _char_bigrams(a), _char_bigrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def _windows(segments: list[Segment], size: int) -> list[dict[str, Any]]:
    ordered = sorted(segments, key=lambda s: s.start)
    wins = []
    for i in range(0, len(ordered), size):
        chunk = ordered[i : i + size]
        wins.append({"start": chunk[0].start, "text": " ".join(s.text for s in chunk)})
    return wins


def detect_topic_shifts(
    segments: list[Segment], window: int = 6, threshold: float = 0.08
) -> list[dict[str, Any]]:
    """隣接ウィンドウ間の類似度が threshold 未満なら話題転換候補。"""
    wins = _windows(segments, window)
    shifts = []
    for prev, nxt in zip(wins, wins[1:]):
        sim = _similarity(prev["text"], nxt["text"])
        if sim < threshold:
            shifts.append({"time": round(nxt["start"], 1), "similarity": round(sim, 3)})
    return shifts


def detect_loops(
    segments: list[Segment], window: int = 6, threshold: float = 0.25, min_distance: int = 2
) -> list[dict[str, Any]]:
    """離れたウィンドウ同士が高類似 = 同じ話題に戻っている(ループ)候補。"""
    wins = _windows(segments, window)
    loops = []
    for j in range(len(wins)):
        for i in range(j - min_distance + 1):
            sim = _similarity(wins[i]["text"], wins[j]["text"])
            if sim >= threshold:
                loops.append(
                    {
                        "returned_at": round(wins[j]["start"], 1),
                        "similar_to": round(wins[i]["start"], 1),
                        "similarity": round(sim, 3),
                    }
                )
    return loops


# --- 集約 --------------------------------------------------------------------


def compute_all(segments: list[Segment], coach_speaker: str = COACH) -> dict[str, Any]:
    """全メトリクスをまとめて計算する。"""
    return {
        "talk_ratio": talk_ratio(segments),
        "silences": detect_silences(segments),
        "speech_rate_shifts": speech_rate_shifts(segments),
        "interruptions": detect_interruptions(segments),
        "coach_questions": question_stats(segments, coach_speaker),
        "topic_shifts": detect_topic_shifts(segments),
        "loops": detect_loops(segments),
    }
