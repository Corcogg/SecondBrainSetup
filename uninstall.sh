#!/usr/bin/env bash
# uninstall.sh — removes the launchd watcher, the MCP registration, and the
# Claude Code hooks. Never touches the vault (your notes) and, by default,
# never touches .env (your keys). Safe to re-run.
#
# Flags:
#   --purge   also delete .venv and .env from the app folder (never the vault)
#
# Env overrides:
#   SECONDBRAIN_ROOT      install root (default: ~/SecondBrain)
#   BRAIN_LAUNCHD_LABEL   launchd label (default: com.secondbrain.watcher)

set -euo pipefail

PURGE=0
for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: uninstall.sh [--purge]
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

SECONDBRAIN_ROOT="${SECONDBRAIN_ROOT:-$HOME/SecondBrain}"
LABEL="${BRAIN_LAUNCHD_LABEL:-com.secondbrain.watcher}"
APP="$SECONDBRAIN_ROOT/app"
VAULT="$SECONDBRAIN_ROOT/vault"

echo "================================================="
echo "  Second Brain — Uninstall"
echo "================================================="

# ── Watcher ───────────────────────────────────────────────────────────────

PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
echo "[1/4] Stopping background watcher..."
launchctl bootout "gui/$UID/${LABEL}" >/dev/null 2>&1 || true
if [ -f "$PLIST_DST" ]; then
  rm -f "$PLIST_DST"
  echo "  Removed $PLIST_DST"
else
  echo "  Nothing to remove ($PLIST_DST not found)."
fi

# ── MCP ───────────────────────────────────────────────────────────────────

echo "[2/4] Removing MCP registration..."
if command -v claude >/dev/null 2>&1; then
  claude mcp remove claude-brain --scope user >/dev/null 2>&1 || true
  echo "  Removed 'claude-brain' from Claude Code (if it was registered)."
else
  echo "  'claude' not on PATH — skipping (nothing registered to remove)."
fi

# ── Hooks ─────────────────────────────────────────────────────────────────

echo "[3/4] Removing Claude Code hooks..."
if [ -x "$APP/.venv/bin/python" ] && [ -f "$APP/scripts/install_hooks.py" ]; then
  "$APP/.venv/bin/python" "$APP/scripts/install_hooks.py" --uninstall
  echo "  Hooks removed from ~/.claude/settings.json (backed up first)."
else
  echo "  App venv/scripts not found — skipping (nothing to uninstall)."
fi

# ── Purge (optional) ─────────────────────────────────────────────────────

echo "[4/4] App files..."
if [ "$PURGE" = "1" ]; then
  rm -rf "$APP/.venv"
  rm -f "$APP/.env"
  echo "  --purge: removed $APP/.venv and $APP/.env."
else
  echo "  Left $APP/.venv and $APP/.env in place. Re-run with --purge to remove them."
fi

echo
echo "================================================="
echo "  Uninstall complete."
echo "================================================="
echo
echo "Your notes were NOT touched. They still live at:"
echo "  $VAULT"
echo
echo "To delete them permanently (this cannot be undone):"
echo "  rm -rf \"$VAULT\""
echo
echo "To remove the app folder entirely:"
echo "  rm -rf \"$APP\""
