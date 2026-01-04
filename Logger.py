from enum import IntEnum, auto


class LogLevel(IntEnum):
    Status = auto()
    Warning = auto()
    Error = auto()


def log(level: LogLevel, *args, **kwargs) -> None:
    print(f"[{level.name}]:", *args, **kwargs)
