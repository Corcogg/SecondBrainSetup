#!/usr/bin/env bash
# Install the bundled Claude Code skills (plan, delegate, thinking-model-router)
# into ~/.claude/skills. Existing copies are moved to a timestamped backup
# folder first, never deleted. Re-runnable.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BACKUP="$DEST/_backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"
for skill in plan delegate thinking-model-router; do
  if [ -e "$DEST/$skill" ]; then
    mkdir -p "$BACKUP"
    mv "$DEST/$skill" "$BACKUP/$skill"
    echo "  backed up existing $skill -> $BACKUP/$skill"
  fi
  cp -R "$SRC/$skill" "$DEST/$skill"
  echo "  installed $skill"
done
echo "Done. Restart Claude Code (/exit, then claude) to load the skills."
