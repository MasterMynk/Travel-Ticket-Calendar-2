from pathlib import Path
from typing import Self
from datetime import datetime
from httplib2 import ServerNotFoundError

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, UnknownApiNameOrVersion

from common import SCOPES


class GServicesHandler:
    def __init__(self: Self, credentials_fp: Path, token_fp: Path) -> None:
        # credentials_fp must exist for this script to run successfully
        # token_fp will exist if this script has been used once before and the user has logged in using oAuth 2.0 atleast once but is not strictly necessary for the functioning of this script

        creds = None

        if token_fp.is_file():
            creds = Credentials.from_authorized_user_file(
                str(token_fp), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_fp), SCOPES
                )
                creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_fp, "w") as token:
            token.write(creds.to_json())

        try:
            self._calendar = build("calendar", "v3", credentials=creds)
        except UnknownApiNameOrVersion as error:
            print(f"Invalid API or version: {error}")

    @staticmethod
    def _handle_http_error(error: HttpError) -> None:
        # TODO: Handle this better perhaps checking the code and acting accordingly
        print(f"An error occurred: {error}")
        print(f"Status code: {error.status_code}")
        print(f"Reason: {error.reason}")
        print(f"URI: {error.uri}")

    @staticmethod
    def _handle_server_not_found_error(error: ServerNotFoundError) -> None:
        print(
            "Unable to reach Google APIs while creating an event -- Are you connected to the Internet?")
        print(f"Error: {error}")

    @staticmethod
    def _handle_event_error(error: Exception) -> None:
        print(f"Failed to create event: {error}")

    @staticmethod
    def _ensure_tz_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.astimezone()
        return dt

    def insert_event(self: Self, summary: str, location: str, description: str, start: datetime, end: datetime) -> None:
        try:
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
            }

            self._calendar.events().insert(
                calendarId='primary', body=event_data).execute()
        except HttpError as error:
            self._handle_http_error(error)
        except ServerNotFoundError as error:
            self._handle_server_not_found_error(error)
        except Exception as error:
            self._handle_event_error(error)

    def search_event(self: Self, ) -> list[object]:
        return []
