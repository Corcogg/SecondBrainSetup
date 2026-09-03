# Second Brain — architecture and contracts (2026-09-03)

This doc is the shared brief for anyone (human or agent) working on this repo.
Every load-bearing claim cites a file. If you change a contract below, update this doc in the same change.

## Install layout on the user's machine

```
~/SecondBrain/
├── app/                 # this repo, cloned. Code only. `git pull` here updates code.
│   ├── .venv/           # uv-managed Python 3.11 venv (gitignored)
│   ├── .env             # VOYAGE_API_KEY, ANTHROPIC_API_KEY — mode 600, gitignored, THE ONLY place keys live
│   ├── brain_config.json  # per-user config (gitignored); brain_config.example.json is the template
│   ├── scripts/         # watcher, MCP server, vector module, CLI, doctor, hook installer
│   ├── hooks/           # Claude Code SessionStart / PreCompact / Stop hooks
│   ├── launchd/         # plist template (rendered copy goes to ~/Library/LaunchAgents)
│   └── templates/       # SOUL/USER/MEMORY templates + interview
└── vault/               # the user's notes. Its own `git init`, NO remote. Never touched by app updates.
    ├── SOUL.md USER.md MEMORY.md
    ├── memory/{facts,projects,system}/   # domain folders (see brain_config.domain_dirs)
    ├── daily/           # YYYY-MM-DD.md session logs written by hooks
    ├── .chroma/         # vector store (gitignored in vault)
    ├── brain_watcher.log
    └── .last_reconcile
```

**Why not ~/Desktop:** macOS TCC blocks launchd daemons from reading Desktop/Documents/Downloads
without Full Disk Access, and the failure is silent (the watcher runs but never sees files).
`setup.sh` must refuse to install under those folders.

## Components

| Component | File | Role |
|---|---|---|
| Config loader | `scripts/brain_config.py` | Single source for every path, domain, model id, owner name. Loads `.env`. |
| Vector module | `scripts/brain_vector.py` | Chroma collection, Voyage embed, hybrid dense+BM25 `query_brain`, `format_for_injection` |
| Watcher daemon | `scripts/brain_watcher.py` | watchdog on `vault/memory`; frontmatter + wikilinks via forced tool-use; sole Chroma writer; reconcile every 6h + vault git auto-commit |
| MCP server | `scripts/brain_mcp.py` | `brain_query`, `brain_remember`, `get_note`, `brain_status`, `list_domains`. Never writes Chroma. |
| CLI | `scripts/query_brain.py`, `scripts/build_index.py` | Manual search; initial full index |
| Doctor | `scripts/doctor.py` | Health checklist, `--json` for agents, non-zero exit on any red |
| Hook installer | `scripts/install_hooks.py` | Merges/removes hook entries in `~/.claude/settings.json`, backs up first |
| Hooks | `hooks/session-start-context.py`, `hooks/pre-compact-flush.py`, `hooks/session-end-flush.py` | Inject SOUL/USER/MEMORY/daily logs + vault query at start; flush transcript excerpts to `vault/daily/` |
| Installer | `setup.sh`, `uninstall.sh` | Idempotent install/uninstall; Claude-drivable with `--non-interactive` |
| Test suite | `scripts/brain_test.py` | End-to-end checks against a live watcher |

## Config contract (`brain_config.json`)

Shape is `brain_config.example.json`. Resolution: `$BRAIN_CONFIG` env var → `<repo root>/brain_config.json`.
All `~` are expanded. Every script and hook imports `brain_config` and uses ONLY these values — no
`Path.home() / "..."` literals, no `/opt/homebrew` literals, no hardcoded domain lists, no owner name.

- `domains`: allowed domain values. Drives the watcher's classifier enum, `brain_mcp.ALLOWED_DOMAINS`,
  `query_brain --domain` choices.
- `domain_dirs`: domain → subfolder under `vault/memory/` used by `brain_remember`.
- `domain_descriptions` (optional): domain → one-line meaning, shown to the classifier so it picks the right domain.
- `launchd_label`: written by `setup.sh` (from `BRAIN_LAUNCHD_LABEL`, default `com.secondbrain.watcher`); `doctor.py` and `brain_test.py` read it from here.
- `cwd_domain_map`: list of `{"fragment": str, "domain": str, "n": int}`; SessionStart hook matches
  `fragment` against the cwd to pick a domain filter. Written by the install interview.
