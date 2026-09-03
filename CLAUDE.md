# Second Brain — agent brief

You are installing this for a non-technical person. They may never have
opened Terminal before today. Assume nothing is obvious to them.

- **Run every command yourself.** Never tell the user to type or paste a
  command — you have Bash. The only thing the user ever does by hand is
  paste their two API keys into a text file you open for them (Step 3).
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
- **API keys never enter this conversation.** Do not ask the user to paste
  a key into chat, and never put one on a command line. INSTALL.md Step 3
  has you open `~/SecondBrain/app/.env` in TextEdit so the user pastes the
  keys there themselves; you verify only that the lines are non-empty
  (character counts), never their contents. Never `cat` that file. If the
  user pastes a key into chat anyway, tell them to revoke it at the
  provider and create a new one, then continue via the file.
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
