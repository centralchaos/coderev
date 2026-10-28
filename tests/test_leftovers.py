from pathlib import Path

from tests.plants import commented_module, fixme_module, todo_module
from tests.support import base_sha, commit_all, cover, init_repo, run


def _commit_module(repo: Path, name: str, source: str, call: str) -> str:
    base = base_sha(repo)
    (repo / "pkg" / f"{name}.py").write_text(source, encoding="utf-8")
    (repo / "tests" / f"test_{name}.py").write_text(cover(name, "live", call), encoding="utf-8")
    commit_all(repo, f"add {name}")
    return base


def test_commented_out_code_fails_era001(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = _commit_module(repo, "note", commented_module(), "live(2) == 2")
    code, text = run(repo, base)
    assert code == 1
    assert "pkg/note.py" in text
    assert "ERA001" in text


def test_todo_fails_fix002(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = _commit_module(repo, "note", todo_module(), "live(2) == 2")
    code, text = run(repo, base)
    assert code == 1
    assert "FIX002" in text
    assert "pkg/note.py" in text


def test_fixme_fails_fix001(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = _commit_module(repo, "note", fixme_module(), "live(2) == 2")
    code, text = run(repo, base)
    assert code == 1
    assert "FIX001" in text


def test_unused_import_fails_f401(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = "import os\n\ndef live(n: int) -> int:\n    return n + 1\n"
    base = _commit_module(repo, "spare", source, "live(1) == 2")
    code, text = run(repo, base)
    assert code == 1
    assert "F401" in text
    assert "pkg/spare.py" in text


def test_unused_variable_fails_f841(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = "def live(n: int) -> int:\n    spare = n\n    return n\n"
    base = _commit_module(repo, "spare", source, "live(1) == 1")
    code, text = run(repo, base)
    assert code == 1
    assert "F841" in text


def test_unused_function_fails_vulture(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = "def live(n: int) -> int:\n    return n\n\ndef leftover(n: int) -> int:\n    return n\n"
    base = _commit_module(repo, "spare", source, "live(1) == 1")
    code, text = run(repo, base)
    assert code == 1
    assert "leftover" in text
    assert "vulture" in text


def test_unreachable_code_fails_vulture(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = "def live(n: int) -> int:\n    return n\n    return n + 1\n"
    base = _commit_module(repo, "dead", source, "live(1) == 1")
    code, text = run(repo, base)
    assert code == 1
    assert "unreachable" in text
    assert "vulture" in text
    assert "pkg/dead.py" in text


def test_not_implemented_error_fails_placeholder(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    stub = "raise " + "NotImplementedError"
    source = f"def live(n: int) -> int:\n    {stub}(n)\n"
    base = base_sha(repo)
    (repo / "pkg" / "stub.py").write_text(source, encoding="utf-8")
    (repo / "tests" / "test_stub.py").write_text(
        "import pytest\nfrom pkg.stub import live\n\n"
        "def test_live() -> None:\n"
        "    with pytest.raises(NotImplementedError):\n"
        "        live(1)\n",
        encoding="utf-8",
    )
    commit_all(repo, "stub")
    code, text = run(repo, base)
    assert code == 1
    assert "placeholder" in text
    assert "tampercheck" in text
    assert "pkg/stub.py" in text


def test_clean_module_passes_leftovers(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = "def live(n: int) -> int:\n    return n + 1\n"
    base = _commit_module(repo, "clean", source, "live(1) == 2")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 5" in text