- `models.embed_dim` must match `models.embed`; watcher refuses to start on mismatch with the stored collection.

## Secrets contract (non-negotiable)

- Keys live ONLY in `~/SecondBrain/app/.env` (mode 600). `brain_config.py` loads it; `.env` values win over inherited env.
- The launchd plist sources `.env` via `bash -c` at launch; it never contains a key.
- `claude mcp add` is called WITHOUT `-e`/`--env`. The server reads `.env` itself.
- Nothing under `~/.claude/` ever receives a key.
- `.env` is gitignored; `setup.sh` must never `git add` it; docs must never show a real key.

## Interfaces the installer relies on

- `scripts/doctor.py [--json] [--config PATH]` → exit 0 iff all checks green.
- `scripts/install_hooks.py [--uninstall] [--config PATH]` → idempotent; backs up settings.json to `settings.json.bak-<timestamp>`.
- `scripts/build_index.py` → embeds every note under `vault/memory`.
- `scripts/brain_watcher.py [--verbose]` → daemon entrypoint.
- `scripts/brain_mcp.py` → stdio MCP entrypoint. Registered as `claude mcp add --scope user claude-brain -- <venv python> <app>/scripts/brain_mcp.py`.
- Hooks are registered with the venv python and absolute paths, e.g. `<venv python> <app>/hooks/session-start-context.py`.

## Runtime pins (`requirements.txt`)
anthropic 0.86.0 · voyageai 0.3.7 · chromadb 1.5.7 · rank-bm25 0.2.2 · watchdog 6.0.0 · mcp 1.27.0 — the versions verified working together on the reference machine.

---

# Windows port — contract (2026-09-03, branch `windows-port`)

Same repo, platform-aware. The Python is shared; only the machine-facing seams differ.
Every rule below is binding for the port. If you must deviate, report it — do not silently change the contract.

## Install layout on Windows

```
%USERPROFILE%\SecondBrain\
├── app\                  # this repo, cloned. Code only.
│   ├── .venv\            # uv-managed Python 3.11 venv; interpreter at .venv\Scripts\python.exe, windowless twin at .venv\Scripts\pythonw.exe
│   ├── .env              # VOYAGE_API_KEY, ANTHROPIC_API_KEY — ACL restricted to the owning user (see Secrets), gitignored, THE ONLY place keys live
│   ├── brain_config.json
│   ├── scripts\ hooks\ templates\
│   └── windows\          # watcher-task.xml.template (rendered copy is registered with schtasks, not kept on disk)
└── vault\                # identical layout to macOS
```

No TCC on Windows, so there is no Desktop/Documents/Downloads guard. `setup.ps1` still requires the repo to be at `$SECONDBRAIN_ROOT\app`, same as `setup.sh`.

## Platform shim — `scripts/brain_platform.py`

The ONLY module allowed to branch on OS. Everything else (`brain_watcher.py`, `brain_mcp.py`, `doctor.py`, `install_hooks.py`, `brain_test.py`) calls these and never imports `subprocess` to reach `osascript`, `pgrep`, `launchctl`, `schtasks`, `tasklist`, or `icacls` directly.

```python
IS_WINDOWS: bool                                   # sys.platform == "win32"
def notify(title: str, message: str) -> None       # macOS: today's osascript code moved verbatim; Windows: no-op (v1 drops toasts). Honors brain_config.NOTIFICATIONS.
def watcher_pids(script_path: Path) -> list[str]   # macOS: pgrep -f <script_path>; Windows: match "brain_watcher.py" in process command lines (tasklist/Get-CimInstance). Empty list = not running. Never raises.
def secrets_file_locked(path: Path) -> tuple[bool, str]   # macOS: stat mode == 0o600; Windows: icacls shows the owning user as the ONLY principal (no BUILTIN\Users, Authenticated Users, Everyone, inherited ACEs). Returns (ok, detail); detail never contains file contents.
def service_loaded(label: str) -> tuple[bool, str]        # macOS: launchctl print gui/<uid>/<label> rc==0; Windows: schtasks /Query /TN <label> /FO CSV /V — ok iff task exists AND state is "Running" or "Ready". detail = state string.
```

`os.getuid()` does not exist on Windows; it may appear only inside the macOS branch of this module.

## Config contract changes

