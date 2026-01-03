from datetime import datetime
from pathlib import Path
import sys
from typing import Self
import re

from pypdf import PdfReader

from RailRadarHandler import RailRadarHandler
from TravelData import TravelData, TravelDataField, TravelType
from common import IRCTC_DATE_FORMAT, IRCTC_DATETIME_FORMAT, IRCTC_REGEX, DATA_MISSING_IRCTC


class Ticket:
    def __init__(self: Self, filepath: Path) -> None:
        self._filepath = filepath
        self._pdf = PdfReader(self._filepath)

        ticket_data = self._pdf.pages[0].extract_text()

        if ticket_data.find("IRCTC") != -1:
            self._data = self._process_as_irctc_tkt(ticket_data)
        else:
            print("Couldn't identify the type of ticket to parse. Unimplemented feature")
            sys.exit(-1)

    def __del__(self: Self) -> None:
        self._pdf.close()

    def _process_as_irctc_tkt(self: Self, ticket_data: str) -> TravelData:
        data = {}

        # Collect as much data as you can from the ticket itself using regex
        for search_group, pattern in IRCTC_REGEX.items():
            match = re.search(pattern, ticket_data, flags=re.DOTALL)

            if match is None:
                print(
                    f"Couldn't find something in {search_group} saerch group from IRCTC ticket {self._filepath}")
                print("Exiting...")
                sys.exit(-1)

            data.update(match.groupdict())

        if data["arrival_datetime"] == DATA_MISSING_IRCTC or data["departure_datetime"] == DATA_MISSING_IRCTC:
            data["departure_date"] = datetime.strptime(
                data["departure_date"], IRCTC_DATE_FORMAT)

            rrh = RailRadarHandler(data["train_number"],
                                   data["departure_date"], data["departure_station_code"], data["arrival_station_code"])

            data["departure_datetime"] = rrh.departure_datetime
            data["arrival_datetime"] = rrh.arrival_datetime
        else:
            data["departure_datetime"] = datetime.strptime(
                data["departure_datetime"], IRCTC_DATETIME_FORMAT)
            data["arrival_datetime"] = datetime.strptime(
                data["arrival_datetime"], IRCTC_DATETIME_FORMAT)

        return TravelData(
            TravelType.Train,
            (f"Seating: {data["seating"]}")
            if data["seating"] is not None
            else "",
            departure=TravelDataField(
                data["departure_station_name"],
                data["departure_datetime"]
            ),
            arrival=TravelDataField(
                data["arrival_station_name"],
                data["arrival_datetime"]
            ),
        )

    @property
    def ttc_id(self: Self) -> str:
        return f"ttc{self._data.departure.where}{self._data.arrival.where}{self._data.departure.when.isoformat()}".replace(' ', '_')

    @property
    def summary(self: Self) -> str:
        return f"{self._data.travel_type.name} to {self._data.arrival.where}"

    @property
    def description(self: Self) -> str:
        return self._data.description

    @property
    def from_where(self: Self) -> str:
        return self._data.departure.where

    @property
    def to_where(self: Self) -> str:
        return self._data.arrival.where

    @property
    def departure(self: Self) -> datetime:
        return self._data.departure.when

    @property
    def arrival(self: Self) -> datetime:
        return self._data.arrival.when
