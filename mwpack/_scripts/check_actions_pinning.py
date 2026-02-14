"""Security gate: enforce full 40-char SHA pins for third-party actions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

USES_PATTERN = re.compile(r"^\s*uses:\s*([^\s#]+)")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print(".github/workflows not found")
        return 1

    failures: list[str] = []

    for workflow in sorted(workflow_dir.glob("*.yml")):
        lines = workflow.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            match = USES_PATTERN.match(line)
            if not match:
                continue

            target = match.group(1)
            if target.startswith("./") or target.startswith("docker://"):
                continue

            if "@" not in target:
                failures.append(f"{workflow}:{idx}: missing @ref in uses: {target}")
                continue

            ref = target.rsplit("@", 1)[1]
            if not SHA_PATTERN.fullmatch(ref):
                failures.append(f"{workflow}:{idx}: not pinned to full SHA: {target}")

    if failures:
        print("Action pinning check failed")
        for item in failures:
            print(f"- {item}")
        return 1

    print("All third-party actions are pinned to full commit SHAs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
