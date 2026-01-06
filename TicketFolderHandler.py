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
        try:
            ticket = Ticket(ticket_fp)
        except Exception as error:
            log(LogLevel.Error,
                f"Failure to parse ticket: {error}")
            log(LogLevel.Error,
                "Unimplemented feature of user intervention to supply correct info. Skipping ticket...")
            return

        try:
            if link := self._gsh.calendar.event_exists(ticket.ttc_id):
                log(LogLevel.Status,
                    f"\tFound the event at {link}. Not creating it again")
            else:
                log(LogLevel.Status,
                    f"\tUploading {ticket_fp} to Google Drive")
                upload_response = self._gsh.drive.upload_pdf(ticket_fp)

                if upload_response:
                    log(LogLevel.Status,
                        f"\tUploaded {ticket_fp} to {upload_response.webViewLink}")
                else:
                    log(LogLevel.Warning, f"Failure to upload {ticket_fp}")

                log(LogLevel.Status, "\tCreating event")
                link = self._gsh.calendar.insert_event(ticket.ttc_id, ticket.summary, ticket.from_where,
                                                ticket.description, upload_response, ticket.departure, ticket.arrival, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR)
                log(LogLevel.Status, f"\tEvent created at {link}")
            log(LogLevel.Status, f"Finished processing {ticket_fp}")
        except Exception as error:
            log(LogLevel.Error,
                "Failure to perform some Google API call. Skipping ticket...")
