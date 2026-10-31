"""Uploads a finished video with the YouTube Data API v3."""
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service(client_secret="client_secret.json", token="token.json"):
    creds = None
    if os.path.exists(token):
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        with open(token, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(folder: str, privacy: str = "private", publish_at: str | None = None) -> str:
    with open(os.path.join(folder, "metadata.json")) as f:
        meta = json.load(f)

    status = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": False,
        # AI voice / generated visuals must be disclosed under YouTube policy.
        "containsSyntheticMedia": True,
    }
    if publish_at:  # ISO 8601, e.g. 2026-11-02T15:00:00Z
        status["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"],
            "tags": meta["tags"][:15],
            "categoryId": "27",  # Education
        },
        "status": status,
    }
    media = MediaFileUpload(os.path.join(folder, "video.mp4"), chunksize=-1, resumable=True)
    request = _service().videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]
