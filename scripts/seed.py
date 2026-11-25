"""Create (or recreate) a database with the fictitious demo data.

Usage: uv run python scripts/seed.py [path]   (default: review.db)
"""

import sys
from pathlib import Path

from review_comments.infrastructure.seed import seed_demo_data
from review_comments.infrastructure.sqlite_repository import SqliteCommentRepository


def main() -> None:
    db_path = Path(sys.argv[1] if len(sys.argv) > 1 else "review.db")
    db_path.unlink(missing_ok=True)
    seed_demo_data(SqliteCommentRepository(db_path))
    print(f"seeded {db_path.resolve()}")


if __name__ == "__main__":
    main()
