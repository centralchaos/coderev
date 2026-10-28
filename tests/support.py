from pathlib import Path
import subprocess
import tomllib

from coderev.run import execute

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def init_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "example@example.com")
    git(repo, "config", "user.name", "Example")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "pkg" / "seed.py").write_text("def seed() -> int:\n    return 1\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_seed.py").write_text(
        "from pkg.seed import seed\n\ndef test_seed() -> None:\n    assert seed() == 1\n"
    )
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n.coverage\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    return repo


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def base_sha(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def run(repo: Path, base: str | None = None) -> tuple[int, str]:
    return execute(repo, base, None)


def write_settings(repo: Path, **overrides: object) -> None:
    data = tomllib.loads((ROOT / "coderev" / "settings_default.toml").read_text(encoding="utf-8"))
    data.update(overrides)
    lines = [f"{key} = {value}" for key, value in data.items()]
    (repo / "coderev.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cover(module: str, func: str, call: str) -> str:
    return (
        f"from pkg.{module} import {func}\n\n"
        f"def test_{func}() -> None:\n"
        f"    assert {call}\n"
    )
