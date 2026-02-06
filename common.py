from enum import Enum, IntEnum, auto
from functools import reduce
from pathlib import Path
import re

from plyer import notification

from Logger import LogLevel, log

from typing import TYPE_CHECKING, Type

from Option import Option

if TYPE_CHECKING:
    from Configuration import Configuration


class ReminderNotificationType(IntEnum):
    popup = auto()
    email = auto()


class CalendarEventColor(IntEnum):
    Lavendar = 1
    Sage = 2
    Grape = 3
    Flamingo = 4
    Banana = 5
    Tangerine = 6
    Peacock = 7
    Graphite = 8
    Blueberry = 9
    Basil = 10
    Tomato = 11


SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned",
          "https://www.googleapis.com/auth/drive.file"]


CONFIGURATION_FOLDER = Path.home() / ".config/Travel Ticket Calendar"

OPTIONS = (
    Option("config-path"),
    Option("gapi-credentials-path"),
    Option("gapi-token-path"),
    Option("rail-radar-credentials-path"),
    Option("ai-model-credentials-path"),
    Option("cache-folder"),
    Option("ticket-folder"),
    Option("done-folder"),
    Option("log-folder"),
    Option("calendar-id"),
    Option("reminder-notification-type"),
    Option("event-color"),
    Option("ai-model"),
    Option("max-retries-for-network-requests", int),
)


def calculate_backoff(attempt: int) -> float:
    return 2 ** attempt


def notify(title: str, message: str, config: "Configuration") -> None:
    try:
        notification.notify(  # type: ignore
            title=title, message=message, app_name="Travel Ticket Calendar", timeout=10
        )
    except Exception as error:
        log(LogLevel.Warning, config, f"Failure to send notification: {error}")


def stringify_enum(enum: Type[Enum]) -> str:
    return ", ".join([val.name for val in enum])


def is_invalid_option_name(name: str) -> bool:
    return re.fullmatch(r"[\w-]+", name) is None


def shorthand_for(option: str) -> str:
    if is_invalid_option_name(option):
        raise Exception(
            f"Invalid option name: {option}. Must only consist of letters or hyphens")

    return reduce(
        lambda res, word: res + word[0],
        option.split("-"), ""
    )
