from enum import IntEnum, auto
from pathlib import Path

from plyer import notification

from Logger import LogLevel, log

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


def calculate_backoff(attempt: int) -> float:
    return 2 ** attempt


def notify(title: str, message: str, config) -> None:
    try:
        notification.notify(  # type: ignore
            title=title, message=message, app_name="Travel Ticket Calendar", timeout=10
        )
    except Exception as error:
        log(LogLevel.Warning, config, f"Failure to send notification: {error}")
