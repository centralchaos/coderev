from pathlib import Path
import tomllib

from tests.plants import long_function, nested_function
from tests.support import ROOT, base_sha, commit_all, cover, init_repo, run, write_settings


def _limits() -> tuple[int, int]:
    data = tomllib.loads((ROOT / "coderev" / "settings_default.toml").read_text(encoding="utf-8"))
    return int(data["max_function_lines"]), int(data["max_nesting_level"])


def test_function_over_length_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    limit, _nesting = _limits()
    base = base_sha(repo)
    (repo / "pkg" / "long.py").write_text(long_function(limit - 2), encoding="utf-8")
    (repo / "tests" / "test_long.py").write_text(
        cover("long", "too_long", "too_long() > 0"),
        encoding="utf-8",
    )
    commit_all(repo, "long function")
    code, text = run(repo, base)
    assert code == 1
    assert "lizard --length" in text
    assert "pkg/long.py" in text
    assert "too_long" in text


def test_function_at_length_limit_passes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    limit, _nesting = _limits()
    base = base_sha(repo)
    (repo / "pkg" / "long.py").write_text(long_function(limit - 3), encoding="utf-8")
    (repo / "tests" / "test_long.py").write_text(
        cover("long", "too_long", "too_long() > 0"),
        encoding="utf-8",
    )
    commit_all(repo, "length at the limit")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 6" in text


def test_nesting_over_limit_fails_plr1702(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    _limit, nesting = _limits()
    base = base_sha(repo)
    (repo / "pkg" / "nest.py").write_text(nested_function(nesting + 1), encoding="utf-8")
    (repo / "tests" / "test_nest.py").write_text(
        "from pkg.nest import nested\n\ndef test_nested() -> None:\n"
        "    assert nested(10) == 10\n    assert nested(-1) == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "deep nesting")
    code, text = run(repo, base)
    assert code == 1
    assert "PLR1702" in text
    assert "pkg/nest.py" in text


def test_nesting_at_limit_passes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    _limit, nesting = _limits()
    base = base_sha(repo)
    (repo / "pkg" / "nest.py").write_text(nested_function(nesting), encoding="utf-8")
    (repo / "tests" / "test_nest.py").write_text(
        "from pkg.nest import nested\n\ndef test_nested() -> None:\n"
        "    assert nested(10) == 10\n    assert nested(-1) == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "nesting at the limit")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 6" in text


def test_complexity_is_not_automated_until_set(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "branch.py").write_text(
        "def branch(flag: int) -> int:\n    if flag:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_branch.py").write_text(
        "from pkg.branch import branch\n\ndef test_branch() -> None:\n"
        "    assert branch(1) == 1\n    assert branch(0) == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "branch")
    code, text = run(repo, base)
    fail_lines = [line for line in text.splitlines() if line.startswith("fail")]
    assert code == 0
    assert fail_lines == []
    assert "not automated check 6" in text


def test_complexity_limit_uses_c901(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    write_settings(repo, complexity_limit=1)
    (repo / "pkg" / "branch.py").write_text(
        "def branch(flag: int) -> int:\n    if flag:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_branch.py").write_text(
        "from pkg.branch import branch\n\ndef test_branch() -> None:\n"
        "    assert branch(1) == 1\n    assert branch(0) == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "branch")
    code, text = run(repo, base)
    assert code == 1
    assert "C901" in text
    assert "not automated check 6" not in text
