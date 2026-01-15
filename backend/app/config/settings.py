import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    YOUTUBE_API_KEY: str
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    GROQ_API_KEY: str

    # URLs
    REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://127.0.0.1:8888/callback")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Spotify
    SPOTIFY_SCOPE: str = "playlist-modify-private playlist-modify-public"

    # LLM
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Email
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "hajar.assim@gmail.com")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    # Vault (optional)
    VAULT_ADDR: str = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    VAULT_TOKEN: str = os.getenv("VAULT_TOKEN", "")
    USE_VAULT: bool = bool(VAULT_TOKEN)

    def __init__(self):
        self._load_secrets()

    def _load_secrets(self):
        if self.USE_VAULT:
            from .vault import get_vault_secrets
            secrets = get_vault_secrets()
            self.YOUTUBE_API_KEY = secrets["YOUTUBE_API_KEY"]
            self.SPOTIFY_CLIENT_ID = secrets["SPOTIFY_CLIENT_ID"]
            self.SPOTIFY_CLIENT_SECRET = secrets["SPOTIFY_CLIENT_SECRET"]
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        else:
            self.YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
            self.SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
            self.SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

            if not all([self.SPOTIFY_CLIENT_ID, self.SPOTIFY_CLIENT_SECRET, self.GROQ_API_KEY]):
                raise ValueError("Missing required API keys: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GROQ_API_KEY")

settings = Settings()
