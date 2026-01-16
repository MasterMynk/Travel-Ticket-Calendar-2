import json
from pathlib import Path
import time
from typing import Self

from google import genai
from google.api_core import exceptions
from google.genai.errors import ClientError

from Configuration import Configuration
from FileCache import FileCache
from Logger import LogLevel, log
from common import calculate_backoff


class Model:
    def __init__(self: Self) -> None:
        self._client = None

    @staticmethod
    def _get_client(config: Configuration) -> genai.Client:
        log(LogLevel.Status, config, "Initializing AI Model")

        try:
            with open(config.ai_model_credentials_path, "r") as credentials_json:
                return genai.Client(**json.loads(credentials_json.read()))
        except FileNotFoundError:
            log(LogLevel.Warning, config,
                f"{config.ai_model_credentials_path} doesn't exist. Required to use AI Model")
            raise
        except json.JSONDecodeError:
            log(LogLevel.Warning, config,
                f"{config.ai_model_credentials_path} is corrupted." "Must be of the format: {api_key: <YOUR_API_KEY_HERE>}")
            raise

    def parse(self: Self, ticket_fp: Path, prompt: str, config: Configuration) -> str:
        if self._client is None:
            self._client = self._get_client(config)

        def impl(config: Configuration) -> str:
            log(LogLevel.Status, config, f"Asking {config.ai_model} for help")

            for attempt in range(config.max_retries_for_network_requests):
                try:
                    if self._client is None:
                        raise Exception(f"self._client in None in {__file__}")

                    response = self._client.models.generate_content(
                        model=config.ai_model,
                        contents=[
                            genai.types.Part.from_bytes(
                                data=ticket_fp.read_bytes(),
                                mime_type="application/pdf"
                            ),
                            prompt
                        ],
                        config=genai.types.GenerateContentConfig(
                            temperature=0.1)
                    )

                    if response.text is None:
                        raise Exception("Response was obtained as None")

                    return response.text
                except exceptions.ResourceExhausted as error:
                    log(LogLevel.Warning, config,
                        f"API quota exhausted: {error}")

                except exceptions.GoogleAPIError as error:
                    log(LogLevel.Warning, config, f"Google API Error: {error}")

                except ClientError as error:
                    if error.code == 429:
                        models = ["gemini-2.5-flash",
                                  "gemini-2.5-flash-lite", "gemini-3-flash"]
                        log(LogLevel.Warning, config,
                            f"Exceeded quota for current model. Trying a new one: {models[attempt % len(models)]}...")
                        config.ai_model = models[attempt % len(models)]
                    else:
                        log(LogLevel.Warning, config,
                            f"Some client error occured: {error}")

                except Exception as error:
                    log(LogLevel.Warning, config,
                        f"Some error occured: {error}")

                log(LogLevel.Status, config,
                    f"Retrying in {calculate_backoff(attempt)} seconds")
                time.sleep(calculate_backoff(attempt))

            raise Exception(
                f"Failure to parse ticket from AI Model after {config.max_retries_for_network_requests} retries")

        return FileCache(ticket_fp.stem, impl, lambda x: x, lambda x: x, config).data
