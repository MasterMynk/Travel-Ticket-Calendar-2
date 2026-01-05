from datetime import datetime
from typing import Callable, Generic, Self, TypeVar

from Logger import LogLevel, log
from common import CACHE_FOLDER, REFRESH_TIME

T = TypeVar("T")


class FileCache(Generic[T]):
    def __init__(self: Self, code: str, to_update: Callable[[], T], to_store: Callable[[T], str], to_parse: Callable[[str], T]) -> None:
        log(LogLevel.Status, f"\t\tChecking for cache with code: {code}")

        self._to_update = to_update
        self._to_store = to_store
        self._to_parse = to_parse
        self._code = code

        self._cache_fp = CACHE_FOLDER / f"{self._code}.txt"

        if self.is_cache_available():
            log(LogLevel.Status,
                f"\t\t\tCache available for code: {self._code}; retrieving cache.")
            self.data = self.retrieve()
        else:
            log(LogLevel.Status,
                f"\t\t\tNo cache available for code: {self._code}.")
            self.data = self.update()

    def update(self: Self) -> T:
        data = self._to_update()
        self._cache_fp.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cache_fp, "w") as cache_file:
            cache_file.write(self._to_store(data))
        return data

    def retrieve(self: Self) -> T:
        try:
            with open(self._cache_fp, "r") as cache_file:
                return self._to_parse(cache_file.read())
        except Exception as error:
            log(LogLevel.Warning,
                f"Error retrieving file from cache for code {self._code}: {error}")
            return self.update()

    def is_cache_available(self: Self) -> bool:
        return self._cache_fp.is_file() and (datetime.now() - datetime.fromtimestamp(self._cache_fp.stat().st_mtime)) < REFRESH_TIME
