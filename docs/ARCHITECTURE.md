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
