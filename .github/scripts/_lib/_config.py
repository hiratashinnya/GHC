"""Workflow constants and configuration."""

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
