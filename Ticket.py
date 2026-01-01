from datetime import datetime
from pathlib import Path
import sys
from typing import Self
import re

from pypdf import PdfReader

from RailRadarHandler import RailRadarHandler
from common import IRCTC_DATE_FORMAT, IRCTC_DATETIME_FORMAT, IRCTC_REGEX, DATA_MISSING_IRCTC

from pprint import pprint


class Ticket:
    def __init__(self: Self, filepath: Path) -> None:
        self._filepath = filepath
        self._pdf = PdfReader(self._filepath)

        ticket_data = self._pdf.pages[0].extract_text()

        if ticket_data.find("IRCTC") != -1:
            self._process_as_irctc_tkt(ticket_data)

    def __del__(self: Self) -> None:
        self._pdf.close()

    def _process_as_irctc_tkt(self: Self, ticket_data: str) -> None:
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

    def get_id(self) -> None:
        pass
