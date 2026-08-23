import os
import json
import requests
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    request,
    jsonify
)

from google_auth_oauthlib.flow import Flow
from gmail.gmail_api import get_emails, move_to_trash


# =========================================
# Flask Configuration
# =========================================

app = Flask(__name__)

app.secret_key = "custom-spam-email-classifier-secret-key"

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True


# =========================================
# User Overrides Persistence
# =========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

OVERRIDES_FILE = os.path.join(
    BASE_DIR,
    "user_overrides.json"
)

def load_overrides():
    if os.path.exists(OVERRIDES_FILE):
        try:
            with open(OVERRIDES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_override(email_id, label):
    overrides = load_overrides()
    overrides[email_id] = label
    try:
        with open(OVERRIDES_FILE, "w") as f:
            json.dump(overrides, f, indent=2)
    except Exception as e:
        print("Failed to save user override:", e)

def apply_overrides(emails):
    overrides = load_overrides()
    for email in emails:
        if email.get("id") in overrides:
            email["classification"] = overrides[email["id"]]
            email["is_overridden"] = True
        else:
            email["is_overridden"] = False
    return emails


# =========================================
# Email Cache
# =========================================
# IMPORTANT:
# Do NOT store complete emails in Flask session.
# They can make the session cookie too large.

email_cache = []


# =========================================
# Google OAuth Configuration
# =========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials",
    "credentials.json"
)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]

def get_user_profile(credentials_data):
    try:
        token = credentials_data.get("token") if isinstance(credentials_data, dict) else getattr(credentials_data, "token", None)
        if not token:
            return {}
        res = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            given_name = data.get("given_name")
            full_name = data.get("name", "")
            first_name = given_name if given_name else (full_name.split()[0] if full_name else "User")
            return {
                "first_name": first_name,
                "full_name": full_name,
                "email": data.get("email", ""),
                "picture": data.get("picture", "")
            }
    except Exception as e:
        print("Error fetching user profile:", e)
    return {}

REDIRECT_URI = (
    "http://127.0.0.1:5000/oauth2callback"
)


# Local development only
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# =========================================
# Create OAuth Flow
# =========================================

def create_flow(state=None):

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        state=state,
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


# =========================================
# Credentials to Dictionary
# =========================================

def credentials_to_dict(credentials):

    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }


# =========================================
# Login Page
# =========================================

@app.route("/")
def login():

    return render_template(
        "login.html"
    )


# =========================================
# Google Login
# =========================================

@app.route("/login")
def google_login():

    # Clear previous OAuth state
    session.pop(
        "state",
        None
    )

    # Create OAuth flow
    flow = create_flow()

    # Generate authorization URL
    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
    )

    # Store only small OAuth state
    session["state"] = state

    session.permanent = True
    session.modified = True

    return redirect(
        authorization_url
    )


# =========================================
# Google OAuth Callback
# =========================================

@app.route("/oauth2callback")
def oauth2callback():

    # Get saved state
    state = session.get(
        "state"
    )

    if not state:
        session.clear()
        return redirect(
            url_for("google_login")
        )

    # Recreate OAuth flow
    flow = create_flow(
        state=state
    )

    # Exchange authorization code safely
    try:
        flow.fetch_token(
            authorization_response=request.url
        )
    except Exception as e:
        print(f"OAuth token exchange error: {e}")
        session.clear()
        return redirect(
            url_for("google_login")
        )

    # Get Google credentials
    credentials = flow.credentials

    # Save ONLY credentials in session
    session["credentials"] = (
        credentials_to_dict(
            credentials
        )
    )

    # Fetch user profile (First Name)
    user_profile = get_user_profile(session["credentials"])
    session["user_profile"] = user_profile

    # Remove temporary OAuth state
    session.pop(
        "state",
        None
    )

    session.modified = True

    # =====================================
    # Fetch Gmail Emails (Fast Initial Batch for Login)
    # =====================================

    global email_cache

    try:
        email_cache = apply_overrides(
            get_emails(
                session["credentials"],
                max_results=50
            )
        )
    except Exception as e:
        print(f"Gmail initial fetch error: {e}")
        session.clear()
        return redirect(
            url_for("google_login")
        )

    # Go to dashboard
    return redirect(
        url_for("dashboard")
    )


# =========================================
# Dashboard
# =========================================

