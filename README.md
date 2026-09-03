# Second Brain

A persistent memory for Claude Code. Tell it something once, and it remembers
— across every future conversation, in every project.

- Your notes are plain markdown files on your own Mac, not in someone else's cloud.
- Claude can search them by meaning ("what did I decide about X?"), not just exact keywords.
- A background helper quietly tags and links new notes as you add them — you don't have to organize anything.

## Before you start

You'll need:

- A Mac, or a Windows 10/11 PC (64-bit).
- **On a Mac:** Claude Code installed and signed in. If you don't have it
  yet: https://docs.claude.com/en/docs/claude-code
- **On Windows:** [Claude Desktop](https://claude.com/download), plus the
  Claude Code CLI and Git for Windows — Claude will install both for you if
  they're missing (see [INSTALL-windows.md](INSTALL-windows.md)).
- About 15 minutes.
- Two free accounts you'll create along the way (below) — one of them
  typically costs a few dollars a month once you're using it regularly.

## Get your two keys

Second Brain needs two API keys: one for search, one for the AI tagging of
your notes. Claude will open a file for you to paste them into during setup —
until then, just get them ready.

### 1. Voyage AI key (free)

1. Go to https://www.voyageai.com/ and sign up.
2. Open the dashboard and find **API Keys**.
3. Create a new key and copy it somewhere safe (a password manager, or a
   sticky note you'll close after pasting it once). Voyage's free tier
   covers this use case for most people.

### 2. Anthropic key

1. Go to https://console.anthropic.com/ and sign up.
2. Add a payment method under **Billing** and add a small amount of credit
   (a few dollars is plenty to start). This system typically costs a few
   dollars a month in normal use — tagging notes and answering questions
   isn't expensive, but it isn't free.
3. Under **API Keys**, create a new key and copy it somewhere safe.

Keep both keys handy. During setup Claude will open a small text file on
your screen and ask you to paste each key on its own line, then save. That
is the only place the keys ever go. Never paste them into the chat itself —
chat history is not a safe place for secrets, and Claude is instructed to
refuse them there.

## The one thing to paste into Claude Code

1. Open **Terminal** (press `Cmd + Space`, type `Terminal`, press Enter) on a
   Mac, or **PowerShell** (press the Windows key, type `PowerShell`, press
   Enter) on Windows.
2. Type `claude` and press Enter.
3. Paste this prompt and press Enter:

```
Please install my second brain from https://github.com/Corcogg/SecondBrainSetup.
Read the README and INSTALL.md in that repo and walk me through it step by
step. I am not technical, so run the commands for me and tell me before
anything pops up.
```

That's it. Claude will clone the project, install everything, and ask before
any command runs or any dialog appears on your screen.

## What Claude will ask you

Near the end of setup, Claude will interview you — about 5 minutes, one
question at a time, plain language, no jargon. Things like your name, what
you're working on, how you want Claude to talk to you, and one thing you'd
want it to already know. Your answers become your profile; you can change
any of it later just by asking Claude.

## Using it day to day

Just talk to Claude normally, in any project, any conversation.

- Tell it something worth remembering ("I prefer X", "the deadline is Y",
  "we decided to use Z") and it saves it.
- Ask about something you mentioned before, even in a different session, and
  it looks it up.
- You can also drop a `.md` file straight into `~/SecondBrain/vault/memory`
  yourself — the background helper will pick it up within seconds.
- If you use [Obsidian](https://obsidian.md) (free), you can open
  `~/SecondBrain/vault` as an Obsidian vault for a visual view of your notes
  and how they link together. Optional — everything works without it.

## If something goes wrong

Tell Claude: **"run the brain doctor and fix what's red."** That's a real
health check script that pinpoints exactly what's broken, and Claude knows
how to read and act on it.

## Updating

Tell Claude: **"update my second brain."** It will pull the latest code and
re-run setup — your notes, keys, and personalization are never touched by an
update.

## Uninstalling

Tell Claude: **"uninstall my second brain."** This stops the background
helper and disconnects it from Claude Code, but keeps your notes and keys on
disk unless you ask it to delete those too — see INSTALL.md for exactly what
each step removes.

## Privacy

See [docs/PRIVACY.md](docs/PRIVACY.md) for exactly what data goes where.
