from enum import IntEnum, auto
from pathlib import Path


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
