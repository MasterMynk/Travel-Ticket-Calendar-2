from dataclasses import dataclass
from pathlib import Path
from typing import Self

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.http import MediaFileUpload

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
    def __init__(self: Self, token_fp: Path, credentials: Credentials | external_account_authorized_user.Credentials) -> None:
        log(LogLevel.Status, "Initializing Google Drive API")
        super().__init__(token_fp, lambda: build("drive", "v3", credentials=credentials))
        log(LogLevel.Status, "Done initializing Google Drive API")

    def upload_pdf(self: Self, path: Path) -> FileUploadResponse:
        return FileUploadResponse(
            **self._service.files().create(
                body={
                    "name": path.name
                },
                media_body=MediaFileUpload(
                    path,
                    mimetype="application/pdf",
                    resumable=True
                ),
                fields="id,name,webViewLink,mimeType"
            ).execute()
        )
