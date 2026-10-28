import argparse
from pathlib import Path
import sys

from coderev.run import execute


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command != "check":
        parser.print_help()
        return 2
    settings = Path(args.settings) if args.settings else None
    code, text = execute(Path.cwd(), args.base, settings)
    sys.stdout.write(text)
    return code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coderev")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check the current branch against its base.")
    check.add_argument("--base", help="Base branch or commit. Default: main, then master.")
    check.add_argument("--settings", help="Settings file. Default: coderev.toml, then packaged defaults.")
    return parser
