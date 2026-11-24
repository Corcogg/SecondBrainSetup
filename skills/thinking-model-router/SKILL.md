---
name: thinking-model-router
description: Manual-only. Route to the right mental model based on domain and problem type, when the user asks to "think harder", names a framework, or requests a specific thinking pass. The single entry point for all thinking frameworks. Returns NONE (justified), one primary framework, or at most three complementary ones.
---
<!-- 2026-11-19: demoted to manual-only (no longer a mandatory /plan step). Upstream's own evals found no lift above
     its +5pp utility bar for any framework, and upstream quarantined all 28 as manual-only. 23 framework SKILL.md
     files synced to upstream 7b8fece lean versions; see NOTICE.md. -->

<!-- Adapted 2026-09-08 from tjboudreaux/cc-thinking-skills (MIT) commit 7b8fece. Local changes: frameworks are read
     from ./frameworks/<slug>/SKILL.md (not invoked as plugin skills); NONE must be justified; (the Complicated/Complex
     framework floor was removed 2026-11-19); regret-minimization is retained as the values check for personal
     decisions. See NOTICE.md. -->

# Model Router

**Core rule:** Prefer NONE or one primary framework. Route by mechanism fit, not habit. Combine only when roles are distinct and necessary. Never let NONE be the lazy answer: it has to name what is absent.

## When to Use

- The right thinking framework is unclear and you would otherwise guess or stack tools.
- Several frameworks seem plausible and you need a single primary (or an explicit, justified NONE).
- High-stakes work where a wrong frame is costly and a quick domain × type match helps.
- Only when invoked: the user asks for it, says "think harder", or `/plan` hands off on their request. Never as an automatic step.

## When NOT to Use

- The match is already known or obvious ("where's the bottleneck?" → theory-of-constraints): read that framework directly; do not route for show.
- The task is routine implementation with no analytical unknown: reason directly (NONE, justified in one sentence).
- You are mid-execution of an agreed plan and only need the next concrete step.
- The ask is outside this catalog (pure coding syntax, tool ops with no judgment call): NONE.

## Reading a Framework

Frameworks are files, not plugin skills. For a routed slug, read
`~/.claude/skills/thinking-model-router/frameworks/thinking-<slug>/SKILL.md` and apply it as written. Never invent a slug not listed in the Catalog below. `NONE` means read nothing.

Each framework directory also holds `EXAMPLES.md`: worked examples, facilitation steps, templates, and key questions. Do not load it for routine planning. Load it when the user asks for a walkthrough, a "teach me," or a seminar-style pass, or when checking that a procedure was applied correctly. `frameworks/_absorbed/` holds frameworks that were merged into others; they are kept for reference and are not routed.

## Procedure

1. **Short-circuit.** If one framework clearly fits by mechanism, return that framework alone. If no framework clearly improves the work, return **NONE** with a one-sentence justification naming the analytical unknown that is absent (e.g. "no competing causes, no decision under uncertainty, no failure modes to bind"). Stop.
2. **Characterize.** Record domain (coding, architecture, product, strategy, personal, abstract, risk, innovation) and problem type (diagnose, decide, understand, create, evaluate, predict, optimize). Note constraints: time, information, stakes, reversibility, complexity.
3. **Candidate by type defaults (override when constraints demand).** Keep only catalog frameworks:
   - Diagnose → five-whys-plus or scientific-method (kepner-tregoe if an IS/IS-NOT matrix is needed)
   - Decide → reversibility first; then opportunity-cost or probabilistic; for personal or career commitments, regret-minimization as the values check after reversibility
   - Understand → systems (map-territory if model-vs-reality gap; cynefin if the approach domain is unclear)
   - Create → first-principles (triz for contradictions; effectuation for means-driven; via-negativa for remove-first)
   - Evaluate → steel-manning (socratic if assumptions or definitions are the unknown)
   - Predict → probabilistic
   - Optimize → theory-of-constraints (ooda under time pressure; bounded-rationality for search stop)
   - Risk / "what fails?" → pre-mortem or red-team; margin-of-safety for buffers
   - Product "what to build?" → jobs-to-be-done
   - Competence / durability → circle-of-competence, lindy-effect
   - Controlled hypothetical → thought-experiment
   - Multi-lens only after one primary fails a blind-spot check → model-combination
