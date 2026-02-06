from datetime import datetime
from pathlib import Path
import sys

from Configuration import DEFAULT_CONFIG, Configuration
from ConfigurationHandler import ConfigurationHandler
from Logger import LogLevel, log
from Option import Option
from termOptionsParser import termOptionsParser
from TicketFolderHandler import TicketFolderHandler

from watchdog.observers import Observer

from common import OPTIONS, shorthand_for


def cache_cleanup(config: Configuration) -> None:
    try:
        for file in config.cache_folder.iterdir():
            if file.is_file() and datetime.now() - datetime.fromtimestamp(file.stat().st_mtime) > config.cache_data_refresh_time:
                file.unlink(missing_ok=True)
    except Exception as error:
        log(LogLevel.Warning, config,
            f"Failure to cleanup outdated cache file: {error}")


def main() -> None:
    try:
        term_config_dict, config_path = termOptionsParser(
            {shorthand_for(option.long_name): option
             for option in OPTIONS}, sys.argv
        )
    except Exception as e:
        log(LogLevel.Error, DEFAULT_CONFIG, e)
        sys.exit(-1)

    config_handler = ConfigurationHandler(term_config_dict,
                                          Path(config_path)) if config_path else ConfigurationHandler(term_config_dict)

    cache_cleanup(config_handler.config)

    observer = Observer()

    observer.schedule(
        TicketFolderHandler(config_handler),
        str(config_handler.config.ticket_folder),
        recursive=True
    )

    try:
        observer.start()
    except FileNotFoundError as error:
        log(LogLevel.Error, config_handler.config,
            f"'{config_handler.config.ticket_folder}' doesn't exist hence cannot monitor it {error}. Exiting...")
        sys.exit(-1)

    try:
        observer.join()
    except KeyboardInterrupt:
        log(LogLevel.Status, config_handler.config, "Stopping")


if __name__ == "__main__":
    main()
