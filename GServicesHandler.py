from pathlib import Path
from typing import Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.auth import external_account_authorized_user

from GCalendar import GCalendar
from common import SCOPES


class GServicesHandler:
    def __init__(self: Self, credentials_fp: Path, token_fp: Path) -> None:
        # credentials_fp must exist for this script to run successfully
        # token_fp will exist if this script has been used once before and the user has logged in using oAuth 2.0 atleast once but is not strictly necessary for the functioning of this script

        try:
            credentials = self._generate_credentials(credentials_fp, token_fp)
        except RefreshError as error:
            print(f"Recoverable error occured: {error}")
            print(f"Deleting {token_fp} and trying again")
            token_fp.unlink(missing_ok=True)
            credentials = self._generate_credentials(credentials_fp, token_fp)

        # Save the credentials for the next run
        with open(token_fp, "w") as token:
            token.write(credentials.to_json())

        self.calendar = GCalendar(credentials)

    @staticmethod
    def _generate_credentials(credentials_fp: Path, token_fp: Path) -> Credentials | external_account_authorized_user.Credentials:
        credentials = None

        if token_fp.is_file():
            credentials = Credentials.from_authorized_user_file(
                str(token_fp), SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_fp), SCOPES
                )
                credentials = flow.run_local_server(port=0)
        return credentials
