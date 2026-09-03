#!/usr/bin/env python3
"""
install_hooks.py — merge or remove the second brain's Claude Code hooks in
~/.claude/settings.json.

Registers three hooks (SessionStart, PreCompact, Stop), each pointing at the
configured PYTHON interpreter and an absolute path under <APP_DIR>/hooks/.
Idempotent: re-running with the same config does not duplicate entries.
Always backs up settings.json before writing.

Usage:
  python3 install_hooks.py                # install/merge
  python3 install_hooks.py --uninstall    # remove only this app's entries
  python3 install_hooks.py --config PATH  # use a specific brain_config.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


HOOK_EVENTS = {
    "SessionStart": "session-start-context.py",
    "PreCompact": "pre-compact-flush.py",
    "Stop": "session-end-flush.py",
}


def _settings_path() -> Path:
    return Path(os.path.expanduser("~/.claude/settings.json"))


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {}
        return json.loads(text)
    except Exception as e:
        print(f"install_hooks: ERROR — could not parse {path}: {e}", file=sys.stderr)
        sys.exit(1)


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-{stamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def _hook_command(python: str, app_dir: Path, hook_file: str) -> str:
    hook_path = app_dir / "hooks" / hook_file
    return f"{python} {hook_path}"


def install(config, settings_path: Path) -> None:
    settings = _load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})

    changed = False
    backup_made = None

    for event, hook_file in HOOK_EVENTS.items():
        command = _hook_command(config.PYTHON, config.APP_DIR, hook_file)
        entries = hooks.setdefault(event, [])

        already_present = any(
            command == h.get("command")
            for entry in entries
            for h in entry.get("hooks", [])
        )
        if already_present:
            print(f"install_hooks: {event} already has this hook — skipping")
            continue

        if backup_made is None:
            backup_made = _backup(settings_path)

        entries.append({"hooks": [{"type": "command", "command": command}]})
        changed = True
        print(f"install_hooks: added {event} -> {command}")

    if not changed:
        print("install_hooks: nothing to do, all hooks already installed")
        return

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    if backup_made is not None:
        print(f"install_hooks: backed up settings to {backup_made}")
    print(f"install_hooks: wrote {settings_path}")


def uninstall(config, settings_path: Path) -> None:
    settings = _load_settings(settings_path)
    hooks = settings.get("hooks", {})
    if not hooks:
        print("install_hooks: no hooks section — nothing to uninstall")
        return

    hooks_dir_marker = str(config.APP_DIR / "hooks") + os.sep

    changed = False
    backup_made = None

    for event in list(HOOK_EVENTS.keys()):
        entries = hooks.get(event)
        if not entries:
            continue
        new_entries = []
        for entry in entries:
            entry_hooks = entry.get("hooks", [])
            kept_hooks = [
                h for h in entry_hooks
                if hooks_dir_marker not in h.get("command", "")
            ]
            if len(kept_hooks) != len(entry_hooks):
                changed = True
            if kept_hooks:
                new_entry = dict(entry)
                new_entry["hooks"] = kept_hooks
                new_entries.append(new_entry)
            # else: entry becomes empty — drop it entirely
            elif entry_hooks:
                # entry had hooks but all were removed
                pass
            else:
                new_entries.append(entry)
        if new_entries:
            hooks[event] = new_entries
        else:
            hooks.pop(event, None)

    if not changed:
        print("install_hooks: no matching hook entries found — nothing to remove")
        return

    backup_made = _backup(settings_path)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    if backup_made is not None:
        print(f"install_hooks: backed up settings to {backup_made}")
    print(f"install_hooks: removed second-brain hook entries from {settings_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/remove second-brain Claude Code hooks")
    parser.add_argument("--uninstall", action="store_true", help="remove this app's hook entries")
    parser.add_argument("--config", type=str, default=None, help="path to brain_config.json")
    args = parser.parse_args()

    if args.config:
        os.environ["BRAIN_CONFIG"] = args.config

    try:
        import brain_config as config
    except Exception as e:
        print(f"install_hooks: ERROR — could not load config: {e}", file=sys.stderr)
        return 1

    settings_path = _settings_path()

    try:
        if args.uninstall:
            uninstall(config, settings_path)
        else:
            install(config, settings_path)
    except Exception as e:
        print(f"install_hooks: ERROR — {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
