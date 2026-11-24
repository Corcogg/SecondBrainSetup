# START HERE — instructions for Claude

You are setting up a "second brain" (long-term memory) for someone who has
**never used AI or a terminal before**. A friend may be sitting next to them.
This file is the whole script: follow it top to bottom. It points into
`INSTALL.md` for exact commands and `templates/interview.md` for the
getting-to-know-you conversation.

## How to behave the whole time

- **Talk like a patient friend, not a manual.** Short messages. One idea at a
  time. No jargon: say "a background helper" not "daemon", "a password for the
  service" not "API key" (then say "it's called an API key" once).
- **They are in Terminal, not the Claude desktop app.** The memory only
  works in Claude Code. If they mention the desktop app, explain that the
  regular chat there won't see their memory and that Terminal is where to
  talk to you.
- **You do all the typing.** Never ask them to type a command. The only things
  they ever do by hand: click "Yes" on permission boxes, paste two keys into a
  file you open, and answer your questions.
- **Say what's about to happen before it happens.** Before every pop-up,
  window, or permission box, tell them what they'll see and what to click.
- **Show progress.** Start each phase with a line like
  `Step 2 of 6 — getting your two keys (about 5 minutes)`.
- **Use clickable choices when you can.** If you have the AskUserQuestion
  tool, use it for any question with a few sensible answers. It's much easier
  than typing for a beginner.
- **Never let a key into the chat.** If they paste one here anyway, calmly
  tell them it's fine, have them delete that key on the website and make a new
  one, then continue with the file method. Never `cat` the `.env` file.
- **When something fails, don't panic them.** Say "that didn't work, I'll fix
  it", run `scripts/doctor.py`, match the failure against INSTALL.md's
  "If it fails" branches, and fix it yourself. Show the user only what they
  need to act on.

## Phase 0 — Welcome (say this first, before doing anything)

Introduce yourself in 3–4 short lines: you're Claude; you're going to set up a
memory so that in future conversations you remember who they are, how they
like to be talked to, and things they've told you; it takes about 20 minutes;
you'll do the technical parts.

Then explain permission boxes, because they'll see one in a moment:

> "Every time I want to run something on your Mac, a box appears asking if
> it's OK. That's a safety feature. During setup it's safe to choose the
> option that says **Yes, and don't ask again** for that kind of action, so you
> don't have to click 50 times. If you ever see a box you're unsure about, ask
> me."

Ask if they're ready (a simple yes/no choice).

## Phase 1 — Check the Mac (Step 1 of 6)

1. Confirm macOS: `uname -s` must print `Darwin`. On Windows, stop and follow
   `INSTALL-windows.md` instead, with the same behavior rules as above.
2. The repo should already be at `~/SecondBrain/app` (the paste prompt
   cloned it). If it isn't, run INSTALL.md Step 1. If it was cloned somewhere
   under `~/Desktop`, `~/Documents` or `~/Downloads`, re-clone it to
   `~/SecondBrain/app` (INSTALL.md explains why).
3. Check `git --version`. If macOS offers to install "command line developer
   tools", tell them beforehand: a box will ask to install developer tools;
   click **Install**, then **Agree**. It takes a few minutes.

## Phase 2 — The two keys (Step 2 of 6)

Explain in plain words, before opening anything:

> "Your memory uses two outside services. **Anthropic** (the company that makes
> me) runs a small, cheap helper that reads each note and labels it. That's
> about half a cent per note. **Voyage** makes your notes searchable by
> meaning. It's free at your usage. Each one gives you a key, which is like a
> password that lets your brain use the service. You'll make two accounts,
> copy two keys, and paste them into a file I open for you. Expect roughly a
> dollar a month in total on top of your Claude plan."

Ask first (clickable choice): "Did you already make your Voyage and
Anthropic accounts and add a card?" The README asks people to do that
beforehand. If yes, skip straight to the **create-a-key** steps below. If
not, walk through sign-up too.

Then walk them through each site **one at a time**. Open it for them with
`open <url>`, then give click-by-click steps, waiting for "done" after each
site:

**Voyage first (it's quicker):**
1. `open https://dashboard.voyageai.com/organization/api-keys`. Say: "Sign
   up with Google or email. After you sign in you'll land on the API keys
   page."
2. "Click **Create new secret key**, name it 'second brain', and click the
   copy button next to the key."
3. "Also add a card. Look for **Billing** in the left menu. You won't be charged at your usage
   (there's a large free allowance), but without a card Voyage slows you down
   so much that setup can fail."
4. "Keep that tab open. Don't paste the key here."

**Anthropic second:**
1. `open https://console.anthropic.com/` — "Sign up. This is a separate
   account from your Claude plan, so the same email is fine."
2. "Go to **Billing**, add a card, and buy **$5** of credit. That will likely
   last months. Leave auto-reload off."
3. "Go to **API Keys**, click **Create Key**, name it 'second brain', and copy
   it."

Then do **INSTALL.md Step 3** exactly: create `.env`, open it in TextEdit,
tell them where to paste each key (warn first: "a small text window will pop
up"), and verify with character counts only. Use one of the copied keys at a
time: if they only have one copied, have them paste it, save, go copy the
other, and come back.

## Phase 3 — Install (Step 3 of 6)

Say: "Now I'll install everything. It takes 2–5 minutes, and you'll see a lot
of text scroll by. That's normal."

Run **INSTALL.md Step 4** (`setup.sh --non-interactive`). Before it runs, warn
about the possible pop-ups listed in INSTALL.md (notifications: either answer
is fine). If anything goes red, fix it using INSTALL.md's failure branches
before moving on. `install_hooks.py` edits `~/.claude/settings.json`. On a
brand-new Claude install that file is empty or missing, so just tell them
"I'm connecting your memory to Claude", and don't ask a technical question
about it.

## Phase 4 — Getting to know you (Step 4 of 6)

Follow **`templates/interview.md`**. This is the heart of the setup and should
feel like a friendly conversation, not a form. It produces their three
memory files and gets their approval before saving.

## Phase 5 — Restart and prove it works (Step 5 of 6)

1. Explain: "To switch the memory on, Claude needs a restart. You'll type two
   short things and I'll pick up right where we left off."
2. Tell them exactly: "Type `/exit` and press Enter. Then type `claude -c`
   and press Enter." (`-c` continues this conversation with the memory now
   loaded.) Copy the second command to their clipboard first with
   `printf 'claude -c' | pbcopy` so they can just press Cmd+V.
3. After the restart, run INSTALL.md Step 7 checks 1–3 quietly (tools listed,
   profile loaded, save the "one thing to remember" with `brain_remember`).
   Wait about 10 seconds, then confirm with `brain_query` that it comes back.
4. **The magic moment:** have them start a completely fresh conversation:
   "Type `/exit`, then `claude`, then ask: **What do you know about me?**"
   Copy `claude` to the clipboard first. The fresh session should answer from
   their profile and the remembered fact. That proves it works.

If you are a fresh session reading this file because they asked "what do you
know about me?", answer warmly and fully from the loaded profile and from
`brain_query`, then continue with Phase 6.

## Phase 6 — Your first five minutes (Step 6 of 6)

Give a short guided tour. Do each item **with** them, not as a list to read:

1. **Remembering:** "Tell me something about you that I should remember
   forever." Save it with `brain_remember` and say "Saved. Ask me about it any
   time, in any conversation."
2. **Changing your settings:** "If you ever want me to act differently, just
   say so. For example: *be more casual*, or *stop using bullet points*. I'll
   update your profile." Offer to make one change now.
3. **A real task:** pick one thing from what they said they want help with in
   the interview and do a small, real piece of it right now (an essay outline,
   a study plan, a budget, a message draft).
4. **Coming back later:** "Next time, open Terminal (Cmd+Space, type
   Terminal, Enter), type `claude`, and press Enter. That's it. I'll
   remember you."
5. **If something ever seems broken:** "Say: *run the brain doctor and fix
   what's red.*"

End with one warm line. Don't tack on a summary of everything you did.
