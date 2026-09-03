# INSTALL.md — runbook

macOS only. On Windows, use [INSTALL-windows.md](INSTALL-windows.md) instead.

This is the ordered list of steps Claude executes to install Second Brain
for a non-technical user. Each step has: the exact command, what success
looks like, the doctor check that proves it, and what to do if it fails.
Run `scripts/doctor.py` after every step and do not move on while it shows
red — match the failure against the branches below first.

## Preconditions

- macOS. `setup.sh` refuses to run on anything else.
- Claude Code installed and this session is running inside it.
- The user has (or is about to get) a Voyage AI key and an Anthropic key —
  see README.md § "Get your two keys" and open both URLs for them with
  `open https://www.voyageai.com/` / `open https://console.anthropic.com/`
  rather than asking them to type the address.

---

## Step 1 — Clone the repo

```
git clone https://github.com/Corcogg/SecondBrainSetup.git ~/SecondBrain/app
```

**Expected output:** `Cloning into '/Users/<user>/SecondBrain/app'...` ending
in a normal git summary line, no error.

**Doctor check:** N/A yet — nothing to check until setup runs.

**If it fails:**
- `fatal: destination path ... already exists and is not an empty directory`
  — a previous install is already there. Run `git -C ~/SecondBrain/app pull`
  instead (this is the update path — see the last section below).
- `git: command not found` — install the Xcode Command Line Tools:
  `xcode-select --install`, wait for it to finish, then retry.

---

## Step 2 — Get the two keys

Point the user at README.md § "Get your two keys". Open both signup pages
for them:

```
open https://www.voyageai.com/
open https://console.anthropic.com/
```

Tell the user: "Copy each key when you create it. In the next step I'll open
a small text file for you to paste them into — please don't paste them into
this chat."

---

## Step 3 — Put the keys in the env file (keys never enter chat)

The keys must not pass through this conversation, a command line, or shell
history. The user pastes them into a file that only they can read; `setup.sh`
reads that file.

1. Create the file with placeholders and owner-only permissions, then open it
   in TextEdit:

```
mkdir -p ~/SecondBrain/app
( umask 077; printf 'VOYAGE_API_KEY=\nANTHROPIC_API_KEY=\n' > ~/SecondBrain/app/.env )
chmod 600 ~/SecondBrain/app/.env
open -e ~/SecondBrain/app/.env
```

2. Tell the user exactly this: "A text file just opened. Paste your Voyage
   key right after `VOYAGE_API_KEY=` on the first line, and your Anthropic
   key right after `ANTHROPIC_API_KEY=` on the second line. No spaces, no
   quotes. Then press Cmd+S to save and close the window. Tell me when
   you're done."

3. Verify without reading the values — only that both lines have something
   after the `=`:

```
awk -F= '/^(VOYAGE|ANTHROPIC)_API_KEY=/ { printf "%s: %d chars\n", $1, length($2) }' ~/SecondBrain/app/.env
```

**Expected output:** two lines, each with a non-zero character count
(Voyage keys are roughly 40–50 characters, Anthropic keys roughly 100+).

**If a count is 0:** the paste didn't take. Re-open the file with
`open -e ~/SecondBrain/app/.env` and ask them to try again. Never `cat` the
file and never ask the user to paste a key into chat.

**If a count looks far too long or the file has extra lines:** the user may
have pasted with a trailing newline or twice. Re-create the file with the
`printf` command above and repeat.

---

## Step 4 — Run setup.sh

```
~/SecondBrain/app/setup.sh --non-interactive
```

`setup.sh` reads the keys from `.env`; nothing needs to be passed on the
command line.

**Expected output:** ten `[n/10] ...` lines, each followed by a one-line
result, ending with `Setup complete — all checks green.` and a doctor
report with no red lines.

**Doctor check:** the script's own Step 10 output — `doctor.py` exits 0.

**If it fails**, match the specific failure:

### uv install blocked (corporate network / curl fails)
Symptom: Step 2 of setup.sh errors on the `curl -LsSf https://astral.sh/uv/install.sh | sh` line.
Fix: ask the user if they have Homebrew (`brew --version`); if so run
`brew install uv` yourself, then re-run `setup.sh` (it detects uv on PATH
and skips its own install).

### `claude` not on PATH
Symptom: Step 1 preflight in setup.sh errors "the 'claude' command is not
on PATH." This happens when Claude Code was installed via the desktop app
only. Tell the user: open the Claude Code desktop app once, check its
Settings for an "Install CLI" or "Shell command" option, then retry. As a
last resort, re-run with `--skip-mcp --skip-hooks` and finish those two
steps manually later once `claude` is on PATH.

### launchctl "Input/output error"
Symptom: `launchctl bootstrap` prints `Bootstrap failed: 5: Input/output error`.
This is a transient launchd quirk right after a bootout, not a real failure.
setup.sh already retries once after one second and then checks whether the job
is loaded. If it still warns, run the bootstrap once more yourself:

```
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.secondbrain.watcher.plist
launchctl print gui/$UID/com.secondbrain.watcher | head -3
```

