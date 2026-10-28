import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from coderev.findings import Finding, fail, ok
from coderev.gitdiff import Diff, full_diff
from coderev.proc import CommandResult, last_line, run_command
from coderev.settings import Settings

_OMIT = "*/tests/*,*/test_*.py,*/conftest.py"


def check_coverage(repo: Path, base: str, settings: Settings, diff: Diff) -> list[Finding]:
    if diff.added_python_count() == 0:
        return [ok("check 10", "no new Python lines to cover (diff-cover)")]
    missing = _missing_tool()
    if missing is not None:
        return [missing]
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        diff_file = work / "changes.diff"
        diff_file.write_text(full_diff(repo, base), encoding="utf-8")
        xml_path = work / "coverage.xml"
        report_path = work / "diff-cover.json"
        data_path = work / "coverage.data"
        measured = _measure(repo, data_path, xml_path)
        if isinstance(measured, Finding):
            return [measured]
        return _gate(repo, settings, xml_path, diff_file, report_path)


def _missing_tool() -> Finding | None:
    for name in ("coverage", "pytest", "diff-cover"):
        if shutil.which(name) is None:
            return fail("check 10", f"{name} is not on PATH. pip install . provides it.")
    return None


def _measure(repo: Path, data_path: Path, xml_path: Path) -> Finding | None:
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(data_path)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("COVERAGE_PROCESS_START", None)
    ran = run_command(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--source=.",
            "--omit",
            _OMIT,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
        ],
        repo,
        env,
    )
    if ran.code != 0:
        return fail("check 10", f"pytest exited {ran.code}, so coverage was not measured. {last_line(ran)}")
    wrote = run_command([sys.executable, "-m", "coverage", "xml", "-o", str(xml_path)], repo, env)
    if wrote.code != 0 or not xml_path.is_file():
        return fail("check 10", f"coverage xml was not written. {last_line(wrote)}")
    return None


def _gate(
    repo: Path,
    settings: Settings,
    xml_path: Path,
    diff_file: Path,
    report_path: Path,
) -> list[Finding]:
    limit = settings.coverage_percent
    result = run_command(
        [
            "diff-cover",
            str(xml_path),
            "--diff-file",
            str(diff_file),
            "--fail-under",
            str(limit),
            "--format",
            f"json:{report_path}",
        ],
        repo,
    )
    if not report_path.is_file():
        return [fail("check 10", f"diff-cover failed. {last_line(result)}")]
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    return _from_report(payload, result, limit)


def _from_report(payload: object, result: CommandResult, limit: float) -> list[Finding]:
    if not isinstance(payload, dict):
        return [fail("check 10", "diff-cover did not return a JSON object.")]
    total_lines = int(payload.get("total_num_lines") or 0)
    if total_lines == 0:
        return [ok("check 10", "diff-cover found no executable new lines")]
    percent = float(payload.get("total_percent_covered") or 0)
    if percent >= limit and result.code == 0:
        return [ok("check 10", f"coverage on new code is {percent:g}%, at least {limit:g}% (diff-cover)")]
    failures = _missing_lines(payload, percent, limit)
    if failures:
        return failures
    return [fail("check 10", f"coverage on new code is {percent:g}%, at least {limit:g}% (diff-cover)")]


def _missing_lines(payload: dict[str, object], percent: float, limit: float) -> list[Finding]:
    stats = payload.get("src_stats")
    if not isinstance(stats, dict):
        return []
    failures: list[Finding] = []
    for path, info in stats.items():
        if not isinstance(info, dict):
            continue
        for line in info.get("violation_lines") or []:
            failures.append(
                fail(
                    "check 10",
                    f"{path}:{line} new line is not covered ({percent:g} percent, at least {limit:g} percent, diff-cover)",
                )
            )
    return failures
