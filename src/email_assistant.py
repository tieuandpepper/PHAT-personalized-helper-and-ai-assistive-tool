import base64
from email.message import EmailMessage
import os

from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set scopes for Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def send_email(sender:str, receiver:str, subject:str, content:str)->str:
  creds = None
  # Load pre-authorized user credentials from the environment.
  if os.path.exists('google_kevin_tieu_tamu_gmail_auth.json'):
    # Use OAuth flow to get credentials
    flow = InstalledAppFlow.from_client_secrets_file(
        'google_kevin_tieu_tamu_gmail_auth.json', SCOPES)
    creds = flow.run_local_server(port=0)

  try:
    # create gmail api client
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()
    message.set_content(content)

    message["To"] = receiver
    message["From"] = sender
    message["Subject"] = subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"message": {"raw": encoded_message}}
    # pylint: disable=E1101
    email = (
      service.users()
      .drafts()
      .create(userId="me", body=create_message)
      .execute()
    )

    # print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

  except HttpError as error:
    output = f"An error occurred: {error}"
    return output

  email_id = email["id"]
  sent_message = service.users().drafts().send(userId="me", body={"id": email_id}).execute()
  output = "Message sent successfully. Log: " + str(sent_message)
  return output

# print(send_email("kevin.tieu.tamu@gmail.com","phattieuthien@gmail.com","Automated message", "This is a test email message."))