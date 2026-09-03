#!/usr/bin/env bash
# setup.sh — one-shot, idempotent installer for the second brain, macOS only.
#
# Normally run by Claude Code, not typed by hand. See INSTALL.md for the
# runbook this script is one step of.
#
# Flags:
#   --non-interactive   never prompt; fail with a clear message if keys are missing
#   --skip-mcp           don't register the MCP server with Claude Code
#   --skip-hooks         don't install the SessionStart/PreCompact/Stop hooks
#   --skip-index         don't build the initial vector index
#
# Env overrides:
#   SECONDBRAIN_ROOT      install root (default: ~/SecondBrain)
#   BRAIN_LAUNCHD_LABEL   launchd label (default: com.secondbrain.watcher)
#   VOYAGE_API_KEY / ANTHROPIC_API_KEY  optional; the preferred path is to put
#     them in <app>/.env (KEY=value lines) before running — setup reads that file
#     and never needs the keys on a command line or in a chat message.

set -euo pipefail

TOTAL=10
step() { printf '[%s/%s] %s\n' "$1" "$TOTAL" "$2"; }

# ── Argument parsing ─────────────────────────────────────────────────────────

NONINTERACTIVE=0
SKIP_MCP=0
SKIP_HOOKS=0
SKIP_INDEX=0

for arg in "$@"; do
  case "$arg" in
    --non-interactive) NONINTERACTIVE=1 ;;
    --skip-mcp) SKIP_MCP=1 ;;
    --skip-hooks) SKIP_HOOKS=1 ;;
    --skip-index) SKIP_INDEX=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: setup.sh [--non-interactive] [--skip-mcp] [--skip-hooks] [--skip-index]
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ "$NONINTERACTIVE" = "1" ] || [ ! -t 0 ]; then
  INTERACTIVE=0
else
  INTERACTIVE=1
fi

SECONDBRAIN_ROOT="${SECONDBRAIN_ROOT:-$HOME/SecondBrain}"
LABEL="${BRAIN_LAUNCHD_LABEL:-com.secondbrain.watcher}"
APP="$SECONDBRAIN_ROOT/app"
VAULT="$SECONDBRAIN_ROOT/vault"

echo "================================================="
echo "  Second Brain — Setup"
echo "================================================="

# ── Step 1: Preflight ────────────────────────────────────────────────────────

step 1 "Preflight checks"

