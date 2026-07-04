"""共通データモデル."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

COACH = "coach"
CLIENT = "client"


@dataclass
class Segment:
    """発話セグメント。speaker は "coach" / "client" を推奨。"""

    speaker: str
    start: float  # 秒
    end: float    # 秒
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def char_count(self) -> int:
        # 日本語向け: 空白を除いた文字数
        return len("".join(self.text.split()))


def load_segments(path: str | Path) -> list[Segment]:
    """JSONファイル([{speaker, start, end, text}, ...])からセグメントを読み込む。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data["segments"]
    return [Segment(**{k: d[k] for k in ("speaker", "start", "end", "text")}) for d in data]


def save_segments(segments: list[Segment], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps([asdict(s) for s in segments], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_transcript(segments: list[Segment]) -> str:
    """LLMに渡すためのタイムスタンプ付きトランスクリプト文字列。"""
    lines = []
    for s in segments:
        m, sec = divmod(int(s.start), 60)
        lines.append(f"[{m:02d}:{sec:02d}] {s.speaker}: {s.text}")
    return "\n".join(lines)
