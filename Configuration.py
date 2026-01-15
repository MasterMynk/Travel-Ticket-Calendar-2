import copy
from typing import Self, TypedDict, cast
from dataclasses import dataclass
from pathlib import Path
from datetime import timedelta
from enum import Enum

from common import ReminderNotificationType, CalendarEventColor, stringify_enum
from Logger import log, LogLevel


class TimedeltaDict(TypedDict):
    magnitude: float
    unit: str


class TravellerDict(TypedDict):
    name: list[str] | str
    color: str


class ConfigurationDict(TypedDict, total=False):
    # This is what we will get on parsing config.toml

    gapi_credentials_path: str
    gapi_token_path: str
    rail_radar_credentials_path: str
    ai_model_credentials_path: str
    log_folder: str

    cache_folder: str
    ticket_folder: str
    done_folder: str
    configuration_folder: str

    calendar_id: str
    reminder_notification_type: str
    reminders: list[TimedeltaDict]
    event_color: str
    traveller: list[TravellerDict]

    cache_data_refresh_time: TimedeltaDict
    max_retries_for_network_requests: int

    file_transfer_timeout: TimedeltaDict
    file_transfer_polling_interval: TimedeltaDict

    ai_model: str


@dataclass
class Traveller:
    name: list[str]
    color: CalendarEventColor

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
    done_folder: Path
    configuration_folder: Path

    calendar_id: str
    reminder_notification_type: ReminderNotificationType
    reminders: list[timedelta]
    event_color: CalendarEventColor
    traveller: list[Traveller]

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
                setattr(config, key, val)
                pass

            if type(value) is type(config_attr):
                if type(value) is list:
                    assert type(config_attr) is list

                    match key:
                        case "reminders":
                            log(LogLevel.Status, config,
                                f"Configuring reminders...")
                            setter(
                                [_to_timedelta(val) for val in value if _is_valid_timedeltadict(val, config)], False)
                            log(LogLevel.Status, config,
                                f"\tConfigured {key} -> {[str(val) for val in getattr(config, key)]}")

                        case "traveller":
                            log(LogLevel.Status, config,
                                f"Configuring travellers...")
                            setter([_to_traveller(val) for val in value if _is_valid_travellerdict(
                                val, config)], False)
                            log(LogLevel.Status, config,
                                f"\tConfigured {key} -> {getattr(config, key)}")

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
                            f"Invalid value {value} for {key}. {key} can only take values: {stringify_enum(type(config_attr))}")
                        log(LogLevel.Status, config,
                            f"Using default value: {config_attr.name}")

                else:
                    log(LogLevel.Warning, config,
                        f"This key '{key}' must not be storing a data type of string or is invalid. Please check documentation.")

            elif type(value) is dict and _is_valid_timedeltadict(value, config):
                setter(_to_timedelta(
                    cast(TimedeltaDict, value)), False)
                log(LogLevel.Status, config,
                    f"Configured {key} -> {config_attr}")

            else:
                log(LogLevel.Status, config,
                    f"Ignoring unrecognizable key: {key}")

        return config

    def traveller_to_color(self: Self, name: str) -> CalendarEventColor:
        for traveller in self.traveller:
            if name.lower() in traveller.name:
                return traveller.color
        return self.event_color



def _is_valid_timedeltadict(data: TimedeltaDict | dict, config: Configuration) -> bool:
    def error(msg: str) -> bool:
        log(LogLevel.Warning, config,
            f"Failure to process duration from config: {data}. {msg}")
        return False

    if "magnitude" not in data:
        return error("'magnitude' field must be present")

    if type(data["magnitude"]) is not float and type(data["magnitude"]) is not int:
        return error("'magnitude' must be of type float/int")

    if data["magnitude"] <= 0:
        return error("'magnitude' must be positive")

    if "unit" not in data:
        return error("'unit' field must be present")

    if type(data["unit"]) is not str:
        return error("'unit' field must be of type string")

    possible_units = ["days", "seconds", "microseconds",
                      "milliseconds", "minutes", "hours", "weeks"]
    if data["unit"] not in possible_units:
        return error(f"'unit' field must only be one of these: {", ".join(possible_units)}")

    return True


def _to_timedelta(data: TimedeltaDict) -> timedelta:
    return timedelta(**{data["unit"]: data["magnitude"]})


def _is_valid_travellerdict(data: TravellerDict, config: Configuration) -> bool:
    if "name" not in data:
        log(LogLevel.Warning, config,
            f"Failure to process traveller: {data}. Each traveller must have a 'name'. See documentation.")
        return False

    if not (type(data["name"]) is str or (type(data["name"]) is list and len(data["name"]) > 0 and all(type(name) is str for name in data["name"]))):
        log(LogLevel.Warning, config,
            f"Failure to process traveller: {data}. Malformed 'name' attribute. 'name' must be either a string or a list of strings with atleast 1 element!")
        return False

    if "color" not in data:
        log(LogLevel.Warning, config,
            f"Failure to process traveller: {data}. Each traveller must have a 'color'. See documentation.")
        return False

    if type(data["color"]) is not str:
        log(LogLevel.Warning, config,
            f"Failure to process traveller: {data}. 'color' attribute must be of type str.")
        return False

    if not hasattr(CalendarEventColor, data["color"]):
        log(LogLevel.Warning, config,
            f"Failure to process traveller: {data}. 'color' attribute must be only one of: {stringify_enum(CalendarEventColor)}")
        return False

    return True


def _to_traveller(data: TravellerDict) -> Traveller:
    return Traveller([data["name"].lower()] if isinstance(data["name"], str) else [name.lower() for name in data["name"]], CalendarEventColor[data["color"]])


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
    traveller=[],
    cache_folder=Path.home() / ".cache/Travel Ticket Calendar/",
    cache_data_refresh_time=timedelta(weeks=1),
    rail_radar_credentials_path=Path(
        __file__).parent / "rail_radar_credentials.json",
    ai_model_credentials_path=Path(
        __file__).parent / "gemini_credentials.json",
    ticket_folder=Path.home() / "travels/",
    done_folder=Path.home() / "travels/done/",
    configuration_folder=Path.home() / ".config/Travel Ticket Calendar/",
    max_retries_for_network_requests=7,
    file_transfer_timeout=timedelta(seconds=10),
    file_transfer_polling_interval=timedelta(milliseconds=250),
    ai_model="gemini-2.5-flash-lite"
)
