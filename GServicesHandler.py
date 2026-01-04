import json
from pathlib import Path
import sys
from typing import Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.auth import external_account_authorized_user
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

from GCalendar import GCalendar
from GDrive import GDrive
from Logger import LogLevel, log
from common import SCOPES


class GServicesHandler:
    def __init__(self: Self, credentials_fp: Path, token_fp: Path) -> None:
        # credentials_fp must exist for this script to run successfully
        # token_fp will exist if this script has been used once before and the user has logged in using oAuth 2.0 atleast once but is not strictly necessary for the functioning of this script

        try:
            credentials = self._generate_credentials(credentials_fp, token_fp)
        except RefreshError as error:
            log(LogLevel.Warning, error)
            credentials = self._delete_token_and_retry(
                credentials_fp, token_fp)
        except json.JSONDecodeError:
            log(LogLevel.Warning, f"{token_fp} corrupted.")
            credentials = self._delete_token_and_retry(
                credentials_fp, token_fp)

        # Save the credentials for the next run
        log(LogLevel.Status, "Saving token for future use")
        token_fp.parent.mkdir(parents=True, exist_ok=True)
        with open(token_fp, "w") as token:
            token.write(credentials.to_json())
        log(LogLevel.Status, "Saved token for future use")

        self.calendar = GCalendar(token_fp, credentials)
        self.drive = GDrive(token_fp, credentials)

    @staticmethod
    def _generate_credentials(credentials_fp: Path, token_fp: Path) -> Credentials | external_account_authorized_user.Credentials:
        credentials = None

        if token_fp.is_file():
            log(LogLevel.Status, f"Loading from '{token_fp}'")
            credentials = Credentials.from_authorized_user_file(
                str(token_fp), SCOPES)
            log(LogLevel.Status, f"Done loading from '{token_fp}'")

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                log(LogLevel.Status, f"Requesting a refresh of token")
                credentials.refresh(Request())
                log(LogLevel.Status, f"Token refreshed")
            else:
                log(LogLevel.Status, f"Trying to sign user in")

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_fp), SCOPES
                    )
                except FileNotFoundError:
                    log(LogLevel.Error,
                        f"'{credentials_fp}' not found. Exiting...")
                    sys.exit(-1)
                except json.JSONDecodeError:
                    log(LogLevel.Error,
                        f"'{credentials_fp}' corrupted. Exiting...")
                    sys.exit(-1)

                try:
                    credentials = flow.run_local_server(port=0)
                except AccessDeniedError:
                    log(LogLevel.Error,
                        f"User sign in unsuccessful. Did you cancel it? Exiting...")
                    sys.exit(-1)
                except Warning as warning:
                    log(LogLevel.Error,
                        f"Looks like you didn't give all the required permissions {warning}")
                    sys.exit(-1)

                log(LogLevel.Status, f"User signed in")

        return credentials

    def _delete_token_and_retry(self: Self, credentials_fp: Path, token_fp: Path) -> Credentials | external_account_authorized_user.Credentials:
        log(LogLevel.Status, f"Deleting '{token_fp}' and trying again...")
        token_fp.unlink(missing_ok=True)
        return self._generate_credentials(credentials_fp, token_fp)
