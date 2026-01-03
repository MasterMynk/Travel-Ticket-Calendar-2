from GServicesHandler import GServicesHandler
from Ticket import Ticket


from common import DEFAULT_EVENT_COLOR, DEFAULT_REMINDERS, GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP, REMINDER_NOTIFICATION_TYPE, TICKET_FOLDER


def main() -> None:
    # Start with connecting to ensuring a connection to Google API
    gsh = GServicesHandler(GOOGLE_CREDENTIALS_FP, GOOGLE_TOKEN_FP)

    # config = ConfigurationHandler()
    # load(config)
    for ticket_fp in TICKET_FOLDER.glob("*.pdf"):
        print(f"Processing {ticket_fp}")
        ticket = Ticket(ticket_fp)

        if not gsh.calendar.event_exists(ticket.ttc_id):
            print(f"\tUploading {ticket_fp} to Google Drive")
            upload_response = gsh.drive.upload_pdf(ticket_fp)

            print(f"\tCreating event")
            gsh.calendar.insert_event(ticket.ttc_id, ticket.summary, ticket.from_where,
                                      ticket.description, upload_response, ticket.departure, ticket.arrival, DEFAULT_REMINDERS, REMINDER_NOTIFICATION_TYPE, DEFAULT_EVENT_COLOR)
        else:
            print("\tFound the event. Not creating it again")

if __name__ == "__main__":
    main()
