# Skills

Optional Claude Code skills that pair with the second brain.

| Skill | What it does | How to use it |
|---|---|---|
| `/plan` | Writes a structured plan for a bigger task: it asks questions before assuming, lists risks, and checks your brain for past decisions. | Type `/plan` and describe what you want to build or change. |
| `/delegate` | Decides whether to hand part of a task to helper agents, and writes a clear brief when it does. Mostly used by `/plan`. | Say "delegate this" or let `/plan` call it. |
| `thinking-model-router` | 25+ thinking frameworks (pre-mortem, first principles, five whys…), used only when you ask. | Say "think harder", or name a framework ("pre-mortem this"). |

## Install

Paste this into Claude Code:

```
Install the skills from the "skills" branch of https://github.com/Corcogg/SecondBrainSetup:
git -C ~/SecondBrain/app fetch origin skills && git -C ~/SecondBrain/app worktree add ~/SecondBrain/skills origin/skills
then run ~/SecondBrain/skills/skills/install.sh and tell me how to use them.
```

Any existing skill with the same name is moved to `~/.claude/skills/_backup-<timestamp>/` first. Restart Claude Code afterwards (`/exit`, then `claude`).

The thinking frameworks come from tjboudreaux/cc-thinking-skills (MIT). See `thinking-model-router/NOTICE.md` and `thinking-model-router/LICENSE-cc-thinking-skills`.
