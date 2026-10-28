from dataclasses import dataclass
from pathlib import Path
import tomllib

from coderev.errors import CheckError


@dataclass(frozen=True)
class Settings:
    duplication_percent: float
    coverage_percent: float
    max_function_lines: int
    max_nesting_level: int
    complexity_limit: int | None


def load_settings(repo: Path, override: Path | None) -> Settings:
    path = _settings_path(repo, override)
    if not path.is_file():
        raise CheckError(f"Settings file {path} does not exist.")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise CheckError(f"Settings file {path.name} is not valid TOML.") from exc
    return Settings(
        duplication_percent=_number(data, "duplication_percent"),
        coverage_percent=_number(data, "coverage_percent"),
        max_function_lines=_whole(data, "max_function_lines"),
        max_nesting_level=_whole(data, "max_nesting_level"),
        complexity_limit=_optional_whole(data, "complexity_limit"),
    )


def _settings_path(repo: Path, override: Path | None) -> Path:
    if override is not None:
        return override
    local = repo / "coderev.toml"
    if local.is_file():
        return local
    return Path(__file__).with_name("settings_default.toml")


def _number(data: dict[str, object], key: str) -> float:
    value = _present(data, key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CheckError(f"Settings file {key} must be a number.")
    return float(value)


def _whole(data: dict[str, object], key: str) -> int:
    value = _present(data, key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise CheckError(f"Settings file {key} must be a whole number.")
    return value


def _optional_whole(data: dict[str, object], key: str) -> int | None:
    if key not in data:
        return None
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise CheckError(f"Settings file {key} must be a whole number.")
    return value


def _present(data: dict[str, object], key: str) -> object:
    if key not in data:
        raise CheckError(f"Settings file is missing {key}.")
    return data[key]
