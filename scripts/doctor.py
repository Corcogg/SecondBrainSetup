#!/usr/bin/env python3
"""
doctor.py — health checklist for a second-brain install.

Runs a fixed list of checks (config, dependencies, secrets presence, vault
layout, watcher/launchd/MCP/hooks registration, Chroma openability, reconcile
freshness) and reports each as {name, ok, detail}.

Never makes a network call. Never prints a secret value or prefix — only
"present, N chars" for API keys.

Usage:
  python3 doctor.py             # human-readable table
  python3 doctor.py --json      # machine-readable
  python3 doctor.py --config PATH

Exit code: 0 iff every check is ok, else 1.
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": bool(ok), "detail": detail}


def check_config() -> tuple[dict, object | None]:
    try:
        import brain_config as config
        return check("config loads and validates", True, f"loaded {config.CONFIG_PATH}"), config
    except Exception as e:
        return check("config loads and validates", False, f"{type(e).__name__}: {e}"), None


def check_python(config) -> dict:
    try:
        # A uv/venv python is a symlink to the base interpreter, so compare the
        # environment prefix (the venv dir) rather than the resolved binary.
        current = str(Path(sys.prefix).resolve())
        configured = str(Path(config.PYTHON).parent.parent.resolve())
        if current == configured:
            return check("running python matches config PYTHON", True, f"venv {current}")
        # Warn, don't fail: doctor may legitimately run under a different
        # interpreter (e.g. system python3.11) than the venv python configured
        # for hooks/watcher.
        return check(
            "running python matches config PYTHON", True,
            f"warn: running under {current}, configured PYTHON is {configured}",
        )
    except Exception as e:
        return check("running python matches config PYTHON", True, f"warn: {type(e).__name__}: {e}")


def check_import(module_name: str) -> dict:
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", "unknown")
        return check(f"import {module_name}", True, f"version {version}")
    except Exception as e:
        return check(f"import {module_name}", False, f"{type(e).__name__}: {e}")


def check_api_key(env_var: str) -> dict:
    value = os.environ.get(env_var)
    if value:
        return check(f"{env_var} present", True, f"present, {len(value)} chars")
    return check(f"{env_var} present", False, "not set")


def check_vault_dirs(config) -> list[dict]:
    results = []
    results.append(check("vault dir exists", config.VAULT_DIR.exists(), str(config.VAULT_DIR)))
    results.append(check("vault memory/ exists", config.VAULT_MEMORY.exists(), str(config.VAULT_MEMORY)))
    for fname in ("SOUL.md", "USER.md", "MEMORY.md"):
        p = config.VAULT_DIR / fname
        results.append(check(f"vault {fname} exists", p.exists(), str(p)))
    return results


def check_env_mode(config) -> dict:
    env_path = config.APP_DIR / ".env"
    if not env_path.exists():
        return check(".env mode is 600", False, f"{env_path} does not exist")
    mode = stat.S_IMODE(env_path.stat().st_mode)
    ok = mode == 0o600
    return check(".env mode is 600", ok, f"mode={oct(mode)}")


def check_watcher_process(config) -> dict:
    watcher_path = config.APP_DIR / "scripts" / "brain_watcher.py"
    try:
        out = subprocess.run(
            ["pgrep", "-f", str(watcher_path)],
            capture_output=True, text=True, timeout=3,
        )
        pids = [p for p in out.stdout.split() if p.strip()]
        if pids:
            return check("watcher process running", True, f"pid {', '.join(pids)}")
        return check("watcher process running", False, "no matching process")
    except Exception as e:
        return check("watcher process running", False, f"{type(e).__name__}: {e}")


def check_launchd(config) -> dict:
    try:
        uid = os.getuid()
        target = f"gui/{uid}/{config.LAUNCHD_LABEL}"
        r = subprocess.run(
            ["launchctl", "print", target],
            capture_output=True, text=True, timeout=5,
        )
        return check("launchd job loaded", r.returncode == 0, target)
    except Exception as e:
        return check("launchd job loaded", False, f"{type(e).__name__}: {e}")


def check_mcp_registered() -> dict:
    if shutil.which("claude") is None:
        return check("MCP registered (claude-brain)", False, "claude CLI not found on PATH")
    try:
        r = subprocess.run(
            ["claude", "mcp", "get", "claude-brain"],
            capture_output=True, text=True, timeout=10,
        )
        return check("MCP registered (claude-brain)", r.returncode == 0,
                      "" if r.returncode == 0 else (r.stderr or r.stdout).strip()[:200])
    except Exception as e:
        return check("MCP registered (claude-brain)", False, f"{type(e).__name__}: {e}")


def check_hooks_installed(config) -> dict:
    settings_path = Path(os.path.expanduser("~/.claude/settings.json"))
    if not settings_path.exists():
        return check("hooks installed in settings.json", False, f"{settings_path} does not exist")
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as e:
        return check("hooks installed in settings.json", False, f"could not parse: {e}")

    hooks = settings.get("hooks", {})
    hook_files = {
        "SessionStart": "session-start-context.py",
        "PreCompact": "pre-compact-flush.py",
        "Stop": "session-end-flush.py",
    }
    missing = []
    for event, fname in hook_files.items():
        marker = str(config.APP_DIR / "hooks" / fname)
        entries = hooks.get(event, [])
        found = any(
            marker in h.get("command", "")
            for entry in entries
            for h in entry.get("hooks", [])
        )
        if not found:
            missing.append(event)

    if missing:
        return check("hooks installed in settings.json", False, f"missing: {', '.join(missing)}")
    return check("hooks installed in settings.json", True, "SessionStart, PreCompact, Stop present")


def check_chroma(config) -> dict:
    # PersistentClient creates its directory as a side effect of opening, so
    # only open it when the index already exists on disk.
    if not config.CHROMA_PATH.exists():
        return check("Chroma collection openable", False, f"{config.CHROMA_PATH} does not exist (index not built yet)")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(config.CHROMA_PATH))
        collection = client.get_collection(name="notes")
        count = collection.count()
        return check("Chroma collection openable", True, f"{count} notes indexed")
    except Exception as e:
        return check("Chroma collection openable", False, f"{type(e).__name__}: {e}")


def check_reconcile(config) -> dict:
    marker = config.LAST_RECONCILE_FILE
    if not marker.exists():
        return check("last reconcile freshness", False, "never run")
    try:
        ts = int(marker.read_text(encoding="utf-8").strip())
        age_min = int((datetime.now().timestamp() - ts) / 60)
        return check("last reconcile freshness", True, f"{age_min} min ago")
    except Exception as e:
        return check("last reconcile freshness", False, f"{type(e).__name__}: {e}")


def run_checks() -> list[dict]:
    results = []

    config_check, config = check_config()
    results.append(config_check)

    if config is None:
        # Nothing else can run meaningfully without a valid config.
        return results

    results.append(check_python(config))

    for module_name in ("anthropic", "voyageai", "chromadb", "rank_bm25", "watchdog", "mcp"):
        results.append(check_import(module_name))

    results.append(check_api_key("VOYAGE_API_KEY"))
    results.append(check_api_key("ANTHROPIC_API_KEY"))

    results.extend(check_vault_dirs(config))
    results.append(check_env_mode(config))
    results.append(check_watcher_process(config))
    results.append(check_launchd(config))
    results.append(check_mcp_registered())
    results.append(check_hooks_installed(config))
    results.append(check_chroma(config))
    results.append(check_reconcile(config))

    return results


def print_human(results: list[dict]) -> None:
    name_width = max((len(r["name"]) for r in results), default=0)
    for r in results:
        marker = "✅" if r["ok"] else "❌"
        detail = f"  — {r['detail']}" if r["detail"] else ""
        print(f"{marker} {r['name']:<{name_width}}{detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Second-brain health checklist")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--config", type=str, default=None, help="path to brain_config.json")
    args = parser.parse_args()

    if args.config:
        os.environ["BRAIN_CONFIG"] = args.config

    results = run_checks()
    overall_ok = all(r["ok"] for r in results)

    if args.json:
        print(json.dumps({"checks": results, "ok": overall_ok}, indent=2))
    else:
        print_human(results)
        print()
        print("All checks passed." if overall_ok else "Some checks failed.")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
