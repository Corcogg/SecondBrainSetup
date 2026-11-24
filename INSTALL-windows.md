# INSTALL-windows.md — runbook

Windows only. On macOS, use [INSTALL.md](INSTALL.md) instead.

This is the ordered list of steps Claude executes to install Second Brain
for a non-technical user, run entirely through **PowerShell** (not Bash,
even if Git Bash is also installed). Each step has: the exact command, what
success looks like, the doctor check that proves it, and what to do if it
fails. Run `scripts/doctor.py` after every step and do not move on while it
shows red — match the failure against the branches below first.

## Preconditions

- Windows 10 or 11, 64-bit (x64). `setup.ps1` refuses to run on ARM64 —
  `chromadb` has no `win_arm64` wheel.
- [Claude Desktop](https://claude.com/download) installed.
- The Claude Code CLI installed. If `claude` isn't recognized in PowerShell,
  install it yourself:
  ```
  irm https://claude.ai/install.ps1 | iex
  ```
- Git for Windows installed. If `git` isn't recognized:
  ```
  winget install Git.Git
  ```
  (may require closing and reopening PowerShell afterward so PATH updates)
- The user has (or is about to get) a Voyage AI key and an Anthropic key —
  see README.md § "Get your two keys" and open both URLs for them with
  `Start-Process`:
  ```
  Start-Process "https://www.voyageai.com/"
  Start-Process "https://console.anthropic.com/"
  ```
  rather than asking them to type the address.

---

## Step 1 — Clone the repo

```
git clone https://github.com/Corcogg/SecondBrainSetup.git "$env:USERPROFILE\SecondBrain\app"
```

**Expected output:** `Cloning into 'C:\Users\<user>\SecondBrain\app'...`
ending in a normal git summary line, no error.

**Doctor check:** N/A yet — nothing to check until setup runs.

**If it fails:**
- `fatal: destination path ... already exists and is not an empty directory`
  — a previous install is already there. Run
  `git -C "$env:USERPROFILE\SecondBrain\app" pull` instead (this is the
  update path — see the last section below).
- `git: command not found` / `'git' is not recognized` — install Git for
  Windows: `winget install Git.Git`, close and reopen PowerShell, then
  retry.

---

## Step 2 — Get the two keys

Point the user at README.md § "Get your two keys". Open both signup pages
for them:

```
Start-Process "https://www.voyageai.com/"
Start-Process "https://console.anthropic.com/"
```

Tell the user: "Copy each key when you create it. In the next step I'll open
a small text file for you to paste them into — please don't paste them into
this chat."

---

## Step 3 — Put the keys in the env file (keys never enter chat)

The keys must not pass through this conversation, a command line, or
PowerShell history. The user pastes them into a file that only they can
read; `setup.ps1` reads that file.

1. Create the file with placeholders and lock it to the current user, then
   open it in Notepad:

```
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SecondBrain\app" | Out-Null
$envFile = "$env:USERPROFILE\SecondBrain\app\.env"
[System.IO.File]::WriteAllText($envFile, "VOYAGE_API_KEY=`r`nANTHROPIC_API_KEY=`r`n", (New-Object System.Text.UTF8Encoding($false)))
icacls $envFile /inheritance:r /grant:r "$env:USERDOMAIN\$env:USERNAME:(R,W)"
notepad $envFile
```

2. Tell the user exactly this: "A text file just opened. Paste your Voyage
   key right after `VOYAGE_API_KEY=` on the first line, and your Anthropic
   key right after `ANTHROPIC_API_KEY=` on the second line. No spaces, no
   quotes. Then press Ctrl+S to save, and close the window. Tell me when
   you're done."

3. Verify without reading the values — only that both lines have something
   after the `=`, printing character counts only:

```
Get-Content "$env:USERPROFILE\SecondBrain\app\.env" | ForEach-Object {
  if ($_ -match '^(VOYAGE|ANTHROPIC)_API_KEY=(.*)$') {
    "$($Matches[1]): $($Matches[2].Length) chars"
  }
}
```

**Expected output:** two lines, each with a non-zero character count
(Voyage keys are roughly 40–50 characters, Anthropic keys roughly 100+).

**If a count is 0:** the paste didn't take. Re-open the file with
`notepad "$env:USERPROFILE\SecondBrain\app\.env"` and ask them to try
again. **Never `Get-Content` or `type` the file to view its values**, and
never ask the user to paste a key into chat — the command above prints
lengths only, never the key text.

**If a count looks far too long or the file has extra lines:** the user may
have pasted with a trailing newline or twice. Re-create the file with the
`New-Item`/`WriteAllText` commands above and repeat.

---

## Step 4 — Run setup.ps1

```
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\SecondBrain\app\setup.ps1" -NonInteractive
```

`setup.ps1` reads the keys from `.env`; nothing needs to be passed on the
command line.

**Expected output:** ten `[n/10] ...` lines, each followed by a one-line
result, ending with `Setup complete — all checks green.` and a doctor
report with no red lines.

**Doctor check:** the script's own Step 10 output — `doctor.py` exits 0.

**If it fails**, match the specific failure:

### uv install blocked (corporate network / Defender)
Symptom: Step 2 of setup.ps1 errors fetching or running
`https://astral.sh/uv/install.ps1`, or Windows Defender SmartScreen shows
*"Windows protected your PC"* over the download. Tell the user to click
**More info → Run anyway** if they recognize and trust the source (it's the
official uv installer script from astral.sh); if the network blocks it
outright, ask whether `winget` is available and run
`winget install astral-sh.uv` yourself, then re-run `setup.ps1` (it detects
`uv` on PATH and skips its own install).

### `claude` not on PATH
Symptom: Step 1 preflight in setup.ps1 errors "the 'claude' command is not
on PATH." The native installer sometimes doesn't add
`%USERPROFILE%\.local\bin` to PATH in the current session. setup.ps1
already checks that folder directly (`%USERPROFILE%\.local\bin\claude.exe`)
before giving up. If it's truly missing, tell the user to open the Claude
Desktop app once, or re-run `irm https://claude.ai/install.ps1 | iex`, then
retry. As a last resort, re-run with `-SkipMcp -SkipHooks` and finish those
two steps manually later once `claude` is on PATH.

### Git for Windows missing
Symptom: setup.ps1's own preflight errors "git is required." Run
`winget install Git.Git`, close and reopen PowerShell (so PATH picks up the
new install), then retry.

### PowerShell execution policy error
Symptom: `setup.ps1 : File ... cannot be loaded because running scripts is
disabled on this system.` The `-ExecutionPolicy Bypass` flag on the Step 4
command above should prevent this for that one invocation — if it still
appears (e.g. because a Group Policy pins execution policy machine-wide),
tell the user this is a locked-down machine and ask whether they can run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` themselves, or contact
their IT admin. Never suggest disabling execution policy machine-wide.

### `schtasks` "Access is denied"
Symptom: setup.ps1 Step 6 warns that `schtasks /Create` failed with "Access
is denied." This can happen on a managed/corporate machine where task
creation is restricted, or if a task with the same name exists under a
different user context. Ask the user if this is a work-managed PC (if so,
their IT policy may block it — the rest of setup still completes, just
without the background watcher). Otherwise try running the same
`setup.ps1` command from an elevated PowerShell (right-click PowerShell →
**Run as administrator**) once, then re-run normally.

### Voyage 401 (unauthorized)
Symptom: setup.ps1 Step 9 (`build_index.py`) errors with a 401 / "Provided
API key is invalid", or `%USERPROFILE%\SecondBrain\vault\brain_watcher.log`
shows the same. (`doctor.py` makes no network calls, so it only confirms
the key is present, not that it works.) The pasted key is wrong or has a
typo. Re-open the env file with
`notepad "$env:USERPROFILE\SecondBrain\app\.env"`, ask the user to replace
the Voyage line's value from https://www.voyageai.com/ (API Keys page),
save, then re-run `setup.ps1 -NonInteractive`.

### Anthropic 401 / billing not enabled / credit required
Symptom: `%USERPROFILE%\SecondBrain\vault\brain_watcher.log` shows a 401,
or an error mentioning "credit balance" or "billing", after the first note
is saved. (The Anthropic key is used only by the watcher when it tags a
note, so a bad key shows up at the recall demo, not during setup.) Ask the
user to check https://console.anthropic.com/settings/billing has a payment
method and some credit, or fix the key via
`notepad "$env:USERPROFILE\SecondBrain\app\.env"`, then restart the
watcher:
```
schtasks /End /TN com.secondbrain.watcher
schtasks /Run /TN com.secondbrain.watcher
```
(use the actual task name if `BRAIN_SERVICE_LABEL` was customized).

### doctor red on hooks (settings.json malformed)
Symptom: `doctor.py` reports the hooks check red, mentioning
`%USERPROFILE%\.claude\settings.json`. `install_hooks.py` always backs up
this file before editing as `settings.json.bak-<timestamp>` in the same
directory. Restore it and retry:

```
$bak = Get-ChildItem "$env:USERPROFILE\.claude\settings.json.bak-*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $bak.FullName "$env:USERPROFILE\.claude\settings.json" -Force
& "$env:USERPROFILE\SecondBrain\app\.venv\Scripts\python.exe" "$env:USERPROFILE\SecondBrain\app\scripts\install_hooks.py"
```

### Python wheel build failure
Symptom: `uv pip install` fails trying to build a wheel from source (usually
`chromadb` or one of its native deps). This is almost always a transient
index/network issue. Retry the same `setup.ps1` command once (it's
idempotent — it will pick up where it left off); if it fails a second time
with the same error, report the exact error text to the user rather than
guessing further.

---

## Step 5 — Interview

Follow `templates/interview.md` exactly: one question at a time, offer the
stated default, show the three finished files (SOUL.md, USER.md, MEMORY.md)
for approval before writing. On approval:

1. Write the three files to `%USERPROFILE%\SecondBrain\vault\`.
2. Update `cwd_domain_map` in
   `%USERPROFILE%\SecondBrain\app\brain_config.json` using Python's `json`
   module (never text substitution on this file).

**Doctor check:** re-run `doctor.py` — it should still be all green (the
interview doesn't change anything doctor checks other than file presence,
which was already green).

---

## Step 6 — Restart Claude Code and Claude Desktop

Tell the user to fully quit **both** Claude Desktop and any Claude Code
terminal session (close the tray icon via right-click → Quit, and close the
PowerShell/terminal window — closing just the window is not enough if
Claude Desktop is still running in the tray) and reopen them. Explain why in
one sentence: the new MCP server and hooks are only loaded when Claude Code
starts up.

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
> drop a `.md` file into `%USERPROFILE%\SecondBrain\vault\memory` and I'll
> pick it up within a few seconds. If something ever seems off, just say
> 'run the brain doctor and fix what's red.'"

---

## Updating later

```
git -C "$env:USERPROFILE\SecondBrain\app" pull
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\SecondBrain\app\setup.ps1" -NonInteractive
```

Notes, keys, and the vault are never touched by this — `setup.ps1` only
writes vault files that don't already exist, and never overwrites `.env`
without a value being supplied.
