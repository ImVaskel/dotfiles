#!/usr/bin/env python3

from __future__ import annotations
import argparse
import enum
import logging
import platform
import re

import typing
from pathlib import Path

logger = logging.Logger("dotfiles", level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[{levelname:<8}]: {message}", style="{"))
logger.addHandler(handler)


class Condition(enum.IntEnum):
    host = 2
    hostname = 2
    os = 1
    default = 0


class Override(typing.NamedTuple):
    cond: Condition
    comp: str | None
    name: str


def hostname_condition(comp: str | None):
    res = platform.uname()
    return comp == res.node


def os_condition(comp: str | None):
    res = platform.uname()
    # Check if we are WSL first.
    if "WSL" in res.release and comp == "WSL":
        return True
    return comp == res.system


CONDITIONS_CALLABLE_MAP: dict[Condition, typing.Callable[[str | None], bool]] = {
    Condition.hostname: hostname_condition,
    Condition.host: hostname_condition,
    Condition.os: os_condition,
}

DOTFILES = Path(__file__).absolute().parent
HOME = Path.home()

# A list of ignored file/directory names.
# .git shouldn't be symlinked, and bin, overrides, and this script are special cased
# pycache shouldn't be either, gitignore is local to this directory, readme is too.
IGNORED_NAMES = [
    ".git",
    "overrides",
    "bin",
    "dotfiles.py",
    "__pycache__",
    ".gitignore",
    "README.md",
]
IGNORED_PATHS = [DOTFILES / Path(p) for p in IGNORED_NAMES]

# This regex matches foo.bar@baz, where ``foo`` is a condition, ``bar`` is a comparison for that condition,
# and baz is the file name. It also includes groups to extract these variables if applicable.
CONDITIONAL_REGEX = re.compile(r"(?P<cond>[a-zA-Z]+)\.(?P<comp>[a-zA-Z]+)@(?P<name>.+)")
VALID_CONDITIONS = ["os", "host", "hostname"]
# This regex only matches default@name (case insensitive).
DEFAULT_REGEX = re.compile(r"default@(?P<name>.+)", flags=re.I)


def get_relative_to_home(path: Path) -> Path:
    # turns /home/person/dotfiles/path to path/, then to /home/person/path
    return HOME / path.relative_to(DOTFILES)


def get_relative_overrides_to_home(path: Path) -> Path:
    # turns /home/person/dotfiles/overrides/path to path/ then to /home/person/path
    return HOME / path.relative_to(DOTFILES / "overrides")


def parse_override_name(name: str) -> Override:
    """Parses a given file name into 3 strings: the condition (if applicable), the comparison for that condition, and the real name.
    The syntax for the condition (if applicable) should be ``cond.Comp@name`` or ``default@name``. Files can contain an ``@`` in their filename
    regardless of whether they have a condition.

    Args:
        name (str): The name of the file. It should be in the format ``cond.Comp@name``, ``default@name``, or ``name``.

    Returns:
        Override:  A NamedTuple, with the first element being the condition (os, hostname, etc),
            the second being the parsed conditional to compare to, and the third being the parsed file name.
            If ``default`` is parsed out, element 2 will be ``None``.
            ``name`` will always be present, regardless of whether an override match was found.
    """
    if match := DEFAULT_REGEX.match(name):
        return Override(Condition["default"], None, match.group("name"))
    elif match := CONDITIONAL_REGEX.match(name):
        cond: str = match.group("cond").lower()
        if cond not in VALID_CONDITIONS:
            logger.error(
                "encountered invalid condition when parsing conditions from %s: %s",
                name,
                cond,
            )
            logger.error("assuming this was an error and exiting.")
            exit(1)
        return Override(Condition[cond], match.group("comp"), match.group("name"))  # type: ignore : valid conditions were checked above.
    else:
        logger.error("could not find valid condition when parsing the file: %s", name)
        exit(1)


def get_symlink_files() -> list[Path]:
    """Gets the files that should be symlinked. This should be paths relative to the dotfiles directory

    Returns:
        list[Path]: The list of files.
    """
    paths: list[Path] = []

    for file in DOTFILES.glob("**/*"):
        if (
            file.is_dir()
            or file in IGNORED_PATHS
            or any(parent in IGNORED_PATHS for parent in file.parents)
        ):
            continue
        paths.append(file)

    return paths


def get_override_files() -> list[Path]:
    """Get the override files to symlink. These are parsed and validated, then the best fit is picked.
    The best fit is ranked as follows (1 is the best fit):
    1. Hostname
    2. OS
    3. Default
    If there 2 matches, this will error and exit.

    Returns:
        list[Path]: A list of path objects to symlink.
    """
    file_overrides: dict[Path, list[tuple[Path, Override]]] = {}
    for path in DOTFILES.glob("overrides/**/*"):
        if path.is_dir():
            continue
        overrides = parse_override_name(path.name)
        normalized_file = path.parent / overrides.name
        if normalized_file in file_overrides:
            file_overrides[normalized_file].append((path, overrides))
        else:
            file_overrides[normalized_file] = [(path, overrides)]

    symlinks = []
    for path, overrides in file_overrides.items():
        # Initialize our best pick.
        best, best_overrides = None, None
        for f, f_overrides in overrides:
            if f_overrides.cond == Condition.default and best == None:
                best = f
                best_overrides = f_overrides
                continue

            condition = CONDITIONS_CALLABLE_MAP[f_overrides.cond](f_overrides.comp)

            if condition and (
                best_overrides == None or f_overrides.cond > best_overrides.cond
            ):
                best = f
                best_overrides = f_overrides
        symlinks.append(best)

    return symlinks


def symlink_file(original: Path, to: Path):
    if to.exists(follow_symlinks=False) and to.resolve() != original:
        logger.critical("attempted to symlink to path that existed and wasn't symlinked to us: %s.", to.name)
        logger.critical("please move or delete the file and try again.")
        exit(1)
    elif not to.exists(follow_symlinks=False):
        if not to.parent.exists():
            to.parent.mkdir(parents=True)

        to.symlink_to(original)
        logger.debug("successfully symlinked %s to %s.", to, original)
    else:
        logger.debug("file %s already existed, skipping.", to.name)

def symlink_bin_and_self():
    for file in (DOTFILES / "bin").iterdir():
        real_path = HOME / ".local" / file.relative_to(DOTFILES)
        if not real_path.parent.exists():
            real_path.parent.mkdir(parents=True)
        symlink_file(file, real_path)

    # Symlink the self binary.
    symlink_file(Path(__file__), HOME / ".local/bin/dotfiles")

def cli_apply(action: typing.Literal["all", "overrides", "regular"], dry: bool):
    files = []
    override_files = []
    if action == "all":
        files = get_symlink_files()
        override_files = get_override_files()
        symlink_bin_and_self()
    elif action == "overrides":
        override_files = get_override_files()
    elif action == "regular":
        files = get_symlink_files()
        symlink_bin_and_self()

    for file in files:
        real_path = get_relative_to_home(file)
        logger.info("%s => %s", file.absolute(), real_path.absolute())
        if not dry:
            symlink_file(file, real_path)

    for file in override_files:
        overrides = parse_override_name(file.name)
        real_path = get_relative_overrides_to_home(file.parent / overrides.name)
        logger.info("%s => %s", file.absolute(), real_path.absolute())
        if not dry:
            symlink_file(file, real_path)

def main():
    parser = argparse.ArgumentParser(prog="dotfiles", description="Dotfiles helper")
    subparsers = parser.add_subparsers(title="subcommands", required=True)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Run the process to symlink the dotfiles",
    )
    apply_parser.add_argument("apply", choices=["all", "overrides", "regular"], help="The ")

    for _, subp in subparsers.choices.items():
        # add dry-run to all subparsers so that it can be put anywhere in the program.
        subp.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="Preforms a dry run, only printing out what would change.",
        )
        subp.add_argument(
            "-v",
            "--verbose",
            "--debug",
            action="store_true",
            help="Enables debug/verbose mode. This internally just sets the logger's mode to DEBUG.",
            dest="debug"
        )

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.apply:
        cli_apply(args.apply, args.dry_run)


if __name__ == "__main__":
    main()
