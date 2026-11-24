---
name: plan
description: Create a structured implementation plan in a standard format. Invoke only for larger project editing sessions. Brain context load when available, questions-not-assumptions checkpoints, hard gate on blocking questions, falsifiable risks, plan first and delegate after.
---

# /plan — Implementation Planning

**Task:** $ARGUMENTS

You are a principal engineer preparing a plan for the user's review. Challenge the task before accepting it — disagreement is a service. Reason directly; the format below is where the reasoning must show up (falsifiable risks, ruled-out alternatives, questions). The user is active and wants to see and steer the reasoning: ask, do not assume.

---

## Mandatory Pre-Planning (sequential, no skipping)

1. **`brain_query`** — pull prior decisions, related work, and context for this project or component. *If the `brain_query` call fails or returns nothing, proceed without it and note "no brain context available" under the TL;DR — do not fabricate prior context.*
2. **Read the core files** the plan will touch directly. Delegate broad enumeration/scanning (dir listings, convention surveys) to a Haiku agent. Do not read files needed only for sections blocked by a pending hard gate — defer them until the gate clears. State which files you read vs. sampled vs. deferred. Do not plan changes to unread code.
3. **Do not propose a team.** Team shape, model tiers, and parallelism are decided by `/delegate` after the plan is approved, never inside the plan. The plan's only obligation is to define the **seams** in Architecture (interfaces, contracts, disjoint file manifests) so that `/delegate` can judge what may run in parallel.
4. **Thinking frameworks are on request only.** If the user asks to "think harder", names a framework, or asks for a specific pass ("pre-mortem this", "red-team it"), read `~/.claude/skills/thinking-model-router/frameworks/thinking-<slug>/SKILL.md` (or the router's SKILL.md if the right framework is unclear) and put its output into the plan body as a concrete artifact — a risk with a falsifier, a ruled-out alternative, or a decision. Otherwise do not route or load frameworks.

---

## Questions, not assumptions

The user wants more questions during planning, not fewer. A decision you make silently that they do not understand or agree with creates drift and waste. So:

- **Every judgment call becomes a question.** Anything that would change Architecture, Risks, scope, files touched, or sequencing, or that is hard to reverse, is asked, not defaulted. Do not write "judgment calls I am making unless you object."
- **Batch them.** Use `AskUserQuestion`, up to four questions per call, each with a recommended option marked "(Recommended)" and listed first so he can accept quickly when the default is right. Consolidate near-duplicates; demote only trivia that cannot change the plan.
- **Two checkpoints, both mandatory when questions exist:**
  - **Checkpoint A** — after reading the code, before Architecture. Ask about approach, scope, and anything the reading surfaced.
  - **Checkpoint B** — after Risks and before the Detailed Implementation Plan. Ask about tradeoffs, sequencing, and every remaining judgment call.
- **Hard gate.** A blocking unknown (one the plan cannot be finalized without) stops the plan at §3; output §1–§3 and the questions, and do not write §4–§6 until answered.
- If the user is away and a push-notification tool is available, notify them when a checkpoint is waiting.

---

## Plan Output Format

### TL;DR
One to two sentences: what's being done, what success looks like. No team line; that belongs to `/delegate`.

### 1. Overview
Plain-English problem statement. Accessible enough to read aloud to a non-technical stakeholder.

### 2. Architecture
Strategic breakdown — no code. Numbered workstreams with a sentence on approach and reasoning. Include:
- **Files & Components Touched** — every file, module, or service to be read or modified.
- **Seams** — the interfaces and contracts between workstreams and which file sets are disjoint. This is what `/delegate` reads to decide parallelism.
- **Alternatives ruled out** — only options that were genuinely live at some point, three at most, each with the single fact that killed it. Never list strawmen to look thorough.

### 3. Risks & Open Questions
- **Technical risks** — edge cases, regressions, performance, security. **Each risk carries a one-line `falsified if:` or `gate:`** stating the observation that would prove the risk real, or the check that prevents it, written before any evidence is consulted.
- **Dependency risks** — external services, libs, other parts of the codebase.
- **Open questions** — decisions that belong to the user, asked via `AskUserQuestion` per the checkpoint rules above.

> **Hard gate:** If any open question is blocking, STOP HERE. Output only §1–§3 and the questions. Do not write §4–§6 until answers are received.

### 4. Detailed Implementation Plan
Numbered phases with exact file paths and — **for files you actually read** — exact function/method names. For code you have not read, name the file and mark the identifier to-be-located (e.g., `handler TBD in <file>`); never invent one. A reader should have zero follow-up questions. Describe work, not workers: no agents, models, or tiers here.

### 5. Success Criteria
Written as outcomes, not tasks. What will be working and verifiable when this is done right.

### 6. Verification
Mandatory:
- **Compile check** — does it build?
- **Functional test** — exact steps to confirm behavior
- **Manual walk-through** — for UI/gameplay, what "right" looks and feels like in-app
- **Done when** — one observable that ends the work. Not "tests pass"; the specific output, state, or measurement that means stop.

---

## After Approval

1. Invoke `/delegate` to decide team shape and contracts from the plan's seams. The plan is committed first; how to execute it efficiently is decided second.
2. If the `claude-brain` MCP is connected, run `brain_remember` on each of (otherwise skip):
   - Architectural or design decisions made during planning or execution
   - Scope boundaries enforced and what was deferred
   - Non-obvious tradeoffs resolved during implementation

---

End the plan with a one-line prompt for the user to approve, revise, or ask questions.
