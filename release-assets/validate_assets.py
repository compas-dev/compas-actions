from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path


def matched_files(patterns: list[str], *, allow_missing: bool = False) -> list[Path]:
    files: set[Path] = set()
    missing: list[str] = []
    for pattern in patterns:
        matches = [Path(path) for path in glob.glob(pattern, recursive=True)]
        expanded = [
            path
            for match in matches
            for path in ([match] if match.is_file() else match.rglob("*"))
            if path.is_file()
        ]
        if not expanded:
            missing.append(pattern)
        files.update(expanded)
    if missing and not allow_missing:
        raise ValueError(f"no files match: {', '.join(missing)}")
    empty = sorted(str(path) for path in files if path.stat().st_size == 0)
    if empty:
        raise ValueError(f"empty release assets: {', '.join(empty)}")
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pattern", nargs="+")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()
    try:
        files = matched_files(args.pattern, allow_missing=args.allow_missing)
    except (OSError, ValueError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    for path in files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
