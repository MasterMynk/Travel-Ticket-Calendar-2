from enum import IntEnum, auto
from datetime import timedelta
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

GOOGLE_CREDENTIALS_FP = Path(__file__).parent / "credentials.json"
GOOGLE_TOKEN_FP = Path(__file__).parent / "token.json"

DEFAULT_CALENDAR_ID = "primary"
REMINDER_NOTIFICATION_TYPE = ReminderNotificationType.popup
DEFAULT_REMINDERS = [
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(weeks=1),
]
DEFAULT_EVENT_COLOR = CalendarEventColor.Banana

IRCTC_REGEX = {
    # "station_info": r"Booked From\n To\n(?P<departure_station_name>.*?) \((?P<departure_station_code>\w{3,4})\).*?\) (?P<arrival_station_name>.*) \((?P<arrival_station_code>\w{3,4})\)\n",
    # "time_info": r"Start Date\* (?P<departure_date>.*?) Departure\* (?P<departure_datetime>.*?) Arrival\* (?P<arrival_datetime>.*?)\n",
    "time_info": r"Start Date\* (?P<departure_date>.*?)\s",
    "train_number": r"PNR Train No./Name Class\n\d+ (?P<train_number>\d\d\d\d\d)",
    "seating": r"CNF/(?P<seating>\w\d{1,2}/\d{1,2}/(?:SIDE )?(?:UPPER|MIDDLE|LOWER|WINDOW SIDE|NO CHOICE))|RLWL|PQWL"
}

DATA_MISSING_IRCTC = "N.A."

IRCTC_DATE_FORMAT = "%d-%b-%Y"
IRCTC_DATETIME_FORMAT = "%H:%M %d-%b-%Y"

CACHE_FOLDER = Path.home() / ".cache/Travel Ticket Calendar/"
REFRESH_TIME = timedelta(weeks=1)

RAIL_RADAR_CREDENTIALS_FP = Path(
    __file__).parent / "rail_radar_credentials.json"

TICKET_FOLDER = Path.home() / "travels/"

MAX_RETRIES_FOR_NETWORK_REQUESTS = 7


def calculate_backoff(attempt: int) -> float:
    return 2 ** attempt
