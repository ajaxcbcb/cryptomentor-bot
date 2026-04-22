#!/usr/bin/env python3
"""Fail CI/pre-commit when tracked files contain high-risk secret patterns."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


DISALLOWED_TRACKED_PATHS = [
    re.compile(r"(^|/)\.env$", re.IGNORECASE),
    re.compile(r"(^|/)\.env\.local$", re.IGNORECASE),
    re.compile(r"^Bismillah/data/users_local\.json$", re.IGNORECASE),
]

PLACEHOLDER_HINTS = {
    "replace_with",
    "your_",
    "example",
    "<",
    ">",
    "changeme",
    "redacted",
}

PATTERNS = [
    ("telegram_bot_token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b")),
    ("supabase_jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("hardcoded_ssh_password", re.compile(r"ssh\.connect\([^\n]*password\s*=\s*['\"][^'\"]+['\"]")),
    ("hardcoded_vps_password", re.compile(r"\bVPS_PASSWORD\s*=\s*['\"][^'\"]+['\"]")),
    ("wl_secret_uuid", re.compile(r"\bWL_SECRET_KEY\s*=\s*[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}")),
    ("hardcoded_api_key", re.compile(r"\bAPI_KEY\s*=\s*['\"][A-Za-z0-9_-]{20,}['\"]")),
]


def _tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], text=True, encoding="utf-8", errors="ignore")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _looks_like_placeholder(line: str) -> bool:
    low = line.lower()
    return any(hint in low for hint in PLACEHOLDER_HINTS)


def main() -> int:
    violations: list[str] = []
    tracked = _tracked_files()

    for rel in tracked:
        for blocked in DISALLOWED_TRACKED_PATHS:
            if blocked.search(rel):
                violations.append(f"disallowed_tracked_file|{rel}")
                break

        path = Path(rel)
        if not path.exists() or not path.is_file():
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS:
                if not pattern.search(line):
                    continue
                if _looks_like_placeholder(line):
                    continue
                violations.append(f"{name}|{rel}:{lineno}")

    if violations:
        print("Security policy violation(s) found:")
        for row in violations:
            print(f" - {row}")
        print(
            "\nFix the values (use env/secret manager placeholders) and retry. "
            "Do not commit live credentials or local runtime data snapshots."
        )
        return 1

    print("Security policy check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

