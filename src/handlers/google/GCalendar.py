from typing import Callable, Self, TypedDict
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user

from src.classes.Configuration import Configuration
from src.handlers.google.GDrive import FileUploadResponse, GDrive
from src.handlers.google.GService import GService
from src.misc.Logger import LogLevel, log
from src.misc.common import CalendarEventColor


class Event(TypedDict):
    link: str
    ticket_file_id: str | None
    id: str


class GCalendar(GService):
    def __init__(self: Self, config: Configuration, credentials: Credentials | external_account_authorized_user.Credentials, refresh_credentials: Callable[[Configuration], None]) -> None:
        super().__init__("calendar", "v3", credentials, refresh_credentials, config)
        log(LogLevel.Status, config, "Done initializing Google Calendar API")

    def insert_event(self: Self, ttc_id: str, summary: str, location: str, description: str, ticket_upload: FileUploadResponse | None, start: datetime, end: datetime, color: CalendarEventColor, config: Configuration) -> str:
        event_data = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": self._ensure_tz_aware(start).isoformat(),
            },
            "end": {
                "dateTime": self._ensure_tz_aware(end).isoformat(),
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {
                        "method": config.reminder_notification_type.name,
                        "minutes": reminder.total_seconds() // 60
                    } for reminder in config.reminders
                ]
            },
            "colorId": str(color.value),
            "extendedProperties": {
                "private": {
                    "ttc_id": ttc_id
                }
            },
        }

        if ticket_upload:
            event_data["attachments"] = [
                ticket_upload.gcalendar_format
            ]

        return self._perform_gapi_call(
            lambda: self._service.events()
            .insert(
                calendarId=config.calendar_id,
                body=event_data,
                supportsAttachments=ticket_upload is not None
            )
            .execute(), config
        )["htmlLink"]

    def event_exists(self: Self, ttc_id: str, config: Configuration) -> Event | None:
        found_events = self._perform_gapi_call(
            lambda: self._service.events()
            .list(
                calendarId=config.calendar_id,
                privateExtendedProperty=f"ttc_id={ttc_id}",
                singleEvents=True
            )
            .execute(), config
        )["items"]

        if len(found_events) > 0:
            return {
                "link": found_events[0]["htmlLink"],
                "ticket_file_id": found_events[0].get("attachments", [{"fileId": None}])[0]["fileId"],
                "id": found_events[0]["id"]
            }

    def delete_event(self: Self, ttc_id: str, drive: GDrive, config: Configuration) -> bool:
        event = self.event_exists(ttc_id, config)
        if event == None:
            return False
        if event["ticket_file_id"] is not None:
            drive.trash(event["ticket_file_id"], config)
        self._perform_gapi_call(lambda: self._service.events().delete(
            calendarId=config.calendar_id, eventId=event["id"]).execute(), config)
        log(LogLevel.Status, config, f"Deleted event with id: {event["id"]}")
        return True
