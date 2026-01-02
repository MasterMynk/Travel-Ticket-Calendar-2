from pathlib import Path

from GServicesHandler import GServicesHandler
from Ticket import Ticket


from common import DEFAULT_EVENT_COLOR, DEFAULT_REMINDERS, GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP, REMINDER_NOTIFICATION_TYPE


def main() -> None:
    # Start with connecting to ensuring a connection to Google API
    gsh = GServicesHandler(GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP)

    # config = ConfigurationHandler()
    # load(config)
    ticket = Ticket(Path.home() / "travels/JUC NZM 191225.pdf")
    # ticket = Ticket(Path.home() / "travels/MAO NZM 170126.pdf")
    # ticket = Ticket(Path.home() / "travels/NZM JUC 180125.pdf")
    # ticket = Ticket(Path.home() / "travels/NZM MAO 202525.pdf")
    gsh.insert_event(ticket.summary, ticket.from_where,
                     ticket.description, ticket.departure, ticket.arrival, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR)

if __name__ == "__main__":
    main()
