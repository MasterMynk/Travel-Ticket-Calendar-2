from typing import Callable, Self
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user

from Configuration import Configuration
from GDrive import FileUploadResponse
from GService import GService
from Logger import LogLevel, log


class GCalendar(GService):
    def __init__(self: Self, config: Configuration, credentials: Credentials | external_account_authorized_user.Credentials, refresh_credentials: Callable[[Configuration], None]) -> None:
        super().__init__("calendar", "v3", credentials, refresh_credentials, config)
        log(LogLevel.Status, config, "Done initializing Google Calendar API")

    def insert_event(self: Self, ttc_id: str, summary: str, location: str, description: str, ticket_upload: FileUploadResponse | None, start: datetime, end: datetime, config: Configuration) -> str:
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
            "colorId": str(config.event_color.value),
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

    def event_exists(self: Self, ttc_id: str, config: Configuration) -> str | None:
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
            return found_events[0]["htmlLink"]
