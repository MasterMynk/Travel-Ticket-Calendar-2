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

from Configuration import Configuration
from GCalendar import GCalendar
from GDrive import GDrive
from GService import GService
from Logger import LogLevel, log
from common import SCOPES, calculate_backoff


class GServicesHandler:
    def __init__(self: Self, config: Configuration) -> None:
        # credentials_fp must exist for this script to run successfully
        # token_fp will exist if this script has been used once before and the user has logged in using oAuth 2.0 atleast once but is not strictly necessary for the functioning of this script

        credentials = self._generate_credentials(config)

        # Save the credentials for the next run
        self._save_credentials(credentials.to_json(), config)

        self.calendar = GCalendar(
            config, credentials, self._refresh_credentials)
        self.drive = GDrive(config, credentials, self._refresh_credentials)
        self.services: list[GService] = [self.calendar, self.drive]

    def _generate_credentials(self: Self, config: Configuration) -> Credentials | external_account_authorized_user.Credentials:
        attempt = 0
        while True:
            try:
                credentials = self._load_token_fp(config)

                if not self._credentials_verified(credentials):
                    if self._credentials_expired(credentials):
                        assert credentials is not None
                        self._refresh_token(credentials, config)
                    else:
                        credentials = self._sign_user_in(config)

                assert credentials is not None
                return credentials
            except TransportError as error:
                attempt = min(
                    [config.max_retries_for_network_requests, attempt + 1])
                log(LogLevel.Warning, config,
                    f"Having some trouble getting to Google APIs. Retrying in {calculate_backoff(attempt)} seconds")
                time.sleep(calculate_backoff(attempt))

            except RefreshError as error:
                log(LogLevel.Warning, config, error)
                self._delete_token_fp(config)

            except json.JSONDecodeError:
                log(LogLevel.Warning, config,
                    f"{config.gapi_token_path} corrupted.")
                self._delete_token_fp(config)

            except AccessDeniedError:
                log(LogLevel.Error, config,
                    f"User sign in unsuccessful. Did you cancel it? Exiting...")
                sys.exit(-1)

            except Warning as warning:
                log(LogLevel.Error, config,
                    f"Looks like you didn't give all the required permissions {warning}. Exiting...")
                sys.exit(-1)

    def _delete_token_fp(self: Self, config: Configuration) -> None:
        log(LogLevel.Status, config,
            f"Deleting '{config.gapi_token_path}' and trying again...")

        # If the file doesn't exist and there's an attempt to delete it means we've already been here
        # This is a fatal error and the program can't continue
        config.gapi_token_path.unlink()

    def _load_token_fp(self: Self, config: Configuration) -> Credentials | None:
        if config.gapi_token_path.is_file():
            log(LogLevel.Status, config,
                f"Loading from '{config.gapi_token_path}'")
            return Credentials.from_authorized_user_file(
                str(config.gapi_token_path), SCOPES)

    @staticmethod
    def _credentials_verified(credentials: Credentials | None) -> bool:
        return bool(credentials and credentials.valid)

    @staticmethod
    def _credentials_expired(credentials: Credentials | None) -> bool:
        return bool(credentials and credentials.expired and credentials.refresh_token)

    @staticmethod
    def _refresh_token(credentials: Credentials, config: Configuration) -> None:
        log(LogLevel.Status, config, f"Requesting a refresh of token")
        credentials.refresh(Request())
        log(LogLevel.Status, config, f"Token refreshed")

    def _sign_user_in(self: Self, config: Configuration) -> Credentials | external_account_authorized_user.Credentials:
        log(LogLevel.Status, config, f"Trying to sign user in")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.gapi_credentials_path), SCOPES
            )
        except FileNotFoundError:
            log(LogLevel.Error, config,
                f"'{config.gapi_credentials_path}' not found. Exiting...")
            sys.exit(-1)
        except json.JSONDecodeError:
            log(LogLevel.Error, config,
                f"'{config.gapi_credentials_path}' corrupted. Exiting...")
            sys.exit(-1)

        credentials = flow.run_local_server(port=0)
        log(LogLevel.Status, config, f"User signed in")

        return credentials

    def _save_credentials(self: Self, content: str, config: Configuration) -> None:
        config.gapi_token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config.gapi_token_path, "w") as token:
            token.write(content)
        log(LogLevel.Status, config, "Saved token for future use")

    # To be called by a service initialized in the handler if while performing an API call it is found out that the permissions have been revoked
    def _refresh_credentials(self: Self, config: Configuration) -> None:
        credentials = self._sign_user_in(config)
        self._save_credentials(credentials.to_json(), config)
        for service in self.services:
            service.rebuild(credentials, config)
