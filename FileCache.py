from datetime import datetime
from typing import Callable, Generic, Self, TypeVar

from common import CACHE_FOLDER, REFRESH_TIME

T = TypeVar("T")


class FileCache(Generic[T]):
    def __init__(self: Self, code: str, to_update: Callable[[], T], to_store: Callable[[T], str], to_parse: Callable[[str], T]) -> None:
        self._to_update = to_update
        self._to_store = to_store
        self._to_parse = to_parse

        self._cache_fp = CACHE_FOLDER / f"{code}.txt"

        if self.is_cache_available():
            self.data = self.retrieve()
        else:
            self.data = self.update()

    def update(self: Self) -> T:
        data = self._to_update()
        self._cache_fp.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cache_fp, "w") as cache_file:
            cache_file.write(self._to_store(data))
        return data

    def retrieve(self: Self) -> T:
        with open(self._cache_fp, "r") as cache_file:
            return self._to_parse(cache_file.read())

    def is_cache_available(self: Self) -> bool:
        return self._cache_fp.is_file() and (datetime.now() - datetime.fromtimestamp(self._cache_fp.stat().st_mtime)) < REFRESH_TIME
