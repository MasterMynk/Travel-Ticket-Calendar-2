from datetime import datetime
from pathlib import Path
from typing import Callable, Generic, Self, TypeVar

from Configuration import Configuration
from Logger import LogLevel, log

T = TypeVar("T")


class FileCache(Generic[T]):
    def __init__(self: Self, code: str, to_update: Callable[[Configuration], T], to_store: Callable[[T], str], to_parse: Callable[[str], T], config: Configuration) -> None:
        log(LogLevel.Status, f"\t\tChecking for cache with code: {code}")

        self._to_update = to_update
        self._to_store = to_store
        self._to_parse = to_parse
        self._code = code

        if self.is_cache_available(config):
            log(LogLevel.Status,
                f"\t\t\tCache available for code: {self._code}; retrieving cache.")
            self.data = self.retrieve(config)
        else:
            log(LogLevel.Status,
                f"\t\t\tNo cache available for code: {self._code}.")
            self.data = self.update(config)

    def update(self: Self, config: Configuration) -> T:
        data = self._to_update(config)
        self._get_cache_fp(self._code, config).parent.mkdir(
            parents=True, exist_ok=True)
        with open(self._get_cache_fp(self._code, config), "w") as cache_file:
            cache_file.write(self._to_store(data))
        return data

    def retrieve(self: Self, config: Configuration) -> T:
        try:
            with open(self._get_cache_fp(self._code, config), "r") as cache_file:
                return self._to_parse(cache_file.read())
        except Exception as error:
            log(LogLevel.Warning,
                f"Error retrieving file from cache for code {self._code}: {error}")
            return self.update(config)

    def is_cache_available(self: Self, config: Configuration) -> bool:
        return self._get_cache_fp(self._code, config).is_file() and (datetime.now() - datetime.fromtimestamp(self._get_cache_fp(self._code, config).stat().st_mtime)) < config.cache_data_refresh_time

    @staticmethod
    def _get_cache_fp(code: str, config: Configuration) -> Path:
        return config.cache_folder / f"{code}.txt"
