# AIメンターコーチ (Phase 1 プロトタイプ)

コーチングセッションの録音・トランスクリプトを分析し、ICF PCCマーカーに準拠した
メンターコーチングレポートを生成するツール。

設計方針(調査レポートに基づく):
- **セッション後分析型**。リアルタイム割り込みはコーチのプレゼンスを損なうため行わない。
- **感情の断定をしない**。話速変化・沈黙などの客観指標を「確認すべき候補」として提示する。
- **表情分析は行わない**(EU AI Act・科学的妥当性・実装コストの観点から)。

## 構成

```
トランスクリプトJSON or 音声ファイル
  → (音声の場合) faster-whisper + pyannote で文字起こし・話者分離
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
