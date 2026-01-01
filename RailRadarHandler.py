from datetime import datetime, timedelta
import json
from typing import Any, Self

import requests

from FileCache import FileCache
from common import RAIL_RADAR_CREDENTIALS_FP


class RailRadarHandler:
    def _get_train_info(self: Self) -> Any:
        # TODO: Add error handling
        with open(RAIL_RADAR_CREDENTIALS_FP, "r") as credentials_json:
            # Returning a list containing dictionaries representing all the stations the train stops at with only the required fields to save data
            return [{
                "day": route["day"],
                "scheduledDeparture": route.get("scheduledDeparture", 0),
                "scheduledArrival": route.get("scheduledArrival", 0),
                "stationCode": route["stationCode"]
            } for route in requests
                .get(
                f"https://api.railradar.in/api/v1/trains/{self._train_number}", headers=json.loads(credentials_json.read()))
                .json()["data"]["route"]
                if route["isHalt"] == 1
            ]

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
