import json
from pathlib import Path
import shutil
import tempfile

from coderev.findings import Finding, fail, ok
from coderev.gitdiff import Diff
from coderev.proc import last_line, run_command
from coderev.settings import Settings


def check_duplication(
    repo: Path,
    base: str,
    settings: Settings,
    diff: Diff,
) -> list[Finding]:
    binary = shutil.which("jscpd")
    if binary is None:
        return [fail("check 4", "jscpd is not on PATH. pip install . provides it.")]
    added = diff.added_python_count()
    if added == 0:
        return [ok("check 4", "no new Python lines (jscpd)")]
    data = _report(repo, base, binary)
    if isinstance(data, Finding):
        return [data]
    return _gate(data, added, settings.duplication_percent)


def _report(repo: Path, base: str, binary: str) -> Finding | dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_command(
            [
                binary,
                ".",
                "--format",
                "python",
                "--baseline-from-ref",
                base,
                "--reporters",
                "json",
                "--output",
                tmp,
                "--silent",
            ],
            repo,
        )
        report = Path(tmp) / "jscpd-report.json"
        if not report.is_file():
            return fail("check 4", f"jscpd failed. {last_line(result)}")
        loaded = json.loads(report.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return fail("check 4", "jscpd did not return a JSON object.")
    return loaded


def _gate(data: dict[str, object], added: int, limit: float) -> list[Finding]:
    total = _total(data)
    new_lines = int(total.get("newDuplicatedLines") or 0)
    percent = (new_lines / added) * 100
    if percent <= limit:
        return [
            ok(
                "check 4",
                f"duplication on new Python lines is {percent:.1f}%, at most {limit:g}% (jscpd newDuplicatedLines)",
            )
        ]
    failures = _clones(data, percent, limit)
    if failures:
        return failures
    return [
        fail(
            "check 4",
            f"duplication on new Python lines is {percent:.1f}%, at most {limit:g}% (jscpd newDuplicatedLines)",
        )
    ]


def _total(data: dict[str, object]) -> dict[str, object]:
    statistics = data.get("statistics")
    if not isinstance(statistics, dict):
        return {}
    total = statistics.get("total")
    if not isinstance(total, dict):
        return {}
    return total


def _clones(data: dict[str, object], percent: float, limit: float) -> list[Finding]:
    clones = data.get("duplicates")
    if not isinstance(clones, list):
        return []
    failures: list[Finding] = []
    for clone in clones:
        if not isinstance(clone, dict) or not clone.get("isNew"):
            continue
        first = clone.get("firstFile") if isinstance(clone.get("firstFile"), dict) else {}
        second = clone.get("secondFile") if isinstance(clone.get("secondFile"), dict) else {}
        failures.append(
            fail(
                "check 4",
                (
                    f"{first.get('name')}:{first.get('start')} duplicates "
                    f"{second.get('name')}:{second.get('start')} "
                    f"(jscpd, {percent:.1f}% of new Python lines, at most {limit:g}%)"
                ),
            )
        )
    return failures
