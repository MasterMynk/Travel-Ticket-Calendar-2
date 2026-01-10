from pathlib import Path
import sys
import time
from typing import Self

from watchdog.events import DirCreatedEvent, FileCreatedEvent, PatternMatchingEventHandler

from AiModelHandler import Model
from Configuration import Configuration
from ConfigurationHandler import _ConfigurationHandler
from GServicesHandler import GServicesHandler
from Logger import LogLevel, log
from Ticket import Ticket
from common import notify


class TicketFolderHandler(PatternMatchingEventHandler):
    def __init__(self: Self, config_handler: _ConfigurationHandler) -> None:
        super().__init__(patterns=["*.pdf"], ignore_directories=True)
        self.config = config_handler.config

        try:
            self._gsh = GServicesHandler(self.config)
        except Exception as error:
            log(LogLevel.Error, self.config,
                f"Unhandled exception {error} while initializing Google APIs. Exiting...")
            sys.exit(-1)

        self._model = Model()

        for ticket_fp in self.config.ticket_folder.glob("*.pdf"):
            self._process_ticket(ticket_fp, self._gsh,
                                 self._model, self.config, False)

    def on_created(self: Self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if isinstance(event.src_path, str):
            ticket_fp = Path(event.src_path)
            if self._wait_for_transfer_completion(ticket_fp, self.config):
                notify("Detected New Ticket",
                       f"Processing {event.src_path}", self.config)

                self._process_ticket(ticket_fp, self._gsh,
                                     self._model, self.config, True)

            else:
                notify("Skipping Ticket",
                       f"{event.src_path} due to timeout", self.config)
                log(LogLevel.Warning, self.config,
                    f"Timeout reached but file transfer not complete. Skipping ticket '{ticket_fp}'...")

    @staticmethod
    def _process_ticket(ticket_fp: Path, gsh: GServicesHandler, model: Model, config: Configuration, to_notify: bool) -> None:
        log(LogLevel.Status, config, f"Processing {ticket_fp}")

        try:
            ticket = Ticket(ticket_fp, model, config)
        except Exception as error:
            log(LogLevel.Error, config,
                f"Failure to parse ticket: {error}")
            log(LogLevel.Error, config,
                "Unimplemented feature of user intervention to supply correct info. Skipping ticket...")
            notify("Skipping Ticket",
                   f"Failure to parse {ticket_fp}", config)
            return

        try:
            if link := gsh.calendar.event_exists(ticket.ttc_id, config):
                log(LogLevel.Status, config,
                    f"\tFound the event at {link}. Not creating it again")
                if to_notify:
                    notify("Event Already Present",
                           f"{ticket_fp} at {link}", config)
            else:
                log(LogLevel.Status, config,
                    f"\tUploading {ticket_fp} to Google Drive")
                upload_response = gsh.drive.upload_pdf(ticket_fp, config)

                if upload_response:
                    log(LogLevel.Status, config,
                        f"\tUploaded {ticket_fp} to {upload_response.webViewLink}")
                else:
                    log(LogLevel.Warning, config,
                        f"Failure to upload {ticket_fp}")

                log(LogLevel.Status, config, "\tCreating event")
                link = gsh.calendar.insert_event(ticket.ttc_id, ticket.summary, ticket.from_where,
                                                 ticket.description, upload_response, ticket.departure, ticket.arrival, config)
                log(LogLevel.Status, config, f"\tEvent created at {link}")

                if to_notify:
                    notify("Finished Processing Ticket",
                           f"{ticket_fp} to {link}", config)
            log(LogLevel.Status, config, f"Finished processing {ticket_fp}")
        except Exception as error:
            log(LogLevel.Error, config,
                "Failure to perform some Google API call. Skipping ticket...")

    # The on_created event fires as soon as the file is created. This may result in the script getting an incompletely transferred file to parse resulting in parsing errors
    # Hence we are polling every file_transfer_polling_interval seconds to check if the file size of the ticket is growing or not
    @staticmethod
    def _wait_for_transfer_completion(ticket_fp: Path, config: Configuration) -> bool:
        start_time = time.time()

        prev_size = -1
        while time.time() - start_time < config.file_transfer_timeout.total_seconds():
            if ticket_fp.is_file():
                new_size = ticket_fp.stat().st_size

                if prev_size == new_size:
                    return True
                prev_size = new_size

            time.sleep(
                config.file_transfer_polling_interval.total_seconds())
        return False
