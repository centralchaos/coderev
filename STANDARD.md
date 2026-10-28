# Standard for reviewing AI-assisted code (v0.1, draft)

Status: draft for the owner's approval. Not yet pushed to any repository.

This standard says what a change must show before it merges when an AI agent wrote some or all of it. It is short on purpose. Every check is either run by the tool or signed by a named human. A check that neither can do is not in this document.

## Rules that apply to every change

1. Every AI-assisted change has one named human owner who approves it. An AI review never replaces that approval. (Source: OWASP Secure Coding with AI cheat sheet, section 14.)
2. The owner must be able to explain how the change works. If the author cannot describe it, it is not ready to merge. (Source: OWASP DevSecOps Guideline, Secure Code Review.)
3. Evidence comes from the project's CI run, shown as a link. The agent's own report of a passing run is not evidence. (Our own rule.)
4. Checks run on new code only (the lines in the diff), so old debt does not block new work. (Source: the Sonar quality gate also measures new code only.)

## The ten checks

Mode: AUTO means the tool checks it and fails the run. HUMAN means the owner signs a checklist line. Thresholds marked "to test" are starting values with no published backing. Run them on real code and change them with evidence.

| # | Check | What it catches in AI-written code | Mode | Default threshold | Source |
|---|---|---|---|---|---|
| 1 | The change does what the request says and nothing else | Unrelated edits, scope creep, silent behavior changes | HUMAN | none | GitHub guide to reviewing AI-generated code (context and intent) |
| 2 | Names and packages are real | Invented APIs, functions, config keys and packages | AUTO for packages, HUMAN for APIs | Every new dependency is listed in the diff with a reason, and the package exists | Red Hat AI code review (hallucinated APIs), OWASP Secure Coding with AI (check that suggested packages exist and pass an audit) |
| 3 | Every branch is traced | Plausible but wrong logic, missed empty and malformed input | HUMAN | none | Red Hat AI code review (plausible-but-wrong logic) |
| 4 | No duplicated code | Near copies of code that already exists | AUTO | Duplication on new code at most 3% | Sonar way for agentic AI gate |
| 5 | No dead code or leftovers | Unused imports and variables, unreachable code, commented-out code, stubs, abandoned scaffolding | AUTO | Zero new findings. Leftover markers (TODO, FIXME, NotImplementedError, commented-out code) are findings | Red Hat AI code review (abandoned scaffolding), Sonar gate (no new maintainability issues at Medium or above) |
| 6 | Functions stay small and flat | Long, deeply nested functions | AUTO | At most about 50 lines and nesting at most 3 levels (community source). Complexity limit: to test | local-review CHECKLIST.md (community, not a formal standard) |
| 7 | No abstraction with a single caller | Layers and options built for a need nobody asked for | HUMAN | none | Our own rule. The motivation is the measured growth in verbosity of agent code (see Evidence) |
| 8 | Errors are not swallowed | Missing or silent error handling, leaks on failure paths | HUMAN | none | Red Hat AI code review (incomplete error handling) |
| 9 | No secrets in the diff | Keys, tokens and personal data in code or logs | AUTO | Zero findings | Sonar gate (no new security issues). Secret scanning by gitleaks or detect-secrets |
| 10 | Tests are real | Tests that were deleted, weakened or never exercise the code; tests the agent wrote to pass its own change | AUTO for coverage, deletions and unlinked tests. HUMAN for "fails before the fix" | Coverage on new code at least 80%. Any deleted or skipped test is flagged. A changed test file that never imports the changed code is flagged | Sonar gate (coverage), OWASP Secure Coding with AI (distrust tests from the same agent, flag test deletions), GitHub guide (tests deleted instead of fixed), Red Hat (tests fail before the fix) |

## Automatic gate, in plain words

The tool fails the run when any of these is true on new code:

- duplication is above 3%
- there is a new dead-code or leftover finding
- a function breaks the length or nesting limit
- a secret is found
- coverage is below 80%
- a test was deleted or skipped, or a test change does not touch the changed code
- a new dependency has no reason listed

Sonar way for agentic AI also has gate conditions for new Reliability issues (Low or above), new Security issues (Low or above), new Maintainability issues (Medium or above) and new Dependency Risks (Low or above, which needs a paid subscription). This tool does not rebuild those. Adopting SonarQube is a separate decision for the owner.

## Human sign-off list

The owner signs each line on the PR:

- [ ] Check 1: the change matches the request, with no unrelated edits.
- [ ] Check 2: every API and name the change calls exists in our code and versions.
- [ ] Check 3: I traced each branch, including empty, malformed and other-tenant input.
- [ ] Check 7: no abstraction exists for a future need nobody asked for.
- [ ] Check 8: failures fail closed and nothing is swallowed.
- [ ] Check 10: the tests fail before the change and pass after it.
- [ ] Rules 1 to 3: I own this change, I can explain it, and the evidence is a CI link.
- [ ] Files that set rules or build behavior (agent rule files, CI and build files) got extra scrutiny. (Source: OWASP Secure Coding with AI.)

## Evidence behind the standard, with limits

- Duplicated code blocks rose 81% over 2023, from 40.3 to 73.0 per million changed lines, in a study of 623 million changed lines from 2023 to 2026. Moved lines fell from 13% in 2023 to 3.8% in 2026 year to date. (GitClear, vendor research. Its page states the base year for the refactoring figure inconsistently, so we quote the two raw percentages.)
- Agent code was 2.3 times more verbose and 2.0 times more eroded than 473 human repositories, and it got worse over iterations: erosion rose in 77% of runs and verbosity in 75.5%. (SlopCodeBench, arXiv 2603.24755.)
- In one benchmark, 64 of 483 outcomes (13.3%) passed every functional test but failed the structural checks. The unit is outcomes, not edits. (Needle in the Repo, arXiv 2603.27745.)
- Across 4,442 Java tasks and five models there was no direct correlation between passing functional tests and code quality or security. (Sonar study, arXiv 2508.14727, vendor research.)

These are warning signs from vendor and preprint research. They are not a formal standard, and no formal benchmark for AI-assisted code review exists that we could verify.

## Tools the checker may wrap

Existing open-source tools only. The checker writes no analyzers of its own.

| Need | Tool | License |
|---|---|---|
| Dead code | vulture | MIT |
| Unused imports and variables, complexity | ruff (F401, F841, C901) | MIT |
| Duplication | jscpd | MIT |
| Secrets | gitleaks | MIT |
| New dependencies | a plain git diff of requirements and pyproject files | none needed |

pylint's duplicate-code check (R0801) works but pylint is GPL-2.0, so prefer jscpd. detect-secrets (Apache-2.0) is an alternative to gitleaks. Pick one per need.

## Out of scope for v0.1

A hosted service, a pull-request bot, other languages, a dashboard, a plugin system, and SonarQube itself.

## Open for the owner

- Approve, change or drop each check.
- The 3% duplication, 80% coverage, 50-line and 3-level numbers are defaults to test on real code before they become policy. All other numeric limits are "to test".
