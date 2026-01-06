from datetime import datetime
from pathlib import Path
from typing import Self
import re

from pypdf import PdfReader

from Logger import LogLevel, log
from RailRadarHandler import RailRadarHandler
from TravelData import TravelData, TravelDataField, TravelType
from common import IRCTC_DATE_FORMAT


class Ticket:
    def __init__(self: Self, filepath: Path) -> None:
        self._filepath = filepath

        log(LogLevel.Status, "\tExtracting Ticket text")
        with PdfReader(self._filepath) as pdf:
            ticket_data = pdf.pages[0].extract_text()

        if ticket_data.find("IRCTC") != -1:
            log(LogLevel.Status, "\tIdentified ticket as IRCTC ticket")
            self._data = self._process_as_irctc_tkt(ticket_data)
        else:
            log(LogLevel.Error, "Couldn't identify the type of ticket to parse.")
            log(LogLevel.Error, "Unimplemented feature. Skipping ticket...")
            raise Exception("Failure to parse ticket.")

    def _process_as_irctc_tkt(self: Self, ticket_text: str) -> TravelData:
        data = self._extract_data_from_irctc_ticket(ticket_text)

        log(LogLevel.Status,
            f"\tFiguring out information for train number: {data["train_number"]} from RailRadar")

        rrh = self._get_rrh_stations_marked(data, ticket_text)

        if rrh.is_data_missing:
            raise Exception(
                "Failure to find your departure/arrival station code in the list of stations the train stops at")

        assert rrh.departure_station_name and rrh.departure_datetime and rrh.arrival_datetime and rrh.arrival_station_name is not None
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
            ttc_id=data["pnr"],
        )

    def _extract_data_from_irctc_ticket(self: Self, ticket_text: str) -> dict:
        # Collecting:
        # 1. Date of departure
        # 2. PNR number for generating TTC ID
        # 3. Train number for getting any departure/arrival station name, code and time through RailRadar
        # 4. Seating arrangement if available to include in event description

        PATTERNS = [
            r"Start Date\* (?P<departure_date>.*?)\s",
            r"PNR Train No./Name Class\n(?P<pnr>\d+) (?P<train_number>\d\d\d\d\d)",
            r"CNF/(?P<seating>\w\d{1,2}/\d{1,2}/(?:SIDE )?(?:UPPER|MIDDLE|LOWER|WINDOW SIDE|NO CHOICE))|RLWL|PQWL",
        ]

        data = {}
        for i, pattern in enumerate(PATTERNS, 1):
            match = re.search(pattern, ticket_text,
                              flags=re.DOTALL | re.IGNORECASE)

            if match is None:
                raise Exception(
                    f"IRCTC ticket.\nCouldn't find something in pattern no.: {i} search group from IRCTC ticket {self._filepath}")

            data.update(match.groupdict())
        data["departure_date"] = datetime.strptime(
            data["departure_date"], IRCTC_DATE_FORMAT
        )

        log(LogLevel.Status, "\tParsed IRCTC ticket for Date of departure, pnr, train number and seating arrangement.")

        return data

    @staticmethod
    def _get_rrh_stations_marked(data: dict, ticket_text: str) -> RailRadarHandler:
        rrh = RailRadarHandler(data["train_number"], data["departure_date"])

        # Strip off any part of the text where we know the station code won't be present to make the search more efficient
        code_extract = re.search(
            r"Booked From\s+To\s+(.*?)Start Date", ticket_text, re.DOTALL | re.IGNORECASE)

        if code_extract is None:
            code_extract = ticket_text
        else:
            code_extract = code_extract.group(1)

        for code, mark in rrh.station_codes():
            code_match = re.search(
                f"{r"\W"}{code}{r"\W"}", code_extract)
            if code_match is not None:
                # This will be set while marking the departure station
                # That way we won't be searching the part of the extract that we know contains the departure station code anyways
                code_extract = code_extract[code_match.end():]

                if rrh.departure_station_marked:
                    # If we've reached here means we've already marked the departure station before
                    # The following mark call will mark the arrival station hence we're done
                    mark()
                    break
                else:
                    # Marking the departure station
                    mark()
        return rrh

    @property
    def ttc_id(self: Self) -> str:
        return self._data.ttc_id

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
