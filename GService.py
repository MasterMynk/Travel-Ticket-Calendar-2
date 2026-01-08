from pathlib import Path
import time
from typing import Any, TypeVar, Self, Callable
from datetime import datetime
import sys
from httplib2 import ServerNotFoundError

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, UnknownApiNameOrVersion
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user

from Configuration import Configuration
from Logger import LogLevel, log
from common import calculate_backoff


class GService:
    def __init__(self: Self, api_name: str, api_version: str, credentials: Credentials | external_account_authorized_user.Credentials, refresh_credentials: Callable[[Configuration], None]) -> None:
        self._api_name = api_name
        self._api_version = api_version
        self._service = self._build_service(credentials)
        self._refresh_credentials = refresh_credentials

    def _build_service(self: Self, credentials: Credentials | external_account_authorized_user.Credentials) -> Any:
        try:
            return build(self._api_name, self._api_version, credentials=credentials)
        except UnknownApiNameOrVersion as error:
            log(LogLevel.Error, f"Invalid API or version: {error}. Exiting...")
            sys.exit(-1)

    def rebuild(self: Self, credentials: Credentials | external_account_authorized_user.Credentials) -> None:
        self._service = self._build_service(credentials)

    @staticmethod
    def _ensure_tz_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.astimezone()
        return dt

    @staticmethod
    def _handle_http_error(error: HttpError) -> None:
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

    def _handle_refresh_error(self: Self, error: RefreshError, config: Configuration) -> None:
        log(LogLevel.Error,
            f"Permissions revoked from Google's side {error}. Trying to sign you in again.")
        self._refresh_credentials(config)

    T = TypeVar("T")

    def _perform_gapi_call(self: Self, fn: Callable[[], T], config: Configuration) -> T:
        for attempt in range(config.max_retries_for_network_requests):
            try:
                return fn()
            except HttpError as error:
                self._handle_http_error(error)
            except ServerNotFoundError as error:
                self._handle_server_not_found_error(error)
            except RefreshError as error:
                self._handle_refresh_error(error, config)
            except Exception as error:
                self._handle_event_error(error)
            log(LogLevel.Status,
                f"Retrying Google API call in {calculate_backoff(attempt)} seconds")
            time.sleep(calculate_backoff(attempt))

        raise Exception
