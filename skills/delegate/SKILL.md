---
name: delegate
description: Decide whether and how to delegate work to subagents, and build the delegation contract. Invoke when about to start implementation work in a Fable session, when asked "delegate this" / "spawn an agent for" / "who should do this", or before any multi-agent fan-out. Encodes the economic threshold test, model-tier heuristic, contract template, scout-and-brief pattern, and review floors.
---

# /delegate — Delegation Rubric

Companion to the soul's Model-tier delegation policy (adopted 2026-08-03) and the
four-methods brief. The objective function is **decision quality per dollar-hour**,
not minimized tokens. One bad prod decision outweighs a year of savings.

## 1. The threshold test (run this first)

DELEGATE when ANY of:
- The task requires substantial context not already loaded (~≥30k tokens of file reads)
- It involves an iterate-until-green loop (test-fix-retest, build-debug cycles)
- It is parallelizable across independent items
- Its transcript would pollute the main context past useful reasoning range

ACT DIRECTLY when: the change is small AND the relevant files are already in context.
Subagent overhead is real — ~15–25k tokens of bootstrap before the first useful read,
plus spec-writing and review at Fable prices. Delegating a two-line fix is waste
dressed as discipline. When acting directly on mechanical work, say so in one line.

## 2. Tier heuristic

| Tier | Use for | Never for |
|---|---|---|
| Haiku | Enumeration, scanning, simple lookups | Reading ambiguous code |
| Sonnet | **Default implementer** — contained implementation, refactors, tests, docs | Architecture decisions |
| Opus | Multi-file / cross-system implementation, complex mechanical work | — |
| Fable | Spec authorship, review, architecture, security, synthesis | Grinding loops, bulk reads |

Escalate-don't-decide: a cheaper-tier session that hits an architecture, security,
or prod-mutating decision stops and reports; it does not decide.

## 3. The delegation contract (every delegated task)

1. **Objective** — one sentence.
2. **File manifest** — exact paths, read vs. edit, labeled "starting points — verify
   before editing" (the manifest is advisory; the map may be stale).
   When a `/plan` preceded this, take manifests and parallelism from its Architecture
   **Seams** section (interfaces + disjoint file sets); `/delegate` runs after the plan
   is approved, never inside it (agreed 2026-09-08).
3. **Constraints** — the invariants that must not break. Cite them from the project's own
   rules doc (its `CLAUDE.md`, plus any decisions/spec doc it points to) rather than
   restating them here; that doc is the source of truth.
4. **Verification command** — chosen by the delegator, run by the agent, with RAW
   output and exit code pasted into the report. Never a summary. Exit codes don't lie.
5. **Output schema** — what changed / verification output / deviations from spec /
   surprises encountered.

## 4. Review floors (codified, not discretionary)

- Security, prod, and migration diffs: **always read in full.**
- Mechanical renames/formatting/docs: accept on report + spot-check.
- Never merge on a self-report alone; the pasted verification output is the floor.
- If you delegate, commit to it — don't re-derive the agent's findings after it reports.

## 5. Scout-and-brief (mechanical fan-outs of ≥2 agents only)

- One Haiku/Sonnet scout produces a ≤2k-token brief: file map, conventions, key
  types, invariants, gotchas — **with a file-path citation on every load-bearing claim.**
- Workers get the brief in their contract and skip broad exploration; any worker
  acting on a load-bearing claim verifies it against the cited file first.
- Mutating fan-outs: worktree isolation + non-overlapping file manifests, always.
- **BANNED for discovery work** (bug hunts, audits, reviews): independent, blind
  exploration is the point — a shared brief blinds every finder the same way.
- Batch independent agent spawns in a single message so they run concurrently.

## 5b. Persistent context briefs (standing rule)

Cheap agents are only expensive when they re-derive context. Kill that cost with
pre-built context, but under these rules:

- **Prefer the repo's existing docs over new brief files.** Most projects already
  maintain a brief set — typically `CLAUDE.md` (rules), a spec or `DECISIONS.md`
  (source of truth), and a `HANDOFF.md` (state). The contract's file manifest points
  agents at the relevant paths/sections — do NOT create a parallel "brief.md" that
  duplicates them; a second source of truth is a drift generator.
- **Create a dedicated brief file only where no doc covers the domain**, keep it
  ≤2k tokens, cite file paths for every load-bearing claim, and date-stamp it.
- **Staleness is the failure mode.** A brief is a cache with no invalidation: any
  session that lands work invalidating a load-bearing claim updates the relevant
  doc as part of landing the work — not later. A confidently wrong brief produces
  correlated error, which is worse than no brief.
- Briefs bound *exploration* (where things live, conventions, invariants). They do
  not replace the agent reading the files it actually edits — that cost is
  intrinsic to the task at any tier.

## 6. Standing config rules

- New plugins default OFF globally, ON per project where their domain lives.
- Boot-payload re-audit quarterly (stray CLAUDE.md files, plugin listings, hook output).
- Thinking frameworks live at `~/.claude/skills/thinking-model-router/frameworks/` —
  manual-only (on the user's request), not individually listed.