### Notification permission dialog
The first time the watcher runs, macOS may show *"Terminal" (or "python")
wants to send you notifications. Allow / Don't Allow.* Tell the user this
is just so the watcher can tell them when it finishes tagging a note, and
either answer is fine — nothing breaks if they click **Don't Allow**.

### Voyage 401 (unauthorized)
Symptom: setup.sh Step 9 (`build_index.py`) errors with a 401 / "Provided API
key is invalid", or `~/SecondBrain/vault/brain_watcher.log` shows the same.
(`doctor.py` makes no network calls, so it only confirms the key is present,
not that it works.) The pasted key is wrong or has a typo. Re-open the env
file with `open -e ~/SecondBrain/app/.env`, ask the user to replace the
Voyage line's value from https://www.voyageai.com/ (API Keys page), save,
then re-run `setup.sh --non-interactive`.

### Anthropic 401 / billing not enabled / credit required
Symptom: `~/SecondBrain/vault/brain_watcher.log` shows a 401, or an error
mentioning "credit balance" or "billing", after the first note is saved.
(The Anthropic key is used only by the watcher when it tags a note, so a bad
key shows up at the recall demo, not during setup.) Ask the user to check
https://console.anthropic.com/settings/billing has a payment method and
some credit, or fix the key via `open -e ~/SecondBrain/app/.env`, then
restart the watcher: `launchctl kickstart -k gui/$UID/com.secondbrain.watcher`.

### Vault under Desktop/Documents/Downloads
Symptom: setup.sh's own preflight (Step 1) refuses to run and explains
this. If this happens it means the repo was cloned to the wrong place in
Step 1 — re-clone straight to `~/SecondBrain/app` as shown above, don't try
to relocate a Desktop clone by hand.

### Python wheel build failure on Intel Macs
Symptom: `uv pip install` fails trying to build a wheel from source
(usually `chromadb` or one of its native deps) on an Intel (non-Apple
Silicon) Mac. This is not a Rosetta problem — do not install Rosetta to fix
it. It's almost always a transient index/network issue or a missing system
header. Retry the same `setup.sh` command once (it's idempotent — it will
pick up where it left off); if it fails a second time with the same error,
report the exact error text to the user rather than guessing further.

### doctor red on hooks (settings.json malformed)
Symptom: `doctor.py` reports the hooks check red, mentioning
`~/.claude/settings.json`. `install_hooks.py` always backs up this file
before editing as `settings.json.bak-<timestamp>` in the same directory.
Restore it and retry:

```
ls -t ~/.claude/settings.json.bak-* | head -1
cp "<that file>" ~/.claude/settings.json
~/SecondBrain/app/.venv/bin/python ~/SecondBrain/app/scripts/install_hooks.py
```

---

## Step 5 — Interview

Follow `templates/interview.md` exactly: one question at a time, offer the
stated default, show the three finished files (SOUL.md, USER.md, MEMORY.md)
for approval before writing. On approval:

1. Write the three files to `~/SecondBrain/vault/`.
2. Update `cwd_domain_map` in `~/SecondBrain/app/brain_config.json` using
   Python's `json` module (never sed/regex on this file).

**Doctor check:** re-run `doctor.py` — it should still be all green (the
interview doesn't change anything doctor checks other than file presence,
which was already green).

---

## Step 6 — Restart Claude Code

Tell the user to fully quit Claude Code (**Cmd+Q** — closing the window is
not enough) and reopen it. Explain why in one sentence: the new MCP server
and hooks are only loaded when Claude Code starts up.

---

## Step 7 — Verify, in the new session

Do these checks after the restart, in a **new** Claude Code session:

1. Run `/mcp`. **Expected:** `claude-brain` is listed with 5 tools
   (`brain_query`, `brain_remember`, `get_note`, `brain_status`,
   `list_domains`).
2. Look at the start of this session's context — the SessionStart hook
   should have injected the user's SOUL.md content. **Expected:** you can
   see the personality/rules text the interview just wrote.
3. Call `brain_remember` with the "one thing to remember" answer from
   interview Q8 (title it something short and descriptive; domain
   `general`).
4. Open **another** new Claude Code session and ask a question that should
   surface that fact (e.g. "what should you remember about me?"). Confirm
   `brain_query` retrieves it correctly.

If any of these fail, run `doctor.py` and go back to the matching failure
branch above — don't debug blind.

---

## Step 8 — Day-to-day briefing

Read this to the user once everything is verified:

> "You're set up. Just talk to me normally — tell me things worth
> remembering and I'll save them, ask me about things you've told me
> before and I'll look them up. If you ever want to write a note directly,
> drop a `.md` file into `~/SecondBrain/vault/memory` and I'll pick it up
> within a few seconds. If something ever seems off, just say 'run the
> brain doctor and fix what's red.'"

---

## Updating later

```
git -C ~/SecondBrain/app pull && ~/SecondBrain/app/setup.sh --non-interactive
```

Notes, keys, and the vault are never touched by this — `setup.sh` only
writes vault files that don't already exist, and never overwrites `.env`
without a value being supplied.
