"""CLI: トランスクリプト(JSON)または音声ファイルからメンターレポートを生成する。

使い方:
    # メトリクスのみ (API不要・オフライン)
    python -m mentor_coach.cli metrics --transcript samples/sample_transcript.json

    # フル分析 (要 ANTHROPIC_API_KEY)
    python -m mentor_coach.cli analyze --transcript samples/sample_transcript.json -o report.md

    # 音声から (要 requirements-audio.txt / HF_TOKEN)
    python -m mentor_coach.cli analyze --audio session.mp3 -o report.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import metrics as m
from .models import load_segments, save_segments
from .report import build_report


def _get_segments(args: argparse.Namespace):
    if args.transcript:
        segments = load_segments(args.transcript)
    elif args.audio:
        from .transcribe import transcribe_and_diarize

        segments = transcribe_and_diarize(args.audio, hf_token=os.environ.get("HF_TOKEN"))
        if args.save_transcript:
            save_segments(segments, args.save_transcript)
    else:
        raise SystemExit("--transcript または --audio を指定してください")
    if args.swap_speakers:
        from .transcribe import swap_speakers

        segments = swap_speakers(segments)
    return segments


def _add_input_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--transcript", help="セグメントJSONファイル")
    p.add_argument("--audio", help="音声ファイル (mp3/wav等)")
    p.add_argument("--save-transcript", help="音声認識結果のJSON保存先")
    p.add_argument("--swap-speakers", action="store_true", help="coach/client を入れ替える")
    p.add_argument("-o", "--output", help="レポートの出力先 (.md)")


def main(argv: list[str] | None = None) -> int:
    # Windowsコンソール(cp932)での文字化け防止
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="mentor_coach", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_metrics = sub.add_parser("metrics", help="定量メトリクスのみ (API不要)")
    _add_input_args(p_metrics)

    p_analyze = sub.add_parser("analyze", help="メトリクス + PCCマーカー分析")
    _add_input_args(p_analyze)
    p_analyze.add_argument("--model", default=None, help="Claudeモデル ID")

    args = parser.parse_args(argv)
    segments = _get_segments(args)
    computed = m.compute_all(segments)

    analysis = None
    if args.command == "analyze":
        from .analyze import DEFAULT_MODEL, analyze_session

        analysis = analyze_session(segments, computed, model=args.model or DEFAULT_MODEL)

    report = build_report(computed, analysis)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"レポートを書き出しました: {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
