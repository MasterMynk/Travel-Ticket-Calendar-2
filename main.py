from pathlib import Path

from GServicesHandler import GServicesHandler
from Ticket import Ticket

from pypdf import PdfReader

from impl import load


def main() -> None:
    # Start with connecting to ensuring a connection to Google API
    # gsh = GServicesHandler(Path(__file__).parent / "credentials.json",
    #                        Path(__file__).parent / "token.json")

    # config = ConfigurationHandler()
    # load(config)
    Ticket(Path.home() / "travels/JUC NZM 191225.pdf")


if __name__ == "__main__":
    main()
