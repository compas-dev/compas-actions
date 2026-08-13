from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def git(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, text=True, stdout=subprocess.PIPE).stdout


def read_at(ref: str, path: str) -> bytes:
    return subprocess.run(("git", "show", f"{ref}:{path}"), check=True, stdout=subprocess.PIPE).stdout


def config_at(ref: str, path: str) -> dict:
    return tomllib.loads(read_at(ref, path).decode())


def version(config: dict) -> str:
    try:
        return str(config["tool"]["bumpversion"]["current_version"])
    except KeyError as error:
        raise SystemExit("Missing tool.bumpversion.current_version") from error


def configured_files(config: dict, config_path: str) -> set[str]:
    files = {config_path}
    for item in config["tool"]["bumpversion"].get("files", []):
        files.add(str(item["filename"]))
    return files


def write_output(path: Path, name: str, value: str) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"{name}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--config", default="pyproject.toml")
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument("--pull-request-branch", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base_config = config_at(args.base, args.config)
    head_config = config_at(args.head, args.config)
    old_version = version(base_config)
    new_version = version(head_config)

    if old_version == new_version:
        write_output(args.output, "is-release", "false")
        write_output(args.output, "version", "")
        write_output(args.output, "tag", "")
        return

    old_match = SEMVER.fullmatch(old_version)
    new_match = SEMVER.fullmatch(new_version)
    if not old_match or not new_match:
        raise SystemExit(f"Only stable semantic versions are supported: {old_version} -> {new_version}")
    old_parts = tuple(map(int, old_match.groups()))
    new_parts = tuple(map(int, new_match.groups()))
    if new_parts <= old_parts:
        raise SystemExit(f"Version must increase: {old_version} -> {new_version}")
    valid_bumps = {
        (old_parts[0], old_parts[1], old_parts[2] + 1),
        (old_parts[0], old_parts[1] + 1, 0),
        (old_parts[0] + 1, 0, 0),
    }
    if new_parts not in valid_bumps:
        raise SystemExit(f"Version must be one patch, minor, or major bump: {old_version} -> {new_version}")

    expected_branch = f"release/v{new_version}"
    if args.pull_request_branch and args.pull_request_branch != expected_branch:
        raise SystemExit(f"A version change must use branch {expected_branch}, not {args.pull_request_branch}")

    changelog = read_at(args.head, args.changelog).decode()
    if len(re.findall(r"^## Unreleased$", changelog, re.MULTILINE)) != 1:
        raise SystemExit("The changelog must contain exactly one Unreleased section")
    release_heading = re.compile(rf"^## \[{re.escape(new_version)}\] (?:- )?\d{{4}}-\d{{2}}-\d{{2}}$", re.MULTILINE)
    if len(release_heading.findall(changelog)) != 1:
        raise SystemExit(f"The changelog must contain exactly one release heading for {new_version}")

    allowed = configured_files(head_config, args.config)
    changed = set(git("diff", "--name-only", args.base, args.head).splitlines())
    unexpected = sorted(changed - allowed)
    if unexpected:
        raise SystemExit("Release changes files outside the version configuration: " + ", ".join(unexpected))

    write_output(args.output, "is-release", "true")
    write_output(args.output, "version", new_version)
    write_output(args.output, "tag", f"v{new_version}")


if __name__ == "__main__":
    main()
