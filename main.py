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
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        print("\nStopping")


if __name__ == "__main__":
    main()
