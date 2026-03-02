import json
from pathlib import Path
from typing import Callable, Self

from src.classes.Configuration import Configuration
from src.misc.Logger import LogLevel, log


class IndexHandler:
    def __init__(self: Self, config: Configuration) -> None:
        self._data: dict[str, str] = {}
        self._config = config
        self._output_path = self._config.cache_folder / "index.json"

    def __getitem__(self: Self, ticket_fp: Path) -> str:
        return self._data[ticket_fp.name]

    def hold(self: Self, ticket_fp: Path, ttc_id: str) -> None:
        self._data[ticket_fp.name] = ttc_id

    def __setitem__(self: Self, ticket_fp: Path, ttc_id: str) -> None:
        self._data[ticket_fp.name] = ttc_id
        self.flush()

    def __contains__(self: Self, ticket_fp: Path) -> bool:
        return ticket_fp.name in self._data

    def pop(self: Self, ticket_fp: Path) -> str:
        to_ret = self._data.pop(ticket_fp.name, "")
        self.flush()
        return to_ret

    def flush(self: Self) -> None:
        try:
            with open(self._output_path, "w") as output_file:
                output_file.write(json.dumps(self._data))
            log(LogLevel.Status, self._config,
                f"Successfully updated {self._output_path}")
        except Exception as error:
            log(LogLevel.Warning, self._config,
                f"Failed to create/update {self._output_path} due to error: {error}")

    def for_missing(self: Self, action: Callable[[str, str], None]) -> None:
        try:
            with open(self._output_path, "r") as output_file:
                prev_data: dict[str, str] = json.loads(output_file.read())
                for deleted_path in set(prev_data.keys()) - set(self._data.keys()):
                    log(LogLevel.Status, self._config,
                        f"{deleted_path} ticket is missing")
                    action(deleted_path, prev_data[deleted_path])
        except Exception as error:
            log(LogLevel.Warning, self._config,
                f"Failure to open {self._output_path} for reading to compare with current tickets")
