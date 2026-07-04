"""音声→セグメント変換 (オプション機能)。

faster-whisper (ASR) と pyannote.audio (話者分離) が必要。
requirements-audio.txt を参照。pyannote は Hugging Face のアクセストークンと
モデル利用規約への同意が必要: https://huggingface.co/pyannote/speaker-diarization-3.1
"""

from __future__ import annotations

from .models import CLIENT, COACH, Segment
from .metrics import is_question


def transcribe_and_diarize(
    audio_path: str,
    hf_token: str | None = None,
    language: str = "ja",
    whisper_model: str = "large-v3",
) -> list[Segment]:
    """音声ファイルから話者ラベル付きセグメントを生成する。"""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise ImportError(
            "faster-whisper が必要です: pip install -r requirements-audio.txt"
        ) from e
    try:
        from pyannote.audio import Pipeline
    except ImportError as e:
        raise ImportError(
            "pyannote.audio が必要です: pip install -r requirements-audio.txt"
        ) from e

    # 1. ASR
    model = WhisperModel(whisper_model, device="auto", compute_type="auto")
    whisper_segments, _ = model.transcribe(audio_path, language=language, vad_filter=True)
    asr = [(s.start, s.end, s.text.strip()) for s in whisper_segments]

    # 2. 話者分離
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
    )
    diarization = pipeline(audio_path, num_speakers=2)
    turns = [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]

    # 3. ASRセグメントに最大重複の話者を割り当て
    segments = []
    for start, end, text in asr:
        best, best_overlap = "unknown", 0.0
        for t_start, t_end, speaker in turns:
            overlap = min(end, t_end) - max(start, t_start)
            if overlap > best_overlap:
                best, best_overlap = speaker, overlap
        segments.append(Segment(speaker=best, start=start, end=end, text=text))

    return relabel_speakers(segments)


def relabel_speakers(segments: list[Segment]) -> list[Segment]:
    """SPEAKER_00/01 を coach/client に置き換える。

    ヒューリスティック: 発話あたりの質問率が高い話者をコーチとみなす。
    誤判定の可能性があるため、CLIの --swap-speakers で反転可能。
    """
    speakers = sorted({s.speaker for s in segments})
    if len(speakers) != 2:
        return segments
    rates = {}
    for sp in speakers:
        utterances = [s for s in segments if s.speaker == sp]
        rates[sp] = sum(1 for s in utterances if is_question(s.text)) / len(utterances)
    coach_label = max(speakers, key=lambda sp: rates[sp])
    mapping = {sp: (COACH if sp == coach_label else CLIENT) for sp in speakers}
    return [
        Segment(speaker=mapping[s.speaker], start=s.start, end=s.end, text=s.text)
        for s in segments
    ]


def swap_speakers(segments: list[Segment]) -> list[Segment]:
    flip = {COACH: CLIENT, CLIENT: COACH}
    return [
        Segment(speaker=flip.get(s.speaker, s.speaker), start=s.start, end=s.end, text=s.text)
        for s in segments
    ]
