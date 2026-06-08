# structured-analysis エージェント

## 概要

確定した I/O とイベントから、プロセス設計一式を作成する。

| 成果物 | 内容 |
|--------|------|
| コンテキスト図（Level 0） | 外部エンティティ＋純入出力 |
| Level-1 DFD | STS 分割（Source → Transform → Sink）+ データストア |
| 単一責務分解 | STS × ワーニエ法で再帰分解 |
| 状態インベントリ | データストアごとに「なぜ要るか・永続性・MVP要否」 |

## 起動タイミング

要件定義が固まった後、論理プロセス設計に着手するとき。

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `.github/agents/structured-analysis.agent.md` | エージェント定義 |
| `.claude/agents/structured-analysis.md` | Claude Code 版 |
| `.github/skills/spec-principles/SKILL.md` | 判断基準 PR1–PR10 |
| `.github/skills/io-event-ledger/SKILL.md` | 入力（I/O台帳・イベントリスト） |
