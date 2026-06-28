# CLAUDE.md

このファイルは、このリポジトリでの作業時に Claude Code に向けたガイダンスです。

## プロジェクト概要

Python による自動化プロジェクト。

## 開発環境

- Python 3.13
- 仮想環境は `.venv/`（Git 管理外）

### セットアップ

```powershell
# 仮想環境の有効化（PowerShell）
.\.venv\Scripts\Activate.ps1

# 依存パッケージのインストール（requirements.txt がある場合）
pip install -r requirements.txt
```

## Git 運用ルール

- **コードを変更するたびに、GitHub にプッシュすること。**
  - 意味のある単位で変更をコミットし、その都度リモート（GitHub）へ push する。
  - 変更を手元に溜め込まず、こまめに同期する。
- コミットメッセージは変更内容が分かるように簡潔に書く。
- `.venv/` やキャッシュ等の生成物はコミットしない（`.gitignore` で管理）。

## コーディング方針

- 周囲の既存コードのスタイル・命名・規約に合わせる。
