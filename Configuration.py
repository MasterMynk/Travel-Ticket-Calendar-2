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

    gapi_credentials_path: str
    gapi_token_path: str
    rail_radar_credentials_path: str
    ai_model_credentials_path: str
    log_folder: str

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
    gapi_credentials_path: Path
    gapi_token_path: Path
    rail_radar_credentials_path: Path
    ai_model_credentials_path: Path
    log_folder: Path | None

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

    @classmethod
    def from_config_dict(cls: type[Self], config_dict: ConfigurationDict) -> Self:
        config = cast(Self, copy.copy(DEFAULT_CONFIG))

        if "log_folder" in config_dict:
            config.log_folder = Path(config_dict["log_folder"])

        log(LogLevel.Status, config, f"config.toml found. Loading configuration.")

        for key, value in config_dict.items():
            config_attr = getattr(config, key, None)

            def setter(val, to_print=True) -> None:
                if to_print:
                    log(LogLevel.Status, config,
                        f"Configuring {key} -> {value}")
                return setattr(config, key, val)

            if type(value) is type(config_attr):
                if type(value) is list:
                    assert type(config_attr) is list

                    log(LogLevel.Status, config, f"Configuring reminders...")
                    setter(
                        [_timedeltadict_to_timedelta(val) for val in value if _is_valid_timedeltadict(val, config)], False)
                    log(LogLevel.Status, config,
                        f"\tConfigured {key} -> {[str(val) for val in config_attr]}")
                else:
                    setter(value)

            elif type(value) is str:
                if isinstance(config_attr, Path):
                    setter(Path(value))

                elif isinstance(config_attr, Enum):
                    if hasattr(type(config_attr), value):
                        setter(type(config_attr)[value])
                    else:
                        log(LogLevel.Warning, config,
                            f"Invalid value {value} for {key}. {key} can only take values: {", ".join([val.name for val in type(config_attr)])}")
                        log(LogLevel.Status, config,
                            f"Using default value: {config_attr.name}")

                else:
                    log(LogLevel.Warning, config,
                        f"This key '{key}' must not be storing a data type of string or is invalid. Please check documentation.")

            elif type(value) is dict and _is_valid_timedeltadict(value, config):
                setter(_timedeltadict_to_timedelta(
                    cast(TimedeltaDict, value)), False)
                log(LogLevel.Status, config,
                    f"Configured {key} -> {config_attr}")

            else:
                log(LogLevel.Status, config,
                    f"Ignoring unrecognizable key: {key}")

        return config


def _is_valid_timedeltadict(data: TimedeltaDict | dict, config: Configuration) -> bool:
    possible_units = ["days", "seconds", "microseconds",
                      "milliseconds", "minutes", "hours", "weeks"]
    is_valid = data["unit"] in possible_units

    if not is_valid:
        log(LogLevel.Warning, config,
            f"Failure to process time duration set in configuration file: {data}. 'unit' field must only be one of these: {", ".join(possible_units)}")

    return is_valid


def _timedeltadict_to_timedelta(data: TimedeltaDict) -> timedelta:
    return timedelta(**{data["unit"]: data["magnitude"]})


DEFAULT_CONFIG = Configuration(
    gapi_credentials_path=Path(__file__).parent / "credentials.json",
    gapi_token_path=Path(__file__).parent / "token.json",
    log_folder=None,
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
    rail_radar_credentials_path=Path(
        __file__).parent / "rail_radar_credentials.json",
    ai_model_credentials_path=Path(
        __file__).parent / "gemini_credentials.json",
    ticket_folder=Path.home() / "travels/",
    configuration_folder=Path.home() / ".config/Travel Ticket Calendar/",
    max_retries_for_network_requests=7,
    file_transfer_timeout=timedelta(seconds=10),
    file_transfer_polling_interval=timedelta(milliseconds=250),
    ai_model="gemini-2.5-flash-lite"
)