UNAME_S="$(uname -s)"
if [ "$UNAME_S" != "Darwin" ]; then
  echo "  ERROR: this installer only supports macOS (found: $UNAME_S)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$SCRIPT_DIR" in
  "$HOME/Desktop"|"$HOME/Desktop"/*|"$HOME/Documents"|"$HOME/Documents"/*|"$HOME/Downloads"|"$HOME/Downloads"/*)
    echo "  ERROR: this folder is under Desktop, Documents, or Downloads." >&2
    echo "  macOS (TCC) silently blocks the background watcher from reading files in those folders, with no error." >&2
    echo "  Move the folder first, then re-run from the new location:" >&2
    echo "    mkdir -p \"$SECONDBRAIN_ROOT\" && mv \"$SCRIPT_DIR\" \"$APP\" && \"$APP/setup.sh\" $*" >&2
    exit 1
    ;;
esac

case "$SECONDBRAIN_ROOT" in
  "$HOME/Desktop"|"$HOME/Desktop"/*|"$HOME/Documents"|"$HOME/Documents"/*|"$HOME/Downloads"|"$HOME/Downloads"/*)
    echo "  ERROR: SECONDBRAIN_ROOT ($SECONDBRAIN_ROOT) is under Desktop, Documents, or Downloads." >&2
    echo "  The background watcher cannot read those folders (macOS TCC). Use the default (~/SecondBrain) or another location under your home folder." >&2
    exit 1
    ;;
esac

if [ "$SCRIPT_DIR" != "$APP" ]; then
  if [ -e "$APP" ]; then
    echo "  ERROR: $APP already exists and is not this folder. Remove it, or set SECONDBRAIN_ROOT to install elsewhere." >&2
    exit 1
  fi
  if [ "$INTERACTIVE" = "1" ]; then
    read -rp "  This repo isn't at $APP yet. Move it there now? [Y/n] " mv_ans
    case "$mv_ans" in
      [nN]*)
        echo "  ERROR: setup.sh must run from $APP. Move it manually and re-run." >&2
        exit 1
        ;;
      *)
        mkdir -p "$SECONDBRAIN_ROOT"
        mv "$SCRIPT_DIR" "$APP"
        echo "  Moved to $APP — re-launching setup.sh from there."
        exec "$APP/setup.sh" "$@"
        ;;
    esac
  else
    echo "  ERROR: setup.sh must run from $APP (found: $SCRIPT_DIR). Move the folder and re-run, or set SECONDBRAIN_ROOT." >&2
    exit 1
  fi
fi

if ! command -v git >/dev/null 2>&1; then
  echo "  ERROR: git is required. Install the Xcode Command Line Tools: xcode-select --install" >&2
  exit 1
fi

if { [ "$SKIP_MCP" != "1" ] || [ "$SKIP_HOOKS" != "1" ]; } && ! command -v claude >/dev/null 2>&1; then
  echo "  ERROR: the 'claude' command is not on PATH. Install Claude Code, or re-run with --skip-mcp --skip-hooks." >&2
  exit 1
fi

echo "  OK: macOS, install path is $APP, git and claude present."

# ── Step 2: uv ────────────────────────────────────────────────────────────────

step 2 "Checking for uv (Python package manager)"

UV=""
if command -v uv >/dev/null 2>&1; then
  UV="uv"
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "  uv not found — installing via the official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  if command -v uv >/dev/null 2>&1; then
    UV="uv"
  elif [ -x "$HOME/.local/bin/uv" ]; then
    UV="$HOME/.local/bin/uv"
  fi
fi
if [ -z "$UV" ]; then
  echo "  ERROR: uv install did not put 'uv' on PATH. See https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi
echo "  OK: $("$UV" --version 2>&1 | head -1)"

# ── Step 3: venv + dependencies ─────────────────────────────────────────────

step 3 "Python 3.11 virtual environment"

if [ -d "$APP/.venv" ]; then
  echo "  $APP/.venv already exists — skipping creation."
else
  "$UV" venv --python 3.11 "$APP/.venv"
  echo "  Created $APP/.venv"
fi
"$UV" pip install --python "$APP/.venv/bin/python" -r "$APP/requirements.txt"
echo "  OK: dependencies installed from requirements.txt."

# ── Step 4: API keys ─────────────────────────────────────────────────────────

step 4 "API keys"

resolve_key() {
  local var_name="$1"
  local current="${!var_name:-}"
  if [ -z "$current" ] && [ -f "$APP/.env" ]; then
    current="$(grep -m1 "^${var_name}=" "$APP/.env" 2>/dev/null | cut -d= -f2- || true)"
  fi
  if [ -z "$current" ] && [ "$INTERACTIVE" = "1" ]; then
    printf '  Paste your %s (input hidden): ' "$var_name"
    read -rs current
    echo
  fi
  if [ -z "$current" ]; then
    echo "  ERROR: $var_name is not set." >&2
    echo "  Put it in $APP/.env as a line of the form ${var_name}=<your key> (see INSTALL.md Step 3), then re-run." >&2
    exit 1
  fi
  printf -v "$var_name" '%s' "$current"
}

resolve_key VOYAGE_API_KEY
resolve_key ANTHROPIC_API_KEY

(
  umask 077
  cat > "$APP/.env" <<EOF
VOYAGE_API_KEY=$VOYAGE_API_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
EOF
)
chmod 600 "$APP/.env"
echo "  OK: keys saved to $APP/.env (mode 600)."

# ── Step 5: Vault ────────────────────────────────────────────────────────────

step 5 "Vault"

mkdir -p "$VAULT/memory/facts" "$VAULT/memory/projects" "$VAULT/memory/system" "$VAULT/daily"

for f in SOUL.md USER.md MEMORY.md; do
  if [ ! -f "$VAULT/$f" ]; then
    cp "$APP/templates/$f" "$VAULT/$f"
  fi
done

if [ ! -d "$VAULT/.git" ]; then
  git -C "$VAULT" init -q
fi

cat > "$VAULT/.gitignore" <<'EOF'
.chroma/
*.log
.last_reconcile
.DS_Store
EOF

if [ ! -f "$APP/brain_config.json" ]; then
  cp "$APP/brain_config.example.json" "$APP/brain_config.json"
  echo "  Created brain_config.json from the example."
fi
# Always sync the install-determined fields (paths + launchd label) so the
# config file, not this script's env, is the single source of truth.
"$APP/.venv/bin/python" - "$APP/brain_config.json" "$APP" "$VAULT" "$LABEL" <<'PYEOF'
import json
import sys

cfg_path, app_dir, vault_dir, label = sys.argv[1:5]
with open(cfg_path) as f:
    cfg = json.load(f)
cfg["app_dir"] = app_dir
cfg["vault_dir"] = vault_dir
cfg["python"] = app_dir + "/.venv/bin/python"
cfg["launchd_label"] = label
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
PYEOF
echo "  OK: brain_config.json paths and launchd label are current."

echo "  OK: vault at $VAULT (own git repo, no remote)."

# ── Step 6: launchd ──────────────────────────────────────────────────────────

step 6 "Background watcher (launchd)"

PLIST_SRC="$APP/launchd/com.secondbrain.watcher.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
mkdir -p "$HOME/Library/LaunchAgents"

PLIST_CONTENT="$(cat "$PLIST_SRC")"
PLIST_CONTENT="${PLIST_CONTENT//__LABEL__/$LABEL}"
PLIST_CONTENT="${PLIST_CONTENT//__APP__/$APP}"
PLIST_CONTENT="${PLIST_CONTENT//__PYTHON__/$APP/.venv/bin/python}"
PLIST_CONTENT="${PLIST_CONTENT//__LOG__/$VAULT/brain_watcher.log}"
printf '%s\n' "$PLIST_CONTENT" > "$PLIST_DST"
chmod 644 "$PLIST_DST"

set +e
launchctl bootout "gui/$UID/${LABEL}" >/dev/null 2>&1
BOOT_OUT="$(launchctl bootstrap "gui/$UID" "$PLIST_DST" 2>&1)"
BOOT_STATUS=$?
if [ "$BOOT_STATUS" -ne 0 ]; then
  # launchctl bootstrap can return "5: Input/output error" transiently right
  # after a bootout; a second attempt one second later normally succeeds.
  sleep 1
  BOOT_OUT="$(launchctl bootstrap "gui/$UID" "$PLIST_DST" 2>&1)"
  BOOT_STATUS=$?
fi
set -e
if [ "$BOOT_STATUS" -ne 0 ]; then
  if launchctl print "gui/$UID/${LABEL}" >/dev/null 2>&1; then
    echo "  OK: watcher is loaded (bootstrap said: $BOOT_OUT)."
  else
    echo "  WARNING: launchctl bootstrap failed twice: $BOOT_OUT" >&2
    echo "  Run: launchctl bootstrap gui/$UID \"$PLIST_DST\"   (see INSTALL.md failure branches)" >&2
  fi
else
  echo "  OK: watcher loaded ($PLIST_DST)."
fi

# ── Step 7: MCP registration ────────────────────────────────────────────────

if [ "$SKIP_MCP" = "1" ]; then
  step 7 "MCP server registration (skipped: --skip-mcp)"
else
  step 7 "MCP server registration"
  claude mcp remove claude-brain --scope user >/dev/null 2>&1 || true
  claude mcp add --scope user claude-brain -- "$APP/.venv/bin/python" "$APP/scripts/brain_mcp.py"
  echo "  OK: claude-brain registered (scope: user)."
fi

# ── Step 8: Hooks ────────────────────────────────────────────────────────────

if [ "$SKIP_HOOKS" = "1" ]; then
  step 8 "Claude Code hooks (skipped: --skip-hooks)"
else
  step 8 "Claude Code hooks"
  "$APP/.venv/bin/python" "$APP/scripts/install_hooks.py"
  echo "  OK: hooks installed into ~/.claude/settings.json (backed up first)."
fi

# ── Step 9: Initial index ───────────────────────────────────────────────────

if [ "$SKIP_INDEX" = "1" ]; then
  step 9 "Initial vector index (skipped: --skip-index)"
else
  step 9 "Initial vector index"
  (
    set -a
    # shellcheck disable=SC1091
    [ -f "$APP/.env" ] && . "$APP/.env"
    set +a
    "$APP/.venv/bin/python" "$APP/scripts/build_index.py"
  )
  echo "  OK: initial index built."
fi

# ── Step 10: Doctor ──────────────────────────────────────────────────────────

step 10 "Health check"
set +e
"$APP/.venv/bin/python" "$APP/scripts/doctor.py"
DOCTOR_STATUS=$?
set -e

echo
echo "================================================="
if [ "$DOCTOR_STATUS" -eq 0 ]; then
  echo "  Setup complete — all checks green."
else
  echo "  Setup finished with problems — see the red checks above."
fi
echo "================================================="
echo
echo "Next steps:"
echo "  1. Fully quit and reopen Claude Code (Cmd+Q, then relaunch) so it picks up"
echo "     the new MCP server and hooks."
echo "  2. In a new session, run /mcp — you should see 'claude-brain' with 5 tools."
echo "  3. Vault:   $VAULT"
echo "  4. Log:     $VAULT/brain_watcher.log"
echo "  5. Re-run this script any time — it's safe (idempotent)."

exit "$DOCTOR_STATUS"
