from pathlib import Path

from coderev.checks.coverage import check_coverage
from coderev.checks.dependencies import check_dependencies
from coderev.checks.duplication import check_duplication
from coderev.checks.leftovers import check_leftovers
from coderev.checks.secrets import check_secrets
from coderev.checks.shape import check_shape
from coderev.checks.suite import check_suite
from coderev.errors import CheckError
from coderev.findings import Finding, fail
from coderev.gitdiff import Diff, ensure_committed, read_diff, resolve_base
from coderev.report import render
from coderev.settings import Settings, load_settings


def execute(repo: Path, requested_base: str | None, settings_file: Path | None) -> tuple[int, str]:
    try:
        settings = load_settings(repo, settings_file)
        base = resolve_base(repo, requested_base)
        ensure_committed(repo)
        diff = read_diff(repo, base)
    except CheckError as exc:
        return 1, render([fail("setup", str(exc))], None)
    findings = _collect(repo, base, settings, diff)
    code = 1 if any(item.status == "fail" for item in findings) else 0
    return code, render(findings, settings)


def _collect(repo: Path, base: str, settings: Settings, diff: Diff) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_dependencies(diff))
    findings.extend(check_duplication(repo, base, settings, diff))
    findings.extend(check_leftovers(repo, settings, diff))
    findings.extend(check_shape(repo, settings, diff))
    findings.extend(check_secrets(repo, base))
    findings.extend(check_coverage(repo, base, settings, diff))
    findings.extend(check_suite(repo, base))
    return findings
