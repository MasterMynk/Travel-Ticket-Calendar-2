import json
from pathlib import Path
from typing import Self

from src.classes.Configuration import Configuration
from src.misc.Logger import LogLevel, log


class IndexHandler:
    def __init__(self: Self, config: Configuration) -> None:
        self._data: dict[str, str] = {}
        self._config = config
        self._output_path = self._config.cache_folder / "index.json"

    def __getitem__(self: Self, ticket_fp: Path) -> str:
        return self._data[ticket_fp.name]

    def __setitem__(self: Self, ticket_fp: Path, ttc_id: str) -> None:
        self._data[ticket_fp.name] = ttc_id

    def flush(self: Self) -> None:
        try:
            with open(self._output_path, "w") as output_file:
                output_file.write(json.dumps(self._data))
            log(LogLevel.Status, self._config,
                f"Successfully updated {self._output_path}")
        except Exception as error:
            log(LogLevel.Warning, self._config,
                f"Failed to create/update {self._output_path} due to error: {error}")
