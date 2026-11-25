"""Check that the tests fail when the rules they protect are broken.

Each mutation deliberately breaks one rule in the source, runs the test
suite and restores the original file (also on error or Ctrl+C). A mutation is
"killed" when at least one test fails; a "survived" mutation means no test
noticed the broken rule.

Usage: uv run python scripts/mutation_check.py
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "review_comments"


@dataclass(frozen=True)
class Mutation:
    id: str
    rule: str
    file: Path
    original: str
    mutated: str


MUTATIONS = [
    Mutation(
        "M1",
        "RF-02 atomic guard: insert without checking the round is still open",
        PKG / "infrastructure" / "sqlite_repository.py",
        "WHERE EXISTS (SELECT 1 FROM rounds WHERE id = ? AND status = 'open')",
        "WHERE EXISTS (SELECT 1 FROM rounds WHERE id = ?)",
    ),
    Mutation(
        "M2",
        "RF-02 service pre-check removed (storage guard still in place)",
        PKG / "application" / "service.py",
        "        if not round_.is_open:\n            raise RoundClosedError(round_.id)\n",
        "",
    ),
    Mutation(
        "M3",
        "RF-01 region not clipped to the item",
        PKG / "domain" / "geometry.py",
        "    left = max(box.x, 0.0)\n    top = max(box.y, 0.0)\n"
        "    right = min(box.right, item_width)\n    bottom = min(box.bottom, item_height)\n"
        "    return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)",
        "    return box",
    ),
    Mutation(
        "M4",
        "RF-01 bounding box off by one pixel",
        PKG / "domain" / "geometry.py",
        "width=right - left, height=bottom - top)\n\n\ndef clip_to_item",
        "width=right - left + 1, height=bottom - top + 1)\n\n\ndef clip_to_item",
    ),
    Mutation(
        "M5",
        "RF-03 closing again overwrites closed_at",
        PKG / "infrastructure" / "sqlite_repository.py",
        "WHERE id = :round_id AND status = 'open'",
        "WHERE id = :round_id",
    ),
    Mutation(
        "M6",
        "RF-01 blank text accepted",
        PKG / "application" / "service.py",
        "        if not command.text.strip():\n            raise BlankFieldError(\"text\")\n",
        "",
    ),
    Mutation(
        "M7",
        "RF-01 reviewer's words rewritten (stripped) before storing",
        PKG / "application" / "service.py",
        "                text=command.text,\n",
        "                text=command.text.strip(),\n",
    ),
    Mutation(
        "M8",
        "DEF-02 fix: closed_at taken from the clock only",
        PKG / "infrastructure" / "sqlite_repository.py",
        "closed_at = max(:closed_at,",
        "closed_at = coalesce(:closed_at,",
    ),
]


def run_tests() -> tuple[bool, list[str]]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    failed = [line.split(" ")[1] for line in result.stdout.splitlines() if line.startswith("FAILED ")]
    return result.returncode == 0, failed


def main() -> int:
    passed, _ = run_tests()
    if not passed:
        print("Baseline suite is not green; fix it before checking mutations.")
        return 2

    survived = 0
    for m in MUTATIONS:
        source = m.file.read_text(encoding="utf-8", newline="")
        if source.count(m.original) != 1:
            print(f"{m.id}  SKIPPED  pattern not found exactly once in {m.file.name}")
            survived += 1
            continue
        try:
            m.file.write_text(source.replace(m.original, m.mutated), encoding="utf-8", newline="")
            passed, failed = run_tests()
        finally:
            m.file.write_text(source, encoding="utf-8", newline="")
        status = "SURVIVED" if passed else "KILLED"
        survived += passed
        print(f"{m.id}  {status:8} {m.rule}")
        for test in failed:
            print(f"      failed: {test}")

    print(f"\n{len(MUTATIONS) - survived}/{len(MUTATIONS)} mutations killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
