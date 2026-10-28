import json
from pathlib import Path
import shutil

from coderev.findings import Finding, fail, ok
from coderev.proc import last_line, run_command

_KINDS = {"test-deleted", "test-skipped"}


def check_suite(repo: Path, base: str) -> list[Finding]:
    binary = shutil.which("tampercheck")
    if binary is None:
        return [fail("check 10", "tampercheck is not on PATH. pip install . provides it.")]
    result = run_command([binary, "--from", base, "--to", "HEAD", "--json"], repo)
    try:
        payload = json.loads(result.out)
    except json.JSONDecodeError:
        return [fail("check 10", f"tampercheck did not return JSON. {last_line(result)}")]
    if not isinstance(payload, dict):
        return [fail("check 10", "tampercheck did not return a JSON object.")]
    failures = _findings(payload)
    if failures:
        return failures
    return [
        ok(
            "check 10",
            "no deleted test file and no newly skipped test (tampercheck test-deleted, test-skipped)",
        )
    ]


def _findings(payload: dict[str, object]) -> list[Finding]:
    items = payload.get("findings")
    if not isinstance(items, list):
        return []
    failures: list[Finding] = []
    for item in items:
        if not isinstance(item, dict) or item.get("kind") not in _KINDS or item.get("allowed"):
            continue
        path = str(item.get("path") or "unknown")
        line = item.get("line")
        where = f"{path}:{line}" if isinstance(line, int) else path
        failures.append(fail("check 10", f"{where} {item.get('kind')} (tampercheck)"))
    return failures
