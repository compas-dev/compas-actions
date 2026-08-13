from __future__ import annotations

import argparse
import re
from pathlib import Path


UNRELEASED = "## Unreleased\n\n### Added\n\n### Changed\n\n### Removed\n\n\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("changelog", type=Path)
    parser.add_argument("version")
    args = parser.parse_args()

    content = args.changelog.read_text(encoding="utf-8")
    release_heading = re.compile(rf"^## \[{re.escape(args.version)}\] (?:- )?\d{{4}}-\d{{2}}-\d{{2}}$", re.MULTILINE)
    matches = list(release_heading.finditer(content))
    if len(matches) != 1:
        raise SystemExit(f"Expected one release heading for {args.version}, found {len(matches)}")
    if re.search(r"^## Unreleased$", content, re.MULTILINE):
        raise SystemExit("The version bump left an unexpected Unreleased heading")

    start = matches[0].start()
    args.changelog.write_text(content[:start] + UNRELEASED + content[start:], encoding="utf-8")


if __name__ == "__main__":
    main()
