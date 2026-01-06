from datetime import datetime
from pathlib import Path
from typing import Self
import re

from pypdf import PdfReader

from Logger import LogLevel, log
from RailRadarHandler import RailRadarHandler
from TravelData import TravelData, TravelDataField, TravelType
from common import IRCTC_DATE_FORMAT, IRCTC_DATETIME_FORMAT, IRCTC_REGEX, DATA_MISSING_IRCTC


class Ticket:
    def __init__(self: Self, filepath: Path) -> None:
        self._filepath = filepath

        log(LogLevel.Status, "\tExtracting Ticket text")
        with PdfReader(self._filepath) as pdf:
            ticket_data = pdf.pages[0].extract_text()

        if ticket_data.find("IRCTC") != -1:
            self._data = self._process_as_irctc_tkt(ticket_data)
        else:
            log(LogLevel.Error, "Couldn't identify the type of ticket to parse.")
            log(LogLevel.Error, "Unimplemented feature. Skipping ticket...")
            raise Exception("Failure to parse ticket.")

    def _process_as_irctc_tkt(self: Self, ticket_text: str) -> TravelData:
        log(LogLevel.Status, "\tIdentified ticket as IRCTC ticket")
        data = {}  # Data extracted from ticket pdf
        # print("\n\n", "-"*5, self._filepath, "-"*5)
        # print(ticket_data)
        # print("-"*10, "\n\n")

        # Collect as much data as you can from the ticket itself using regex
        for search_group, pattern in IRCTC_REGEX.items():
            match = re.search(pattern, ticket_text,
                              flags=re.DOTALL | re.IGNORECASE)

            if match is None:
                raise Exception(
                    f"IRCTC ticket.\nCouldn't find something in {search_group} search group from IRCTC ticket {self._filepath}")

            data.update(match.groupdict())

        data["departure_date"] = datetime.strptime(
            data["departure_date"], IRCTC_DATE_FORMAT
        )
        log(LogLevel.Status,
            f"\tFiguring out information for train number: {data["train_number"]} from RailRadar")
        rrh = RailRadarHandler(data["train_number"], data["departure_date"])

        for station_code, mark in rrh.station_codes():
            if ticket_text.count(station_code) > 0:
                mark()

        # data["departure_datetime"] = rrh.departure_datetime
        # data["arrival_datetime"] = rrh.arrival_datetime

        # if data["arrival_datetime"] == DATA_MISSING_IRCTC or data["departure_datetime"] == DATA_MISSING_IRCTC:
        # pass
        # else:
        #     data["departure_datetime"] = datetime.strptime(
        #         data["departure_datetime"], IRCTC_DATETIME_FORMAT)
        #     data["arrival_datetime"] = datetime.strptime(
        #         data["arrival_datetime"], IRCTC_DATETIME_FORMAT)

        return TravelData(
            TravelType.Train,
            (f"Seating: {data["seating"]}")
            if data["seating"] is not None
            else "",
            departure=TravelDataField(
                rrh.departure_station_name,
                rrh.departure_datetime
            ),
            arrival=TravelDataField(
                rrh.arrival_station_name,
                rrh.arrival_datetime
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
