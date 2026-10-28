from pathlib import Path

from tests.plants import secret_module
from tests.support import base_sha, commit_all, cover, init_repo, run


def test_secret_in_the_diff_fails_gitleaks(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pkg" / "secret.py").write_text(secret_module(), encoding="utf-8")
    (repo / "tests" / "test_secret.py").write_text(
        cover("secret", "token", 'token().startswith("sk-")'),
        encoding="utf-8",
    )
    commit_all(repo, "add a token")
    code, text = run(repo, base)
    assert code == 1
    assert "fail check 9" in text
    assert "gitleaks" in text
    assert "pkg/secret.py" in text
    assert "generic-api-key" in text
    assert "A1b2" not in text


def test_clean_diff_passes_secrets(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "README.md").write_text("A made up note.\n", encoding="utf-8")
    commit_all(repo, "note")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 9" in text


def test_secret_already_in_the_base_does_not_fail(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "pkg" / "secret.py").write_text(secret_module(), encoding="utf-8")
    (repo / "tests" / "test_secret.py").write_text(
        cover("secret", "token", 'token().startswith("sk-")'),
        encoding="utf-8",
    )
    commit_all(repo, "old token")
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
    assert "pass check 9" in text
