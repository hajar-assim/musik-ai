# vault_client.py
import hvac
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# read Vault env vars
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

# Flag to determine if we're using Vault or .env
USE_VAULT = VAULT_TOKEN is not None

if USE_VAULT:
    # initialize Vault client
    client = hvac.Client(
        url=VAULT_ADDR,
        token=VAULT_TOKEN
    )
    MOUNT_POINT = "secret"

    def get_secret(path: str, field: str) -> str:
        """
        Fetch a single field from a KV v2 secret.
        path: relative to the mount_point (e.g., "api-keys/youtube")
        field: the key name inside the secret (e.g., "YOUTUBE_API_KEY")
        """
        try:
            secret = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=MOUNT_POINT
            )
            return secret["data"]["data"][field]
        except KeyError:
            raise RuntimeError(f"Field '{field}' not found in secret '{path}' at mount '{MOUNT_POINT}'")
        except hvac.exceptions.InvalidPath:
            raise RuntimeError(f"Secret path '{path}' does not exist at mount '{MOUNT_POINT}'")
        except hvac.exceptions.Forbidden:
            raise RuntimeError(f"Permission denied: check your VAULT_TOKEN and policies")

    # preload commonly used secrets from Vault
    print("📦 Using Vault for secrets")
    YOUTUBE_API_KEY = get_secret("api-keys/youtube", "YOUTUBE_API_KEY")
    SPOTIFY_CLIENT_ID = get_secret("api-keys/spotify", "SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = get_secret("api-keys/spotify", "SPOTIFY_CLIENT_SECRET")
else:
    # Fallback to .env file
    print("📄 Using .env file for secrets (Vault not configured)")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    # Validate that required keys are present
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env file", file=sys.stderr)
        sys.exit(1)
    if not SPOTIFY_CLIENT_ID:
        print("ERROR: SPOTIFY_CLIENT_ID not found in .env file", file=sys.stderr)
        sys.exit(1)
    if not SPOTIFY_CLIENT_SECRET:
        print("ERROR: SPOTIFY_CLIENT_SECRET not found in .env file", file=sys.stderr)
        sys.exit(1)
