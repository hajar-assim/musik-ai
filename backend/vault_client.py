# vault_client.py
import hvac
import os
import sys

# read Vault env vars
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

if VAULT_TOKEN is None:
    print("VAULT_TOKEN not set. Make sure to source start_vault.sh before running.", file=sys.stderr)
    sys.exit(1)

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

# preload commonly used secrets
YOUTUBE_API_KEY = get_secret("api-keys/youtube", "YOUTUBE_API_KEY")
SPOTIFY_CLIENT_ID = get_secret("api-keys/spotify", "SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_secret("api-keys/spotify", "SPOTIFY_CLIENT_SECRET")
