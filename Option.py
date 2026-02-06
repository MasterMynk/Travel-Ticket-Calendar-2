from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Option:
    long_name: str
    type_fn: Callable[[str], Any]
