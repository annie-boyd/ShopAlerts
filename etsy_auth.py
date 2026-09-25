"""
 etsy_auth.py - one-time Etsy OAuth setup, plus token helpers for the app

 Run it once:  python3 etsy_auth.py
 It opens Etsy in your browser so you can approve read access to your shop's
 orders, then saves the tokens to .etsy_tokens.json (gitignored).

 After that, the app calls get_access_token(), which refreshes the token
 automatically when it expires (access tokens last 1 hour, refresh tokens 90 days).

 Uses OAuth 2.0 with PKCE, which is what Etsy's API v3 requires.

 By: Annie Boyd
 9-22-2026
"""
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
API_BASE = "https://api.etsy.com/v3/application"
SCOPES = "transactions_r"  # read-only access to orders/receipts

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")
TOKENS_PATH = os.path.join(HERE, ".etsy_tokens.json")


def load_env() -> dict:
    """Read KEY=value lines from .env (tiny parser so we don't need python-dotenv)."""
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    for key in ("ETSY_KEYSTRING", "ETSY_SHARED_SECRET", "ETSY_REDIRECT_URI"):
        if not env.get(key):
            raise SystemExit(f"{key} is missing from .env")
    return env


def api_headers(access_token: str) -> dict:
    """Headers every Etsy API call needs."""
    env = load_env()
    return {
        "x-api-key": f"{env['ETSY_KEYSTRING']}:{env['ETSY_SHARED_SECRET']}",
        "Authorization": f"Bearer {access_token}",
    }


def _post_token_request(fields: dict) -> dict:
    """POST to Etsy's token endpoint and return the JSON response."""
    data = urllib.parse.urlencode(fields).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data)) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Etsy token request failed ({e.code}): {e.read().decode()}")


def _save_tokens(token_response: dict) -> dict:
    tokens = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response["refresh_token"],
        # refresh a minute early so a request never goes out with an expired token
        "expires_at": time.time() + token_response["expires_in"] - 60,
    }
    with open(TOKENS_PATH, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKENS_PATH, 0o600)  # only you can read it
    return tokens


def get_access_token() -> str:
    """Return a valid access token, refreshing it first if it has expired."""
    if not os.path.exists(TOKENS_PATH):
        raise SystemExit("No Etsy tokens yet. Run: python3 etsy_auth.py")

    with open(TOKENS_PATH) as f:
        tokens = json.load(f)

    if time.time() >= tokens["expires_at"]:
        env = load_env()
        tokens = _save_tokens(_post_token_request({
            "grant_type": "refresh_token",
            "client_id": env["ETSY_KEYSTRING"],
            "refresh_token": tokens["refresh_token"],
        }))
    return tokens["access_token"]


def _wait_for_callback(redirect_uri: str) -> dict:
    """Run a tiny local web server and return the query params Etsy redirects back with."""
    parsed = urllib.parse.urlparse(redirect_uri)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path != parsed.path:
                self.send_response(404)
                self.end_headers()
                return
            result.update(urllib.parse.parse_qs(url.query))
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>ShopAlerts is connected. You can close this tab.</h2>")

        def log_message(self, *args):
            pass  # keep the terminal quiet

    server = HTTPServer((parsed.hostname, parsed.port or 80), Handler)
    while not result:
        server.handle_request()
    server.server_close()
    return {key: values[0] for key, values in result.items()}


def authorize() -> None:
    """Walk through the one-time browser approval and save the tokens."""
    env = load_env()

    # PKCE: a random secret (verifier) and its hash (challenge). Etsy sees the hash
    # now and the secret later, which proves the same program made both requests.
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)  # protects against forged redirects

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": env["ETSY_KEYSTRING"],
        "redirect_uri": env["ETSY_REDIRECT_URI"],
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })

    print("Opening Etsy in your browser to approve access...")
    print(f"If it doesn't open, visit:\n{url}\n")
    webbrowser.open(url)

    params = _wait_for_callback(env["ETSY_REDIRECT_URI"])
    if "error" in params:
        raise SystemExit(f"Etsy returned an error: {params['error']} {params.get('error_description', '')}")
    if params.get("state") != state:
        raise SystemExit("State mismatch, so the redirect didn't come from this login attempt. Try again.")

    tokens = _save_tokens(_post_token_request({
        "grant_type": "authorization_code",
        "client_id": env["ETSY_KEYSTRING"],
        "redirect_uri": env["ETSY_REDIRECT_URI"],
        "code": params["code"],
        "code_verifier": code_verifier,
    }))
    print(f"Tokens saved to {os.path.basename(TOKENS_PATH)}")

    # the access token starts with your Etsy user ID, so look up your shop
    user_id = tokens["access_token"].split(".")[0]
    request = urllib.request.Request(f"{API_BASE}/users/{user_id}/shops",
                                     headers=api_headers(tokens["access_token"]))
    try:
        with urllib.request.urlopen(request) as resp:
            json.load(resp)
        print("Connected to your Etsy shop.")  
    except urllib.error.HTTPError as e:
        print(f"Tokens are saved, but the shop lookup failed ({e.code}): {e.read().decode()}")


if __name__ == "__main__":
    authorize()
