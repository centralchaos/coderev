from pathlib import Path

from tests.support import base_sha, commit_all, init_repo, run


def test_requirements_line_without_a_reason_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "requirements.txt").write_text("madeup-widget==1.0\n", encoding="utf-8")
    commit_all(repo, "add a dependency")
    code, text = run(repo, base)
    assert code == 1
    assert "fail check 2" in text
    assert "requirements.txt" in text
    assert "madeup-widget" in text


def test_requirements_line_with_a_reason_passes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "requirements.txt").write_text(
        "madeup-widget==1.0  # example client for the widget\n",
        encoding="utf-8",
    )
    commit_all(repo, "add a dependency")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 2" in text


def test_pyproject_dependency_without_a_reason_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = base_sha(repo)
    (repo / "pyproject.toml").write_text(
        "[project]\nname = 'sample'\nversion = '0.0.0'\ndependencies = [\n"
        '    "madeup-widget==1.0",\n]\n',
        encoding="utf-8",
    )
    commit_all(repo, "add pyproject")
    code, text = run(repo, base)
    assert code == 1
    assert "fail check 2" in text
    assert "pyproject.toml" in text
    assert "madeup-widget" in text


def test_version_bump_is_not_a_new_dependency(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "requirements.txt").write_text(
        "madeup-widget==1.0  # example client\n",
        encoding="utf-8",
    )
    commit_all(repo, "first pin")
    base = base_sha(repo)
    (repo / "requirements.txt").write_text("madeup-widget==2.0\n", encoding="utf-8")
    commit_all(repo, "bump")
    code, text = run(repo, base)
    assert code == 0
    assert "pass check 2" in text


def test_new_name_beside_a_bump_still_needs_a_reason(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "requirements.txt").write_text(
        "madeup-widget==1.0  # example client\n",
        encoding="utf-8",
    )
    commit_all(repo, "first pin")
    base = base_sha(repo)
    (repo / "requirements.txt").write_text(
        "madeup-widget==2.0\nother-widget==1.0\n",
        encoding="utf-8",
    )
    commit_all(repo, "bump and add")
    code, text = run(repo, base)
    fail_lines = [line for line in text.splitlines() if line.startswith("fail check 2")]
    assert code == 1
    assert fail_lines
    assert any("other-widget" in line for line in fail_lines)
    assert all("madeup-widget" not in line for line in fail_lines)
