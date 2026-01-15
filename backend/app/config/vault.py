import hvac
import os
import logging

logger = logging.getLogger(__name__)

def get_vault_secrets() -> dict:
    """Fetch secrets from Vault"""
    vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_token:
        raise ValueError("VAULT_TOKEN not set")

    client = hvac.Client(url=vault_addr, token=vault_token)
    mount_point = "secret"

    def get_secret(path: str, field: str) -> str:
        try:
            secret = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            return secret["data"]["data"][field]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {field} from {path}: {e}")

    logger.info("📦 Using Vault for secrets")

    return {
        "YOUTUBE_API_KEY": get_secret("api-keys/youtube", "YOUTUBE_API_KEY"),
        "SPOTIFY_CLIENT_ID": get_secret("api-keys/spotify", "SPOTIFY_CLIENT_ID"),
        "SPOTIFY_CLIENT_SECRET": get_secret("api-keys/spotify", "SPOTIFY_CLIENT_SECRET"),
    }
