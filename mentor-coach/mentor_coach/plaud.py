"""Plaud MCP アダプタ: Plaud の録音から文字起こしを取得して Segment に変換する。

Plaud MCP (https://docs.plaud.ai/plaud-mcp-cli/mcp) は stdio で起動し、
`get_transcript` が「話者ラベル＋タイムスタンプ付きの全文」を返す。
このため faster-whisper / pyannote を使わず、Plaud の録音から直接分析できる。

必要なもの:
    - Node.js / npx (Plaud MCP は `npx -y @plaud-ai/mcp@latest` で起動)
    - Python MCP SDK: pip install -r requirements-plaud.txt
    - 初回のみブラウザでの Plaud OAuth ログイン (トークンは ~/.plaud/tokens-mcp.json)

なお Plaud のレスポンス項目名・時間単位は環境により差がありうるため、
_map_item() と TIME_SCALE の2箇所だけ実データに合わせて微調整できるようにしている。
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
from typing import Any

from .models import Segment
from .transcribe import relabel_speakers

# get_transcript の時間がミリ秒で返る場合は 0.001 を指定 (秒なら 1.0)
TIME_SCALE = 1.0


def _resolve_npx() -> str:
    for candidate in ("npx", "npx.cmd"):
        found = shutil.which(candidate)
        if found:
            return found
    return "npx"


def _server_params():
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=_resolve_npx(), args=["-y", "@plaud-ai/mcp@latest"]
    )


async def _call_tool(tool: str, arguments: dict[str, Any]) -> Any:
    """Plaud MCP のツールを1回呼び、テキスト結果を JSON としてパースして返す。"""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
    except ImportError as e:
        raise ImportError(
            "Python MCP SDK が必要です: pip install -r requirements-plaud.txt"
        ) from e

    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)

    text = "".join(
        getattr(c, "text", "") for c in result.content if getattr(c, "type", None) == "text"
    )
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text}


# --- 時間・話者・項目のパース (実データに合わせて調整しやすくしている) ----------


def _to_seconds(value: Any) -> float:
    """数値(秒/ミリ秒) または "HH:MM:SS(.ms)" 文字列を秒に変換する。"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) * TIME_SCALE
    if isinstance(value, str):
        value = value.strip()
        if re.fullmatch(r"\d+(\.\d+)?", value):
            return float(value) * TIME_SCALE
        if ":" in value:
            sec = 0.0
            for part in value.split(":"):
                sec = sec * 60 + float(part)
            return sec
    return 0.0


def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _map_item(item: dict) -> Segment | None:
    text = _first(item, "text", "content", "transcript", "sentence", default="")
    if not str(text).strip():
        return None
    speaker = _first(
        item, "speaker", "speaker_label", "speakerLabel", "speaker_name", "speaker_id",
        default="unknown",
    )
    start = _to_seconds(_first(item, "start", "start_time", "startTime", "begin", "ts"))
    end = _to_seconds(_first(item, "end", "end_time", "endTime", "stop", default=start))
    if end < start:
        end = start
    return Segment(speaker=str(speaker), start=start, end=end, text=str(text).strip())


def _extract_list(data: Any) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("segments", "transcript", "utterances", "sentences", "results",
                    "items", "data", "files", "recordings"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                nested = _extract_list(value)
                if nested:
                    return nested
    return []


# --- 公開 API ---------------------------------------------------------------


def list_recordings(
    keyword: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """録音一覧 (id / title / date を含む dict のリスト) を返す。"""
    args: dict[str, Any] = {}
    if keyword:
        args["keyword"] = keyword
    if since:
        args["start_date"] = since
    if until:
        args["end_date"] = until
    if limit:
        args["limit"] = limit
    data = asyncio.run(_call_tool("list_files", args))
    return _extract_list(data)


def fetch_transcript(file_id: str) -> list[Segment]:
    """指定録音の文字起こしを取得し、coach/client ラベル付きの Segment 列を返す。"""
    data = asyncio.run(_call_tool("get_transcript", {"file_id": file_id}))
    items = _extract_list(data)
    segments = [s for s in (_map_item(i) for i in items) if s is not None]
    if not segments:
        raise RuntimeError(
            f"文字起こしを解釈できませんでした (file_id={file_id})。"
            "plaud.py の _map_item() を実データに合わせて調整してください。"
        )
    segments.sort(key=lambda s: s.start)
    # Plaud の話者ラベル(例: Speaker 1/2)を質問率ヒューリスティックで coach/client に割当
    return relabel_speakers(segments)


def latest_file_id() -> str:
    """最新の録音の file_id を返す。"""
    recordings = list_recordings(limit=1)
    if not recordings:
        raise RuntimeError("Plaud に録音が見つかりませんでした。")
    file_id = _first(recordings[0], "id", "file_id", "fileId", "uuid")
    if not file_id:
        raise RuntimeError(f"録音IDを特定できませんでした: {recordings[0]!r}")
    return str(file_id)
