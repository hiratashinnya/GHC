"""Workflow constants and configuration.

責務:
    SDLC ワークフロー全体で共通使用する定数群を定義する。
    フェーズ一覧、ファイル名マッピング、ステータス絵文字などを提供する。

入力:
    なし (定数のみ)。

出力:
    インポートした変数で参照する:
    PHASES, PHASE_INDEX, PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION,
    STATUS_EMOJI, NOT_STARTED

副作用:
    なし (定数定義のみ)。

依存モジュール:
    なし (Python 組み込みのみ)。
"""

PHASES = [
    "requirements", "basic-design", "detailed-design",
    "implementation", "testing", "release",
]

PHASE_INDEX = {p: i for i, p in enumerate(PHASES)}

PHASE_LABEL = {
    "requirements": "要件定義",
    "basic-design": "基本設計",
    "detailed-design": "詳細設計",
    "implementation": "実装",
    "testing": "テスト",
    "release": "リリース",
}

# Standard process → filename (non-detailed-design phases)
PROC_FILE = {
    1: "01-validation.md",
    2: "02-breakdown.md",
    3: "03-decisions.md",
    4: "04-artifact.md",
    5: "05-verification.md",
}

# Detailed-design overview-level files
DD_OVERVIEW = {
    1: "01-validation.md",
    2: "02-breakdown-overview.md",
    3: "03-decisions-overview.md",
    4: "04-artifact-overview.md",
    5: "05-verification-overview.md",
}

DD_VALIDATION = "02-breakdown-validation.md"

STATUS_EMOJI = {
    "approved":          "✅",
    "awaiting-approval": "⏳",
    "draft":             "📝",
    "rejected":          "❌",
    "under-revision":    "🔙",
}

NOT_STARTED = "─"
