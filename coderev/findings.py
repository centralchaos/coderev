from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    status: str
    check: str
    text: str


def fail(check: str, text: str) -> Finding:
    return Finding("fail", check, text)


def ok(check: str, text: str) -> Finding:
    return Finding("pass", check, text)
