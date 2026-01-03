from dataclasses import dataclass
from pathlib import Path
from typing import Self

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.http import MediaFileUpload

from GService import GService


@dataclass
class FileUploadResponse:
    id: str
    name: str
    mimeType: str
    webViewLink: str


class GDrive(GService):
    def __init__(self: Self, credentials: Credentials | external_account_authorized_user.Credentials) -> None:
        super().__init__(lambda: build("drive", "v3", credentials=credentials))

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
