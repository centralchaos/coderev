from pathlib import Path
import re

from coderev.findings import Finding, fail, ok
from coderev.gitdiff import Diff

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_QUOTED = re.compile(r"""^\s*["']([A-Za-z0-9][A-Za-z0-9_.-]*)""")


def check_dependencies(diff: Diff) -> list[Finding]:
    removed = _names(diff.removed_lines)
    failures: list[Finding] = []
    for path, line_no, text in diff.added_lines:
        name = _dependency_name(path, text)
        if name is None or (path, name) in removed or _has_reason(text):
            continue
        failures.append(
            fail("check 2", f"{path}:{line_no} new dependency {name} has no same-line reason")
        )
    if failures:
        return failures
    return [ok("check 2", "every new dependency has a same-line reason")]


def _names(lines: tuple[tuple[str, str], ...]) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path, text in lines:
        name = _dependency_name(path, text)
        if name is not None:
            found.add((path, name))
    return found


def _dependency_name(path: str, text: str) -> str | None:
    if _is_requirements(path):
        return _requirement_name(text)
    if Path(path).name == "pyproject.toml":
        return _quoted_name(text)
    return None


def _is_requirements(path: str) -> bool:
    name = Path(path).name
    return "requirements" in name and name.endswith(".txt")


def _requirement_name(text: str) -> str | None:
    code = text.split("#", 1)[0].strip()
    if not code or code.startswith(("-", "#")):
        return None
    code = code.split(";", 1)[0].strip()
    match = _NAME.match(code)
    if match is None:
        return None
    return match.group(0).lower()


def _quoted_name(text: str) -> str | None:
    match = _QUOTED.match(text)
    if match is None:
        return None
    return match.group(1).lower()


def _has_reason(text: str) -> bool:
    if "#" not in text:
        return False
    return bool(text.split("#", 1)[1].strip())
