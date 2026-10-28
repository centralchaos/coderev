from pathlib import Path
import re
import shutil

from coderev.findings import Finding, fail, ok
from coderev.gitdiff import Diff
from coderev.proc import last_line, run_command
from coderev.ruff_run import COMPLEXITY_RULE, NESTING_RULE, run_ruff
from coderev.settings import Settings

_LENGTH = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+): warning: (?P<name>\S+) has (?P<nloc>\d+) NLOC"
)


def check_shape(repo: Path, settings: Settings, diff: Diff) -> list[Finding]:
    if not diff.python_paths():
        return [ok("check 6", "no new Python lines (lizard, ruff PLR1702)")]
    failures = _length(repo, settings, diff)
    failures.extend(_ruff_shape(repo, settings, diff))
    if failures:
        return failures
    text = (
        f"functions in the diff stay within {settings.max_function_lines} lines "
        f"(lizard --length) and nesting {settings.max_nesting_level} (ruff PLR1702)"
    )
    return [ok("check 6", text)]


def _length(repo: Path, settings: Settings, diff: Diff) -> list[Finding]:
    binary = shutil.which("lizard")
    if binary is None:
        return [fail("check 6", "lizard is not on PATH. pip install . provides it.")]
    result = run_command(
        [binary, *diff.python_paths(), "-L", str(settings.max_function_lines), "-l", "python", "-w"],
        repo,
    )
    if result.code != 0 and "warning:" not in result.out:
        return [fail("check 6", f"lizard failed. {last_line(result)}")]
    return _length_lines(settings, diff, result.out)


def _length_lines(settings: Settings, diff: Diff, text: str) -> list[Finding]:
    failures: list[Finding] = []
    limit = settings.max_function_lines
    for raw in text.splitlines():
        match = _LENGTH.match(raw.strip())
        if match is None:
            continue
        nloc = int(match.group("nloc"))
        start = int(match.group("line"))
        path = _norm(match.group("path"))
        if nloc <= limit or not _overlaps(diff, path, start, nloc):
            continue
        name = match.group("name")
        failures.append(
            fail("check 6", f"{path}:{start} {name} has {nloc} NLOC, at most {limit} (lizard --length)")
        )
    return failures


def _ruff_shape(repo: Path, settings: Settings, diff: Diff) -> list[Finding]:
    rules = [NESTING_RULE]
    if settings.complexity_limit is not None:
        rules.append(COMPLEXITY_RULE)
    error, hits = run_ruff(repo, settings, diff, tuple(rules), "check 6")
    if error is not None:
        return [error]
    return [
        fail("check 6", f"{hit.path}:{hit.line} {hit.message} (ruff {hit.code})")
        for hit in hits
    ]


def _overlaps(diff: Diff, path: str, start: int, nloc: int) -> bool:
    lines = diff.added.get(path)
    if not lines:
        return False
    end = start + nloc
    return any(start <= number < end for number in lines)


def _norm(path: str) -> str:
    if path.startswith("./"):
        return path[2:]
    return path
