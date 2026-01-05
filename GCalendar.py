from pathlib import Path
from typing import Callable, Self
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user

from GDrive import FileUploadResponse
from GService import GService
from Logger import LogLevel, log
from common import ReminderNotificationType, DEFAULT_CALENDAR_ID, CalendarEventColor


class GCalendar(GService):
    def __init__(self: Self, token_fp: Path, credentials: Credentials | external_account_authorized_user.Credentials, refresh_credentials: Callable) -> None:
        super().__init__(token_fp, "calendar", "v3", credentials, refresh_credentials)
        log(LogLevel.Status, "Done initializing Google Calendar API")

    def insert_event(self: Self, ttc_id: str, summary: str, location: str, description: str, ticket_upload: FileUploadResponse | None, start: datetime, end: datetime, reminders: list[timedelta], reminder_type: ReminderNotificationType, color: CalendarEventColor) -> None:
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
                        "method": reminder_type.name,
                        "minutes": reminder.total_seconds() // 60
                    } for reminder in reminders
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

        self._perform_gapi_call(
            lambda: self._service.events()
            .insert(
                calendarId=DEFAULT_CALENDAR_ID,
                body=event_data,
                supportsAttachments=ticket_upload is not None
            )
            .execute()
        )

    def event_exists(self: Self, ttc_id: str) -> bool:
        return len(self._perform_gapi_call(
            lambda: self._service.events()
            .list(
                calendarId=DEFAULT_CALENDAR_ID,
                privateExtendedProperty=f"ttc_id={ttc_id}",
                singleEvents=True
            )
            .execute()
        )["items"]) > 0
