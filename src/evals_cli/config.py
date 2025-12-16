"""Configuration management for the CLI."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

CONFIG_FILE = Path.home() / ".evals-cli" / "config"


def get_config() -> dict:
    """Get configuration from environment or config file."""
    config = {
        "base_url": os.getenv("EVALS_API_BASE_URL", "http://localhost:8080"),
        "auth_token": os.getenv("EVALS_API_AUTH_TOKEN", ""),
    }

    # Try to load from config file if env vars not set
    if CONFIG_FILE.exists() and not config["auth_token"]:
        with open(CONFIG_FILE) as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key == "base_url" and not os.getenv("EVALS_API_BASE_URL"):
                        config["base_url"] = value
                    elif key == "auth_token":
                        config["auth_token"] = value

    return config


def save_config(base_url: str, auth_token: str) -> None:
    """Save configuration to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        f.write(f"base_url={base_url}\n")
        f.write(f"auth_token={auth_token}\n")


def get_headers(auth_token: str) -> dict:
    """Get headers for API requests."""
    return {
        "Authorization": auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
