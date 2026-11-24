---
name: thinking-regret-minimization
description: For a personal or career commitment where costs are legible but values are not, project to a future self and ask which path you would regret not taking; run after reversibility, never instead of it.
disable-model-invocation: true
---
<!-- Rewritten locally 2026-09-08 in the shape of tjboudreaux/cc-thinking-skills (MIT) after upstream deleted this
     framework. Worked examples and the original lesson live in EXAMPLES.md next to this file. -->

# Regret Minimization

**Core rule:** Regrets of inaction grow; regrets of action fade. When the cost analysis is done and the choice still will not settle, the missing input is values, and the future self is the instrument that reads them.

## When to Use

- A career, founding, relocation, or relationship-scale decision where reversibility and opportunity cost are already assessed and still leave two live options.
- Fear of failure or short-term cost is visibly distorting the choice.
- The options differ in kind (growth vs. proximity, security vs. meaning), so a value delta in one unit cannot rank them.

## When NOT to Use

- Technical, product, or resourcing decisions: use reversibility and opportunity-cost; regret is not the objective there.
- Cost or undo path is still unknown: run reversibility first.
- One option is ruinous or harms a third party: refuse or redesign; regret does not license ruin.
- The choice is already clear on cost grounds: do not add a values ritual.

## Procedure

1. **State the two options and the horizon.** Name a concrete future age or date far enough that today's fear is small at that scale.
2. **Project and ask the inaction question for each option.** "At that point, looking back, do I regret not having tried this?" Answer yes, no, or both, with one sentence of why. A "both" answer means the decision is about which value matters more; name the two values.
3. **Separate regret of action from regret of inaction.** For each option record the worst plausible action-regret and whether it is recoverable, and the inaction-regret and whether it compounds.
4. **Check who else bears the consequences.** Name the people affected by each path and what each has actually said, not what you assume. Pure self-regret is not sufficient when others carry real cost; if their stated positions point the other way, say so before deciding.
5. **Strongest countercase.** State the best evidence-based case that the projection is wrong: the "would rather regret trying" framing is aspirational rather than accurate, the future self is being written to flatter the bold option, or a cost the facts do not price (re-entry, relationship, health) is what will actually be regretted. Revise the projection if the countercase survives.
6. **Check the asymmetry against reversibility.** If the action-regret is recoverable and the inaction-regret compounds, the framework favors acting. If both compound, decide on the named values, not on regret.
7. **Decide and state what would change your mind.** Commit to one path and name the observation within the horizon that would show the projection was wrong.

## Output

```text
decision: <two options>
horizon: <age or date>
inaction_regret: A: yes|no|both — <why> ; B: yes|no|both — <why>
action_regret: A: <worst case> recoverable: yes|no ; B: ...
others_affected: <who, what they have said, which way it points>
values_named: <only if any answer was "both">
countercase: <best case the projection is wrong, and whether it survived>
asymmetry: favors_acting | favors_waiting | values_decide
choice: <path>
revisit_if: <observation that falsifies the projection>
```

## Verification

- **Falsify/stop:** if every inaction answer is "no," there is no regret problem; decide on cost and stop. If the projection only restates the cost analysis, you have not reached values; ask what you would want to have been true, not what would have been cheaper. If the countercase was not written, the check is incomplete.
- **Over-application guard:** never apply to reversible or technical choices, never use "I would regret not trying" to override a ruin constraint or a stated position of someone who bears the cost, and do not run it before reversibility has classified the decision.
