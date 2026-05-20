#!/usr/bin/env python3
"""
Pre-commit hook to check Alembic migrations for unsafe patterns.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple


def check_syntax(filepath: str, content: str) -> List[Tuple[int, str]]:
    """Check Python syntax. Returns list of (line, error) tuples."""
    errors = []
    try:
        compile(content, filepath, 'exec')
    except (SyntaxError, IndentationError) as e:
        errors.append((e.lineno or 0, f"{type(e).__name__}: {e.msg}"))
    return errors


def check_migration_safety(filepath: str) -> List[Tuple[int, str]]:
    """
    Check migration file for unsafe patterns.
    Returns list of (line_num, description) tuples.
    """
    issues = []

    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.splitlines()

    # 1. Check Python syntax first
    syntax_errors = check_syntax(filepath, content)
    if syntax_errors:
        issues.extend([(l, f"Syntax error: {e}") for l, e in syntax_errors])
        return issues  # No point checking further

    # 2. Check for ALTER TABLE on tables that might not exist
    # Look for lines with ALTER TABLE that are NOT inside a DO $$ block
    in_do_block = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track DO $$ block depth
        if re.search(r'DO\s+\$\$', stripped, re.IGNORECASE):
            in_do_block += 1
        if re.search(r'END\s+\$\$', stripped, re.IGNORECASE):
            in_do_block = max(0, in_do_block - 1)

        # Only check outside of DO $$ blocks (inside is already guarded)
        if in_do_block == 0:
            # ALTER TABLE without IF EXISTS/IF NOT EXISTS on the table itself
            if re.search(r'ALTER TABLE\s+\w+\s+ADD\s+COLUMN', stripped, re.IGNORECASE):
                if 'IF NOT EXISTS' not in stripped:
                    issues.append((i, f"ALTER TABLE ADD COLUMN without IF NOT EXISTS"))

            # Bare UPDATE statement (not inside DO block)
            if re.search(r'^UPDATE\s+\w+', stripped, re.IGNORECASE):
                issues.append((i, "UPDATE statement without table existence check - wrap in DO $$ block"))

            # INSERT INTO without DO block
            if re.search(r'^INSERT INTO\s+\w+', stripped, re.IGNORECASE):
                issues.append((i, "INSERT statement without table existence check - wrap in DO $$ block"))

    return issues


def main(filenames: List[str]) -> int:
    failed = []

    for filename in filenames:
        if not filename.endswith('.py'):
            continue
        if 'alembic/versions' not in filename and '/versions/' not in filename:
            continue
        if '__init__' in filename:
            continue

        issues = check_migration_safety(filename)
        if issues:
            print(f"\n⚠️  {Path(filename).name}:")
            for line_num, description in issues:
                print(f"  Line {line_num}: {description}")
            failed.append(filename)

    if failed:
        print(f"\n❌ {len(failed)} migration file(s) have issues.")
        print("See backend/alembic/MIGRATION_BEST_PRACTICES.md for guidance.")
        print("\nTo bypass (not recommended): git commit --no-verify\n")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
