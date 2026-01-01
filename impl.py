from pathlib import Path
from ConfigurationHandler import ConfigurationHandler


def gen_custom_id() -> str:
    return ""


def ensure_event(ticket: Path) -> None:
    print(ticket)


def load(config: ConfigurationHandler) -> None:
    for ticket in config.tickets_folder.glob("*.pdf"):
        ensure_event(ticket)
