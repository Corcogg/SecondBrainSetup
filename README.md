# Second Brain

A persistent memory for Claude Code. Tell it something once, and it remembers
— across every future conversation, in every project.

- Your notes are plain markdown files on your own Mac, not in someone else's cloud.
- Claude can search them by meaning ("what did I decide about X?"), not just exact keywords.
- A background helper quietly tags and links new notes as you add them — you don't have to organize anything.

## Setting up (about 25 minutes)

You do **Before you begin** and **Step 0** yourself. After that, Claude walks
you through everything and does the technical parts.

> **Use Terminal, not the Claude desktop app.** The memory lives in Claude
> Code. The regular chat in the Claude desktop app can't see it.

### Before you begin: make three accounts (about 10 minutes)

Have your Mac login password, a card, and your phone (for verification codes)
ready. Make all three accounts now, but **don't create any keys yet**. Claude
walks you through the keys later and shows you where to paste them.

1. **Claude Pro** ($20/month): go to https://claude.ai, sign up, and upgrade
   to Pro.
2. **Anthropic Console** (buy $5 of credit; it usually lasts months): go to
   https://console.anthropic.com and sign up. This is separate from Claude
   Pro, and the same email is fine. Under **Billing**, add a card and buy
   $5. Leave auto-reload off.
3. **Voyage AI** (free at normal use): go to https://dashboard.voyageai.com
   and sign up. Under **Billing**, add a card. You won't be charged, but
   without one Voyage is slow enough that setup can fail.

### Step 0: Get Claude on your Mac (one time, about 5 minutes)

1. Open **Terminal**: press `Cmd + Space`, type `Terminal`, and press Enter.
   A window with text appears. That's where you'll talk to Claude.
2. Copy this line, paste it into Terminal, and press Enter. It installs
   Claude Code:

   ```
   curl -fsSL https://claude.ai/install.sh | bash
   ```

3. When it finishes, type `claude` and press Enter. Pick a color theme, then
   choose **Claude account with subscription** and sign in in the browser
   window that opens. Come back to Terminal when it says you're signed in.
   (If it says `command not found`, close Terminal, open it again, and retry.)

### Step 1: Paste this into Claude

Copy all of this, paste it into Claude, and press Enter:

```
Please set up my second brain. First run:
git clone https://github.com/Corcogg/SecondBrainSetup.git ~/SecondBrain/app
Then read ~/SecondBrain/app/START-HERE.md and follow it exactly.
I've never used AI or a terminal before, so go slowly and explain things simply.
```

From here, Claude guides you. It will:

- explain the permission boxes you'll see (it's safe to click **Yes, and
  don't ask again** during setup),
- help you make two small accounts and get two keys (see the costs below),
- install everything,
- have a short conversation with you to set up your profile, and
- show you that it really remembers you.

### What it costs

| What | Why | Cost |
|---|---|---|
| Claude Pro | The Claude you talk to | $20/month |
| Anthropic API key | A small helper that labels each new note | about half a cent per note, usually under $1/month. Buy $5 of credit to start. |
| Voyage AI key | Makes your notes searchable by meaning | Free at normal use (200M free tokens). Add a card anyway to avoid slowdowns. |

The keys go into a file on your Mac that Claude opens for you. **Never paste
a key into the chat.**

## What Claude will ask you

Near the end of setup, Claude has a 10-minute conversation with you: your
name, what you'd like help with, and how you want it to talk to you (it shows
you sample replies so you can pick). Then it drafts your profile for you to
approve. Your answers become your profile; you can change
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
