# spec-inspector エージェント

## 概要

I/O台帳・イベントリスト・DFD・スキーマ・実装設計の凍結セットを**読み取り専用で点検**し、カバレッジギャップ・台帳番号不一致・矛盾を番号付き gap リスト（G#）として返す。矛盾は解決せず STOP として報告する。

## 起動タイミング

- 要件・台帳・イベントリスト・設計ドキュメントを編集した後に実行
- `impl-design-pipeline` の総点検として使用

## 出力

- 矛盾があれば **「🛑 STOP — 要確認」** 節
- gap 表: `G# | 種別 | 箇所 | 根拠(PR#) | 推奨アクション`
- 1–2行の総括

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `.github/agents/spec-inspector.agent.md` | エージェント定義 |
| `.claude/agents/spec-inspector.md` | Claude Code 版 |
| `.github/skills/spec-principles/SKILL.md` | 判断基準 PR1–PR10 |
