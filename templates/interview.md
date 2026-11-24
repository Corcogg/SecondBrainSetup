# Getting to know you — the setup conversation

Claude: this is where the person's memory gets its personality. They have
probably never used AI before, so they don't yet know what's worth telling
you. Your job is to make it easy: explain why you're asking, offer examples,
and draft things *for* them to react to. Reacting is much easier than writing
from a blank page.

**Rules**
- One topic at a time. Wait for the answer. Briefly reflect it back ("Got it,
  you're in your second year studying nursing").
- Offer examples or clickable choices (AskUserQuestion) whenever the question
  is open-ended. "Skip" is always allowed. Use the stated default.
- Ask a natural follow-up when an answer is thin, but at most one per topic.
- Never mention YAML, frontmatter, markdown, or placeholders.
- About 10 minutes total. If they're tiring, offer to skip the optional
  topics. They can add more any time later.

## 1. Explain the three files (say this first, in your own words)

> "I'm going to save three short notes that I read at the start of every
> conversation:
> - **Your profile**: who you are, so you don't have to re-introduce yourself.
> - **My personality**: how you want me to talk to you and what I should never
>   do.
> - **Your pinboard**: the few things that matter most right now, like goals,
>   deadlines, and big decisions.
>
> Everything else you tell me goes into a searchable memory I check when it's
> relevant. I'll ask a few questions, write drafts, and you tell me what to
> change. Nothing gets saved until you say it looks right."

(The files are USER.md, SOUL.md and MEMORY.md. Use the plain names above when
talking to them.)

## 2. Topics, in order

### A. Name (required)
"What should I call you?" Ask if they have a nickname they prefer.
→ USER.md Identity `Name`; replace every `{{OWNER_NAME}}` in all three files;
also `owner_name` in `brain_config.json` (see "Saving" below).

### B. What you do
"What do you spend most of your days on? School, work, something else?" If
it's school: what they study and what year. If it's work: what kind of work.
→ USER.md Identity `Role`, one line.

### C. What you want help with (the most important topic)
"What would you love help with? Here are some things people use me for. Pick
any that sound useful, or tell me your own:"
Offer a multi-select: *school or studying*, *writing (essays, emails,
messages)*, *planning (schedules, trips, events)*, *money and budgeting*,
*job or career stuff*, *creative projects*, *learning something new*,
*just thinking things through*.
Follow up on their top pick: "Tell me a bit more. What's one real thing
coming up where I could help?"
→ MEMORY.md `## Goals` (what they want help with, in their words) and, if
they named a concrete upcoming thing, `## Ongoing Deadlines` or
`## Active Projects`. Remember the concrete thing for the first-five-minutes
tour in START-HERE.md.

### D. How I should talk to you. *Show, don't ask.*
Don't ask "what tone do you want?" since beginners can't answer that in the
abstract. Instead, pick a simple, relevant question (for example "How should
I study for a big exam?") and show **three very short sample replies** in
clearly different styles:
1. Warm and chatty, with encouragement.
2. Short and straight to the point.
3. Detailed and thorough, explaining the why.
Ask which one feels most like what they'd want (clickable choice), then:
"Anything else? For example, humor, emojis, no bullet points, explain things
simply, push back on me when I'm wrong."
→ SOUL.md `## Personality` and `## Communication Style`: replace the
`{{PERSONALITY_EXTRA}}` / `{{STYLE_EXTRA}}` lines with 2–4 concrete bullets
in plain words (e.g. "Warm and encouraging; light humor is welcome", "Keep
answers short unless asked for detail", "No emojis").

### E. Things I should never do
"Is there anything I should never do, or always check with you first? Most
people say something like *always ask before deleting anything*." Offer that
as the default.
→ SOUL.md `## Behavioral Rules`, replacing `{{RULES_EXTRA}}`.

### F. Timezone (confirm, don't ask)
Run `date +%Z` and `readlink /etc/localtime` yourself, then confirm: "Looks
like you're on Pacific time. Is that right?"
→ USER.md Identity `Timezone`.

### G. Anything else about you (optional)
"Anything else that would help me help you? For example, people you talk
about a lot, a job you're applying for, a health thing you're managing,
favorite apps, or how you learn best. Totally optional."
Before saving anything personal about other people or health, make sure
they're comfortable having it written down.
→ USER.md `## Preferences` (replacing `{{PREFERENCES_EXTRA}}`) or `## Notes`.

### H. One thing to remember (required, this becomes the proof)
"Last one. Tell me one thing that's true today that you'd want me to
remember. A goal, a decision, a fun fact, anything."
→ MEMORY.md `## Key Decisions` or `## Goals`, whichever fits. Keep the
exact wording: START-HERE.md Phase 5 saves it with `brain_remember` and
recalls it in a fresh conversation.

**Project folders:** skip this for beginners. Remove the `{{PROJECT_EXAMPLE}}`
line from USER.md and leave `cwd_domain_map` empty.

## 3. Draft, show, approve

1. Fill `templates/SOUL.md`, `templates/USER.md` and `templates/MEMORY.md`
   from the answers. **No `{{...}}` may remain**: delete any placeholder
   line that has no answer. Keep the template's own comments and default
   bullets. Don't invent facts they didn't tell you.
2. Don't dump raw files on them. Show a friendly summary of each file
   (headings and bullets, in plain words), then ask: "Does this sound like
   you? Anything to change?" Make changes until they're happy. If they want
   to see the actual files, show them.
3. Tell them: "You can change any of this any time. Just tell me, for
   example, *update my profile: I switched majors*."

## 4. Saving (only after they approve)

1. Write the three files to `~/SecondBrain/vault/SOUL.md`, `USER.md` and
   `MEMORY.md`, overwriting the placeholder copies setup created.
2. Set `owner_name` in `~/SecondBrain/app/brain_config.json` to their name
   using Python's `json` module (load, set, write back with `indent=2`).
   Never sed or regex this file.
3. Run `~/SecondBrain/app/.venv/bin/python ~/SecondBrain/app/scripts/doctor.py`
   and check that it's still green.
4. Continue with START-HERE.md Phase 5.
