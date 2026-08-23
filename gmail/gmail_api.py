import os
import sys
import base64
import pickle
import re
from html import unescape
from concurrent.futures import ThreadPoolExecutor

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# =========================================
# Project Base Directory
# =========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)


# =========================================
# Spam Classifier
# =========================================

from classifier.classifier import classify_email


# =========================================
# Gmail Configuration
# =========================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]


CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials",
    "credentials.json"
)


TOKEN_FILE = os.path.join(
    BASE_DIR,
    "credentials",
    "token.pickle"
)


# =========================================
# Create Gmail Service
# =========================================

def get_gmail_service(credentials_data=None):

    creds = None

    # Use credentials received from Flask
    if credentials_data:

        creds = Credentials(
            token=credentials_data.get("token"),
            refresh_token=credentials_data.get("refresh_token"),
            token_uri=credentials_data.get("token_uri"),
            client_id=credentials_data.get("client_id"),
            client_secret=credentials_data.get("client_secret"),
            scopes=credentials_data.get("scopes")
        )

    # Fallback to old token if available
    elif os.path.exists(TOKEN_FILE):

        with open(TOKEN_FILE, "rb") as token:

            creds = pickle.load(token)

    # Refresh expired credentials
    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    # Make sure credentials are valid
    if not creds or not creds.valid:

        raise Exception(
            "Gmail authentication required."
        )

    # Create Gmail API service
    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service


# =========================================
# Decode Gmail Data
# =========================================

def decode_data(data):

    try:

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


# =========================================
# Convert HTML to Plain Text
# =========================================

def html_to_text(html):

    if not html:

        return ""

    # Remove script blocks
    html = re.sub(
        r"<script.*?>.*?</script>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove style blocks
    html = re.sub(
        r"<style.*?>.*?</style>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Replace common block tags with new lines
    html = re.sub(
        r"<(br|p|div|tr|li|h[1-6])[^>]*>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    # Replace closing block tags
    html = re.sub(
        r"</(p|div|tr|li|h[1-6])>",
        "\n",
        html,
        flags=re.IGNORECASE
    )

    # Remove remaining HTML tags
    html = re.sub(
        r"<[^>]+>",
        "",
        html
    )

    # Decode HTML entities
    html = unescape(html)

    # Normalize spaces
    html = re.sub(
        r"[ \t]+",
        " ",
        html
    )

    # Normalize multiple blank lines
    html = re.sub(
        r"\n\s*\n+",
        "\n\n",
        html
    )

    return html.strip()


# =========================================
# Extract Email Body
# =========================================

def get_email_body(payload):

    plain_text = ""
    html_text = ""

    # Email contains multiple parts
    if "parts" in payload:

        for part in payload["parts"]:

            mime_type = part.get(
                "mimeType",
                ""
            )

            body_data = part.get(
                "body",
                {}
            ).get(
                "data"
            )

            # Plain text
            if mime_type == "text/plain":

                if body_data:

                    plain_text += decode_data(
                        body_data
                    )

            # HTML
            elif mime_type == "text/html":

                if body_data:

                    html_text += decode_data(
                        body_data
                    )

            # Nested multipart email
            elif "parts" in part:

                nested_body = get_email_body(
                    part
                )

                if nested_body:

                    plain_text += nested_body

    # Email contains a single body
    else:

        body_data = payload.get(
            "body",
            {}
        ).get(
            "data"
        )

        if body_data:

            decoded_body = decode_data(
                body_data
            )

            mime_type = payload.get(
                "mimeType",
                ""
            )

            if mime_type == "text/html":

                html_text = decoded_body

            else:

                plain_text = decoded_body

    # Prefer plain text
    if plain_text.strip():

        return plain_text.strip()

    # Otherwise convert HTML to text
    if html_text.strip():

        return html_to_text(
            html_text
        )

    return ""


import threading

_thread_local = threading.local()

def get_thread_service(credentials_data):
    if not hasattr(_thread_local, "service") or _thread_local.service is None:
        _thread_local.service = get_gmail_service(credentials_data)
    return _thread_local.service


# =========================================
# Helper: Fetch Single Email Detail
# =========================================

def fetch_single_email(credentials_data, msg_id):
    try:
        service = get_thread_service(credentials_data)
        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        snippet = msg.get("snippet", "")

        subject = ""
        sender = ""

        for header in headers:
            header_name = header.get("name", "").lower()
            header_value = header.get("value", "")

            if header_name == "subject":
                subject = header_value
            elif header_name == "from":
                sender = header_value

        body = get_email_body(payload)
        if not body.strip():
            body = unescape(snippet)

        classification = classify_email(
            subject + " " + body
        )

        return {
            "id": msg_id,
            "sender": sender,
            "subject": subject,
            "body": body,
            "classification": classification
        }
    except Exception as err:
        print(f"Error fetching message {msg_id}: {err}")
        return None


# =========================================
# Get Gmail Emails
# =========================================

def get_emails(credentials_data=None, max_results=50):

    service = get_gmail_service(
        credentials_data
    )

    messages = []
    page_token = None

    # Fetch email message IDs
    while True:
        request_params = {
            "userId": "me",
            "maxResults": min(500, max_results) if max_results else 500
        }

        if page_token:
            request_params["pageToken"] = page_token

        results = service.users().messages().list(
            **request_params
        ).execute()

        page_messages = results.get("messages", [])
        if page_messages:
            messages.extend(page_messages)

        page_token = results.get("nextPageToken")

        if max_results and len(messages) >= max_results:
            messages = messages[:max_results]
            break

        if not page_token:
            break

    email_ids = [m["id"] for m in messages]

    # Parallelize HTTP calls using thread-safe service instances per worker thread
    with ThreadPoolExecutor(max_workers=20) as executor:
        fetched_results = list(
            executor.map(
                lambda mid: fetch_single_email(credentials_data, mid),
                email_ids
            )
        )

    emails = [e for e in fetched_results if e is not None]
    return emails


# =========================================
# Move Email(s) to Gmail Trash
# =========================================

def move_to_trash(credentials_data, email_ids):
    if not email_ids:
        return True

    if isinstance(email_ids, str):
        email_ids = [email_ids]

    service = get_gmail_service(credentials_data)

    def trash_single(msg_id):
        try:
            service.users().messages().trash(
                userId="me",
                id=msg_id
            ).execute()
            return True
        except Exception as err:
            print(f"Error moving message {msg_id} to Gmail Trash: {err}")
            return False

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            executor.map(trash_single, email_ids)
        )

    return any(results)



# =========================================
# Direct Test
# =========================================

if __name__ == "__main__":

    print(
        "This Gmail API module is designed "
        "to work through Flask Google Login."
    )

    print()

    print(
        "Start the project using:"
    )

    print(
        "python app.py"
    )
