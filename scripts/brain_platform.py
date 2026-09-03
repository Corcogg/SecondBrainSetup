#!/usr/bin/env python3
"""
brain_platform.py — the ONLY module in this repo allowed to branch on
sys.platform/os.name.

Everything else (brain_watcher.py, doctor.py, install_hooks.py,
brain_test.py) calls the functions here instead of importing subprocess to
reach osascript, pgrep, launchctl, schtasks, tasklist, or icacls directly.
See docs/ARCHITECTURE.md — "Windows port — contract (2026-09-03)" for the
binding function signatures this module implements.

Every public Windows helper below catches all exceptions and returns a
not-ok result with the exception folded into the detail string; none of
them raise. macOS behaviour is preserved byte-for-byte from the pre-port
code (same osascript script, same pgrep invocation, same launchctl target
string, same 0o600 test) — this module only relocates that code, it does
not change it.

Secrets note: `secrets_file_locked`'s detail is permission/ACL information
only. It must never contain the contents of the file it inspects.
"""

import csv
import io
import logging
import os
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config  # noqa: E402 — for NOTIFICATIONS in notify()

IS_WINDOWS = sys.platform == "win32"


# ── notify ───────────────────────────────────────────────────────────────────

def notify(title: str, message: str) -> None:
    """Best-effort desktop notification.

    macOS: osascript, argv-passed to avoid code injection (moved verbatim
    from the old brain_watcher.notify()). Windows: no-op — v1 drops toasts,
    per the Windows port contract. No-op on either platform if notifications
    are disabled in config. Never raises.
    """
    if not brain_config.NOTIFICATIONS:
        return
    if IS_WINDOWS:
        return
    try:
        # Script reads message/title from argv, so no string interpolation
        # into AppleScript.
        script = (
            "on run argv\n"
            "  display notification (item 1 of argv) with title (item 2 of argv)\n"
            "end run\n"
        )
        subprocess.run(
            ["osascript", "-", message, title],
            input=script, text=True, check=False, capture_output=True,
        )
    except Exception as e:
        logging.getLogger(__name__).warning(
            "osascript notify failed (%s): %s", type(e).__name__, e
        )


# ── watcher_pids ─────────────────────────────────────────────────────────────

def _parse_process_csv(output: str) -> list[str]:
    """Parse `Get-CimInstance Win32_Process | ... | ConvertTo-Csv` output.

    Returns the ProcessId of every row whose CommandLine mentions
    brain_watcher.py. Never raises — malformed input yields an empty list.
    """
    pids: list[str] = []
    try:
        rows = list(csv.reader(io.StringIO(output)))
    except Exception:
        return pids
    if not rows:
        return pids
    header = [h.strip() for h in rows[0]]
    try:
        pid_idx = header.index("ProcessId")
        cmd_idx = header.index("CommandLine")
    except ValueError:
        return pids
    for row in rows[1:]:
        if len(row) <= max(pid_idx, cmd_idx):
            continue
        cmdline = row[cmd_idx] or ""
        if "brain_watcher.py" in cmdline:
            pid = row[pid_idx].strip()
            if pid:
                pids.append(pid)
    return pids


def watcher_pids(script_path: Path) -> list[str]:
    """PIDs of any running brain_watcher.py process. Empty list = not running.

    macOS: `pgrep -f <script_path>` (unchanged from the pre-port doctor.py /
    brain_mcp.py invocation). Windows: tasklist's `/V` output does not carry
    full command lines, so this shells out to PowerShell's Win32_Process
    (which does) and matches "brain_watcher.py" in CommandLine. Never raises.
    """
    if not IS_WINDOWS:
        try:
            out = subprocess.run(
                ["pgrep", "-f", str(script_path)],
                capture_output=True, text=True, timeout=3,
            )
            return [p for p in out.stdout.split() if p.strip()]
        except Exception:
            return []

    try:
        ps_cmd = (
            "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" "
            "| Select-Object ProcessId,CommandLine | ConvertTo-Csv -NoTypeInformation"
        )
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10,
        )
        return _parse_process_csv(out.stdout)
    except Exception:
        return []


# ── secrets_file_locked ──────────────────────────────────────────────────────

# Principals that may appear on the .env ACL besides the owner. Both can read
# any file on the machine regardless of ACL (Administrators can take ownership),
# so allowing them costs nothing; OpenSSH for Windows applies the same rule to
# private keys. Observed on windows-latest: `icacls /inheritance:r /grant:r`
# still leaves explicit SYSTEM + Administrators ACEs on files under the profile.
_ADMIN_PRINCIPALS = {"nt authority\\system", "builtin\\administrators"}


