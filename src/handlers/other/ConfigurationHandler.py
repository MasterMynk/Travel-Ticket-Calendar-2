import copy
from pathlib import Path
import tomllib
from typing import Self, cast

from src.misc.Logger import LogLevel, log
from src.misc.common import CONFIGURATION_FOLDER
from src.classes.Configuration import Configuration, ConfigurationDict, DEFAULT_CONFIG


class ConfigurationHandler:
    def __init__(self: Self, term_config_dict: ConfigurationDict, config_fp: Path | None = CONFIGURATION_FOLDER / "config.toml") -> None:
        if config_fp is None:
            self.config = Configuration.from_config_dict(term_config_dict)
            log(LogLevel.Status, self.config,
                "config-path specified as default. Using default config with the above changes")
            return

        self.config = self._load(config_fp, term_config_dict)

    def _load(self: Self, config_fp: Path, term_config_dict: ConfigurationDict) -> Configuration:
        if not config_fp.is_file():
            log(LogLevel.Status, DEFAULT_CONFIG,
                f"{config_fp} not present. Using default configuration.")
            return Configuration.from_config_dict(term_config_dict)

        try:
            with open(config_fp, "r") as config_toml:
                config_dict = cast(ConfigurationDict,
                                   tomllib.loads(config_toml.read()))
                config_dict.update(term_config_dict)

                return Configuration.from_config_dict(config_dict)
        except tomllib.TOMLDecodeError as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"{config_fp} corrupted; Failure to parse it: {error}")
        except IOError as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"IO error while opening {config_fp}: {error}")
        except Exception as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"Unexpected error while loading configuration: {error}")

        log(LogLevel.Status, DEFAULT_CONFIG, "Using default configuration.")
        return self._get_default_config()

    @staticmethod
    def _get_default_config() -> Configuration:
        return copy.deepcopy(DEFAULT_CONFIG)
