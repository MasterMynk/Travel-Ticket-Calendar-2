import copy
from typing import Self, TypedDict, cast
from dataclasses import dataclass
from pathlib import Path
from datetime import timedelta
from enum import Enum

from common import ReminderNotificationType, CalendarEventColor
from Logger import log, LogLevel


class TimedeltaDict(TypedDict):
    magnitude: float
    unit: str


class ConfigurationDict(TypedDict, total=False):
    # This is what we will get on parsing config.toml

    google_api_credentials_json: str
    google_api_token_json: str
    rail_radar_credentials_json: str
    ai_model_credentials_json: str

    cache_folder: str
    ticket_folder: str
    configuration_folder: str

    calendar_id: str
    reminder_notification_type: str
    reminders: list[TimedeltaDict]
    event_color: str

    cache_data_refresh_time: TimedeltaDict
    max_retries_for_network_requests: int

    file_transfer_timeout: TimedeltaDict
    file_transfer_polling_interval: TimedeltaDict

    ai_model: str


# This is what the consumers of this module will use
@dataclass
class Configuration:
    google_api_credentials_json: Path
    google_api_token_json: Path
    rail_radar_credentials_json: Path
    ai_model_credentials_json: Path

    cache_folder: Path
    ticket_folder: Path
    configuration_folder: Path

    calendar_id: str
    reminder_notification_type: ReminderNotificationType
    reminders: list[timedelta]
    event_color: CalendarEventColor

    cache_data_refresh_time: timedelta
    max_retries_for_network_requests: int

    file_transfer_timeout: timedelta
    file_transfer_polling_interval: timedelta

    ai_model: str

    @staticmethod
    def _is_valid_timedeltadict(data: TimedeltaDict | dict) -> bool:
        possible_units = ["days", "seconds", "microseconds",
                          "milliseconds", "minutes", "hours", "weeks"]
        is_valid = data["unit"] in possible_units

        if not is_valid:
            log(LogLevel.Warning,
                f"Failure to process time duration set in configuration file: {data}. 'unit' field must only be one of these: {", ".join(possible_units)}")

        return is_valid

    @staticmethod
    def _timedeltadict_to_timedelta(data: TimedeltaDict) -> timedelta:
        return timedelta(**{data["unit"]: data["magnitude"]})

    @classmethod
    def from_config_dict(cls: type[Self], config_dict: ConfigurationDict) -> Self:
        config = cast(Self, copy.copy(DEFAULT_CONFIG))

        for key, value in config_dict.items():
            config_attr = getattr(config, key, None)

            def setter(val, to_print=True) -> None:
                if to_print:
                    log(LogLevel.Status, f"Configuring {key} -> {value}")
                return setattr(config, key, val)

            if type(value) is type(config_attr):
                setter(value)

            elif type(value) is str:
                if isinstance(config_attr, Path):
                    setter(Path(value))

                if isinstance(config_attr, Enum):
                    if hasattr(type(config_attr), value):
                        setter(type(config_attr)[value])
                    else:
                        log(LogLevel.Warning,
                            f"Invalid value {value} for {key}. {key} can only take values: {", ".join([val.name for val in type(config_attr)])}")
                        log(LogLevel.Status,
                            f"Using default value: {config_attr.name}")

            elif type(value) is list and type(config_attr) is list:
                log(LogLevel.Status, f"Configuring reminders...")
                setter(
                    [cls._timedeltadict_to_timedelta(val) for val in value if cls._is_valid_timedeltadict(val)], False)
                log(LogLevel.Status,
                    f"Configured {key} -> {[str(val) for val in config_attr]}")

            elif type(value) is dict and cls._is_valid_timedeltadict(value):
                setter(cls._timedeltadict_to_timedelta(
                    cast(TimedeltaDict, value)), False)
                log(LogLevel.Status, f"Configured {key} -> {config_attr}")

            else:
                log(LogLevel.Status, f"Ignoring unrecognizable key: {key}")

        return config


DEFAULT_CONFIG = Configuration(
    google_api_credentials_json=Path(__file__).parent / "credentials.json",
    google_api_token_json=Path(__file__).parent / "token.json",
    calendar_id="primary",
    reminder_notification_type=ReminderNotificationType.popup,
    reminders=[
        timedelta(minutes=30),
        timedelta(hours=2),
        timedelta(weeks=1),
    ],
    event_color=CalendarEventColor.Banana,
    cache_folder=Path.home() / ".cache/Travel Ticket Calendar/",
    cache_data_refresh_time=timedelta(weeks=1),
    rail_radar_credentials_json=Path(
        __file__).parent / "rail_radar_credentials.json",
    ai_model_credentials_json=Path(
        __file__).parent / "gemini_credentials.json",
    ticket_folder=Path.home() / "travels/",
    configuration_folder=Path.home() / ".config/Travel Ticket Calendar/",
    max_retries_for_network_requests=7,
    file_transfer_timeout=timedelta(seconds=10),
    file_transfer_polling_interval=timedelta(milliseconds=250),
    ai_model="gemini-2.5-flash-lite"
)
