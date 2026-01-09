from enum import IntEnum, auto

# To avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Configuration import Configuration

class LogLevel(IntEnum):
    Status = auto()
    Warning = auto()
    Error = auto()


def log(level: LogLevel, config: "Configuration", *args) -> None:
    try:
        if config.log_path is None:
            print(f"[{level.name}]: ", *args)
        else:
            with open(config.log_path, "a") as output:
                output.write(f"[{level.name}]: {" ".join(args)}\n")
    except Exception as error:
        print(f"[Error]: Failure to open a log file: {error}")
        print(f"[{level.name}]: ", *args)
