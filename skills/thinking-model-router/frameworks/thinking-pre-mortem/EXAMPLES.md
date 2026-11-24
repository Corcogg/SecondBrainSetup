# Pre Mortem — worked examples and seminar material

> Read this when studying the method or when a plan asks for a walkthrough ("teach me"). `SKILL.md` is the
> procedure /plan loads; this file is the correctness reference for it and keeps everything the short
> procedure left out: origin, worked examples, facilitation steps, templates, and key questions.
> Source: the April 2026 snapshot of tjboudreaux/cc-thinking-skills (MIT). Retained 2026-09-08.

---

# Pre-Mortem Analysis

## Overview
The pre-mortem, developed by psychologist Gary Klein, uses "prospective hindsight" to improve risk identification. Instead of asking "What could go wrong?" (which triggers defensiveness), assume the project HAS failed and ask "Why did it fail?" This simple reframe improves risk identification by approximately 30%.

**Core Principle:** It's easier to explain failure after the fact than predict it beforehand. Use this bias productively.

## When to Use
- Project kickoff (before work begins)
- Before committing to a major technical decision
- Sprint planning for high-risk work
- Before launch or major release
- When team seems overconfident
- After a plan is formed but before execution

Decision flow:
```
Starting significant work? → yes → Team confident? → yes → PRE-MORTEM ESSENTIAL
                                                   ↘ no → Pre-mortem still valuable
                         ↘ no → Standard risk assessment may suffice
```

## The Process

### Step 1: Set the Stage (2 min)
Gather the team. Explain:
> "Imagine we're 6 months in the future. The project has failed—not just missed a deadline, but failed spectacularly. We're in the postmortem. Your job: explain what went wrong."

Key: Use past tense. The failure has already happened.

### Step 2: Silent Brainstorming (5-7 min)
Each person independently writes reasons for failure:
- No discussion during this phase
- Aim for 5-10 reasons each
- Include technical, process, people, and external factors
- Think about what YOU specifically might have contributed to failure

Prompt: "It's [future date]. The project failed. Write down all the reasons why."

### Step 3: Round-Robin Sharing (10-15 min)
Go around the room, each person shares ONE reason per round:
- No critiquing or dismissing
- Facilitator captures all items
- Continue until all unique reasons surfaced
- Duplicates show consensus on key risks

### Step 4: Categorize and Prioritize (5-10 min)
Group by theme and assess:

| Category | Risk | Likelihood | Impact | Priority |
|----------|------|------------|--------|----------|
| Technical | API integration fails | High | Critical | P0 |
| Process | Requirements unclear | Medium | High | P1 |
| People | Key person leaves | Low | Critical | P1 |
| External | Vendor delays | Medium | Medium | P2 |

### Step 5: Develop Mitigations (10-15 min)
For top risks, define:
```
Risk: API integration fails
Mitigation: 
- Spike on integration in week 1
- Identify fallback vendor
- Build abstraction layer for swap-ability
Owner: [Name]
Checkpoint: Week 2 review
```

### Step 6: Update the Plan
Incorporate mitigations into project plan:
- Add spike/investigation tasks
- Build in contingency time
- Assign risk owners
- Schedule risk review checkpoints

## Pre-Mortem Template

```markdown
# Pre-Mortem: [Project Name]
Date: [Date]
Participants: [Names]

## The Scenario
It is [Future Date]. [Project] has failed spectacularly. 

## Failure Reasons Identified

### Technical
- [Reason 1]
- [Reason 2]

### Process  
- [Reason 1]
- [Reason 2]

### People/Team
- [Reason 1]
- [Reason 2]

### External/Dependencies
- [Reason 1]
- [Reason 2]

## Priority Risks and Mitigations

### P0: [Risk Name]
- **Description**: [What went wrong]
- **Mitigation**: [How to prevent]
- **Owner**: [Who]
- **Checkpoint**: [When to verify]

### P1: [Risk Name]
...

## Plan Updates
- [ ] [Action item from pre-mortem]
- [ ] [Action item from pre-mortem]

## Review Schedule
- [Date]: First risk checkpoint
- [Date]: Mid-project risk review
```

