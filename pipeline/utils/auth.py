"""
utils/auth.py — Google OAuth2 credential helper.

Shared by: connectors/gsc.py, connectors/ga4.py, connectors/google_ads.py

The refresh token is stored in .env. This module handles auto-refresh of
the 1-hour access token without re-prompting the user.

Setup (one-time):
1. Create OAuth 2.0 Client ID in Google Cloud Console (Desktop app type)
2. Run: python utils/auth.py --generate-token
3. Copy the refresh_token output to GOOGLE_REFRESH_TOKEN in .env
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
except ImportError:
    raise ImportError(
        "Missing google-auth. Run: pip install google-auth google-auth-oauthlib"
    )

# Scopes required across all three Google APIs
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adwords",
]


def get_google_credentials() -> Credentials:
    required = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(
            f"[auth] Missing required environment variables: {', '.join(missing)}. "
            "Check your .env file and run python utils/auth.py --generate-token to get a refresh token."
        )

    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=GOOGLE_SCOPES,
    )

    try:
        if not creds.valid or creds.expired:
            creds.refresh(Request())
    except RefreshError as exc:
        raise RefreshError(
            f"[auth] Google refresh token is invalid or revoked. "
            "Re-run: python utils/auth.py --generate-token\n"
            f"Original error: {exc}"
        ) from exc

    return creds


def generate_token_cli() -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env first.")
        sys.exit(1)

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                "http://localhost:8080/",
                "http://127.0.0.1:8080/",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "urn:ietf:wg:oauth:2.0:oob",
                "http://localhost",
            ],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_SCOPES)
    creds = flow.run_local_server(port=8080)
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    if "--generate-token" in sys.argv:
        generate_token_cli()
    else:
        print("Usage: python utils/auth.py --generate-token")
