def cloned(name: str) -> str:
    body = "\n".join(f"    total = total + {index}" for index in range(12))
    return f"def {name}(value: int) -> int:\n    total = value\n{body}\n    return total\n"


def long_function(extra: int) -> str:
    lines = ["def too_long() -> int:", "    total = 0"]
    for index in range(extra):
        lines.append(f"    total = total + {index}")
    lines.append("    return total")
    return "\n".join(lines) + "\n"


def nested_function(levels: int) -> str:
    lines = ["def nested(flag: int) -> int:"]
    for index in range(levels):
        pad = "    " * (index + 1)
        lines.append(f"{pad}if flag > {index}:")
    lines.append(f"{'    ' * (levels + 1)}return flag")
    lines.append("    return 0")
    return "\n".join(lines) + "\n"


def secret_module() -> str:
    parts = ["A1", "b2", "C3", "d4", "E5", "f6", "G7", "h8", "I9", "j0"]
    value = "sk-" + ("".join(parts) * 3)
    return f'def token() -> str:\n    api_key = "{value}"\n    return api_key\n'


def commented_module() -> str:
    return 'def live(n: int) -> int:\n    # print("hello")\n    return n\n'


def marker_module(kind: str) -> str:
    return f"def live(n: int) -> int:\n    # {kind}: later\n    return n\n"


def todo_module() -> str:
    return marker_module("TO" + "DO")


def fixme_module() -> str:
    return marker_module("FIX" + "ME")