## Why Pre-Mortems Work

1. **Legitimizes Pessimism**: Team members can voice concerns without seeming negative
2. **Bypasses Groupthink**: Individual brainstorming before sharing prevents anchoring
3. **Uses Hindsight Bias**: Easier to explain past than predict future
4. **Creates Psychological Safety**: "The project failed" removes blame
5. **Surfaces Hidden Knowledge**: People share concerns they wouldn't otherwise raise

## Common Failure Categories to Prompt

| Category | Example Failures |
|----------|-----------------|
| Requirements | Scope creep, unclear success criteria, missing stakeholder |
| Technical | Wrong architecture, integration failures, scale issues |
| Timeline | Underestimation, dependencies delayed, parallel work blocked |
| Team | Key person unavailable, skill gaps, communication breakdown |
| External | Vendor issues, regulatory changes, market shift |
| Process | Insufficient testing, deployment problems, no rollback |

## Facilitation Tips
- **Enforce silence** during brainstorming—no discussion
- **Use past tense** consistently ("failed" not "might fail")
- **Capture everything**—don't filter during collection
- **Include yourself**—what might YOU have done wrong?
- **Follow up**—pre-mortem is worthless without action

## Verification Checklist
- [ ] Conducted at appropriate time (before significant work)
- [ ] All team members participated
- [ ] Silent brainstorming enforced
- [ ] 20+ failure reasons collected
- [ ] Risks prioritized by likelihood × impact
- [ ] Top 3-5 risks have explicit mitigations
- [ ] Mitigations assigned owners and checkpoints
- [ ] Plan updated to incorporate findings
- [ ] Follow-up risk review scheduled

## Key Questions
- "The project failed. Why?"
- "What did we miss that was obvious in retrospect?"
- "What warning signs did we ignore?"
- "What did I personally contribute to the failure?"
- "What did we assume that turned out to be wrong?"
- "Who did we forget to involve?"


---

# Absorbed framework: Inversion

> Upstream folded this framework's mechanism into `pre-mortem` (see SKILL.md). The original lesson is kept here in full.

# Inversion Thinking

## Overview
Inversion thinking, championed by Charlie Munger and rooted in mathematician Carl Jacobi's principle "Invert, always invert," approaches problems by considering their opposite. Instead of asking "How do I succeed?", ask "How would I guarantee failure?" then avoid those paths.

**Core Principle:** "All I want to know is where I'm going to die, so I'll never go there." — Charlie Munger

## When to Use
- Planning a new project, feature, or initiative
- Evaluating a decision before committing
- Identifying risks that optimistic thinking obscures
- Stuck on how to achieve a positive outcome
- Need to challenge assumptions in a plan
- Writing requirements or acceptance criteria

Decision flow:
```
Have a goal? → yes → Can you list ways to achieve it? → maybe → INVERT FIRST
                                                      ↘ no → Definitely invert
           ↘ no → Define goal, then invert
```

## The Process

### Step 1: Define the Goal Clearly
State what success looks like:
```
Goal: "Ship a reliable authentication system by Q2"
Goal: "Build a high-performing engineering team"
Goal: "Launch product with strong user retention"
```

### Step 2: Invert — Ask "How Would I Fail?"
List all ways to guarantee failure, ruin, or the opposite of your goal:

```
Goal: Ship reliable auth system
Inversions (How to guarantee failure):
- Skip security review and pen testing
- No rate limiting or brute force protection  
- Store passwords in plaintext
- No monitoring or alerting
- Skip edge cases in testing
- No documentation for on-call
- Single point of failure, no redundancy
- Ignore compliance requirements
- No rollback plan
- Deploy on Friday before vacation
```

