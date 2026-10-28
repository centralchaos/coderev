from pathlib import Path

from tests.support import base_sha, commit_all, init_repo, run


def test_deleted_test_file_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "tests" / "test_extra.py").write_text(
        "from pkg.seed import seed\n\ndef test_extra() -> None:\n    assert seed() == 1\n",
        encoding="utf-8",
    )
    commit_all(repo, "extra test")
    base = base_sha(repo)
    (repo / "tests" / "test_extra.py").unlink()
    commit_all(repo, "delete extra test")
    code, text = run(repo, base)
    assert code == 1
    assert "test-deleted" in text
    assert "tampercheck" in text
    assert "tests/test_extra.py" in text


def test_skipped_test_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "tests" / "test_later.py").write_text(
        "import pytest\n\n@pytest.mark.skip(reason='later')\n"
        "def test_later() -> None:\n    assert 1 == 0\n",
        encoding="utf-8",
    )
    commit_all(repo, "skip a test")
    code, text = run(repo, base)
    assert code == 1
    assert "test-skipped" in text
    assert "tampercheck" in text
    assert "tests/test_later.py" in text


def test_kept_tests_pass(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "gamma.py").write_text(
        "def gamma(value: int) -> int:\n    return value + 1\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_gamma.py").write_text(
        "from pkg.gamma import gamma\n\ndef test_gamma() -> None:\n    assert gamma(1) == 2\n",
        encoding="utf-8",
    )
    commit_all(repo, "add gamma")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 10" in text
    assert "tampercheck" in text


def test_pytest_skip_call_is_not_automated(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "tests" / "test_later.py").write_text(
        "import pytest\n\ndef test_later() -> None:\n    pytest.skip('later')\n",
        encoding="utf-8",
    )
    commit_all(repo, "call skip")
    code, text = run(repo, base)
    fail_lines = [line for line in text.splitlines() if line.startswith("fail")]
    assert code == 0
    assert fail_lines == []
    assert "pytest.skip()" in text


def test_deleted_test_function_inside_a_file_is_not_automated(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    path = repo / "tests" / "test_seed.py"
    path.write_text(
        "from pkg.seed import seed\n\ndef test_seed() -> None:\n    assert seed() == 1\n\n"
        "def test_extra() -> None:\n    assert seed() == 1\n",
        encoding="utf-8",
    )
    commit_all(repo, "extra function")
    base = base_sha(repo)
    path.write_text(
        "from pkg.seed import seed\n\ndef test_seed() -> None:\n    assert seed() == 1\n",
        encoding="utf-8",
    )
    commit_all(repo, "drop extra function")
    code, text = run(repo, base)
    fail_lines = [line for line in text.splitlines() if line.startswith("fail")]
    assert code == 0
    assert fail_lines == []
    assert "file that stays" in text
