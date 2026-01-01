# If modifying these scopes, delete the file token.json.
from datetime import timedelta
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]

IRCTC_REGEX = {
    "station_info": r"Booked From\n To\n(?P<departure_station_name>.*?) \((?P<departure_station_code>\w{3,4})\).*?\) (?P<arrival_station_name>.*) \((?P<arrival_station_code>\w{3,4})\)\n",
    "time_info": r"Start Date\* (?P<departure_date>.*?) Departure\* (?P<departure_datetime>.*?) Arrival\* (?P<arrival_datetime>.*?)\n",
    "train_number": r"PNR Train No./Name Class\n\d+ (?P<train_number>\d\d\d\d\d)"
}

DATA_MISSING_IRCTC = "N.A."

IRCTC_DATE_FORMAT = "%d-%b-%Y"
IRCTC_DATETIME_FORMAT = "%H:%M %d-%b-%Y"

CACHE_FOLDER = Path.home() / ".cache/Travel Ticket Calendar/"
REFRESH_TIME = timedelta(weeks=1)

RAIL_RADAR_CREDENTIALS_FP = Path(
    __file__).parent / "rail_radar_credentials.json"
