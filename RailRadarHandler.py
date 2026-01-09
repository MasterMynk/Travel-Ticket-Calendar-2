from collections.abc import Iterator
from datetime import datetime, timedelta
import json
import time
from typing import Any, Callable, Self, TypedDict

import requests
from requests import HTTPError, RequestException

from Configuration import Configuration
from FileCache import FileCache
from Logger import LogLevel, log
from common import calculate_backoff


class Station(TypedDict):
    day: int
    departure: int
    arrival: int
    code: str
    name: str


class RailRadarHandler:
    def __init__(self: Self, train_number: str, departure_date: datetime, config: Configuration) -> None:
        self.train_number = train_number

        self._data = FileCache(
            self.train_number, self._get_train_info, json.dumps, json.loads, config).data

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
            self.departure_station_marked = False

        return impl

    def _get_train_info(self: Self, config: Configuration) -> list[Station]:
        for attempt in range(config.max_retries_for_network_requests):
            try:
                with open(config.rail_radar_credentials_path, "r") as credentials_json:
                    # Returning a list containing dictionaries representing all the stations the train stops at with only the required fields to save data
                    return [
                        {
                            "day": station["day"],
                            "departure": station.get("scheduledDeparture", 0),
                            "arrival": station.get("scheduledArrival", 0),
                            "code": station["stationCode"],
                            "name": station["stationName"],
                        }
                        for station in self._api_call(self.train_number, json.loads(credentials_json.read()), config)["data"]["route"]
                        if station["isHalt"] == 1
                    ]
            except FileNotFoundError:
                log(LogLevel.Warning, config,
                    f"'{config.rail_radar_credentials_path}' doesn't exist")
                raise
            except HTTPError:
                raise
            except RequestException:
                log(LogLevel.Warning, config,
                    f"Network error while retrieving RailRadar info. Retrying in {calculate_backoff(attempt)} seconds...")
                time.sleep(calculate_backoff(attempt))
            except IOError:
                log(LogLevel.Warning, config,
                    f"Couldn't open '{config.rail_radar_credentials_path}'")
                raise
            except json.JSONDecodeError:
                log(LogLevel.Warning, config,
                    f"Unable to parse '{config.rail_radar_credentials_path}'")
                raise
        raise Exception(
            "Connection Error. Are you connected to the internet?")

    @staticmethod
    def _api_call(train_number: str, header: dict, config: Configuration) -> dict:
        log(LogLevel.Status, config, f"\t\tPerforming API call to RailRadar")

        response = requests.get(
            f"https://api.railradar.in/api/v1/trains/{train_number}",
            headers=header
        )
        response.raise_for_status()
        return response.json()
