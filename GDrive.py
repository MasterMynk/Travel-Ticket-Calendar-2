from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Self

from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.http import MediaFileUpload

from Configuration import Configuration
from GService import GService

from Logger import log, LogLevel

@dataclass
class FileUploadResponse:
    id: str
    name: str
    mimeType: str
    webViewLink: str

    @property
    def gcalendar_format(self: Self) -> object:
        return {
            'fileId': self.id,
            'title': self.name,
            'mimeType': self.mimeType,
            'fileUrl': self.webViewLink
        }


class GDrive(GService):
    def __init__(self: Self, config: Configuration, credentials: Credentials | external_account_authorized_user.Credentials, refresh_credentials: Callable) -> None:
        super().__init__("drive", "v3", credentials, refresh_credentials)
        log(LogLevel.Status, "Done initializing Google Drive API")

    def upload_pdf(self: Self, path: Path, config: Configuration) -> FileUploadResponse | None:
        try:
            return FileUploadResponse(
                **self._perform_gapi_call(
                    lambda: self._service.files().create(
                        body={
                            "name": path.name
                        },
                        media_body=MediaFileUpload(
                            path,
                            mimetype="application/pdf",
                            resumable=True
                        ),
                        fields="id,name,webViewLink,mimeType"
                    ).execute(), config
                )
            )
        except:
            return None
