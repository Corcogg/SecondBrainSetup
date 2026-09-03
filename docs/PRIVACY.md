# Privacy

Plain statement of where your data lives and where it goes.

## Where your notes live

All of your notes — your profile, your memory file, and everything Claude
saves or you write by hand — live in one folder on your Mac:

```
~/SecondBrain/vault/
```

Nothing is uploaded to any cloud storage, synced to any account, or backed
up anywhere unless you set that up yourself (e.g. by adding a git remote or
using Obsidian Sync — this system does neither on its own).

## What leaves your machine, and to whom

When a note is saved (by you, or by Claude via the `brain_remember` tool),
two things happen automatically:

1. **The text of the note is sent to Voyage AI** to be turned into a search
   embedding (a list of numbers used for semantic search). This is the only
   thing Voyage AI receives.
2. **The text of the note is sent to Anthropic** (the company that makes
   Claude) to generate tags and links between notes, and — separately —
   whenever you talk to Claude, your messages and any notes retrieved from
   the vault are sent to Anthropic to generate a response, the same as any
   other Claude Code conversation.

Nothing else leaves your machine. The background watcher, the index, and
the vault itself are all local.

## Where your keys live

Your two API keys (Voyage and Anthropic) live in exactly one file:

```
~/SecondBrain/app/.env
```

That file is set to be readable only by you (`chmod 600`). It is never
copied anywhere else, never committed to git (the app folder's `.gitignore`
excludes it), and no other file in this system — not the launchd config, not
Claude Code's own settings — ever contains a copy of a key.

## How to delete everything

- **Delete your notes:** `rm -rf ~/SecondBrain/vault` (this cannot be
  undone — consider a backup first if you want one).
- **Delete your keys:** `rm ~/SecondBrain/app/.env`, then revoke the keys
  at https://www.voyageai.com/ and https://console.anthropic.com/ so they
  stop working even if a copy exists elsewhere.
- **Remove the whole system:** run `uninstall.sh --purge` (see README.md),
  then `rm -rf ~/SecondBrain`.
