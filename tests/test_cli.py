from pathlib import Path
import shutil
import tomllib

from coderev.cli import main
from tests.support import ROOT, base_sha, commit_all, git, init_repo, run


def test_cli_on_an_empty_diff(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.chdir(repo)
    code = main(["check", "--base", base_sha(repo)])
    text = capsys.readouterr().out
    assert code == 0
    assert "Human sign-off" in text
    assert "Check 1:" in text
    assert "not automated check 5" in text
    assert "not automated check 10" in text


def test_default_base_is_main(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    git(repo, "checkout", "-b", "feature")
    (repo / "requirements.txt").write_text("madeup-widget==1.0\n", encoding="utf-8")
    commit_all(repo, "add a dependency")
    code, text = run(repo, None)
    assert code == 1
    assert "fail check 2" in text
    assert "madeup-widget" in text


def test_dirty_tree_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "pkg" / "seed.py").write_text("def seed() -> int:\n    return 2\n", encoding="utf-8")
    code, text = run(repo, base_sha(repo))
    assert code == 1
    assert "uncommitted" in text


def test_missing_base_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    code, text = run(repo, "no-such-branch")
    assert code == 1
    assert "fail setup" in text
    assert "no-such-branch" in text


def test_not_a_repository_fails(tmp_path: Path) -> None:
    code, text = run(tmp_path, None)
    assert code == 1
    assert "fail setup" in text


def test_settings_missing_a_key_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "coderev.toml").write_text("duplication_percent = 3\n", encoding="utf-8")
    commit_all(repo, "partial settings")
    code, text = run(repo, base_sha(repo))
    assert code == 1
    assert "coverage_percent" in text


def test_settings_bad_toml_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "coderev.toml").write_text("duplication_percent = \n", encoding="utf-8")
    commit_all(repo, "broken settings")
    code, text = run(repo, base_sha(repo))
    assert code == 1
    assert "TOML" in text


def test_missing_gitleaks_fails(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    real = shutil.which

    def hidden(name: str) -> str | None:
        if name == "gitleaks":
            return None
        return real(name)

    monkeypatch.setattr("coderev.checks.secrets.shutil.which", hidden)
    code, text = run(repo, base_sha(repo))
    assert code == 1
    assert "gitleaks" in text


def test_packaged_defaults_match_the_standard() -> None:
    data = tomllib.loads((ROOT / "coderev" / "settings_default.toml").read_text(encoding="utf-8"))
    assert data["duplication_percent"] == 3
    assert data["coverage_percent"] == 80
    assert data["max_function_lines"] == 50
    assert data["max_nesting_level"] == 3
    assert "complexity_limit" not in data
