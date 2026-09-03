# Setup interview

Claude: this is the last step of installation. Ask these 8 questions **one at
a time**, in order — do not dump the whole list at once. After each answer,
briefly confirm what you heard before moving on. Every question has a
reasonable default; offer it and let a blank/"skip"/"default" answer accept
it. When all 8 are answered, assemble SOUL.md, USER.md, MEMORY.md, and the
`cwd_domain_map` entry, **show the three finished files in full**, and ask
for approval before writing anything to the vault or to `brain_config.json`.

Keep questions in plain language — this person may never have opened a
terminal before today. No jargon, no mention of "YAML," "frontmatter," or
"schema."

---

### Q1. "What's your name?"
- Default: none — this one is required.
- Writes to:
  - `USER.md` → `## Identity` → `- Name: {{OWNER_NAME}}`
  - Every `{{OWNER_NAME}}` placeholder in `SOUL.md` and `MEMORY.md`

### Q2. "In one line, what do you do? (job, school, main project — whatever describes you)"
- Default: "—" (leave blank, fill in later)
- Writes to: `USER.md` → `## Identity` → `- Role: {{ROLE}}`

### Q3. "What timezone are you in?"
- Default: infer from the system clock if possible; otherwise ask plainly (e.g. "Eastern time").
- Writes to: `USER.md` → `## Identity` → `- Timezone: {{TIMEZONE}}`

### Q4. "How do you want Claude to talk to you — professional and concise, casual and friendly, or something else?"
- Default: "Direct and concise, no filler."
- Writes to:
  - `SOUL.md` → `## Personality` → `{{PERSONALITY_EXTRA}}`
  - `SOUL.md` → `## Communication Style` → `{{STYLE_EXTRA}}` (a short restatement, e.g. "casual, use plain language" vs "formal, precise")

### Q5. "Is there anything Claude should never do without asking you first? (e.g. never send emails, never delete files, never touch a specific folder)"
- Default: "Ask before anything destructive or irreversible."
- Writes to: `SOUL.md` → `## Behavioral Rules` → `{{RULES_EXTRA}}`

### Q6. "What are the main project folders you work in? For each, tell me the folder name and one line about what it is."
- Default: skip if none yet.
- Ask for one or more `{folder name, short description}` pairs.
- Writes to:
  - `USER.md` → `## Projects` → one bullet per folder: `- **<folder name>** — <description>`
  - `MEMORY.md` → `## Active Projects` → same, one bullet per folder
  - `brain_config.json` → `cwd_domain_map`, one entry per folder:
    `{"fragment": "<folder name>", "domain": "projects", "n": 5}`
    (`fragment` is matched against the current working directory path by the
    SessionStart hook to auto-filter recall to that project; `n` is how many
    notes to pull in by default — 5 is a sane default, don't ask about it.)

### Q7. "Any working preferences Claude should know? (favorite tools, languages, how you like explanations — anything goes)"
- Default: skip.
- Writes to: `USER.md` → `## Preferences` → `{{PREFERENCES_EXTRA}}`

### Q8. "Last one — tell me one thing you'd want your second brain to already know. Something true today: a decision, a fact, a goal, anything."
- Default: none — this one is required; it becomes the recall demo.
- Writes to: `MEMORY.md` → `## Key Decisions` or `## Goals` (pick whichever fits the answer's shape)
- **Also**: after the files are written, this is the fact Claude will save
  with `brain_remember` in the verification step of INSTALL.md, then recall
  with `brain_query` in a fresh session to prove the system works end to end.

---

## After all 8 answers

1. Fill in `templates/SOUL.md`, `templates/USER.md`, `templates/MEMORY.md`
   with the answers above, replacing every `{{PLACEHOLDER}}`. Leave any
   section with no answer as its template default (don't invent content).
2. Show the three completed files to the user in full and ask: "Does this
   look right? Anything to change before I save it?"
3. On approval, write them to `~/SecondBrain/vault/SOUL.md`, `USER.md`,
   `MEMORY.md` (overwriting the placeholder copies `setup.sh` put there).
4. Read `~/SecondBrain/app/brain_config.json`, append the `cwd_domain_map`
   entries from Q6 using Python's `json` module (load, modify the list,
   write back with `indent=2`) — never hand-edit with sed/regex.
5. Continue to the verification step in INSTALL.md.
