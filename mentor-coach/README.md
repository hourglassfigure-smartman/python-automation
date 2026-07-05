# AIメンターコーチ (Phase 1 プロトタイプ)

コーチングセッションの録音・トランスクリプトを分析し、ICF PCCマーカーに準拠した
メンターコーチングレポートを生成するツール。

設計方針(調査レポートに基づく):
- **セッション後分析型**。リアルタイム割り込みはコーチのプレゼンスを損なうため行わない。
- **感情の断定をしない**。話速変化・沈黙などの客観指標を「確認すべき候補」として提示する。
- **表情分析は行わない**(EU AI Act・科学的妥当性・実装コストの観点から)。

## 構成

```
トランスクリプトJSON / 音声ファイル / Plaud録音
  → (音声の場合)  faster-whisper + pyannote で文字起こし・話者分離
  → (Plaudの場合) Plaud MCP の get_transcript で文字起こし取得 (話者・時刻付き)
  → metrics.py: 発話比率 / 沈黙 / 話速変化 / 割り込み / 質問分類 / 話題転換・ループ
  → analyze.py: Claude が PCCマーカー照合・強力な質問・見逃しテーマを分析
  → report.py: Markdownレポート
```

## セットアップ

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r mentor-coach\requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # analyze コマンドに必要
```

音声ファイルから直接分析する場合(オプション、モデルのダウンロードが発生します):

```powershell
pip install -r mentor-coach\requirements-audio.txt
$env:HF_TOKEN = "hf_..."  # pyannote の話者分離モデルに必要
```

## 使い方

```powershell
cd mentor-coach

# 定量メトリクスのみ (APIキー不要)
python -m mentor_coach.cli metrics --transcript samples\sample_transcript.json

# フル分析レポート (Claude API 使用)
python -m mentor_coach.cli analyze --transcript samples\sample_transcript.json -o report.md

# 音声ファイルから
python -m mentor_coach.cli analyze --audio session.mp3 --save-transcript transcript.json -o report.md
```

話者の自動判定(質問率ヒューリスティック)が誤っていた場合は `--swap-speakers` を付けてください。

## Plaud の録音から直接分析する

Plaud は録音時に話者ラベル・タイムスタンプ付きの文字起こしを生成するため、
`get_transcript` の結果をそのまま分析に流し込めます(自前のASR・話者分離が不要)。

セットアップ:

```powershell
pip install -r mentor-coach\requirements-plaud.txt   # Python MCP SDK
# Node.js / npx が必要 (Plaud MCP は npx -y @plaud-ai/mcp@latest で起動)
# 初回実行時にブラウザで Plaud OAuth ログインが走ります
```

使い方:

```powershell
cd mentor-coach
python -m mentor_coach.cli plaud-list                          # 録音一覧 (ID / 日付 / タイトル)
python -m mentor_coach.cli analyze --plaud-latest -o report.md # 最新録音を分析
python -m mentor_coach.cli analyze --plaud-file-id <ID> -o report.md
```

Plaud のレスポンス項目名や時間単位(秒/ミリ秒)が想定と異なる場合は、
[mentor_coach/plaud.py](mentor_coach/plaud.py) の `_map_item()` と `TIME_SCALE` を調整してください。

> Claude Desktop / Claude Code から会話的に使う場合は、`~/.claude/` 等のMCP設定に
> `{"mcpServers": {"plaud": {"command": "npx", "args": ["-y", "@plaud-ai/mcp@latest"]}}}`
> を追加し、「Plaudの最新録音の文字起こしを取得して」と依頼 → 得たJSONを本ツールに渡します。

## テスト

```powershell
cd mentor-coach
python -m unittest discover -s tests -v
```

## トランスクリプトJSONの形式

```json
[
  {"speaker": "coach", "start": 0.0, "end": 6.0, "text": "今日は何をお話ししますか。"},
  {"speaker": "client", "start": 7.0, "end": 20.0, "text": "..."}
]
```

## 倫理・法的注意

- セッションの録音・AI分析には**クライアントの事前同意**が必要です(ICF倫理規程 2025)。
- EU圏の企業内コーチング(クライアント=従業員)では、生体データからの感情推定は
  EU AI Act 第5条により禁止されています。本ツールが感情を断定しないのはこのためです。
- 本ツールはICF資格取得に必要なメンターコーチング時間の代替にはなりません。