- `launchd_label` is renamed **`service_label`**. `brain_config.py` reads `service_label`, falling back to `launchd_label`, and exports `SERVICE_LABEL` (keep `LAUNCHD_LABEL` as an alias for one release). `brain_config.example.json` uses `service_label`. Default label is `com.secondbrain.watcher` on both platforms (schtasks accepts dotted names).
- `python` is written by the installer: `<app>/.venv/bin/python` on macOS, `<app>\.venv\Scripts\python.exe` on Windows. Both installers sync `app_dir`, `vault_dir`, `python`, `service_label` into `brain_config.json` via a Python `json` round-trip (never text substitution).
- Installer env override is `BRAIN_SERVICE_LABEL`; `setup.sh`/`uninstall.sh` also accept the old `BRAIN_LAUNCHD_LABEL`.

## Hooks on Windows — exec form

Claude Code on Windows runs shell-form hook commands through Git Bash when Git for Windows is installed and through PowerShell otherwise. To be independent of that, **Windows installs use exec form**:

```json
{"type": "command", "command": "C:\\Users\\j\\SecondBrain\\app\\.venv\\Scripts\\python.exe",
 "args": ["C:\\Users\\j\\SecondBrain\\app\\hooks\\session-start-context.py"]}
```

macOS keeps today's shell-form string (`'<python>' '<hook>'`) unchanged. `install_hooks.py` install/uninstall and `doctor.check_hooks_installed` must recognise BOTH forms: an entry belongs to this app if `<app>/hooks/` appears in `command` OR in any element of `args`. Use `os.path.normcase` on both sides when comparing paths so `C:\Users\J` and `c:\users\j` match.

## Watcher supervisor on Windows — Task Scheduler

- Template: `windows/watcher-task.xml.template`, placeholders `__LABEL__`, `__PYTHONW__`, `__APP__`, `__LOG__`, `__USERID__`.
- Registered with `schtasks /Create /F /TN <label> /XML <rendered>`; rendered file written to `%TEMP%` as UTF-16LE (the encoding schtasks' importer expects; the checked-in template stays UTF-8 and `setup.ps1` rewrites the declaration) and deleted after registration. Values are XML-escaped and substituted literally, never via regex. Run as the current user, interactive logon token (`LogonType InteractiveToken`), so no password is stored.
- Trigger: `LogonTrigger` for the current user. Settings: `RestartOnFailure` interval `PT1M` count `3`, `ExecutionTimeLimit PT0S`, `DisallowStartIfOnBatteries false`, `StopIfGoingOnBatteries false`, `StartWhenAvailable true`, `Hidden true`, `MultipleInstancesPolicy IgnoreNew`.
- Action: `__PYTHONW__` with arguments `-u "__APP__\scripts\brain_watcher.py"`, working directory `__APP__`. Environment: the task XML carries NO environment block; the watcher loads `.env` itself via `brain_config` and finds its config at `<repo root>/brain_config.json` by default. (`BRAIN_CONFIG` is therefore unnecessary on Windows.)
- Logging: `pythonw.exe` has no console, so the watcher's `RotatingFileHandler` at `<vault>\brain_watcher.log` is the only sink. This is already the case on macOS by design (see the comment at `scripts/brain_watcher.py` ~line 70).
- `setup.ps1` runs `schtasks /Run /TN <label>` immediately after creating the task so the first install does not wait for a logon.

## Secrets contract on Windows (non-negotiable, same spirit as macOS)

- Keys live ONLY in `%USERPROFILE%\SecondBrain\app\.env`. `setup.ps1` locks it with `icacls <file> /inheritance:r /grant:r "<user>:(R,W)"` immediately after creating it.
- The task XML never contains a key. `claude mcp add` is called WITHOUT `-e`/`--env`. Nothing under `%USERPROFILE%\.claude\` ever receives a key.
- The runbook has Claude open `.env` with `notepad` for the user to paste; verification prints character counts only (`Select-String` / a tiny Python one-liner), never values. Never `Get-Content` / `type` that file.
- CI uses a stub `.env` with obviously fake values (`VOYAGE_API_KEY=ci-stub`, `ANTHROPIC_API_KEY=ci-stub`) and runs with `-SkipIndex`, so no real key ever reaches GitHub.

## Installer parity — `setup.ps1` / `uninstall.ps1`

Same ten steps and same flag semantics as `setup.sh`, PowerShell-style switches: `-NonInteractive`, `-SkipMcp`, `-SkipHooks`, `-SkipIndex`; env overrides `SECONDBRAIN_ROOT`, `BRAIN_SERVICE_LABEL`. Idempotent. Exit code = doctor's exit code. Specific Windows preflight rules:

- Refuse non-x64 (`$env:PROCESSOR_ARCHITECTURE -ne 'AMD64'`): chromadb 1.5.7 has no win_arm64 wheel.
- `git` must be on PATH (Git for Windows). Failure message names `winget install Git.Git`.
- `claude` resolution: `Get-Command claude` first, then `$env:USERPROFILE\.local\bin\claude.exe` (the native installer is known not to add that dir to PATH). Use the resolved absolute path for every later `claude` call in the run.
- uv resolution: `Get-Command uv`, then `$env:USERPROFILE\.local\bin\uv.exe`; install with `irm https://astral.sh/uv/install.ps1 | iex` only if both miss. Use the absolute path afterwards (PATH updates don't reach the current shell).
- Set `$env:PYTHONUTF8 = '1'` and `[Console]::OutputEncoding = [Text.Encoding]::UTF8` at the top so doctor's ✅/❌ render.
- `-NonInteractive` (or a non-interactive host) never prompts; a missing key in `.env` is a hard error with the runbook step named.

## CI — `.github/workflows/install-smoke.yml`

Three jobs. `unit` (ubuntu-latest): `py_compile` of every script and hook, then `python -m unittest discover -s scripts -p 'test_*.py'` — the pure-logic parsers already simulate Windows path semantics, so this runs once, not per OS. `windows` (windows-latest): copy the checkout to `%USERPROFILE%\SecondBrain\app` (the installer requires that path), write a stub `.env`, run `setup.ps1 -NonInteractive -SkipMcp -SkipHooks -SkipIndex`, assert the task is registered, wait for the watcher's startup line in `brain_watcher.log` (falling back to starting the watcher directly if Task Scheduler will not start it in the runner's non-interactive session, with a workflow warning), run `doctor.py --json` through `scripts/ci_assert_doctor.py` (every check must be ok except `MCP registered` and `hooks installed`, which need Claude Code), then `uninstall.ps1 -Purge` and assert the task is gone. `macos` (macos-latest): the same sequence with `BRAIN_SERVICE_LABEL=com.secondbrain.watcher.ci ./setup.sh --non-interactive --skip-mcp --skip-hooks --skip-index`, so the shim cannot regress the Mac path. Stub keys are `ci-stub`; no provider is ever called.

