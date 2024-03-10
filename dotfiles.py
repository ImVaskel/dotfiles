#!/usr/bin/env python3

from __future__ import annotations

import argparse
import enum
import logging
import os
import platform
import re
import typing
from pathlib import Path


# Taken from https://github.com/Rapptz/discord.py/blob/master/discord/utils.py with some minor modification.
class ColorFormatter(logging.Formatter):
    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f"{colour}%(levelname)-8s\x1b[0m%(message)s",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


class Colors:
    GREY = "\x1b[38;21m"
    YELLOW = "\x1b[33;21m"
    RED = "\x1b[31;21m"
    BOLD_RED = "\x1b[31;1m"
    BOLD_HIGH_BLACK = "\x1b[1;90m"
    CYAN = "\x1b[1;96m"
    GREEN = "\x1b[1;32m"
    RESET = "\x1b[0m"


def color(msg: str, color: str) -> str:
    return color + msg + Colors.RESET


logger = logging.Logger("dotfiles", level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
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

DOTFILES = Path(__file__).resolve().parent
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
            if f_overrides.cond == Condition.default and best is None:
                best = f
                best_overrides = f_overrides
                continue

            condition = CONDITIONS_CALLABLE_MAP[f_overrides.cond](f_overrides.comp)

            if condition and (
                best_overrides is None or f_overrides.cond > best_overrides.cond
            ):
                best = f
                best_overrides = f_overrides
        symlinks.append(best)

    return symlinks


def symlink_file(original: Path, to: Path):
    if to.exists(follow_symlinks=False) and to.resolve() != original:
        logger.critical(
            "attempted to symlink to path that existed and wasn't symlinked to us: %s. (original: %s)",
            to,
            original,
        )
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
    symlink_file(Path(__file__).resolve(), HOME / ".local/bin/dotfiles")


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
        logger.info(
            "%s %s %s",
            color(str(file.absolute()), Colors.CYAN),
            color("=>", Colors.BOLD_HIGH_BLACK),
            color(str(real_path.absolute()), Colors.CYAN),
        )
        if not dry:
            symlink_file(file, real_path)

    for file in override_files:
        overrides = parse_override_name(file.name)
        real_path = get_relative_overrides_to_home(file.parent / overrides.name)
        logger.info(
            "%s %s %s",
            color(str(file.absolute()), Colors.CYAN),
            color("=>", Colors.BOLD_HIGH_BLACK),
            color(str(real_path.absolute()), Colors.CYAN),
        )
        if not dry:
            symlink_file(file, real_path)


def cli_add(file: Path, dry: bool):
    if not file.is_file() or file.is_symlink():
        logger.error("The provided file is not a regular file.")
        exit(1)
    elif not file.is_relative_to(HOME):
        if file.root:
            logger.error(
                "The provided file is not relative to home. At this time, only files in $HOME are supported."
            )
            exit(1)
        file = Path.cwd() / file

    path = DOTFILES / file.relative_to(HOME)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        file.rename(path)
        file.symlink_to(path)
    logger.info(
        "File added to dotfiles, the path is: %s", color(str(path), Colors.CYAN)
    )


def cli_remove(file: Path, dry: bool):
    if file.is_dir():
        logger.error("The provided file is not a regular file or symlink.")
        exit(1)
    elif not file.root:
        file = Path.cwd() / file
    if file.is_relative_to(DOTFILES):
        real_file = file
        file = get_relative_to_home(file)

    if file.is_symlink():
        real_file = file.resolve()
    else:
        real_file = file

    if not real_file.is_relative_to(DOTFILES):
        logger.error(
            "The file is not relative to the dotfiles directory after resolving. (is it added?)"
        )
        exit(1)

    logger.debug("The real file is %s and the symlink is %s", str(real_file), str(file))

    if not dry:
        file.unlink()
        real_file.unlink()
    logger.info("File removed from dotfiles.")


def cli_status():
    linked: list[tuple[Path, Path]] = []
    not_linked: list[tuple[Path, Path]] = []
    for file in get_symlink_files():
        real_path = get_relative_to_home(file)
        if not real_path.exists():
            not_linked.append((file, real_path))
        else:
            linked.append((file, real_path))

    for file in get_override_files():
        overrides = parse_override_name(file.name)
        real_path = get_relative_overrides_to_home(file.parent / overrides.name)
        if not real_path.exists(follow_symlinks=False):
            not_linked.append((file, real_path))
        else:
            linked.append((file, real_path))

    if linked:
        logger.info("=" * (os.get_terminal_size().columns - 8))
        logger.info("Managed: ")
        for file, real_path in linked:
            logger.info(
                "%s %s %s",
                color(str(file.absolute()), Colors.GREEN),
                color("=>", Colors.BOLD_HIGH_BLACK),
                color(str(real_path.absolute()), Colors.GREEN),
            )
    if not_linked:
        print()
        logger.info("=" * (os.get_terminal_size().columns - 8))
        logger.info("Unmanaged: ")
        for file, real_path in not_linked:
            logger.info(
                "%s %s %s",
                color(str(file.absolute()), Colors.RED),
                color("=>", Colors.BOLD_HIGH_BLACK),
                color(str(real_path.absolute()), Colors.RED),
            )


def main():
    parser = argparse.ArgumentParser(prog="dotfiles", description="Dotfiles helper")
    subparsers = parser.add_subparsers(title="subcommands", required=True)

    subparsers.add_parser(
        "apply",
        help="Run the process to symlink the dotfiles",
    ).add_argument("action", choices=["all", "overrides", "regular"])
    subparsers.add_parser(
        "add",
        help="Adds a file to the dotfiles location. This moves the file and creates a symlink to where it was originally located.",
    ).add_argument("add", type=Path, metavar="file")
    subparsers.add_parser(
        "remove",
        help="Removes a file from the dotfiles location. This removes the file completely. Note that this does not currently function on files with overrides.",
    ).add_argument("remove", type=Path, metavar="file")
    subparsers.add_parser(
        "status",
        help="List all the dotfiles that are managed. Will also list the ones that are managed, but not yet applied.",
    ).add_argument("status", action="store_true")

    for name, subp in subparsers.choices.items():
        if name in ["status"]:
            continue
        # add dry-run to all subparsers (that are valid to do so) so that it can be put anywhere in the program.
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
            dest="debug",
        )

    args = parser.parse_args()

    if hasattr(args, "debug"):
        logger.setLevel(logging.DEBUG)

    logger.debug("running with args %s", args)

    if hasattr(args, "action"):
        cli_apply(args.action, args.dry_run)
    elif hasattr(args, "add"):
        cli_add(args.add, args.dry_run)
    elif hasattr(args, "remove"):
        cli_remove(args.remove, args.dry_run)
    elif hasattr(args, "status"):
        cli_status()


if __name__ == "__main__":
    main()
