import json
from pathlib import Path
import shutil
import tempfile

from coderev.findings import Finding, fail, ok
from coderev.proc import last_line, run_command


def check_secrets(repo: Path, base: str) -> list[Finding]:
    binary = shutil.which("gitleaks")
    if binary is None:
        return [fail("check 9", "gitleaks is not on PATH. Install the prerequisite in the README.")]
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "leaks.json"
        result = run_command(
            [
                binary,
                "git",
                "--no-banner",
                "--redact=100",
                f"--log-opts={base}..HEAD",
                "--report-format",
                "json",
                "--report-path",
                str(report),
                str(repo),
            ],
            repo,
        )
        if not report.is_file():
            if result.code == 0:
                return [ok("check 9", "no secrets in the diff (gitleaks)")]
            return [fail("check 9", f"gitleaks failed. {last_line(result)}")]
        payload = json.loads(report.read_text(encoding="utf-8") or "[]")
    return _findings(payload)


def _findings(payload: object) -> list[Finding]:
    if not isinstance(payload, list) or not payload:
        return [ok("check 9", "no secrets in the diff (gitleaks)")]
    failures: list[Finding] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        path = str(item.get("File") or "unknown")
        line = item.get("StartLine") or 1
        rule = str(item.get("RuleID") or "secret")
        failures.append(fail("check 9", f"{path}:{line} {rule} (gitleaks)"))
    return failures or [ok("check 9", "no secrets in the diff (gitleaks)")]
