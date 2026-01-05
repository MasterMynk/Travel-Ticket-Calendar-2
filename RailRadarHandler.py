from datetime import datetime, timedelta
import json
import time
from typing import Any, Dict, Self

import requests
from requests import HTTPError, RequestException

from FileCache import FileCache
from Logger import LogLevel, log
from common import MAX_RETRIES_FOR_NETWORK_REQUESTS, RAIL_RADAR_CREDENTIALS_FP, calculate_backoff


class RailRadarHandler:
    def __init__(self: Self, train_number: str, departure_date: datetime, departure_station_code: str, arrival_station_code: str) -> None:
        self._train_number = train_number
        self._data = FileCache(
            train_number, self._get_train_info, json.dumps, json.loads).data

        minute_of_departure = 0
        day_of_departure = 0  # Day of the journey when reaching the boarding station
        minute_of_arrival = 0
        days_of_travel = 0

        for route in self._data:
            if route["stationCode"] == departure_station_code:
                minute_of_departure = int(route["scheduledDeparture"])
                day_of_departure = int(route["day"])
            elif route["stationCode"] == arrival_station_code:
                minute_of_arrival = int(route["scheduledArrival"])
                days_of_travel = int(route["day"]) - day_of_departure
                break

        self.departure_datetime = departure_date + \
            timedelta(minutes=minute_of_departure)
        self.arrival_datetime = departure_date + \
            timedelta(days=days_of_travel, minutes=minute_of_arrival)

    def _get_train_info(self: Self) -> Any:
        for attempt in range(MAX_RETRIES_FOR_NETWORK_REQUESTS):
            try:
                with open(RAIL_RADAR_CREDENTIALS_FP, "r") as credentials_json:
                    # Returning a list containing dictionaries representing all the stations the train stops at with only the required fields to save data
                    return [
                        {
                            "day": route["day"],
                            "scheduledDeparture": route.get("scheduledDeparture", 0),
                            "scheduledArrival": route.get("scheduledArrival", 0),
                            "stationCode": route["stationCode"]
                        }
                        for route in self._api_call(json.loads(credentials_json.read()))["data"]["route"]
                        if route["isHalt"] == 1
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

    def _api_call(self: Self, header: Dict) -> Dict:
        log(LogLevel.Status, f"\t\tPerforming API call to RailRadar")

        response = requests.get(
            f"https://api.railradar.in/api/v1/trains/{self._train_number}",
            headers=header
        )
        response.raise_for_status()
        return response.json()