### Step 3: Categorize the Failure Modes
Group by type and severity:

| Category | Failure Mode | Severity |
|----------|--------------|----------|
| Security | Plaintext passwords | Critical |
| Security | No rate limiting | High |
| Operations | No monitoring | High |
| Operations | No rollback plan | High |
| Process | Skip security review | Critical |
| Process | No documentation | Medium |
| Reliability | Single point of failure | High |

### Step 4: Convert to Avoidance Checklist
Transform each failure mode into a requirement:

```
Anti-goal: Store passwords in plaintext
→ Requirement: Use bcrypt/argon2 with appropriate work factor

Anti-goal: No rate limiting
→ Requirement: Implement rate limiting with exponential backoff

Anti-goal: Deploy Friday before vacation
→ Requirement: No deploys within 48h of team unavailability
```

### Step 5: Prioritize by Impact
Focus on avoiding the failures that would be:
- Most damaging if they occurred
- Most likely to occur without explicit prevention
- Hardest to recover from

## Application Patterns

### For Technical Design
```
Goal: Build scalable API
Invert: How to make it fail under load?
- No caching → Add caching layer
- Synchronous everything → Add async where appropriate  
- No connection pooling → Implement pooling
- N+1 queries → Eager loading, query optimization
- No circuit breakers → Add circuit breakers
```

### For Code Review
```
Goal: Merge high-quality code
Invert: What would make this PR problematic?
- Introduces security vulnerability
- Breaks existing functionality
- No tests for new behavior
- Unclear intent/poor naming
- Performance regression
- Missing error handling
```

### For Career/Team Building
```
Goal: Build successful engineering career
Invert (Munger's list of what to avoid):
- Be unreliable
- Learn only from your own mistakes (ignore others')
- Give up after first failure
- Be resentful and envious
- Stay within comfort zone
- Avoid difficult conversations
- Don't learn continuously
```

### For Project Planning
```
Goal: Successful product launch
Invert: How to guarantee launch failure?
- No user research → Validate with users
- No load testing → Load test before launch
- No rollback capability → Build rollback
- No success metrics defined → Define metrics upfront
- Team burnout → Sustainable pace
- No communication plan → Prepare stakeholder comms
```

## Combining with Pre-Mortem
Inversion + Pre-Mortem creates powerful risk identification:

1. **Inversion**: List ways the project could fail (theoretical)
2. **Pre-Mortem**: Imagine it DID fail, explain why (narrative)
3. **Synthesize**: Combine both lists, prioritize, mitigate

## Common Inversions for Software

| Domain | Goal | Key Inversions to Avoid |
|--------|------|------------------------|
| Security | Secure system | Trusting user input, weak auth, exposed secrets |
| Performance | Fast system | No caching, blocking calls, no indexes |
| Reliability | Stable system | No monitoring, no redundancy, no graceful degradation |
| Maintainability | Clean code | No tests, cryptic names, tight coupling |
| Team | High performance | Poor communication, no psychological safety, unclear goals |

## Verification Checklist
- [ ] Goal clearly defined
- [ ] Listed 10+ ways to fail/achieve opposite
- [ ] Categorized failures by type and severity
- [ ] Converted top failures to explicit requirements
- [ ] Verified plan addresses the most critical inversions
- [ ] Shared inversions with team for blind spot check

## Key Questions
- "What would guarantee failure here?"
- "What mistakes do others commonly make?"
- "What am I most likely to overlook?"
- "If this fails spectacularly, what will the postmortem say?"
- "What would I tell someone else to avoid?"
- "What would the opposite of success look like, specifically?"

## Munger's Warning
"It is remarkable how much long-term advantage people like us have gotten by trying to be consistently not stupid, instead of trying to be very intelligent."

The power of inversion is in avoiding obvious errors that optimism blinds us to. Simple avoidance often beats clever optimization.
