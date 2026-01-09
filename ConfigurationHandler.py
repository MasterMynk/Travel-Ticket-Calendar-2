import copy
import tomllib
from typing import Self, cast

from Logger import LogLevel, log
from common import CONFIGURATION_FOLDER
from Configuration import Configuration, ConfigurationDict, DEFAULT_CONFIG


class _ConfigurationHandler:
    _config_fp = CONFIGURATION_FOLDER / "config.toml"

    def __init__(self: Self) -> None:
        self.config = self._load()

    def _load(self: Self) -> Configuration:
        if not self._config_fp.is_file():
            log(LogLevel.Status, DEFAULT_CONFIG,
                f"{self._config_fp} not present. Using default configuration.")
            return self._get_default_config()

        try:
            with open(self._config_fp, "r") as config_toml:
                return Configuration.from_config_dict(
                    cast(ConfigurationDict, tomllib.loads(config_toml.read())))
        except tomllib.TOMLDecodeError as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"{self._config_fp} corrupted; Failure to parse it: {error}")
        except IOError as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"IO error while opening {self._config_fp}: {error}")
        except Exception as error:
            log(LogLevel.Warning, DEFAULT_CONFIG,
                f"Unexpected error while loading configuration: {error}")

        log(LogLevel.Status, DEFAULT_CONFIG, "Using default configuration.")
        return self._get_default_config()

    @staticmethod
    def _get_default_config() -> Configuration:
        return copy.deepcopy(DEFAULT_CONFIG)


handler = _ConfigurationHandler()