@app.route("/dashboard")
def dashboard():

    # Check Google login
    if "credentials" not in session:
        return redirect(
            url_for("login")
        )

    global email_cache

    # If cache is empty, fetch emails
    if not email_cache:
        try:
            email_cache = apply_overrides(
                get_emails(
                    session["credentials"],
                    max_results=50
                )
            )
        except Exception as e:
            print(f"Gmail dashboard fetch error: {e}")
            session.clear()
            return redirect(
                url_for("google_login")
            )
    else:
        # Ensure latest overrides are applied
        email_cache = apply_overrides(email_cache)


    emails = email_cache


    # =====================================
    # Statistics
    # =====================================

    total_emails = len(
        emails
    )


    spam_emails = sum(
        1
        for email in emails
        if email["classification"] == "spam"
    )


    safe_emails = (
        total_emails - spam_emails
    )


    if total_emails > 0:

        spam_percentage = round(
            (
                spam_emails /
                total_emails
            ) * 100,
            2
        )

    else:

        spam_percentage = 0


    # User Profile (First Name)
    user_profile = session.get("user_profile")
    if not user_profile:
        user_profile = get_user_profile(session["credentials"])
        session["user_profile"] = user_profile

    user_name = user_profile.get("first_name", "User")
    user_picture = user_profile.get("picture", "")

    # =====================================
    # Render Dashboard
    # =====================================

    return render_template(
        "dashboard.html",
        emails=emails,
        total_emails=total_emails,
        spam_emails=spam_emails,
        safe_emails=safe_emails,
        spam_percentage=spam_percentage,
        user_name=user_name,
        user_picture=user_picture
    )


# =========================================
# Refresh Emails
# =========================================

@app.route("/refresh")
def refresh():

    if "credentials" not in session:

        return redirect(
            url_for("login")
        )


    global email_cache


    try:

        email_cache = apply_overrides(
            get_emails(
                session["credentials"],
                max_results=50
            )
        )

        return redirect(
            url_for("dashboard")
        )

    except Exception as e:

        return f"""
        <h2>Unable to Refresh Gmail</h2>

        <p>
            {str(e)}
        </p>

        <a href="/dashboard">
            Back to Dashboard
        </a>
        """


# =========================================
# API Endpoint: Mark Email as Spam/Safe
# =========================================

@app.route("/api/mark_email", methods=["POST"])
def mark_email():

    if "credentials" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    email_id = data.get("email_id")
    label = data.get("label")  # 'spam' or 'ham'

    if not email_id or label not in ["spam", "ham"]:
        return jsonify({"error": "Invalid request payload"}), 400

    # Save user override decision persistently
    save_override(email_id, label)

    # Update in-memory cache
    global email_cache
    for email in email_cache:
        if email["id"] == email_id:
            email["classification"] = label
            email["is_overridden"] = True
            break

    # Recalculate statistics
    total_emails = len(email_cache)
    spam_emails = sum(
        1 for e in email_cache if e.get("classification") == "spam"
    )
    safe_emails = total_emails - spam_emails
    spam_percentage = round((spam_emails / total_emails) * 100, 2) if total_emails > 0 else 0

    return jsonify({
        "success": True,
        "email_id": email_id,
        "classification": label,
        "is_overridden": True,
        "stats": {
            "total_emails": total_emails,
            "spam_emails": spam_emails,
            "safe_emails": safe_emails,
            "spam_percentage": spam_percentage
        }
    })


# =========================================
# API Endpoint: Move Selected Emails to Trash
# =========================================

@app.route("/api/delete_emails", methods=["POST"])
def delete_emails():
    if "credentials" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    email_ids = data.get("email_ids", [])
    if isinstance(email_ids, str):
        email_ids = [email_ids]

    if not email_ids:
        return jsonify({"error": "No email IDs provided"}), 400

    # Call Gmail API to move emails to Trash
    success = move_to_trash(session["credentials"], email_ids)

    # Remove from local email cache
    global email_cache
    email_cache = [e for e in email_cache if e.get("id") not in email_ids]

    # Recalculate statistics
    total_emails = len(email_cache)
    spam_emails = sum(
        1 for e in email_cache if e.get("classification") == "spam"
    )
    safe_emails = total_emails - spam_emails
    spam_percentage = round((spam_emails / total_emails) * 100, 2) if total_emails > 0 else 0

    return jsonify({
        "success": success,
        "deleted_ids": email_ids,
        "stats": {
            "total_emails": total_emails,
            "spam_emails": spam_emails,
            "safe_emails": safe_emails,
            "spam_percentage": spam_percentage
        }
    })



# =========================================
# Email Details
# =========================================

@app.route("/email/<email_id>")
def email_details(email_id):

    if "credentials" not in session:

        return redirect(
            url_for("login")
        )


    global email_cache


    selected_email = None


    # Search cached emails
    for email in email_cache:

        if email["id"] == email_id:

            selected_email = email

            break


    # If cache is empty, fetch again
    if selected_email is None:

        try:

            email_cache = apply_overrides(
                get_emails(
                    session["credentials"],
                    max_results=50
                )
            )

            for email in email_cache:

                if email["id"] == email_id:

                    selected_email = email

                    break

        except Exception as e:

            return f"""
            <h2>Gmail Error</h2>

            <p>
                {str(e)}
            </p>
            """


    return render_template(
        "email.html",
        email=selected_email
    )


# =========================================
# Logout
# =========================================

@app.route("/logout")
def logout():

    global email_cache

    email_cache = []

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================
# Run Flask
# =========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