## Runbook — `INSTALL-windows.md` and `CLAUDE.md`

`INSTALL-windows.md` mirrors `INSTALL.md` section for section (preconditions, Steps 1–8, failure branches, updating). `CLAUDE.md` gains, as its first bullet, an OS check (`uname -s` in Bash / `$env:OS` in PowerShell) that selects the runbook, and Windows twins of the "dialog rule" (Defender SmartScreen on the uv download, the schtasks UAC prompt if any, Notepad) and the keys rule (notepad instead of TextEdit). Windows preconditions add: Claude Desktop installed from claude.com/download, the CLI installed with `irm https://claude.ai/install.ps1 | iex`, Git for Windows.

## Implementation notes (2026-09-03, landed)

- `brain_test.py`'s watcher check collapsed from two macOS-only lines (`launchd agent loaded`, `last exit code zero`, parsed from `launchctl list`) into one `watcher service loaded` check via `brain_platform.service_loaded`. The exit-code sub-signal is gone; the log file carries it.
- `install_hooks.py` dedups per event by "an entry for this app's hooks dir already exists" (form-agnostic) rather than by exact command string. Consequence: if `python` in config changes, re-running does not add a second entry; run `--uninstall` then install to refresh.
- `brain_mcp.brain_status` routes its watcher check through `brain_platform.watcher_pids`.
- `setup.ps1`/`uninstall.ps1` accept `-Help` for parity with `-h`. Not part of the contract.
- `setup.ps1` checks only icacls' exit code (its status text is localized); `doctor.py` re-verifies the ACL by parsing principals, which are not localized.
- CI (`.github/workflows/install-smoke.yml`): the Windows job tolerates Task Scheduler refusing to start a task in the runner's non-interactive session — it registers the task, tries `/Run`, and falls back to starting the watcher directly so doctor and the boot check still run. A real logon session is verified on J's machine, not in CI.
