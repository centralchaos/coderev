from pathlib import Path

from tests.support import base_sha, commit_all, cover, init_repo, run


def test_uncovered_new_function_fails_diff_cover(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "price.py").write_text(
        "def price(qty: int) -> int:\n    if qty < 0:\n        return 0\n    return qty * 2\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_price.py").write_text(
        "def test_unrelated() -> None:\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    commit_all(repo, "uncovered price")
    code, text = run(repo, base)
    assert code == 1
    assert "diff-cover" in text
    assert "pkg/price.py" in text
    assert "fail check 10" in text


def test_covered_new_function_passes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "price.py").write_text(
        "def price(qty: int) -> int:\n    if qty < 0:\n        return 0\n    return qty * 2\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_price.py").write_text(
        "from pkg.price import price\n\ndef test_price() -> None:\n"
        "    assert price(2) == 4\n    assert price(-1) == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "covered price")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 10" in text
    assert "diff-cover" in text


def test_old_uncovered_function_does_not_fail(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "pkg" / "old.py").write_text(
        "def old(qty: int) -> int:\n    return qty\n",
        encoding="utf-8",
    )
    commit_all(repo, "old and uncovered")
    base = base_sha(repo)
    (repo / "pkg" / "price.py").write_text(
        "def price(qty: int) -> int:\n    return qty * 2\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_price.py").write_text(
        cover("price", "price", "price(2) == 4"),
        encoding="utf-8",
    )
    commit_all(repo, "covered price")
    code, text = run(repo, base)
    assert code == 0
    assert "pkg/old.py" not in text
