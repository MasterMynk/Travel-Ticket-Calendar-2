import sys

from ConfigurationHandler import handler as config_handler
from Logger import LogLevel, log
from TicketFolderHandler import TicketFolderHandler

from watchdog.observers import Observer


def main() -> None:
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
