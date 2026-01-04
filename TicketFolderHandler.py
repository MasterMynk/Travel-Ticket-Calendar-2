from pathlib import Path
from typing import Callable, Self
from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEventHandler

from GServicesHandler import GServicesHandler
from Ticket import Ticket
from common import GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR


class TicketFolderHandler(FileSystemEventHandler):
    def __init__(self: Self) -> None:
        super().__init__()
        self._gsh = GServicesHandler(GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP)

    def on_created(self: Self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if isinstance(event, DirCreatedEvent):
            print("Directory Created. Not handling ts")
            return

        if isinstance(event.src_path, str):
            path = Path(event.src_path)
            if path.is_file() and path.suffix.lower() == ".pdf":
                self._process_ticket(path)

    def _process_ticket(self: Self, ticket_fp: Path) -> None:
        print(f"Processing {ticket_fp}")
        ticket = Ticket(ticket_fp)

        if not self._gsh.calendar.event_exists(ticket.ttc_id):
            print(f"\tUploading {ticket_fp} to Google Drive")
            upload_response = self._gsh.drive.upload_pdf(ticket_fp)

            print(f"\tCreating event")
            self._gsh.calendar.insert_event(ticket.ttc_id, ticket.summary, ticket.from_where,
                                            ticket.description, upload_response, ticket.departure, ticket.arrival, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR)
        else:
            print("\tFound the event. Not creating it again")
