from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CommandResult:
    code: int
    out: str
    err: str


def run_command(
    args: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> CommandResult:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def last_line(result: CommandResult) -> str:
    lines = (result.err or result.out).strip().splitlines()
    return lines[-1] if lines else "the command failed"
