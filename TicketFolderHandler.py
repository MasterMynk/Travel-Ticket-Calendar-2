from pathlib import Path
import sys
import time
from typing import Self
from watchdog.events import DirCreatedEvent, FileCreatedEvent,  PatternMatchingEventHandler

from AiModelHandler import Model
from GServicesHandler import GServicesHandler
from Logger import LogLevel, log
from Ticket import Ticket
from common import FILE_TRANSFER_POLLING_INTERVAL, FILE_TRANSFER_TIMEOUT, GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR


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

        self._model = Model()

        for ticket_fp in monitored_fp.glob("*.pdf"):
            self._process_ticket(ticket_fp)

    def on_created(self: Self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if isinstance(event.src_path, str):
            ticket_fp = Path(event.src_path)
            if self._wait_for_transfer_completion(ticket_fp):
                self._process_ticket(ticket_fp)
            else:
                log(LogLevel.Warning,
                    f"Timeout reached but file transfer not complete. Skipping ticket '{ticket_fp}'...")

    def _process_ticket(self: Self, ticket_fp: Path) -> None:
        log(LogLevel.Status, f"Processing {ticket_fp}")

        try:
            ticket = Ticket(ticket_fp, self._model)
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

    # The on_created event fires as soon as the file is created. This may result in the script getting an incompletely transferred file to parse resulting in parsing errors
    # Hence we are polling every FILE_TRANSFER_POLLING_INTERVAL seconds to check if the file size of the ticket is growing or not
    @staticmethod
    def _wait_for_transfer_completion(ticket_fp: Path) -> bool:
        start_time = time.time()

        prev_size = -1
        while time.time() - start_time < FILE_TRANSFER_TIMEOUT:
            if ticket_fp.is_file():
                new_size = ticket_fp.stat().st_size

                if prev_size == new_size:
                    return True
                prev_size = new_size

            time.sleep(FILE_TRANSFER_POLLING_INTERVAL)
        return False
