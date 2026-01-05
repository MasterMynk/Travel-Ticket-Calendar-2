import sys

from Logger import LogLevel, log
from TicketFolderHandler import TicketFolderHandler
from common import TICKET_FOLDER

from watchdog.observers import Observer


def main() -> None:
    # config = ConfigurationHandler()
    # load(config)

    observer = Observer()

    observer.schedule(
        TicketFolderHandler(TICKET_FOLDER),
        str(TICKET_FOLDER),
        recursive=True
    )
    try:
        observer.start()
    except FileNotFoundError as error:
        log(LogLevel.Error,
            f"'{TICKET_FOLDER}' doesn't exist hence cannot monitor it {error}. Exiting...")
        sys.exit(-1)

    try:
        observer.join()
    except KeyboardInterrupt:
        log(LogLevel.Status, "Stopping")


if __name__ == "__main__":
    main()
