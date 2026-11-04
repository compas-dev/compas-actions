from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

from packaging.tags import Tag, sys_tags
from packaging.utils import InvalidWheelFilename, parse_wheel_filename


def find_distributions(directory: Path) -> tuple[list[Path], list[Path]]:
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if not wheels and not sdists:
        raise ValueError(f"no Python distributions found in {directory}")
    return wheels, sdists


def inspect_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
    wheel = [name for name in names if name.endswith(".dist-info/WHEEL")]
    record = [name for name in names if name.endswith(".dist-info/RECORD")]
    if len(metadata) != 1 or len(wheel) != 1 or len(record) != 1:
        raise ValueError(f"{path} does not contain one complete dist-info record")


def wheel_is_compatible(path: Path, supported: set[Tag] | None = None) -> bool:
    try:
        _, _, _, wheel_tags = parse_wheel_filename(path.name)
    except InvalidWheelFilename as error:
        raise ValueError(f"invalid wheel filename: {path.name}") from error
    supported = supported if supported is not None else set(sys_tags())
    return not wheel_tags.isdisjoint(supported)


def validate_import_modules(modules: list[str]) -> None:
    dotted_identifier = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")
    invalid = [module for module in modules if not dotted_identifier.fullmatch(module)]
    if invalid:
        raise ValueError(f"invalid import module names: {', '.join(invalid)}")


def install_and_import(path: Path, modules: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="compas-wheel-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        subprocess.run([str(python), "-m", "pip", "install", str(path)], check=True)
        for module in modules:
            subprocess.run([str(python), "-c", f"import {module}"], check=True)


def write_outputs(distributions: list[Path]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as stream:
        stream.write("distributions<<EOF\n")
        stream.writelines(f"{distribution}\n" for distribution in distributions)
        stream.write("EOF\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--import-module", action="append", default=[])
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    try:
        wheels, sdists = find_distributions(args.directory)
        validate_import_modules(args.import_module)
        subprocess.run(
            [sys.executable, "-m", "twine", "check", *map(str, wheels + sdists)],
            check=True,
        )
        for wheel in wheels:
            inspect_wheel(wheel)
            if not args.skip_install and wheel_is_compatible(wheel):
                install_and_import(wheel, args.import_module)
            elif not args.skip_install:
                print(
                    f"::notice::Structurally verified non-host wheel; target-platform smoke test required: {wheel}"
                )
        write_outputs(wheels + sdists)
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