def _parse_icacls(output: str, user: str) -> tuple[bool, str]:
    """Parse `icacls <path>` output (path prefix already stripped by the
    caller) into (locked, detail).

    Locked iff every listed principal resolves to `user` (matched either as
    the full "DOMAIN\\name" form or the bare "name" form, case-insensitively)
    or is one of _ADMIN_PRINCIPALS, and no ACE carries the inherited flag "(I)". `detail` is permission
    info only — never file contents.
    """
    user_full = user.strip().lower()
    user_name = user_full.rsplit("\\", 1)[-1]

    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    ace_lines = [
        ln for ln in lines
        if not ln.lower().startswith("successfully processed")
        and not ln.lower().startswith("failed processing")
    ]
    if not ace_lines:
        return False, "no ACL entries found in icacls output"

    principals: list[str] = []
    inherited = False
    for ln in ace_lines:
        if ":(" not in ln:
            continue
        principal, _, rest = ln.partition(":(")
        flags = "(" + rest
        principal = principal.strip()
        if principal:
            principals.append(principal)
        if "(I)" in flags:
            inherited = True

    if not principals:
        return False, f"could not parse icacls output: {ace_lines[0]!r}"

    if inherited:
        return False, f"inherited ACE present: {', '.join(principals)}"

    allowed = {user_full, user_name} | _ADMIN_PRINCIPALS
    non_owner = [p for p in principals if p.lower() not in allowed]
    if non_owner:
        return False, f"non-owner principal(s): {', '.join(non_owner)}"

    return True, f"owner-only ACL: {', '.join(principals)}"


def secrets_file_locked(path: Path) -> tuple[bool, str]:
    """Is `path` (the .env file) restricted to the owning user only?

    macOS: stat mode == 0o600 (unchanged from the pre-port doctor.py check).
    Windows: `icacls <path>` shows the current user as the ONLY principal
    (no BUILTIN\\Users, Authenticated Users, Everyone, and no inherited
    ACEs). Returns (ok, detail); detail never contains file contents.
    Never raises.
    """
    if not IS_WINDOWS:
        try:
            if not path.exists():
                return False, f"{path} does not exist"
            mode = stat.S_IMODE(path.stat().st_mode)
            return mode == 0o600, f"mode={oct(mode)}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    try:
        if not path.exists():
            return False, f"{path} does not exist"
        user = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}".strip("\\")
        r = subprocess.run(
            ["icacls", str(path)],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return False, f"icacls failed: {(r.stderr or r.stdout).strip()[:200]}"
        raw = r.stdout.replace(str(path), "", 1)
        return _parse_icacls(raw, user)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ── service_loaded ───────────────────────────────────────────────────────────

def _parse_schtasks_csv(output: str) -> tuple[bool, str]:
    """Parse `schtasks /Query /TN <label> /FO CSV /V` stdout into
    (ok, detail=state string). ok iff the Status column reads "Running" or
    "Ready". Any parse failure (task not found, malformed output) is
    reported as not-ok with an explanatory detail; never raises.
    """
    try:
        rows = [r for r in csv.reader(io.StringIO(output)) if r]
    except Exception as e:
        return False, f"could not parse schtasks output: {e}"
    if len(rows) < 2:
        return False, "task not found"
    header = [h.strip() for h in rows[0]]
    try:
        status_idx = header.index("Status")
    except ValueError:
        return False, "no Status column in schtasks output"
    data_row = rows[1]
    if len(data_row) <= status_idx:
        return False, "malformed schtasks row"
    status = data_row[status_idx].strip()
    return status in ("Running", "Ready"), status


def service_loaded(label: str) -> tuple[bool, str]:
    """Is the watcher's OS-level supervisor loaded and (believed) alive?

    macOS: `launchctl print gui/<uid>/<label>`, rc==0 (unchanged — same
    target string as the pre-port doctor.check_launchd). Windows:
    `schtasks /Query /TN <label> /FO CSV /V`, ok iff Status is "Running" or
    "Ready". detail = state string on Windows, target string on macOS
    (matching the pre-port behaviour, which used the target unconditionally).
    Never raises.
    """
    if not IS_WINDOWS:
        try:
            uid = os.getuid()
            target = f"gui/{uid}/{label}"
            r = subprocess.run(
                ["launchctl", "print", target],
                capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0, target
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    try:
        r = subprocess.run(
            ["schtasks", "/Query", "/TN", label, "/FO", "CSV", "/V"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return False, "task not found"
        return _parse_schtasks_csv(r.stdout)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
