"""Load environment variables from project root and edge-agent .env files."""

import os
from pathlib import Path

from dotenv import load_dotenv

EDGE_AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EDGE_AGENT_DIR.parent


def load_project_env() -> Path:
    """
    Load env files in order (later files override earlier):
      1. <project-root>/.env
      2. <edge-agent>/.env

    Variables already set in the process environment (e.g. Docker env_file)
    are not overwritten by load_dotenv(override=False) on the first file;
    edge-agent/.env may still override with override=True.
    """
    root_env = PROJECT_ROOT / ".env"
    local_env = EDGE_AGENT_DIR / ".env"

    if root_env.is_file():
        load_dotenv(root_env, override=False)
    if local_env.is_file():
        load_dotenv(local_env, override=True)

    return EDGE_AGENT_DIR


def get_r2_config() -> dict[str, str]:
    """Return R2 settings from the environment (after load_project_env)."""
    keys = (
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET",
        "R2_PUBLIC_URL",
    )
    return {key: os.getenv(key, "").strip() for key in keys}


def r2_configured() -> bool:
    return all(get_r2_config().values())