4. **Select with criteria (satisficing).** Score only if 2+ candidates remain or stakes make a forced default unsafe. Rate each criterion 1–5 (1 = absent/wrong fit; 3 = usable with gaps; 5 = direct fit): problem fit (30%), available inputs (20%), time to apply (15%), stakeholder usability (15%), competence to apply correctly (20%). A route must score problem fit ≥4 and weighted total ≥3.5; otherwise return **NONE** (justified). For totals within 0.25, prefer fewer inputs and shorter execution; if still tied, choose NONE unless the frameworks answer distinct complementary questions.
5. **Multi-framework only as exception.** Add a second or third only when each has a distinct complementary role the primary leaves open. Cap at three. Prefer sequential over parallel. Near-neighbors and synonyms do not stack. For composition patterns, hand off to model-combination after naming the primary.
6. **Exit.** State abandon signals (forced fit, ignored factors, no insight after a genuine pass). On mismatch, re-route once or fall back to NONE. Never force a frame.

**Domain cheat-map (primary first; still default to one or NONE):**

| Domain signal | Prefer |
|---------------|--------|
| Bug / root cause / flaky | five-whys-plus, scientific-method, systems |
| Architecture / tech choice | reversibility, systems, lindy-effect, opportunity-cost |
| Feature / roadmap / engagement | jobs-to-be-done, opportunity-cost, theory-of-constraints |
| Strategy / competition / growth | cynefin, systems, red-team, second-order |
| Personal / career commitment | reversibility, regret-minimization, opportunity-cost, circle-of-competence, pre-mortem |
| Argument / belief update | steel-manning, probabilistic, socratic, first-principles |
| Security / disaster / ruin | pre-mortem, red-team, margin-of-safety, via-negativa |
| Innovation / contradiction / simplify | first-principles, triz, effectuation, via-negativa |

## Output

```text
outcome: NONE | one | multi
none_because: <only for NONE: the analytical unknown that is absent>
routes:
  - id: <primary slug or NONE>
    role: <job this framework performs>
    unique_question: <question only this route answers>
  - id: <secondary slug, only for multi>
    role: <distinct complementary job>
    unique_question: <distinct open question>
  - id: <tertiary slug, only for multi>
    role: <distinct complementary job>
    unique_question: <distinct open question>
domain: <domain>
problem_type: <type>
cynefin: clear | complicated | complex | chaotic
constraints: <time/info/stakes/reversibility>
rationale: <mechanism fit in one sentence>
blind_spots: <what the primary still ignores, if any>
exit: <when to abandon or re-route>
```

Default fill: `outcome: NONE` with `none_because` filled, or `outcome: one` with one route. Use `multi` only when every listed framework has a distinct role and unique question. When used inside `/plan`, each routed framework must leave a concrete artifact in the plan body (a risk with a falsifier, a ruled-out alternative, a decision); name it inline where it appears.

## Catalog (28 frameworks: upstream's 27 leaves plus regret-minimization)

bounded-rationality, circle-of-competence, cynefin, effectuation, first-principles, five-whys-plus, jobs-to-be-done, kepner-tregoe, lindy-effect, map-territory, margin-of-safety, model-combination, ooda, opportunity-cost, pre-mortem, probabilistic, red-team, regret-minimization, reversibility, scientific-method, second-order, socratic, steel-manning, systems, theory-of-constraints, thought-experiment, triz, via-negativa.

Absorbed (do not route; their mechanisms live inside the host, their lessons in the host's EXAMPLES.md): inversion → pre-mortem; occams-razor → scientific-method; bayesian, fermi-estimation → probabilistic; archetypes, feedback-loops, leverage-points → systems; model-selection → this router; debiasing → the countercase step in the decision frameworks; dual-process → dropped.

## Verification

- **Falsify / stop:** If the route is habit or familiarity rather than mechanism fit, discard and re-score or return NONE. If multi entries lack distinct roles, collapse to the single best primary. If NONE has no `none_because`, it is not a route; fill it or pick a framework.
- **Over-application guard:** Do not route when the framework is already obvious. Do not return more than three. Do not cite absorbed or non-catalog names. Do not treat the router as a prerequisite for a framework read directly.
