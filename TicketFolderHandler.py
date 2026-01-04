from pathlib import Path
import sys
from typing import Self
from watchdog.events import DirCreatedEvent, FileCreatedEvent,  PatternMatchingEventHandler

from GServicesHandler import GServicesHandler
from Logger import LogLevel, log
from Ticket import Ticket
from common import GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR


class TicketFolderHandler(PatternMatchingEventHandler):
    def __init__(self: Self, monitored_fp: Path) -> None:
        super().__init__(patterns=["*.pdf"], ignore_directories=True)
        try:
            self._gsh = GServicesHandler(
                GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP)
        except Exception as error:
            log(LogLevel.Error,
                f"Unhandled exception {error} while initializing Google APIs. Exiting...")
            sys.exit(-1)

        for ticket_fp in monitored_fp.glob("*.pdf"):
            self._process_ticket(ticket_fp)

    def on_created(self: Self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if isinstance(event.src_path, str):
            self._process_ticket(Path(event.src_path))

    def _process_ticket(self: Self, ticket_fp: Path) -> None:
        log(LogLevel.Status, f"Processing {ticket_fp}")
        ticket = Ticket(ticket_fp)

        if not self._gsh.calendar.event_exists(ticket.ttc_id):
            log(LogLevel.Status, f"\tUploading {ticket_fp} to Google Drive")
            upload_response = self._gsh.drive.upload_pdf(ticket_fp)

            log(LogLevel.Status, f"\tCreating event")
            self._gsh.calendar.insert_event(ticket.ttc_id, ticket.summary, ticket.from_where,
                                            ticket.description, upload_response, ticket.departure, ticket.arrival, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR)
        else:
            print("\tFound the event. Not creating it again")
        log(LogLevel.Status, f"Finished processing {ticket_fp}\n")
