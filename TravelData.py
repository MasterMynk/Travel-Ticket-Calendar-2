
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, auto

from common import CalendarEventColor


@dataclass
class TravelDataField:
    where: str
    when: datetime


class TravelType(IntEnum):
    Train = auto()
    Flight = auto()
    Bus = auto()


@dataclass
class TravelData:
    travel_type: TravelType
    description: str
    departure: TravelDataField
    arrival: TravelDataField
    ttc_id: str
    event_color: CalendarEventColor
