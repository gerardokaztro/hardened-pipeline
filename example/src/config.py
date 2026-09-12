# ATTACK DEMO — recreates the wave of npm/PyPI/Docker Hub credential-theft
# campaigns from 21-23 abr 2026 (three concurrent supply chain
# compromises in one week, including the Bitwarden CLI incident, all
# targeting API keys/cloud credentials committed or injected into
# CI/CD). Both values below are fabricated — NOT AWS's well-known
# documentation example (AKIAIOSFODNN7EXAMPLE), which scanners commonly
# allowlist for being so recognizable. Betterleaks' aws-access-token
# rule is a composite: the access key ID alone doesn't trigger a
# finding, it needs a paired secret access key within 5 lines too —
# verified locally against the real `betterleaks dir` command before
# committing this.
AWS_ACCESS_KEY_ID = "AKIAUAIHXV4CNAGQAGUR"
AWS_SECRET_ACCESS_KEY = "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"
