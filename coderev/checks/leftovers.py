from pathlib import Path
import re
import shutil

from coderev.findings import Finding, fail, ok
from coderev.gitdiff import Diff, relative
from coderev.proc import last_line, run_command
from coderev.ruff_run import LEFTOVER_RULES, RuffHit, run_ruff
from coderev.settings import Settings

_VULTURE = re.compile(r"^(?P<path>.+?):(?P<line>\d+): (?P<message>.*)$")


def check_leftovers(repo: Path, settings: Settings, diff: Diff) -> list[Finding]:
    if not diff.python_paths():
        return [ok("check 5", "no new Python lines (ruff, vulture)")]
    error, hits = run_ruff(repo, settings, diff, LEFTOVER_RULES, "check 5")
    failures = [] if error is None else [error]
    failures.extend(_ruff_failures(hits))
    failures.extend(_vulture(repo, diff))
    if failures:
        return failures
    return [
        ok(
            "check 5",
            "no new dead code or leftovers (ruff F401, F841, ERA001, FIX001, FIX002; vulture)",
        )
    ]


def _ruff_failures(hits: list[RuffHit]) -> list[Finding]:
    return [
        fail("check 5", f"{hit.path}:{hit.line} {hit.message} (ruff {hit.code})")
        for hit in hits
        if hit.code in LEFTOVER_RULES
    ]


def _vulture(repo: Path, diff: Diff) -> list[Finding]:
    binary = shutil.which("vulture")
    if binary is None:
        return [fail("check 5", "vulture is not on PATH. pip install . provides it.")]
    result = run_command(
        [
            binary,
            ".",
            "--exclude",
            ".venv,venv,.git,build,dist",
            "--ignore-names",
            "test_*",
            "--ignore-decorators",
            "@pytest.fixture,@pytest.mark.parametrize",
        ],
        repo,
    )
    if result.code != 0 and not result.out.strip():
        return [fail("check 5", f"vulture failed. {last_line(result)}")]
    return _vulture_lines(repo, diff, result.out)


def _vulture_lines(repo: Path, diff: Diff, text: str) -> list[Finding]:
    failures: list[Finding] = []
    for raw in text.splitlines():
        match = _VULTURE.match(raw.strip())
        if match is None:
            continue
        path = relative(repo, match.group("path"))
        line = int(match.group("line"))
        if line not in diff.added.get(path, set()):
            continue
        failures.append(fail("check 5", f"{path}:{line} {match.group('message')} (vulture)"))
    return failures
