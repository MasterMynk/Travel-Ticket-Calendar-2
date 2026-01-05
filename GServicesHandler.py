import json
from pathlib import Path
import sys
import time
from typing import Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError, TransportError
from google.auth import external_account_authorized_user
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

from GCalendar import GCalendar
from GDrive import GDrive
from GService import GService
from Logger import LogLevel, log
from common import MAX_RETRIES_FOR_NETWORK_REQUESTS, SCOPES, calculate_backoff


class GServicesHandler:
    def __init__(self: Self, credentials_fp: Path, token_fp: Path) -> None:
        # credentials_fp must exist for this script to run successfully
        # token_fp will exist if this script has been used once before and the user has logged in using oAuth 2.0 atleast once but is not strictly necessary for the functioning of this script

        self._credentials_fp = credentials_fp
        self._token_fp = token_fp

        credentials = self._generate_credentials()

        # Save the credentials for the next run
        self._save_credentials(credentials.to_json())

        self.calendar = GCalendar(
            token_fp, credentials, self._refresh_credentials)
        self.drive = GDrive(token_fp, credentials, self._refresh_credentials)
        self.services: list[GService] = [self.calendar, self.drive]

    def _generate_credentials(self: Self) -> Credentials | external_account_authorized_user.Credentials:
        attempt = 0
        while True:
            try:
                credentials = self._load_token_fp()

                if not self._credentials_verified(credentials):
                    if self._credentials_expired(credentials):
                        assert credentials is not None
                        self._refresh_token(credentials)
                    else:
                        credentials = self._sign_user_in()

                assert credentials is not None
                return credentials
            except TransportError as error:
                attempt = min([MAX_RETRIES_FOR_NETWORK_REQUESTS, attempt + 1])
                log(LogLevel.Warning,
                    f"Having some trouble getting to Google APIs. Retrying in {calculate_backoff(attempt)} seconds")
                time.sleep(calculate_backoff(attempt))

            except RefreshError as error:
                log(LogLevel.Warning, error)
                self._delete_token_fp()

            except json.JSONDecodeError:
                log(LogLevel.Warning, f"{self._token_fp} corrupted.")
                self._delete_token_fp()

            except AccessDeniedError:
                log(LogLevel.Error,
                    f"User sign in unsuccessful. Did you cancel it? Exiting...")
                sys.exit(-1)

            except Warning as warning:
                log(LogLevel.Error,
                    f"Looks like you didn't give all the required permissions {warning}. Exiting...")
                sys.exit(-1)

    def _delete_token_fp(self: Self) -> None:
        log(LogLevel.Status,
            f"Deleting '{self._token_fp}' and trying again...")

        # If the file doesn't exist and there's an attempt to delete it means we've already been here
        # This is a fatal error and the program can't continue
        self._token_fp.unlink()

    def _load_token_fp(self: Self) -> Credentials | None:
        if self._token_fp.is_file():
            log(LogLevel.Status, f"Loading from '{self._token_fp}'")
            return Credentials.from_authorized_user_file(
                str(self._token_fp), SCOPES)

    @staticmethod
    def _credentials_verified(credentials: Credentials | None) -> bool:
        return bool(credentials and credentials.valid)

    @staticmethod
    def _credentials_expired(credentials: Credentials | None) -> bool:
        return bool(credentials and credentials.expired and credentials.refresh_token)

    @staticmethod
    def _refresh_token(credentials: Credentials) -> None:
        log(LogLevel.Status, f"Requesting a refresh of token")
        credentials.refresh(Request())
        log(LogLevel.Status, f"Token refreshed")

    def _sign_user_in(self: Self) -> Credentials | external_account_authorized_user.Credentials:
        log(LogLevel.Status, f"Trying to sign user in")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._credentials_fp), SCOPES
            )
        except FileNotFoundError:
            log(LogLevel.Error,
                f"'{self._credentials_fp}' not found. Exiting...")
            sys.exit(-1)
        except json.JSONDecodeError:
            log(LogLevel.Error,
                f"'{self._credentials_fp}' corrupted. Exiting...")
            sys.exit(-1)

        credentials = flow.run_local_server(port=0)
        log(LogLevel.Status, f"User signed in")

        return credentials

    def _save_credentials(self: Self, content: str) -> None:
        self._token_fp.parent.mkdir(parents=True, exist_ok=True)
        with open(self._token_fp, "w") as token:
            token.write(content)
        log(LogLevel.Status, "Saved token for future use")

    # To be called by a service initialized in the handler if while performing an API call it is found out that the permissions have been revoked
    def _refresh_credentials(self: Self) -> None:
        credentials = self._sign_user_in()
        self._save_credentials(credentials.to_json())
        for service in self.services:
            service.rebuild(credentials)
