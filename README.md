# coderev

`coderev check` reads a git diff and passes or fails the new lines against `STANDARD.md`. The report is plain words. Exit code 1 means an automated check failed. The human lines at the end are a sign-off list. The tool does not decide them.

The thresholds in `coderev/settings_default.toml` are the standard's defaults to test: duplication 3%, coverage 80%, function length 50, nesting 3. A repository may override them with `coderev.toml` in its root, same keys. `complexity_limit` is omitted on purpose. STANDARD.md marks that limit as to test and gives no number.

## Install and run

Prerequisite, installed separately. gitleaks 8 is a Go binary (MIT) and is not on PyPI. Check 9 needs it.

```bash
# Linux x86_64 example. Other builds are on the gitleaks releases page.
curl -fsSL -o gitleaks.tar.gz -L https://github.com/gitleaks/gitleaks/releases/download/v8.28.0/gitleaks_8.28.0_linux_x64.tar.gz
tar -xzf gitleaks.tar.gz gitleaks
install -m 755 gitleaks "$HOME/.local/bin/gitleaks"
```

jscpd 5 is a native binary published on PyPI (MIT). `pip install .` installs it with the other Python packages.

```bash
pip install .
coderev check
```

`coderev check` compares the current commit to the merge-base of `main`, then `master`, then `origin/main`, then `origin/master`. `--base` names a different base. The work tree must be clean. The run uses the committed diff, and the wrapped tools read the working tree.

The tests for this repository are `pytest`.

## What each dependency checks

| Dependency | License | Check |
|---|---|---|
| ruff | MIT | Check 5 and check 6 |
| vulture | MIT | Check 5 |
| jscpd | MIT | Check 4 |
| lizard | MIT | Check 6 |
| diff-cover | Apache-2.0 | Check 10 coverage |
| coverage | Apache-2.0 | Check 10, because diff-cover reads its XML and does not run tests |
| pytest | MIT | Check 10. The coverage step runs the target repository's own tests, which runs that repository's code. |
| tampercheck | Apache-2.0 | Check 10 deleted test files and skipped tests. Check 5 kind `placeholder`. |
| gitleaks (prerequisite) | MIT | Check 9 |

## Rules and flags

| Check | Tool | Rule or flag |
|---|---|---|
| 2. New dependency has a reason | git diff of `*requirements*.txt` and `pyproject.toml` | A reason is a `#` comment on the same added line. A line whose package name was removed in the same diff is a change, not a new dependency. |
| 4. Duplication | jscpd `--format python --baseline-from-ref` | JSON `statistics.total.newDuplicatedLines`, divided by added Python lines. Fail when that percent is above `duplication_percent`. jscpd `--threshold` measures the whole tree. |
| 5. Unused import | ruff | `F401` |
| 5. Unused variable | ruff | `F841` |
| 5. Commented-out code | ruff | `ERA001` |
| 5. TODO | ruff | `FIX002` |
| 5. FIXME | ruff | `FIX001` |
| 5. Unused code and unreachable code | vulture | Default report. Unreachable lines contain the words `unreachable code`. Names matching `test_*` are ignored so pytest collection is not a leftover. |
| 5. NotImplementedError and other placeholders | tampercheck | kind `placeholder`, including `raise NotImplementedError` |
| 6. Function length | lizard | `--length` / `-L`, field `NLOC`. A warning is a failure only when NLOC is above `max_function_lines` and the function overlaps a new line. |
| 6. Nesting | ruff | `PLR1702` with `lint.pylint.max-nested-blocks` from `max_nesting_level`. The rule is in preview, so the run passes `--preview`. |
| 9. Secrets | gitleaks | `gitleaks git --log-opts <base>..<head>`. The report line is the rule id, file, and line. |
| 10. Coverage | diff-cover | `--fail-under` from `coverage_percent`, using `coverage xml`. diff-cover is the tool that scores the diff. |
| 10. Deleted test file | tampercheck | kind `test-deleted` |
| 10. Skipped test | tampercheck | kind `test-skipped` |

The coverage step runs the target repository's own tests with `coverage run --source=.`. Running those tests runs that repository's code. It omits `tests/`, `test_*.py`, and `conftest.py`, then diff-cover reads the XML. Test lines do not raise the percentage.

## Not automated

These parts of the standard have no existing tool rule here. The report says `not automated` and repeats them on the human list. The tool does not fail the run for them.

- A new package exists on an index. Check 2 automates the same-line reason only.
- Complexity. Set `complexity_limit` in the settings file to turn on ruff `C901`. Until then it stays on the human list.
- A test function removed inside a file that stays. tampercheck `test-deleted` flags a deleted test file.
- `pytest.skip()`. tampercheck `test-skipped` flags `@pytest.mark.skip`, `@pytest.mark.skipif`, and `@unittest.skip`.
- A changed test file that never imports the changed code.

The duplicate-code check in pylint is GPL-2.0, so this tool wraps jscpd.
