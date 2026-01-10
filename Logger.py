from datetime import datetime
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
        if config.log_folder is None:
            print(f"[{level.name}]: ", *args)
        else:
            today_log_path = config.log_folder / \
                f"log_{datetime.now().strftime("%d_%m_%Y")}.txt"

            today_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(today_log_path, "a") as output:
                output.write(f"[{level.name}]: {" ".join(args)}\n")
    except Exception as error:
        print(f"[Error]: Failure to open a log file: {error}")
        print(f"[{level.name}]: ", *args)
