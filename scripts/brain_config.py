#!/usr/bin/env python3
"""
brain_config.py — single source of truth for every path, domain, model id, and
owner name used by the second-brain scripts and hooks.

Resolution order for the config file:
  1. $BRAIN_CONFIG env var, if set
  2. <repo root>/brain_config.json   (repo root = parent of this scripts/ dir)
  3. <repo root>/brain_config.example.json, WITH a loud stderr warning

The example-config fallback exists only so `doctor.py` and compile checks can
run before a real install has happened. Real installs always have a real
brain_config.json (written by setup.sh from the interview).

Also loads `<APP_DIR>/.env` into os.environ at import time. For
VOYAGE_API_KEY and ANTHROPIC_API_KEY specifically, the .env value WINS over
any value already present in the process environment — session launchers
have been observed injecting stale/empty values via inherited env, so the
canonical file must not be shadowed. Every other key in .env is set only if
not already present (empty-as-unset).
"""

import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent

# Keys whose value in .env must win over an inherited (possibly stale/empty)
# process environment variable of the same name.
_ENV_OVERRIDE_KEYS = {"VOYAGE_API_KEY", "ANTHROPIC_API_KEY"}


class ConfigError(Exception):
    """Raised when brain_config.json fails validation."""


def _resolve_config_path() -> Path:
    env_path = os.environ.get("BRAIN_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    real = REPO_ROOT / "brain_config.json"
    if real.exists():
        return real

    example = REPO_ROOT / "brain_config.example.json"
    sys.stderr.write(
        "brain_config: WARNING — no brain_config.json found; falling back to "
        f"{example} (example config). This is expected only before install "
        "is complete. Set BRAIN_CONFIG or run setup.sh.\n"
    )
    return example


def _load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file.

    Most keys are set only if currently unset or empty (an empty inherited
    value must not shadow the real key in .env). VOYAGE_API_KEY and
    ANTHROPIC_API_KEY are special-cased to always win over inherited env,
    since launchers have been observed injecting stale values for those two.
    """
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not k:
                continue
            if k in _ENV_OVERRIDE_KEYS:
                if v:
                    os.environ[k] = v
            elif not os.environ.get(k):
                os.environ[k] = v
    except Exception as e:
        sys.stderr.write(f"brain_config: dotenv load warning: {e}\n")


def load_dotenv() -> None:
    """Load `<APP_DIR>/.env` into os.environ. Safe to call multiple times."""
    _load_dotenv(APP_DIR / ".env")


def _expand(value: str) -> Path:
    return Path(value).expanduser()


CONFIG_PATH = _resolve_config_path()

try:
    _raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
except Exception as e:
    raise ConfigError(f"brain_config: could not read/parse {CONFIG_PATH}: {e}") from e

# ── Required top-level fields ───────────────────────────────────────────────

try:
    OWNER_NAME = _raw["owner_name"]
    APP_DIR = _expand(_raw["app_dir"])
    VAULT_DIR = _expand(_raw["vault_dir"])
    PYTHON = str(_expand(_raw["python"]))
    LAUNCHD_LABEL = _raw["launchd_label"]
    DOMAINS = list(_raw["domains"])
    DOMAIN_DIRS = dict(_raw["domain_dirs"])
    CWD_DOMAIN_MAP = list(_raw.get("cwd_domain_map", []))
    _models = dict(_raw["models"])
    STRUCTURED_MODEL = _models["structured"]
    CLASSIFY_MODEL = _models["classify"]
    EMBED_MODEL = _models["embed"]
    EMBED_DIM = _models["embed_dim"]
    NOTIFICATIONS = bool(_raw.get("notifications", True))
except KeyError as e:
    raise ConfigError(f"brain_config: missing required key {e} in {CONFIG_PATH}") from e

# ── Derived paths ────────────────────────────────────────────────────────────

VAULT_MEMORY = VAULT_DIR / "memory"
VAULT_DAILY = VAULT_DIR / "daily"
CHROMA_PATH = VAULT_DIR / ".chroma"
LOG_FILE = VAULT_DIR / "brain_watcher.log"
LAST_RECONCILE_FILE = VAULT_DIR / ".last_reconcile"

# ── Validation ───────────────────────────────────────────────────────────────

if not DOMAINS:
    raise ConfigError(f"brain_config: 'domains' must be non-empty in {CONFIG_PATH}")

for _key in DOMAIN_DIRS:
    if _key not in DOMAINS:
        raise ConfigError(
            f"brain_config: domain_dirs key {_key!r} is not in domains {DOMAINS} "
            f"({CONFIG_PATH})"
        )

if not isinstance(EMBED_DIM, int):
    raise ConfigError(f"brain_config: models.embed_dim must be an int in {CONFIG_PATH}")

# ── .env ─────────────────────────────────────────────────────────────────────

load_dotenv()
