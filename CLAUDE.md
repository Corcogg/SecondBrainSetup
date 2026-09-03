# Second Brain — agent brief

You are installing this for a non-technical person. They may never have
opened Terminal before today. Assume nothing is obvious to them.

- **Run every command yourself.** Never tell the user to type or paste a
  command — you have Bash. The only things the user ever pastes are their
  two API keys, and only when a step explicitly asks for them.
- Follow **INSTALL.md** as the ordered runbook. It has the exact commands,
  expected output, and failure branches. Don't improvise steps or reorder
  them.
- **Run `scripts/doctor.py` after every install step** and stop on any red
  result. Match the red check against INSTALL.md's failure branches before
  trying anything else — don't guess at a fix.
- **Before any step that triggers a macOS dialog** (notification
  permission, launchd's first run, the uv installer, a Terminal
  disk-access prompt) tell the user in advance exactly what the dialog will
  say and what to click. Surprise system dialogs are the #1 way to lose a
  non-technical user.
- **Ask before editing anything under `~/.claude/`.** That's the user's
  existing Claude Code configuration; `install_hooks.py` backs it up first,
  but confirm with the user before running it.
- **Never display or repeat the user's API keys in chat**, in full or in
  part — not to confirm you got it right, not in a summary, not in a log
  excerpt you show them. Ask for keys only at the step that needs them, and
  pass them as env vars for that one command (see INSTALL.md) so they never
  land in chat history or shell history.
- **If the cloned repo is under `~/Desktop`, `~/Documents`, or
  `~/Downloads`**, move it before doing anything else — `setup.sh` will
  refuse to run there (macOS TCC silently blocks the background watcher
  from reading files in those folders). INSTALL.md has the exact `mv`.
- When setup finishes, run the **interview** (`templates/interview.md`) —
  one question at a time, defaults offered, show the finished files for
  approval before writing them.
- Finish with the **recall demo**: save the interview's "one thing to
  remember" answer, start a fresh Claude Code session, and show the user it
  comes back. That's the proof the system works.

Full runbook: **INSTALL.md**. Human-facing overview: **README.md**.
