from dataclasses import dataclass
import json
from pathlib import Path
import shutil

from coderev.findings import Finding, fail
from coderev.gitdiff import Diff, relative
from coderev.proc import last_line, run_command
from coderev.settings import Settings

LEFTOVER_RULES = ("F401", "F841", "ERA001", "FIX001", "FIX002")
NESTING_RULE = "PLR1702"
COMPLEXITY_RULE = "C901"


@dataclass(frozen=True)
class RuffHit:
    code: str
    path: str
    line: int
    message: str


def run_ruff(
    repo: Path,
    settings: Settings,
    diff: Diff,
    rules: tuple[str, ...],
    check: str,
) -> tuple[Finding | None, list[RuffHit]]:
    binary = shutil.which("ruff")
    if binary is None:
        return fail(check, "ruff is not on PATH. pip install . provides it."), []
    args = [
        binary,
        "check",
        "--isolated",
        "--preview",
        "--output-format",
        "json",
        "--select",
        ",".join(rules),
        "--config",
        f"lint.pylint.max-nested-blocks = {settings.max_nesting_level}",
    ]
    if COMPLEXITY_RULE in rules and settings.complexity_limit is not None:
        args.extend(
            ["--config", f"lint.mccabe.max-complexity = {settings.complexity_limit}"]
        )
    args.extend(diff.python_paths())
    result = run_command(args, repo)
    if result.code not in (0, 1):
        return fail(check, f"ruff failed. {last_line(result)}"), []
    try:
        payload = json.loads(result.out or "[]")
    except json.JSONDecodeError:
        return fail(check, "ruff did not return JSON."), []
    return None, _hits(repo, diff, payload)


def _hits(repo: Path, diff: Diff, payload: object) -> list[RuffHit]:
    hits: list[RuffHit] = []
    if not isinstance(payload, list):
        return hits
    for item in payload:
        if not isinstance(item, dict):
            continue
        path = relative(repo, str(item.get("filename", "")))
        location = item.get("location") or {}
        line = int(location.get("row") or 0)
        if line not in diff.added.get(path, set()):
            continue
        hits.append(
            RuffHit(
                code=str(item.get("code", "")),
                path=path,
                line=line,
                message=str(item.get("message", "")),
            )
        )
    return hits
