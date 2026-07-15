from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def _parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip() 
        if not line or line.startswith("#") or "=" not in line:
            continue
        
        line = line.split("#", 1)[0].strip()
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def _find_env_file(start_dir: Optional[str | os.PathLike[str]] = None) -> Optional[Path]:
    current = Path(start_dir or os.getcwd()).expanduser().resolve()
    while True:
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        if current.parent == current:
            break
        current = current.parent
    return None


def get_runtime_env() -> str:
    if 'google.colab' in sys.modules:
        return "colab"
    elif os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return "kaggle"
    else:
        return "local"


def _get_raw_value(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    env_file = _find_env_file()
    if env_file:
        return _parse_env_file(env_file).get(key, "")
    return ""


def load_auth_registry() -> Dict[str, str]:
    """Build a mapping of {auth_token: project_name}.

    Priority:
      1. AUTH_TOKENS env var — JSON dict of {"token": "project", ...}
      2. Legacy: AUTH_TOKEN + PROJECT_NAME env vars / .env file
    Returns empty dict when no auth is configured (open dev mode).
    """
    raw = _get_raw_value("AUTH_TOKENS")
    if raw:
        try:
            registry = json.loads(raw)
            if isinstance(registry, dict):
                return registry
        except json.JSONDecodeError:
            pass

    token = _get_raw_value("AUTH_TOKEN")
    project = _get_raw_value("PROJECT_NAME")
    if token and project:
        return {token: project}
    if token:
        return {token: token}

    return {}


def load_server_config() -> Dict[str, str]:
    RUNTIME_ENV = get_runtime_env()
    
    if RUNTIME_ENV == "kaggle":
        print("Running in Kaggle environment.")
        from kaggle_secrets import UserSecretsClient # type: ignore

        user_secrets = UserSecretsClient()
        return {
            "AUTH_TOKEN": user_secrets.get_secret("AUTH_TOKEN"),
            "CL_TUNNEL_TOKEN": user_secrets.get_secret("CL_TUNNEL_TOKEN"),
        }

    elif RUNTIME_ENV == "colab":
        print("Running in Colab environment.")
        from google.colab import userdata # type: ignore
        
        return {
            "AUTH_TOKEN": userdata.get("AUTH_TOKEN", ""),
            "CL_TUNNEL_TOKEN": userdata.get("CL_TUNNEL_TOKEN", ""),
        }
        
    else:
        print("Running in local environment.")
        env_file = _find_env_file()
        parsed = _parse_env_file(env_file) if env_file else {}
        return {
            "AUTH_TOKEN": parsed.get("AUTH_TOKEN", ""),
            "CL_TUNNEL_TOKEN": parsed.get("CL_TUNNEL_TOKEN", ""),
        }


def load_config(start_dir: Optional[str | os.PathLike[str]] = None) -> Dict[str, str]:
    env_file = _find_env_file(start_dir)
    file_values = _parse_env_file(env_file) if env_file else {}

    return {
        "SERVER_URL": os.environ.get("PUBLIC_URL") or file_values.get("PUBLIC_URL", ""),
        "AUTH_TOKEN": os.environ.get("AUTH_TOKEN") or file_values.get("AUTH_TOKEN", ""),
        "PROJECT_NAME": os.environ.get("PROJECT_NAME") or file_values.get("PROJECT_NAME", ""),
    }
