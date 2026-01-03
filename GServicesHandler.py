from pathlib import Path
from typing import Self

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from GCalendar import GCalendar
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

        self.calendar = GCalendar(creds)
