from datetime import datetime
import json
from pathlib import Path
from typing import Self
import re

from pypdf import PdfReader

from AiModelHandler import Model
from Configuration import Configuration
from Logger import LogLevel, log
from RailRadarHandler import RailRadarHandler
from TravelData import TravelData, TravelDataField, TravelType
from common import CalendarEventColor


class Ticket:
    def __init__(self: Self, filepath: Path, model: Model, config: Configuration) -> None:
        self._filepath = filepath

        log(LogLevel.Status, config, "\tExtracting Ticket text")
        with PdfReader(self._filepath) as pdf:
            ticket_text = pdf.pages[0].extract_text()

        if ticket_text.find("IRCTC") != -1:
            log(LogLevel.Status, config, "\tIdentified ticket as IRCTC ticket")
            self._data = self._process_as_irctc_tkt(ticket_text, config)
        else:
            log(LogLevel.Status, config,
                "Couldn't identify the type of ticket to parse. Parsing with AI Model.")
            self._data = self._process_with_ai_model(
                self._filepath, model, config)

    def _process_as_irctc_tkt(self: Self, ticket_text: str, config: Configuration) -> TravelData:
        data = self._extract_data_from_irctc_ticket(
            self._filepath, ticket_text, config)

        log(LogLevel.Status, config,
            f"\tFiguring out information for train number: {data["train_number"]} from RailRadar")

        rrh = self._get_rrh_stations_marked(data, ticket_text, config)

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
            event_color=data["event_color"],
        )

    def _extract_data_from_irctc_ticket(self: Self, ticket_fp: Path, ticket_text: str, config: Configuration) -> dict:
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
        IRCTC_DATE_FORMAT = "%d-%b-%Y"


        data = {}
        for i, pattern in enumerate(PATTERNS, 1):
            match = re.search(pattern, ticket_text,
                              flags=re.DOTALL | re.IGNORECASE)

            if match is None:
                raise Exception(
                    f"IRCTC ticket.\nCouldn't find something in pattern no.: {i} search group from IRCTC ticket {ticket_fp}")

            data.update(match.groupdict())

        data["event_color"] = self._color_from_ticket(ticket_text, config)
        data["departure_date"] = datetime.strptime(
            data["departure_date"], IRCTC_DATE_FORMAT
        )

        log(LogLevel.Status, config,
            "\tParsed IRCTC ticket for Date of departure, pnr, train number and seating arrangement.")

        return data

    @staticmethod
    def _color_from_ticket(ticket_text: str, config: Configuration) -> CalendarEventColor:
        ticket_text = ticket_text.lower()
        for traveller in config.traveller:
            for name in traveller.name:
                if len(name) <= 16 and re.search(name.replace(" ", r"\s+"), ticket_text) is not None:
                    return traveller.color
        return config.event_color

    @staticmethod
    def _get_rrh_stations_marked(data: dict, ticket_text: str, config: Configuration) -> RailRadarHandler:
        rrh = RailRadarHandler(
            data["train_number"], data["departure_date"], config)

        # Strip off any part of the text where we know the station code won't be present to make the search more efficient
        code_extract = re.search(
            r"Booked From\s+To\s+(.*?)Start Date", ticket_text, re.DOTALL | re.IGNORECASE)

        code_extract = ticket_text if code_extract is None else code_extract.group(
            1)

        for code, mark in rrh.station_codes():
            code_match = re.search(
                f"{r"\W"}{code}{r"\W"}", code_extract)
            if code_match is not None:
                # This will shorten the search string when departure station code is found
                # That way we won't be searching the part of the extract that we know contains the departure station code anyways
                code_extract = code_extract[code_match.end():]

                mark()  # First departure station is marked, then arrival station
                if not rrh.departure_station_marked:
                    break  # After arrival station marked we break

        return rrh

    @staticmethod
    def _process_with_ai_model(ticket_fp: Path, model: Model, config: Configuration) -> TravelData:
        TICKET_EXTRACTION_PROMPT = """
Analyze this travel ticket (flight/train/bus) and extract information in valid JSON format.

CRITICAL REQUIREMENTS:
1. All datetime values MUST be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
2. If year is missing, use """ + f"{datetime.now().year}" + """ as default
3. Return ONLY valid JSON, no markdown formatting or code blocks
4. The "description" field must be a string containing different pieces of on new lines
5. If the ticket is for multiple passengers simply consider it being for the first passenger name that appears

REQUIRED FIELDS:
{
  "departure": {
    "when": "ISO datetime string",
    "where": "Full location with terminal/platform/gate if available"
  },
  "arrival": {
    "when": "ISO datetime string", 
    "where": "Full location with terminal/platform/gate if available"
  },
  "ttc_id": "PNR/Booking Reference/Confirmation Number with PNR having the highest priority",
  "travel_type": "Flight|Train|Bus",
  "description": "airline/railway/bus company name\\nflight/train number\\nseat/coach/berth number if available",
  "traveller": "Full name without any honorific (like Mr., Mrs., etc.) of the first passenger that appears in the ticket",
}

LOCATION FORMATTING RULES:
- For airports: Include city and terminal depending on what is available (e.g., "Delhi Airport, Terminal 1D")
- For trains: Include station name and platform if available (e.g., "New Delhi Railway Station, Platform 5")
- For buses: Include station/terminal name
- Always use the full official name when possible

EXTRACTION STRATEGY:
1. First identify the transport type (flight/train/bus)
2. Look for PNR/booking reference prominently displayed
3. Extract departure/arrival times - they're usually in 24-hour format
"""
        response = model.parse(ticket_fp, TICKET_EXTRACTION_PROMPT, config)

        if "```json" in response:
            response = response.split(
                "```json")[1].split("```")[0]
        response = json.loads(response)

        for key in ["departure", "arrival"]:
            response[key]["when"] = datetime.fromisoformat(
                response[key]["when"])

        return TravelData(
            TravelType[response["travel_type"]],
            f"{response["traveller"]}\n{response["description"]}",
            TravelDataField(**response["departure"]),
            TravelDataField(**response["arrival"]),
            response["ttc_id"],
            config.traveller_to_color(response["traveller"]),
        )

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

    @property
    def color(self: Self) -> CalendarEventColor:
        return self._data.event_color
