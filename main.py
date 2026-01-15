from datetime import datetime
import sys

from Configuration import Configuration
from ConfigurationHandler import handler as config_handler
from Logger import LogLevel, log
from TicketFolderHandler import TicketFolderHandler

from watchdog.observers import Observer


def cache_cleanup(config: Configuration) -> None:
    try:
        for file in config.cache_folder.iterdir():
            if file.is_file() and datetime.now() - datetime.fromtimestamp(file.stat().st_mtime) > config.cache_data_refresh_time:
                file.unlink(missing_ok=True)
    except Exception as error:
        log(LogLevel.Warning, config,
            f"Failure to cleanup outdated cache file: {error}")

def main() -> None:
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
