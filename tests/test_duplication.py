from pathlib import Path

from tests.plants import cloned
from tests.support import base_sha, commit_all, cover, init_repo, run, write_settings


def _add_pair(repo: Path) -> None:
    (repo / "pkg" / "one.py").write_text(cloned("alpha"), encoding="utf-8")
    (repo / "pkg" / "two.py").write_text(cloned("beta"), encoding="utf-8")
    (repo / "tests" / "test_pair.py").write_text(
        "from pkg.one import alpha\nfrom pkg.two import beta\n\n"
        "def test_pair() -> None:\n    assert alpha(1) == beta(1)\n",
        encoding="utf-8",
    )


def test_duplicate_new_code_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    _add_pair(repo)
    commit_all(repo, "copy a function")
    code, text = run(repo, base)
    assert code == 1
    assert "fail check 4" in text
    assert "jscpd" in text
    assert "one.py" in text


def test_unique_new_code_passes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "gamma.py").write_text(
        "def gamma(value: int) -> int:\n    return value + 1\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_gamma.py").write_text(
        cover("gamma", "gamma", "gamma(1) == 2"),
        encoding="utf-8",
    )
    commit_all(repo, "add gamma")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 4" in text
    assert "fail check 4" not in text


def test_duplication_limit_comes_from_settings(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    _add_pair(repo)
    write_settings(repo, duplication_percent=100)
    commit_all(repo, "copy a function")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 4" in text


def test_old_clones_do_not_fail_new_work(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    _add_pair(repo)
    commit_all(repo, "old copies")
    base = base_sha(repo)
    (repo / "pkg" / "gamma.py").write_text(
        "def gamma(value: int) -> int:\n    return value + 3\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_gamma.py").write_text(
        cover("gamma", "gamma", "gamma(1) == 4"),
        encoding="utf-8",
    )
    commit_all(repo, "add gamma")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 4" in text
