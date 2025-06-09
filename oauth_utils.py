import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "client_secret.json"

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)
