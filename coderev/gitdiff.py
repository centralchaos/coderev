from dataclasses import dataclass
from pathlib import Path

from coderev.errors import CheckError
from coderev.proc import run_command


@dataclass(frozen=True)
class Diff:
    added: dict[str, set[int]]
    added_lines: tuple[tuple[str, int, str], ...]
    removed_lines: tuple[tuple[str, str], ...]

    def added_python_count(self) -> int:
        return sum(len(lines) for path, lines in self.added.items() if path.endswith(".py"))

    def python_paths(self) -> tuple[str, ...]:
        return tuple(sorted(path for path in self.added if path.endswith(".py")))


def git_output(repo: Path, *args: str) -> str:
    result = run_command(["git", *args], repo)
    if result.code != 0:
        detail = (result.err or result.out).strip() or "git failed"
        raise CheckError(detail.splitlines()[-1])
    return result.out


def ensure_committed(repo: Path) -> None:
    status = git_output(repo, "status", "--porcelain")
    if status.strip():
        raise CheckError(
            "The work tree has uncommitted changes. Commit them, then run coderev check."
        )


def resolve_base(repo: Path, requested: str | None) -> str:
    name = requested or _first_base(repo)
    if not _ref_exists(repo, name):
        raise CheckError(f"Base {name} is not in this repository.")
    return git_output(repo, "merge-base", name, "HEAD").strip()


def read_diff(repo: Path, base: str) -> Diff:
    text = git_output(repo, "diff", "--unified=0", "--find-renames", base, "HEAD")
    return parse_diff(text)


def full_diff(repo: Path, base: str) -> str:
    return git_output(repo, "diff", "--find-renames", base, "HEAD")


def relative(repo: Path, raw: str) -> str:
    path = Path(raw)
    if path.is_absolute():
        try:
            return path.relative_to(repo).as_posix()
        except ValueError:
            return path.as_posix()
    text = path.as_posix()
    if text.startswith("./"):
        return text[2:]
    return text


def parse_diff(text: str) -> Diff:
    added: dict[str, set[int]] = {}
    added_lines: list[tuple[str, int, str]] = []
    removed_lines: list[tuple[str, str]] = []
    path: str | None = None
    new_line: int | None = None
    for raw in text.splitlines():
        path, new_line = _apply_line(raw, path, new_line, added, added_lines, removed_lines)
    return Diff(added, tuple(added_lines), tuple(removed_lines))


def _apply_line(
    raw: str,
    path: str | None,
    new_line: int | None,
    added: dict[str, set[int]],
    added_lines: list[tuple[str, int, str]],
    removed_lines: list[tuple[str, str]],
) -> tuple[str | None, int | None]:
    if raw.startswith("diff --git "):
        return None, None
    if raw.startswith("+++ "):
        return _new_path(raw), new_line
    if raw.startswith("@@"):
        return path, _new_start(raw)
    if path is None or new_line is None or raw.startswith("\\"):
        return path, new_line
    if raw.startswith("+"):
        added.setdefault(path, set()).add(new_line)
        added_lines.append((path, new_line, raw[1:]))
        return path, new_line + 1
    if raw.startswith("-"):
        removed_lines.append((path, raw[1:]))
        return path, new_line
    return path, new_line + 1


def _new_path(line: str) -> str | None:
    raw = line[4:].strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        raw = raw[1:-1]
    if raw.startswith("b/"):
        raw = raw[2:]
    if raw == "/dev/null":
        return None
    return raw


def _new_start(line: str) -> int | None:
    for part in line.split(" "):
        if part.startswith("+") and part[1:2].isdigit():
            return int(part[1:].split(",")[0])
    return None


def _first_base(repo: Path) -> str:
    for name in ("main", "master", "origin/main", "origin/master"):
        if _ref_exists(repo, name):
            return name
    raise CheckError("No base branch. Pass --base, or add a main branch.")


def _ref_exists(repo: Path, name: str) -> bool:
    result = run_command(["git", "rev-parse", "--verify", "--quiet", name], repo)
    return result.code == 0
