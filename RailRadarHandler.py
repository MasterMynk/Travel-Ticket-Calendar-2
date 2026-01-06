from collections.abc import Iterator
from datetime import datetime, timedelta
import json
import time
from typing import Any, Callable, Self, TypedDict

import requests
from requests import HTTPError, RequestException

from FileCache import FileCache
from Logger import LogLevel, log
from common import MAX_RETRIES_FOR_NETWORK_REQUESTS, RAIL_RADAR_CREDENTIALS_FP, calculate_backoff


class Station(TypedDict):
    day: int
    departure: int
    arrival: int
    code: str
    name: str


class RailRadarHandler:
    def __init__(self: Self, train_number: str, departure_date: datetime) -> None:
        self.train_number = train_number

        self._data = FileCache(
            self.train_number, self._get_train_info, json.dumps, json.loads).data

        self._departure_date = departure_date
        self._day_of_departure = 0  # Day of the journey when reaching the boarding station

        self.departure_datetime = None
        self.arrival_datetime = None

        self.departure_station_name = None
        self.arrival_station_name = None

        self.departure_station_marked = False

    @property
    def is_data_missing(self: Self) -> bool:
        return None in [self.departure_datetime, self.arrival_datetime, self.departure_station_name, self.arrival_station_name]

    def station_codes(self: Self) -> Iterator[tuple[str, Callable[[], None]]]:
        for station in self._data:
            yield (station["code"], self.mark_as_arrival_station(station) if self.departure_station_marked else self.mark_as_departure_station(station))

    def mark_as_departure_station(self: Self, station: Station) -> Callable[[], None]:
        def impl() -> None:
            minute_of_departure = int(station["departure"])
            self._day_of_departure = int(station["day"])

            self.departure_datetime = self._departure_date + \
                timedelta(minutes=minute_of_departure)
            self.departure_station_name = station["name"]
            self.departure_station_marked = True

        return impl

    def mark_as_arrival_station(self: Self, station: Station) -> Callable[[], None]:
        def impl() -> None:
            minute_of_arrival = int(station["arrival"])
            days_of_travel = int(station["day"]) - self._day_of_departure

            self.arrival_datetime = self._departure_date + \
                timedelta(days=days_of_travel, minutes=minute_of_arrival)
            self.arrival_station_name = station["name"]

        return impl

    def _get_train_info(self: Self) -> list[Station]:
        for attempt in range(MAX_RETRIES_FOR_NETWORK_REQUESTS):
            try:
                with open(RAIL_RADAR_CREDENTIALS_FP, "r") as credentials_json:
                    # Returning a list containing dictionaries representing all the stations the train stops at with only the required fields to save data
                    return [
                        {
                            "day": station["day"],
                            "departure": station.get("scheduledDeparture", 0),
                            "arrival": station.get("scheduledArrival", 0),
                            "code": station["stationCode"],
                            "name": station["stationName"],
                        }
                        for station in self._api_call(json.loads(credentials_json.read()))["data"]["route"]
                        if station["isHalt"] == 1
                    ]
            except FileNotFoundError:
                log(LogLevel.Warning,
                    f"'{RAIL_RADAR_CREDENTIALS_FP}' doesn't exist")
                raise
            except HTTPError:
                raise
            except RequestException:
                log(LogLevel.Warning,
                    f"Network error while retrieving RailRadar info. Retrying in {calculate_backoff(attempt)} seconds...")
                time.sleep(calculate_backoff(attempt))
            except IOError:
                log(LogLevel.Warning,
                    f"Couldn't open '{RAIL_RADAR_CREDENTIALS_FP}'")
                raise
            except json.JSONDecodeError:
                log(LogLevel.Warning,
                    f"Unable to parse '{RAIL_RADAR_CREDENTIALS_FP}'")
                raise
        raise Exception(
            "Connection Error. Are you connected to the internet?")

    def _api_call(self: Self, header: dict) -> dict:
        log(LogLevel.Status, f"\t\tPerforming API call to RailRadar")

        response = requests.get(
            f"https://api.railradar.in/api/v1/trains/{self.train_number}",
            headers=header
        )
        response.raise_for_status()
        return response.json()
