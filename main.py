from datetime import datetime, timedelta
from pathlib import Path

from GServicesHandler import GServicesHandler


def main() -> None:
    gsh = GServicesHandler(Path(__file__).parent / "credentials.json",
                           Path(__file__).parent / "token.json")
    gsh.insert_event("Hello World Event", "Merces, Goa",
                     "Just saying hi guys", datetime.now(), datetime.now() + timedelta(hours=2))


if __name__ == "__main__":
    main()
