from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Self

from watchdog.events import DirCreatedEvent, DirDeletedEvent, FileCreatedEvent, FileDeletedEvent, PatternMatchingEventHandler

from src.handlers.api.AiModelHandler import Model
from src.classes.Configuration import Configuration
from src.handlers.other.ConfigurationHandler import ConfigurationHandler
from src.handlers.google.GCalendar import Event
from src.handlers.google.GDrive import GDrive
from src.handlers.google.GServicesHandler import GServicesHandler
from src.handlers.other.IndexHandler import IndexHandler
from src.misc.Logger import LogLevel, log
from src.classes.Ticket import Ticket
from src.misc.common import notify


class TicketFolderHandler(PatternMatchingEventHandler):
    def __init__(self: Self, config_handler: ConfigurationHandler) -> None:
        super().__init__(patterns=["*.pdf"],
                         ignore_directories=True, ignore_patterns=[f"{config_handler.config.done_folder}/*.pdf"])
        self.config = config_handler.config

        self.last_processed: Path | None = None

        try:
            self._gsh = GServicesHandler(self.config)
        except Exception as error:
            log(LogLevel.Error, self.config,
                f"Unhandled exception {error} while initializing Google APIs. Exiting...")
            sys.exit(-1)

        self._model = Model()

        self._index = IndexHandler(self.config)
        done_journeys: list[str] = []
        for ticket_fp in self.config.ticket_folder.glob("*.pdf"):
            ret_val = self._process_ticket(ticket_fp, self._gsh,
                                           self._model, self.config, False)
            if ret_val:
                if ret_val[1]:
                    done_journeys.append(ticket_fp.name)
                self._index.hold(ticket_fp, ret_val[0])
        self._index.for_missing(lambda ticket_name, ttc_id: self._delete_ticket(
            self._gsh, ticket_name, ttc_id, self.config))
        for done_journey in done_journeys:
            self._index.pop(done_journey)

        self._index.flush()

    def on_created(self: Self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if isinstance(event.src_path, str):
            ticket_fp = Path(event.src_path)

            # If this is a duplicate event
            if self.last_processed and self.last_processed == ticket_fp:
                log(LogLevel.Status, self.config,
                    f"Identified duplicate event. Not processing {ticket_fp}")
                return

            self.last_processed = ticket_fp

            if self._wait_for_transfer_completion(ticket_fp, self.config):
                notify("Detected New Ticket",
                       f"Processing {event.src_path}", self.config)

                ret_val = self._process_ticket(ticket_fp, self._gsh,
                                               self._model, self.config, True)
                if ret_val:
                    self._index[ticket_fp] = ret_val[0]
            else:
                notify("Skipping Ticket",
                       f"{event.src_path} due to timeout", self.config)
                log(LogLevel.Warning, self.config,
                    f"Timeout reached but file transfer not complete. Skipping ticket '{ticket_fp}'...")

    def on_deleted(self: Self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if not isinstance(event.src_path, str):
            return
        ticket_fp = Path(event.src_path)
        if (ticket_fp in self._index):
            self._delete_ticket(self._gsh, ticket_fp.name,
                                self._index[ticket_fp], self.config)
        else:
            log(LogLevel.Status, self.config,
                f"Deleted pdf: {ticket_fp} that wasn't in the index. Must not be a ticket.")

    def _process_ticket(self: Self, ticket_fp: Path, gsh: GServicesHandler, model: Model, config: Configuration, to_notify: bool) -> tuple[str, bool] | None:
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
            if (event := gsh.calendar.event_exists(ticket.ttc_id, config)) is not None:
                log(LogLevel.Status, config,
                    f"\tFound the event at {event["link"]}. Not creating it again")

                if datetime.now() > ticket.arrival:
                    self._mark_as_done(ticket_fp, gsh.drive, event, config)
                    notify("Journey marked as Done!",
                           f"Hope your journey from {ticket.from_where} to {ticket.to_where} was successful :)", config)
                    return ticket.ttc_id, True

                elif to_notify:
                    notify("Event Already Present",
                           f"{ticket_fp} at {event["link"]}", config)
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
                                                 ticket.description, upload_response, ticket.departure, ticket.arrival, ticket.color, config)
                log(LogLevel.Status, config, f"\tEvent created at {link}")

                if to_notify:
                    notify("Finished Processing Ticket",
                           f"{ticket_fp} to {link}", config)
            log(LogLevel.Status, config, f"Finished processing {ticket_fp}")
        except Exception as error:
            log(LogLevel.Error, config,
                "Failure to perform some Google API call. Skipping ticket...")
            return None
        return ticket.ttc_id, False

    @staticmethod
    def _delete_ticket(gsh: GServicesHandler, ticket_name: str, ttc_id: str, config: Configuration) -> None:
        gsh.calendar.delete_event(
            ttc_id, gsh.drive, config)
        log(LogLevel.Status, config, f"Deleted {ticket_name} -- {ttc_id}")
        notify("Detected Ticket Deletion",
               f"Deleted {ticket_name} from Google Drive and event from Google Calendar", config)

    @staticmethod
    def _mark_as_done(ticket_fp: Path, drive: GDrive, event: Event, config: Configuration) -> None:
        try:
            if event["ticket_file_id"] is not None:
                drive.trash(event["ticket_file_id"], config)
            config.done_folder.mkdir(parents=True, exist_ok=True)
            ticket_fp.rename(config.done_folder / ticket_fp.name)
        except Exception as error:
            log(LogLevel.Warning, config,
                f"Error marking {ticket_fp} as done: {error}")

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
