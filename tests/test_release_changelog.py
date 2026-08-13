from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ReleaseChangelogTests(unittest.TestCase):
    def test_prepare_accepts_both_keep_a_changelog_heading_styles(self) -> None:
        for separator in (" ", " - "):
            with self.subTest(separator=separator), tempfile.TemporaryDirectory() as directory:
                changelog = Path(directory) / "CHANGELOG.md"
                heading = f"## [1.2.3]{separator}2026-08-13"
                changelog.write_text(f"# Changelog\n\n{heading}\n\n### Added\n", encoding="utf-8")

                subprocess.run(
                    (sys.executable, ROOT / "release-pr" / "prepare_changelog.py", changelog, "1.2.3"),
                    check=True,
                )

                content = changelog.read_text(encoding="utf-8")
                self.assertEqual(content.count("## Unreleased"), 1)
                self.assertIn(heading, content)

    def test_release_check_accepts_both_keep_a_changelog_heading_styles(self) -> None:
        for separator in (" ", " - "):
            with self.subTest(separator=separator), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory)
                self._git(repository, "init")
                self._git(repository, "config", "user.name", "Tests")
                self._git(repository, "config", "user.email", "tests@example.com")
                self._write_project(repository, "1.2.2")
                (repository / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
                self._git(repository, "add", ".")
                self._git(repository, "commit", "-m", "Base")
                base = self._git(repository, "rev-parse", "HEAD").stdout.strip()

                self._write_project(repository, "1.2.3")
                heading = f"## [1.2.3]{separator}2026-08-13"
                (repository / "CHANGELOG.md").write_text(
                    f"# Changelog\n\n## Unreleased\n\n{heading}\n",
                    encoding="utf-8",
                )
                self._git(repository, "add", ".")
                self._git(repository, "commit", "-m", "Release")
                head = self._git(repository, "rev-parse", "HEAD").stdout.strip()
                output = repository / "output"

                subprocess.run(
                    (
                        sys.executable,
                        ROOT / "release-check" / "check_release.py",
                        "--base",
                        base,
                        "--head",
                        head,
                        "--config",
                        "pyproject.toml",
                        "--changelog",
                        "CHANGELOG.md",
                        "--pull-request-branch",
                        "release/v1.2.3",
                        "--output",
                        output,
                    ),
                    cwd=repository,
                    check=True,
                )

                self.assertEqual(
                    output.read_text(encoding="utf-8").splitlines(),
                    ["is-release=true", "version=1.2.3", "tag=v1.2.3"],
                )

    @staticmethod
    def _git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *args),
            cwd=repository,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )

    @staticmethod
    def _write_project(repository: Path, version: str) -> None:
        (repository / "pyproject.toml").write_text(
            "\n".join(
                (
                    "[tool.bumpversion]",
                    f'current_version = "{version}"',
                    "",
                    "[[tool.bumpversion.files]]",
                    'filename = "CHANGELOG.md"',
                    "",
                )
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
