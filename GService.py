from pathlib import Path
from typing import Any, TypeVar, Self, Callable
from datetime import datetime
import sys
from httplib2 import ServerNotFoundError

from googleapiclient.errors import HttpError, UnknownApiNameOrVersion
from google.auth.exceptions import RefreshError

from Logger import LogLevel, log


class GService:
    def __init__(self: Self, token_fp: Path, service_builder: Callable[[], Any]) -> None:
        self._token_fp = token_fp
        try:
            self._service = service_builder()
        except UnknownApiNameOrVersion as error:
            log(LogLevel.Error, f"Invalid API or version: {error}. Exiting...")
            sys.exit(-1)

    @staticmethod
    def _ensure_tz_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.astimezone()
        return dt

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

    def _handle_refresh_error(self: Self, error: RefreshError) -> None:
        log(LogLevel.Error,
            f"Permissions revoked from Google's side {error}. Deleting '{self._token_fp}' and exiting...")
        self._token_fp.unlink(missing_ok=True)

    T = TypeVar("T")

    def _perform_gapi_call(self: Self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except HttpError as error:
            self._handle_http_error(error)
        except ServerNotFoundError as error:
            self._handle_server_not_found_error(error)
        except RefreshError as error:
            self._handle_refresh_error(error)
        except Exception as error:
            self._handle_event_error(error)
        sys.exit(-1)
