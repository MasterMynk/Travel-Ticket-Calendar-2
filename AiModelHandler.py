import json
from pathlib import Path
import sys
from typing import Self
from google import genai

from Logger import LogLevel, log
from common import AI_MODEL, MODEL_CREDENTIALS_FP


class Model:
    def __init__(self: Self) -> None:
        self._client = None

    @staticmethod
    def _get_client(credentials_fp: Path) -> genai.Client:
        log(LogLevel.Status, "Initializing AI Model")

        try:
            with open(credentials_fp, "r") as credentials_json:
                return genai.Client(**json.loads(credentials_json.read()))
        except FileNotFoundError:
            log(LogLevel.Warning,
                f"{credentials_fp} doesn't exist. Required to use AI Model")
            raise
        except json.JSONDecodeError:
            log(LogLevel.Warning,
                f"{credentials_fp} is corrupted." "Must be of the format: {api_key: <YOUR_API_KEY_HERE>}")
            raise

    def parse(self: Self, ticket_fp: Path, prompt: str) -> str:
        if self._client is None:
            self._client = self._get_client(MODEL_CREDENTIALS_FP)

        log(LogLevel.Status, f"Asking {AI_MODEL} for help")
        response = self._client.models.generate_content(
            model=AI_MODEL,
            contents=[
                genai.types.Part.from_bytes(
                    data=ticket_fp.read_bytes(),
                    mime_type="application/pdf"
                ),
                prompt
            ],
            config=genai.types.GenerateContentConfig(temperature=0.1)
        )
        if response.text is None:
            sys.exit(-1)

        return response.text
