from typing import Self
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.errors import UnknownApiNameOrVersion

from GService import GService
from common import ReminderNotificationType, DEFAULT_CALENDAR_ID, CalendarEventColor


class GCalendar(GService):
    def __init__(self: Self, credentials: Credentials | external_account_authorized_user.Credentials) -> None:
        super()
        try:
            self._service = build("calendar", "v3", credentials=credentials)
        except UnknownApiNameOrVersion as error:
            print(f"Invalid API or version: {error}")

    def insert_event(self: Self, ttc_id: str, summary: str, location: str, description: str, start: datetime, end: datetime, reminders: list[timedelta], reminder_type: ReminderNotificationType, color: CalendarEventColor) -> None:
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
            }
        }

        self._perform_gapi_call(
            lambda: self._service.events()
            .insert(
                calendarId=DEFAULT_CALENDAR_ID,
                body=event_data
            )
            .execute()
        )

    def search_event(self: Self, ttc_id: str) -> list[object]:
        return self._perform_gapi_call(
            lambda: self._service.events()
            .list(
                calendarId=DEFAULT_CALENDAR_ID,
                privateExtendedProperty=f"ttc_id={ttc_id}",
                singleEvents=True
            )
            .execute()
        ).get("items", [])
