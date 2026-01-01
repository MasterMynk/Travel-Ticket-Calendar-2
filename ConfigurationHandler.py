from pathlib import Path
from typing import Self


class ConfigurationHandler:
    def __init__(self: Self) -> None:
        self._tickets_folder = Path.home() / "travels/"

    @property
    def tickets_folder(self: Self) -> Path:
        return self._tickets_folder
