from coderev.findings import Finding
from coderev.settings import Settings

HUMAN_LINES = (
    "- [ ] Check 1: the change matches the request, with no unrelated edits.",
    "- [ ] Check 2: every API and name the change calls exists in our code and versions.",
    "- [ ] Check 3: I traced each branch, including empty, malformed and other-tenant input.",
    "- [ ] Check 7: no abstraction exists for a future need nobody asked for.",
    "- [ ] Check 8: failures fail closed and nothing is swallowed.",
    "- [ ] Check 10: the tests fail before the change and pass after it.",
    "- [ ] Rules 1 to 3: I own this change, I can explain it, and the evidence is a CI link.",
    "- [ ] Files that set rules or build behavior (agent rule files, CI and build files) got extra scrutiny. (Source: OWASP Secure Coding with AI.)",
)

_NOTES = (
    (
        "check 2",
        "Whether a new package exists on an index. The tool sees a same-line comment in the requirements or pyproject diff.",
    ),
    (
        "check 6",
        "Complexity. STANDARD.md marks the limit as to test and gives no number. Set complexity_limit in the settings file to turn on ruff C901.",
    ),
    (
        "check 10",
        "A test function removed inside a file that stays. tampercheck test-deleted flags a deleted test file.",
    ),
    (
        "check 10",
        "A pytest.skip() call. tampercheck test-skipped flags @pytest.mark.skip, @pytest.mark.skipif, and @unittest.skip.",
    ),
    (
        "check 10",
        "A changed test file that never imports the changed code. No existing tool reports that failure.",
    ),
)


def render(findings: list[Finding], settings: Settings | None) -> str:
    lines = [f"{item.status} {item.check}: {item.text}" for item in findings]
    notes = _notes(settings)
    lines.extend(f"not automated {check}: {text}" for check, text in notes)
    lines.append("Human sign-off. This tool does not decide these lines.")
    lines.extend(HUMAN_LINES)
    lines.extend(f"- [ ] {text}" for _check, text in notes)
    return "\n".join(lines) + "\n"


def _notes(settings: Settings | None) -> tuple[tuple[str, str], ...]:
    if settings is not None and settings.complexity_limit is not None:
        return tuple(item for item in _NOTES if item[0] != "check 6")
    return _NOTES
