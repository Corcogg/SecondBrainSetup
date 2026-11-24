# Systems — worked examples and seminar material

> Read this when studying the method or when a plan asks for a walkthrough ("teach me"). `SKILL.md` is the
> procedure /plan loads; this file is the correctness reference for it and keeps everything the short
> procedure left out: origin, worked examples, facilitation steps, templates, and key questions.
> Source: the April 2026 snapshot of tjboudreaux/cc-thinking-skills (MIT). Retained 2026-09-08.

---

# Systems Thinking

## Overview
Systems thinking views problems as part of interconnected wholes rather than isolated components. It focuses on relationships, feedback loops, and emergent properties—behaviors that arise from interactions and can't be predicted from parts alone. Essential for debugging complex distributed systems and understanding why "obvious" fixes often fail.

**Core Principle:** The behavior of a system cannot be understood by analyzing components in isolation. Look at connections, feedback, and emergence.

## When to Use
- Debugging issues that span multiple services/components
- Understanding unexpected emergent behavior
- Designing resilient architectures
- Analyzing incidents and outages
- When fixing one thing breaks another
- Performance issues with non-obvious causes
- Organizational/process problems

Decision flow:
```
Problem spans multiple components?     → yes → APPLY SYSTEMS THINKING
Fix in one place caused issue in another? → yes → APPLY SYSTEMS THINKING
Behavior seems "emergent" or unexpected?  → yes → APPLY SYSTEMS THINKING
```

## Key Concepts

### 1. Feedback Loops

**Reinforcing (Positive) Loops:** Amplify change
```
Technical Debt Loop:
Deadline pressure → Shortcuts → More bugs → More firefighting 
                                           ↓
                            ← Less time for quality ←
```

**Balancing (Negative) Loops:** Counteract change
```
Auto-scaling Loop:
Load increases → More instances spawn → Load per instance decreases
                                       ↓
                    ← Fewer instances needed ←
```

**Questions to identify loops:**
- Does this effect feed back into its cause?
- Is this self-reinforcing or self-correcting?
- What keeps this system in equilibrium?

### 2. Stocks and Flows
**Stocks:** Accumulated quantities (users, technical debt, cache size)
**Flows:** Rates of change (registrations/day, bugs fixed/sprint)

```
┌─────────────────────────────────────┐
│  Inflow → [Stock] → Outflow         │
│                                     │
│  New bugs → [Bug Backlog] → Fixes   │
│  Requests → [Queue Depth] → Processed│
│  Hires → [Team Size] → Attrition    │
└─────────────────────────────────────┘
```

**Key insight:** Stocks change slowly even when flows change quickly. Queue depth doesn't drop instantly when you add capacity.

### 3. Delays
Time lags between cause and effect obscure relationships:
```
Code deployed → [Delay: Cache TTL] → Users see change
Feature shipped → [Delay: Adoption curve] → Metrics change  
New hire starts → [Delay: Ramp-up] → Productivity impact
```

**Danger:** Acting before feedback arrives leads to overcorrection.

### 4. Non-Linear Relationships
Small changes can have large effects (and vice versa):
```
Linear assumption: 2x traffic = 2x latency
Reality: Traffic crosses threshold → 10x latency (queue buildup)

Linear assumption: Adding engineer adds capacity
Reality: Communication overhead grows O(n²)
```

### 5. Emergent Properties
Behaviors that arise from interactions, not individual components:
- **Distributed system:** No single service is slow, but the system is slow (cascading delays)
- **Team dynamics:** No individual is toxic, but collaboration is toxic (incentive interactions)
- **Market behavior:** No actor intends a bubble, but bubble emerges

## Systems Debugging Process

### Step 1: Map the System
Draw components, connections, and data/control flows:
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │────▶│   API   │────▶│   DB    │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ▼
               ┌─────────┐
               │  Cache  │
               └─────────┘
```

### Step 2: Identify Feedback Loops
For each loop, determine:
- Is it reinforcing or balancing?
- What's the delay in the loop?
- What could make it unstable?

```
Retry Storm Loop (Reinforcing - Dangerous):
Service slow → Clients retry → More load → Service slower → More retries
```

### Step 3: Trace Upstream
Follow the symptom backward to find originating cause:
```
Symptom: High latency in Service C
→ Service C waiting on Service B
  → Service B waiting on Service A
    → Service A doing full table scan (ROOT CAUSE)
```

### Step 4: Look for Interactions
What happens when components interact under stress?
- Circuit breakers tripping
- Cascading timeouts
- Resource contention
- Thundering herd

### Step 5: Consider Time Dynamics
- When did this start?
- What changed recently (deploys, config, traffic)?
- Is it periodic? (Cron jobs, cache expiration, batch processes)
- Is it growing or stabilizing?

## Common System Patterns

### Cascading Failure
```
One component fails → Dependent components overload → They fail
                                                    ↓
                              ← More traffic to remaining ←
```
**Mitigation:** Circuit breakers, bulkheads, graceful degradation

### Thundering Herd
```
Cache expires → All requests hit backend simultaneously → Overload
```
**Mitigation:** Jittered expiration, cache warming, request coalescing

### Queue Backup
```
Processing rate < Arrival rate → Queue grows → Memory pressure → OOM
```
**Mitigation:** Backpressure, rate limiting, queue bounds

### Resource Contention
```
Multiple processes → Same resource → Lock contention → Serialization
                                                     ↓
                    Throughput collapses despite available CPU
```
**Mitigation:** Sharding, optimistic locking, resource isolation

## Causal Loop Diagram Template

```
┌──────────────────────────────────────────────────────────────┐
│                    System: [Name]                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│    ┌─────────┐                        ┌─────────┐           │
│    │ Factor  │──────(+)──────────────▶│ Factor  │           │
│    │    A    │                        │    B    │           │
│    └─────────┘                        └────┬────┘           │
│         ▲                                  │                │
│         │                                  │                │
│        (-)                                (+)               │
│         │                                  │                │
│         │         ┌─────────┐              │                │
│         └─────────│ Factor  │◀─────────────┘                │
│                   │    C    │                               │
│                   └─────────┘                               │
│                                                              │
│   Legend: (+) = same direction, (-) = opposite direction    │
│   Loop type: Reinforcing / Balancing                        │
└──────────────────────────────────────────────────────────────┘
```

## Leverage Points
Where small changes have large effects (Donella Meadows):

| Leverage | Example | Impact |
|----------|---------|--------|
| Parameters | Timeout values | Low |
| Buffer sizes | Queue limits | Low-Medium |
| Feedback loops | Add monitoring | Medium |
| Information flows | Make metrics visible | Medium-High |
| Rules | Change retry policy | High |
| Goals | Redefine SLOs | Very High |
| Paradigm | Rethink architecture | Transformational |

## Verification Checklist
- [ ] Mapped system components and connections
- [ ] Identified at least one feedback loop
- [ ] Traced symptom upstream to potential root causes
- [ ] Considered time delays in the system
- [ ] Looked for emergent/interaction effects
- [ ] Identified leverage points for intervention
- [ ] Considered unintended consequences of fix

## Key Questions
- "What feeds back into what?"
- "Where are the delays in this system?"
- "What happens when this scales 10x?"
- "What would an observer see vs. what's actually happening?"
- "If I fix this here, what breaks over there?"
- "What behavior emerges that no single component intends?"
- "Where is the smallest change with the largest effect?"

## Meadows' Reminder
"We can't control systems or figure them out. But we can dance with them."

Systems resist simple fixes. Effective intervention requires understanding the whole, finding leverage points, and accepting that you're influencing, not controlling.


---

# Absorbed framework: Archetypes

> Upstream folded this framework's mechanism into `systems` (see SKILL.md). The original lesson is kept here in full.

# Systems Archetypes

## Overview

Systems archetypes, developed by Peter Senge in "The Fifth Discipline," are recurring patterns of behavior in organizations and systems. Like design patterns in software, once you recognize them, you see them everywhere—and more importantly, you can predict where they lead and intervene effectively.

**Core Principle:** Most organizational problems aren't unique. They follow predictable patterns with predictable consequences. Recognizing the pattern reveals the leverage points.

## When to Use

- The same problems keep recurring despite multiple "fixes"
- Quick fixes seem to make things worse over time
- Teams or departments are stuck in counterproductive cycles
- Growth has stalled without obvious cause
- Competition or conflict is escalating destructively
- Shared resources are being depleted
- Success in one area is starving others

Decision flow:

```
Problem keeps recurring despite fixes?  → yes → APPLY ARCHETYPES
Growth hit invisible ceiling?           → yes → APPLY ARCHETYPES
Competition escalating destructively?   → yes → APPLY ARCHETYPES
Shared resource degrading?              → yes → APPLY ARCHETYPES
```

## The Seven Core Archetypes

### 1. Fixes That Fail

**Pattern:** A quick fix addresses symptoms but creates side effects that eventually make the original problem worse.

```
        Problem
           │
           ▼
     ┌─────────────┐
     │  Quick Fix  │──────────────┐
     └─────────────┘              │
           │                      │
           ▼                      │
      Symptom Relief              │
      (short-term)                │
                                  ▼
                          Unintended
                          Consequence
                                  │
                                  │ (delay)
                                  │
                                  ▼
                            Problem
                            Worsens
```

**Recognition Signs:**

- "We fixed this last quarter, why is it back?"
- Solution requires repeated application with increasing doses
- New problems emerged after implementing the fix
- The fix addresses symptoms, not root cause

**Software Examples:**

- Adding more servers instead of fixing memory leak → costs spiral, leak remains
- Hiring contractors to meet deadline → knowledge loss increases future delays
- Skipping tests to ship faster → bugs multiply, requiring more hotfixes
- Silencing alerts instead of investigating → system degrades until outage

**Leverage Points:**

- Identify and address root cause, not symptoms
- Ask "What side effects might this create?"
- Build in delay to observe consequences before scaling fix
- Make unintended consequences visible early

---

### 2. Shifting the Burden

**Pattern:** A symptomatic solution is used instead of a fundamental solution, reducing pressure to address the real problem and creating dependency.

```
                 Problem Symptom
                 ┌─────┴─────┐
                 ▼           ▼
          ┌──────────┐  ┌──────────────┐
          │Symptomatic│  │ Fundamental  │
          │ Solution  │  │  Solution    │
          └────┬─────┘  └──────┬───────┘
               │               │
               │ (quick)       │ (slow, hard)
               │               │
               ▼               ▼
          Relief +          Actual
          Dependency        Resolution
               │
               ▼
          Fundamental
          Solution Atrophies
```

**Recognition Signs:**

- Heavy reliance on workarounds
- "We know the real fix, but we don't have time"
- Expertise for fundamental solution is disappearing
- External helpers (consultants, contractors) are permanent

**Software Examples:**

- Using feature flags to hide bugs → never fixing underlying issues
- Operations team manually intervening → no investment in automation
- Senior devs always fixing junior code → juniors never learn
- Buying SaaS tools instead of building core capability → vendor lock-in

**Leverage Points:**

- Make the fundamental solution visible and valued
- Track and limit use of symptomatic solutions
- Invest in building internal capability
- Ask "What capability are we not developing by using this workaround?"

---

### 3. Limits to Growth

**Pattern:** A reinforcing loop drives growth, but eventually encounters a balancing constraint that slows or stops growth.

```
     ┌───────────────────────────────────┐
     │                                   │
     ▼                                   │
  Growing        ────(+)────▶        Results
  Action                                 │
                                         │
                                         │
                    ┌────────────────────┘
                    │
                    ▼
              ┌───────────┐
              │ Limiting  │
              │ Condition │
              └─────┬─────┘
                    │
                    │ (-)
                    ▼
              Slowing
              Action
```

**Recognition Signs:**

- Growth was strong, then plateaued without obvious cause
- More effort yields diminishing returns
- A resource or capability is maxed out
- Success is creating its own bottlenecks

**Software Examples:**

- Team velocity drops as codebase grows (complexity limit)
- Adding engineers doesn't speed delivery (communication overhead)
- Feature growth slows due to technical debt (architectural limit)
- User growth outpaces database capacity (infrastructure limit)

**Leverage Points:**

- Identify the limiting factor early, before it binds
- Invest in removing constraints BEFORE they become critical
- Don't push harder on the reinforcing loop—address the constraint
- Ask "What will limit our growth at 10x scale?"

---

### 4. Tragedy of the Commons

**Pattern:** Individuals gain by using a shared resource, but collective overuse depletes the resource for everyone.

```
     ┌──────────────┐       ┌──────────────┐
     │  Actor A's   │       │  Actor B's   │
     │   Activity   │       │   Activity   │
     └──────┬───────┘       └──────┬───────┘
            │                      │
            │ (individual gain)    │ (individual gain)
            │                      │
            ▼                      ▼
       ┌────────────────────────────────┐
       │       Shared Resource          │
       │    (depletes over time)        │
       └────────────────────────────────┘
                      │
                      │ (delay)
                      ▼
              Resource Degradation
              Affects All Actors
```

**Recognition Signs:**

- Shared resources are degrading (CI/CD, staging environments, shared services)
- Everyone optimizes locally at expense of global system
- "Somebody else will fix it" mentality
- No clear ownership of shared infrastructure

**Software Examples:**

- Teams overload shared CI/CD → everyone's builds slow down
- No one invests in shared libraries → they rot
- Staging environment becomes unreliable → everyone bypasses it
- On-call knowledge isn't documented → tribal knowledge concentrates
- Cloud costs spike as teams spin up resources without cleanup

**Leverage Points:**

- Make usage visible and attributable
- Create feedback loops (chargebacks, quotas, dashboards)
- Establish shared governance with clear ownership
- Align individual incentives with collective health
- Ask "Who is responsible for the long-term health of this?"

---

### 5. Escalation

**Pattern:** Two parties perceive their success as relative to each other. Each side's actions provoke response, leading to escalating competition that harms both.

```
     ┌─────────────┐              ┌─────────────┐
     │  Actor A    │              │  Actor B    │
     │   Action    │              │   Action    │
     └──────┬──────┘              └──────┬──────┘
            │                            │
            │     ┌───────────────┐      │
            └────▶│  Relative     │◀─────┘
                  │  Standing     │
                  └───────────────┘
                          │
                          │ (perceived threat)
            ┌─────────────┴─────────────┐
            ▼                           ▼
       A Increases                 B Increases
         Action                      Action
            │                           │
            └───────────────────────────┘
                     (cycle repeats)
```

**Recognition Signs:**

- "They did X, so we have to do Y"
- Arms race dynamics in spending, features, or resources
- Each side feels defensive, not aggressive
- Win-lose framing of what could be win-win

**Software Examples:**

- Feature war with competitor → both over-invest, neither profits
- Microservices teams duplicating functionality → bloat and inconsistency
- Departments hoarding headcount → organizational inefficiency
- Interview arms race → absurd technical interviews that don't predict success

**Leverage Points:**

- Step back and question the "game" being played
- Find ways to opt out or change the rules
- Establish shared standards or agreements
- Focus on absolute value, not relative position
- Ask "What would happen if we stopped competing on this dimension?"

---

### 6. Success to the Successful

**Pattern:** If success gives access to more resources, initial advantages compound while others are starved, creating winner-take-all dynamics.

```
     ┌─────────────┐              ┌─────────────┐
     │  Actor A    │              │  Actor B    │
     │  (initial   │              │  (initial   │
     │   success)  │              │  struggle)  │
     └──────┬──────┘              └──────┬──────┘
            │                            │
            ▼                            ▼
      More Resources              Fewer Resources
      Allocated to A              Allocated to B
            │                            │
            ▼                            ▼
      A More Likely               B Less Likely
      to Succeed                  to Succeed
            │                            │
            └───────────────────────────┘
                   (cycle compounds)
```

**Recognition Signs:**

- Star performers get more opportunities, others stagnate
- Successful products get more investment, experiments are starved
- Some teams have surplus resources while others are underwater
- Past success is the main predictor of future investment

**Software Examples:**

- Legacy monolith gets all attention → new architecture never matures
- Star engineer gets all interesting projects → others disengage
- Flagship product consumes resources → innovation pipeline dies
- Cloud costs centralized → teams with budget dominate

**Leverage Points:**

- Ensure fair initial resource allocation
- Create protected space for emerging initiatives
- Evaluate on trajectory, not just current position
- Deliberately invest in "underdogs" with potential
- Ask "Are we starving future successes to feed current ones?"

---

### 7. Growth and Underinvestment

**Pattern:** Growth approaches a limit that could be addressed by investment in capacity, but the investment isn't made until performance degrades, triggering a crisis.

```
        Demand
           │
           │ (grows)
           ▼
     ┌───────────┐
     │  Capacity │ (fixed or slowly growing)
     └───────────┘
           │
           │ (demand > capacity)
           ▼
     Performance
     Degradation
           │
           │ (finally triggers)
           ▼
     Investment
     Decision
           │
           │ (but with delay)
           ▼
     Capacity
     Increase
     (too late, crisis already happened)
```

**Recognition Signs:**

- "We'll invest in X when we really need it"
- Performance degrades, then investment happens reactively
- Chronic underinvestment in infrastructure, platform, or people
- Standard is "good enough for now"

**Software Examples:**

- Database not upgraded until it crashes under load
- Security investment only after breach
- Team not grown until burnout causes attrition
- Technical debt addressed only during outages
- Documentation written only when onboarding fails

**Leverage Points:**

- Define performance standards and invest to maintain them
- Lead indicators (not lag) should trigger investment
- Calculate cost of delayed investment (opportunity cost, crisis cost)
- Build investment into growth plans proactively
- Ask "What will fail if we grow 50% without additional investment?"

---

## Archetype Diagnosis Process

### Step 1: Describe the Problem Neutrally

Document what's happening without blame:

- What symptoms are visible?
- Who is involved?
- What has been tried?
- What keeps recurring?

### Step 2: Map the Feedback Loops

Draw the causal connections:

- What causes what?
- Where are reinforcing loops (amplifying)?
- Where are balancing loops (limiting)?
- Where are delays?

### Step 3: Match to Archetype

Compare your map to the seven patterns:

| If You See... | Consider Archetype |
|---------------|-------------------|
| Fix that makes problem worse over time | Fixes That Fail |
| Workaround becoming dependency | Shifting the Burden |
| Growth hitting invisible ceiling | Limits to Growth |
| Shared resource degrading | Tragedy of the Commons |
| Competitive spiral harming both sides | Escalation |
| Winner-take-all resource dynamics | Success to the Successful |
| Reactive investment after crisis | Growth and Underinvestment |

### Step 4: Identify Leverage Points

Don't push on the obvious—find where small changes have large effects:

- Where can you break a reinforcing loop?
- Where can you remove a constraint?
- What information is missing that would change behavior?
- What incentives are misaligned?

### Step 5: Design Intervention

Target the structure, not the symptoms:

- What fundamental solution is being avoided?
- What constraint needs investment?
- What feedback loop is missing or delayed?
- How can you make the system self-correcting?

---

## Quick Reference Card

| Archetype | Pattern | Key Question |
|-----------|---------|--------------|
| Fixes That Fail | Quick fix creates long-term problems | "What side effects will this create?" |
| Shifting the Burden | Dependency on symptomatic solutions | "What capability are we not building?" |
| Limits to Growth | Reinforcing loop hits constraint | "What will limit us at 10x?" |
| Tragedy of the Commons | Individual gain depletes shared resource | "Who owns the long-term health?" |
| Escalation | Competitive loop worsens both | "Can we change the game?" |
| Success to the Successful | Winner-take-all dynamics | "Are we starving future successes?" |
| Growth and Underinvestment | Capacity lags demand until crisis | "What fails at 50% growth?" |

## Verification Checklist

- [ ] Problem described without blame
- [ ] Feedback loops mapped (reinforcing and balancing)
- [ ] Delays identified in the system
- [ ] Matched to one or more archetypes
- [ ] Leverage points identified (not just symptoms)
- [ ] Intervention targets structure, not behavior
- [ ] Unintended consequences of intervention considered

## Key Questions

- "What pattern is this system stuck in?"
- "Where would a small change have a large effect?"
- "What fundamental solution are we avoiding?"
- "What would make this system self-correcting?"
- "If we do nothing, where does this pattern lead?"
- "Who benefits from the current structure persisting?"

## Senge's Wisdom

"Structures of which we are unaware hold us prisoner. Once we can see them, they no longer have the same hold on us."

Recognizing the archetype is the first step to escaping it. The pattern will continue until someone sees it and changes the underlying structure—not the behaviors, but what's driving them.


---

# Absorbed framework: Feedback Loops

> Upstream folded this framework's mechanism into `systems` (see SKILL.md). The original lesson is kept here in full.

# Feedback Loop Analysis

## Overview

Feedback loop analysis, developed by Donella Meadows in "Thinking in Systems," provides a rigorous framework for understanding how systems behave over time. All dynamic systems—software, organizations, markets, products—are driven by feedback loops that either amplify change (reinforcing) or stabilize toward goals (balancing). Understanding these loops reveals why systems grow, collapse, oscillate, or resist change.

**Core Principle:** System behavior emerges from feedback structure. To change behavior, change the loops.

## When to Use

- Analyzing organizational dynamics (growth, stagnation, dysfunction)
- Designing product growth loops and retention mechanisms
- Debugging systems exhibiting runaway growth or collapse
- Understanding why a system oscillates instead of stabilizing
- Finding high-leverage intervention points
- Predicting unintended consequences of changes
- Understanding why "obvious" fixes fail or backfire

Decision flow:

```
System behavior is puzzling or problematic?
  → Is it growing/shrinking unexpectedly?   → Look for REINFORCING LOOPS
  → Is it oscillating around a target?      → Look for DELAYS in BALANCING LOOPS
  → Is it stuck/resistant to change?        → Look for dominant BALANCING LOOPS
  → Need to intervene effectively?          → Find LEVERAGE POINTS
```

## Core Concepts

### 1. Reinforcing Loops (Positive Feedback)

Reinforcing loops amplify change in the same direction—growth or decline. They create exponential behavior: the more you have, the more you get (or lose).

**Structure:** A → increases B → increases A (or: A → decreases B → decreases A)

```
┌─────────────────────────────────────────────────────────┐
│              REINFORCING LOOP (R)                       │
│                                                         │
│         ┌──────────┐         ┌──────────┐              │
│         │  Users   │───(+)──▶│  Content │              │
│         └──────────┘         └────┬─────┘              │
│              ▲                    │                     │
│              │                   (+)                    │
│              │                    │                     │
│              └────────────────────┘                     │
│                                                         │
│   More users → More content → More users (Growth)      │
│   OR: Fewer users → Less content → Fewer users (Death) │
└─────────────────────────────────────────────────────────┘
```

**Characteristics:**

- Exponential growth or collapse
- Self-fulfilling prophecies
- "Rich get richer" dynamics
- Virtuous cycles (when beneficial)
- Vicious cycles (when harmful)

**Software/Product Examples:**

```
Network Effect Loop:
Users → Value to other users → More users → More value
(Slack, social networks, marketplaces)

Technical Debt Loop:
Shortcuts → Bugs → Firefighting → Less time → More shortcuts
(Vicious cycle toward collapse)

Learning Loop:
Practice → Skill → Confidence → More practice → More skill
(Virtuous cycle of improvement)

Viral Growth Loop:
Users → Invitations → New users → More invitations
(Product-led growth)
```

### 2. Balancing Loops (Negative Feedback)

Balancing loops counteract change, pushing the system toward a goal or equilibrium. They create goal-seeking behavior.

**Structure:** Gap between actual and goal → corrective action → reduces gap

```
┌─────────────────────────────────────────────────────────┐
│              BALANCING LOOP (B)                         │
│                                                         │
│   ┌──────────┐                    ┌──────────┐         │
│   │   Goal   │                    │  Actual  │         │
│   │  State   │                    │  State   │         │
│   └────┬─────┘                    └────┬─────┘         │
│        │                               │                │
│        └──────────┬────────────────────┘                │
│                   ▼                                     │
│             ┌──────────┐                               │
│             │   Gap    │                               │
│             └────┬─────┘                               │
│                  │                                      │
│                 (-)                                     │
│                  ▼                                      │
│           ┌────────────┐                               │
│           │ Corrective │                               │
│           │   Action   │────────▶ Closes gap           │
│           └────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**Characteristics:**

- Goal-seeking behavior
- Resistance to change
- Stability (when working well)
- Oscillation (when delays exist)

**Software/Product Examples:**

```
Auto-scaling Loop:
Load increases → Gap from target → Scale up → Load per instance decreases
(Goal: maintain target response time)

Thermostat Pattern:
Temperature differs from setpoint → HVAC adjusts → Temperature approaches setpoint
(Goal-seeking to maintain state)

Hiring Loop:
Work exceeds capacity → Hire → Capacity increases → Work/person normalizes
(Goal: sustainable workload)

Quality Gate Loop:
Defects detected → Review/fix required → Quality improves → Fewer defects
(Goal: maintain quality standards)
```

### 3. Delays

Delays are the time between cause and effect. They are the primary source of oscillation and instability in systems.

```
┌─────────────────────────────────────────────────────────┐
│                   DELAY EFFECTS                         │
│                                                         │
│   Action ───────[DELAY]─────────▶ Effect               │
│                                                         │
│   Short delay: System responds smoothly                 │
│   Long delay: Overshoot and oscillation                │
│                                                         │
│   Examples:                                             │
│   • Code deploy → [Cache TTL] → Users see change       │
│   • New hire → [Ramp-up time] → Productivity impact    │
│   • Feature ship → [Adoption] → Metric movement        │
│   • Training → [Skill development] → Performance gain  │
└─────────────────────────────────────────────────────────┘
```

**Why Delays Cause Oscillation:**

```
Without delay:
  Gap detected → Correction → Gap closes → Done

With delay:
  Gap detected → Correction → [DELAY] → Gap persists →
  More correction → [DELAY] → Original correction arrives →
  Overshoot → Gap in opposite direction → Oscillation
```

**Classic Example: Shower Temperature**

```
Too cold → Turn hot → [Delay: water travels through pipes] →
Still cold → Turn hotter → Hot water arrives → Too hot! →
Turn cold → [Delay] → Still hot → Turn colder →
Cold water arrives → Too cold! → Oscillation continues
```

## Common System Patterns

### Pattern 1: Exponential Growth

**Structure:** Single dominant reinforcing loop

```
┌─────────┐      ┌─────────┐
│ Revenue │─(+)─▶│ Invest- │
│         │      │  ment   │
└────▲────┘      └────┬────┘
     │                │
    (+)              (+)
     │                │
     └────────────────┘
         Growth
```

**Behavior:** J-curve growth (or collapse if running in reverse)

**Examples:**

- Startup hypergrowth phase
- Viral spread
- Compounding interest
- Technical debt accumulation

**Intervention:** Find or create balancing loops before runaway

### Pattern 2: Goal-Seeking (with Oscillation)

**Structure:** Balancing loop with significant delay

```
┌────────┐      ┌────────┐
│  Goal  │      │ Actual │
└───┬────┘      └───┬────┘
    │               │
    └───────┬───────┘
            ▼
         [Gap]
            │
           (-)
            │
            ▼
    ┌────────────┐
    │ Correction │───[DELAY]───▶ Effect
    └────────────┘
```

**Behavior:** Oscillation around goal, amplitude depends on delay length

**Examples:**

- Inventory management (bullwhip effect)
- Hiring cycles (overhire → layoffs → understaffed → overhire)
- Feature prioritization swings
- Performance optimization iterations

**Intervention:** Shorten delays, reduce correction magnitude, accept longer settling time

### Pattern 3: Limits to Growth

**Structure:** Reinforcing loop eventually hits a balancing constraint

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
┌────────┐                          ┌─────┴────┐
│ Growth │──(+)──▶ Success ──(-)──▶│ Resource │
│ Effort │                          │  Limit   │
└────────┘                          └──────────┘
    │
    └──(+)──▶ Results (initially)
```

**Behavior:** S-curve—growth, plateau, then stagnation or decline

**Examples:**

- Market saturation
- Team scaling limits
- System capacity constraints
- Feature exhaustion

**Intervention:** Identify and address the constraint before hitting it

### Pattern 4: Shifting the Burden

**Structure:** Symptomatic solution undermines fundamental solution

```
                    ┌──────────────┐
                    │   Problem    │
                    │   Symptom    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            │            ▼
      ┌───────────┐        │    ┌───────────────┐
      │  Quick    │        │    │  Fundamental  │
      │   Fix     │        │    │   Solution    │
      └─────┬─────┘        │    └───────┬───────┘
            │              │            │
           (+)             │           (+)
            │              │            │
            ▼              │            ▼
    Symptom relief ────────┘    Root cause fixed
            │                          ▲
           (-)                         │
            ▼                          │
    Motivation to ─────────────────────┘
    fix root cause
```

**Behavior:** Addiction to quick fixes; fundamental capability atrophies

**Examples:**

- Heroic firefighting vs. systemic reliability
- Overtime vs. hiring/process improvement
- Manual workarounds vs. automation
- External consultants vs. internal capability

**Intervention:** Deliberately invest in fundamental solution while managing symptoms

### Pattern 5: Escalation (Arms Race)

**Structure:** Two competing reinforcing loops

```
┌─────────┐      ┌─────────┐
│ Party A │──▶   │ Party B │
│ Action  │  ▲   │ Action  │
└────┬────┘  │   └────┬────┘
     │       │        │
    (+)      │       (+)
     │       │        │
     └───────┴────────┘
         Threat
```

**Behavior:** Mutual escalation until resource exhaustion or intervention

**Examples:**

- Feature wars between competitors
- Meeting proliferation
- Process/bureaucracy accumulation
- Alert fatigue spirals

**Intervention:** Break the loop through agreement, constraint, or reframing

## Identifying Loops in Systems

### Step 1: Map the Variables

List all relevant quantities that change over time:

```
Team productivity system:
- Team size
- Individual workload
- Code quality
- Technical debt
- Bug rate
- Firefighting time
- Feature velocity
- Morale
```

### Step 2: Draw Causal Connections

For each pair, ask: "Does A affect B? In which direction?"

```
(+) Same direction: A increases → B increases, A decreases → B decreases
(-) Opposite direction: A increases → B decreases
```

### Step 3: Trace the Loops

Follow the arrows back to starting point. Count the negative signs:

```
Even number of (-) = Reinforcing loop
Odd number of (-) = Balancing loop
```

### Step 4: Identify Dominant Loops

The system behavior is driven by currently dominant loops:

- Growing exponentially? Reinforcing loop dominates
- Oscillating? Balancing loop with delay
- Stable? Balancing loop working well
- Declining? Reinforcing loop in reverse

## Leverage Points

Donella Meadows' hierarchy of intervention effectiveness (increasing power):

| Level | Intervention | Example | Impact |
|-------|-------------|---------|--------|
| 12 | Constants/parameters | Adjust timeout values | Lowest |
| 11 | Buffer sizes | Increase queue limits | Low |
| 10 | Stock-flow structure | Add caching layer | Low |
| 9 | Delays | Shorten feedback cycles | Medium |
| 8 | Balancing loop strength | Improve monitoring | Medium |
| 7 | Reinforcing loop gain | Amplify growth drivers | Medium-High |
| 6 | Information flows | Make metrics visible | High |
| 5 | System rules | Change deployment policy | High |
| 4 | Self-organization | Enable team autonomy | Very High |
| 3 | System goals | Redefine success metrics | Very High |
| 2 | Paradigm/mindset | Shift from output to outcomes | Transformational |
| 1 | Transcend paradigms | Question the frame itself | Highest |

**Key insight:** Most interventions happen at levels 10-12 (parameters). The highest leverage is in goals, rules, and mental models.

## Application Framework

### Analyzing a Problematic System

```markdown
## Feedback Loop Analysis: [System Name]

### Current Behavior
[Describe: growing, declining, oscillating, stuck]

### Key Variables
- [List stocks and flows]

### Loop Diagram
[Draw or describe the loops]

### Identified Loops
| Loop Name | Type | Variables | Currently Dominant? |
|-----------|------|-----------|---------------------|
|           |      |           |                     |

### Delays Present
| Delay | Duration | Effect |
|-------|----------|--------|
|       |          |        |

### Leverage Points
| Level | Intervention | Expected Effect |
|-------|-------------|-----------------|
|       |             |                 |

### Recommended Intervention
[Highest-leverage, lowest-risk option]
```

### Designing a Growth System

```markdown
## Growth Loop Design: [Product/System]

### Core Reinforcing Loop
[User action] → [Value created] → [Trigger for more users] → [More user action]

### Supporting Loops
[Additional loops that feed the core]

### Balancing Constraints
[What limits growth and when it kicks in]

### Delays to Minimize
[Where feedback needs to be faster]

### Metrics to Monitor
[Leading indicators of loop health]
```

## Integration with Systems Thinking

This skill extends the `thinking-systems` skill by providing:

1. **Specific loop identification techniques** (vs. general systems mapping)
2. **Meadows' leverage point hierarchy** (vs. general intervention ideas)
3. **Pattern library** (exponential, oscillating, limits to growth, etc.)
4. **Delay analysis methodology** (root cause of oscillation)

Use together:

- `thinking-systems`: Map the overall system structure
- `thinking-feedback-loops`: Identify and analyze specific loops
- `thinking-second-order`: Trace consequences of interventions
- `thinking-pre-mortem`: Identify loops that could cause failure

## Verification Checklist

- [ ] Identified key variables that change over time
- [ ] Mapped causal connections with direction (+/-)
- [ ] Traced at least one reinforcing loop
- [ ] Traced at least one balancing loop
- [ ] Identified significant delays
- [ ] Determined currently dominant loop
- [ ] Identified leverage points at multiple levels
- [ ] Selected intervention with appropriate leverage
- [ ] Considered unintended effects of intervention

## Key Questions

- "What feeds back into itself here?"
- "Is this self-reinforcing or self-correcting?"
- "What's the goal this system is seeking?"
- "Where are the delays, and how long are they?"
- "Which loop is currently dominant?"
- "What would shift dominance to a different loop?"
- "What's the highest-leverage intervention available?"
- "If I change X, what loops are affected?"

## Meadows' Wisdom

"We can't control systems or figure them out. But we can dance with them."

"The least obvious part of the system, its function or purpose, is often the most crucial determinant of the system's behavior."

"Pay attention to what is important, not just what is quantifiable."

Systems are not puzzles to be solved but patterns to be understood and influenced. Effective intervention requires humility about control and attention to feedback.


---

# Absorbed framework: Leverage Points

> Upstream folded this framework's mechanism into `systems` (see SKILL.md). The original lesson is kept here in full.

# Leverage Points

## Overview

Donella Meadows' "Places to Intervene in a System" provides a hierarchy of intervention points ranked by their power to change system behavior. Most effort goes into low-leverage interventions (parameters, buffers) when high-leverage points (goals, paradigms) offer transformational change with less force.

**Core Principle:** The higher in the hierarchy, the more leverage—but also the more resistance. Find the highest leverage point you can actually move.

## When to Use

- Choosing where to focus engineering effort
- Prioritizing system improvements
- Organizational change initiatives
- Architecture evolution decisions
- Process optimization
- Resource allocation
- When incremental changes aren't working

Decision flow:

```
Want to change system behavior?
  → Have you tried high-leverage interventions? → no → START HIGHER
  → Are you stuck at low leverage? → yes → MOVE UP THE HIERARCHY
  → Is change not sticking? → yes → LOOK FOR BALANCING LOOPS
```

## The 12 Leverage Points (Low to High)

### Level 12: Constants and Parameters (LOWEST LEVERAGE)

**What:** Numbers—budgets, rates, thresholds, timeouts

**Examples:**
- Adjusting cache TTL
- Changing retry counts
- Modifying timeout values
- Tweaking rate limits

**Why low leverage:** Parameters rarely change behavior fundamentally. The system absorbs parameter changes and continues its pattern.

```
Intervention: Increase server timeout from 30s to 60s
Result: Slow requests succeed, but root cause remains
Leverage: Very low—masks symptom, doesn't fix system
```

### Level 11: Buffer Sizes

**What:** Stabilizing stocks—queues, caches, inventories

**Examples:**
- Queue depth limits
- Connection pool sizes
- Memory allocations
- Batch sizes

**Why low leverage:** Buffers absorb fluctuations but don't change system dynamics. Bigger buffer = slower response to change.

```
Intervention: Increase message queue size
Result: Handles traffic spikes, but processing lag grows
Leverage: Low—buys time but doesn't address throughput
```

### Level 10: Stock-and-Flow Structures

**What:** Physical architecture—how things are connected

**Examples:**
- Database schema
- Service topology
- Network architecture
- Team structure

**Why medium leverage:** Hard to change once built; design matters but is often locked in.

```
Intervention: Add read replica to reduce DB load
Result: Significant improvement in read performance
Leverage: Medium—structural change, but within existing paradigm
```

### Level 9: Delays

**What:** Time lags in feedback loops

**Examples:**
- Deployment pipeline duration
- Feedback cycle time
- Onboarding time
- Release frequency

**Why medium leverage:** Shortening delays makes systems more responsive and stable. Many oscillation problems are actually delay problems.

```
Intervention: Reduce deployment time from 2 hours to 10 minutes
Result: Faster feedback, fewer bugs reaching production
Leverage: Medium-high—changes system responsiveness fundamentally
```

### Level 8: Balancing Feedback Loops

**What:** Negative feedback that counteracts change

**Examples:**
- Auto-scaling rules
- Circuit breakers
- Quality gates
- Alerting thresholds

**Why medium-high leverage:** Strengthening balancing loops increases stability; weakening them enables change.

```
Intervention: Implement circuit breaker with automatic recovery
Result: Failures isolated, cascade prevention
Leverage: Medium-high—changes failure dynamics
```

### Level 7: Reinforcing Feedback Loops

**What:** Positive feedback that amplifies change

**Examples:**
- Growth loops (viral, network effects)
- Technical debt spirals
- Talent attraction/attrition cycles
- Performance improvement loops

**Why high leverage:** Reinforcing loops drive exponential growth or collapse. Controlling gain = controlling trajectory.

```
Intervention: Create "fix broken windows" culture that reinforces quality
Result: Quality begets quality, technical debt decreases
Leverage: High—self-sustaining improvement
```

### Level 6: Information Flows

**What:** Who has access to what information

**Examples:**
- Metrics dashboards
- Error visibility
- Cost attribution
- Performance feedback to developers

**Why high leverage:** Adding information where it was missing changes behavior dramatically. People respond to what they can see.

```
Intervention: Show cloud costs per team in real-time dashboard
Result: Teams optimize without mandates
Leverage: High—behavior change through visibility
```

### Level 5: System Rules

**What:** Incentives, constraints, permissions

**Examples:**
- Code review requirements
- Definition of done
- SLA agreements
- Approval processes
- Deployment policies

**Why high leverage:** Rules define what's allowed and rewarded. Change rules, change behavior.

```
Intervention: Require automated tests for all production code
Result: Test coverage increases, bug rate decreases
Leverage: High—changes what's acceptable
```

### Level 4: Self-Organization

**What:** Ability of the system to change its own structure

**Examples:**
- Team autonomy to change processes
- Ability to add/remove services
- Permission to experiment
- Organizational learning capacity

**Why very high leverage:** Systems that can evolve survive; rigid systems eventually fail.

```
Intervention: Give teams authority to choose their own tools/practices
Result: Innovation increases, best practices emerge and spread
Leverage: Very high—enables adaptation
```

### Level 3: System Goals

**What:** The purpose or function of the system

**Examples:**
- Success metrics
- OKRs and KPIs
- Definition of "winning"
- What's optimized for

**Why very high leverage:** Everything else serves the goal. Change the goal, change everything downstream.

```
Intervention: Change metric from "features shipped" to "user outcomes achieved"
Result: Teams focus on impact, not output
Leverage: Very high—redirects all effort
```

### Level 2: Paradigm (Mindset)

**What:** The shared assumptions from which goals arise

**Examples:**
- "Move fast and break things" vs "Boring technology"
- "Monolith is bad" vs "Right tool for context"
- "Engineering is a cost center" vs "Engineering creates value"

**Why transformational:** Paradigms are upstream of goals, rules, and structure. Shift the paradigm, transform the system.

```
Intervention: Shift from "avoid failure" to "learn from failure"
Result: Experimentation increases, innovation accelerates
Leverage: Transformational—changes what's thinkable
```

### Level 1: Transcending Paradigms (HIGHEST LEVERAGE)

**What:** The ability to change paradigms, recognizing no paradigm is "true"

**Examples:**
- Recognizing that current best practices are temporary
- Ability to hold multiple paradigms simultaneously
- Knowing when to abandon a paradigm

**Why highest leverage:** Freedom from paradigm lock-in enables choosing the right paradigm for each context.

```
Mastery: Recognize when "microservices always" became dogma
         Choose monolith when it's right
Result: Optimal architecture for each situation
Leverage: Highest—freedom from ideological constraints
```

## Applying Leverage Points

### Step 1: Identify Current Interventions

Where are you currently trying to create change?

```markdown
Current interventions:
- Increasing server count (Level 11 - buffers)
- Adjusting timeout parameters (Level 12 - parameters)
- Adding monitoring (Level 6 - information flows)
```

### Step 2: Map to Hierarchy

Plot on the hierarchy to see leverage distribution:

```
High Leverage    [3] Goals
                 [5] Rules
                 [6] Information ← Monitoring
                 [7] Reinforcing loops
Medium           [8] Balancing loops
                 [9] Delays
                 [10] Structure
Low Leverage     [11] Buffers ← Server count
                 [12] Parameters ← Timeouts
```

### Step 3: Look Higher

For each low-leverage intervention, ask: "What's the higher-leverage version?"

| Low Leverage | Ask | Higher Leverage |
|--------------|-----|-----------------|
| More servers | Why do we need more capacity? | Fix inefficient algorithm (structure) |
| Longer timeouts | Why are things slow? | Reduce delays in pipeline |
| More QA staff | Why so many bugs? | Change quality rules (Level 5) |

### Step 4: Assess Feasibility

Higher leverage often means more resistance. Evaluate:

```markdown
Intervention: Change success metric from velocity to outcomes
Leverage: Level 3 (Goals) - Very High
Resistance: High - threatens existing measurement systems
Feasibility: Medium - needs executive buy-in
Strategy: Pilot with one team, demonstrate results, expand
```

### Step 5: Choose Highest Feasible Leverage

Select the highest-leverage intervention you can actually execute.

## Common Patterns

### The Parameter Trap

Teams endlessly tune parameters when the real issue is structural:

```
Symptom: Constantly adjusting cache TTLs, retry counts, timeouts
Reality: Architecture doesn't match access patterns
Solution: Redesign data flow (Level 10) instead of tuning parameters
```

### The Information Unlock

Missing information often explains dysfunction:

```
Symptom: Teams make poor resource decisions
Reality: They can't see the cost of their decisions
Solution: Make costs visible (Level 6)
Result: Behavior changes without mandates
```

### The Goal Inversion

Metrics become goals, then become gamed:

```
Symptom: High velocity, low impact
Reality: Measuring output, not outcomes
Solution: Change the goal to user value delivered (Level 3)
```

### The Paradigm Shift

Sometimes the whole frame is wrong:

```
Symptom: Constant firefighting despite process improvements
Reality: "Heroism" paradigm rewards firefighting over prevention
Solution: Shift to "boring is good" paradigm (Level 2)
```

## Leverage Points for Common Problems

| Problem | Low-Leverage Response | High-Leverage Alternative |
|---------|----------------------|---------------------------|
| System too slow | Add caching (11) | Fix algorithm, add feedback on perf (6, 10) |
| Too many bugs | More testing (12) | Quality in definition of done (5) |
| Team conflicts | More meetings (12) | Clear goals and incentives (3, 5) |
| Innovation stalled | Hackathons (12) | Permission to experiment (4) |
| Costs too high | Cut budgets (12) | Visibility + ownership (6, 5) |
| Knowledge silos | Documentation (11) | Information flow changes (6) |

## Verification Checklist

- [ ] Identified current intervention points
- [ ] Mapped interventions to leverage hierarchy
- [ ] Asked "what's the higher-leverage version?" for each
- [ ] Assessed feasibility vs. leverage tradeoff
- [ ] Selected highest feasible leverage point
- [ ] Considered resistance and how to address it
- [ ] Have strategy for paradigm-level resistance if applicable

## Key Questions

- "What level of leverage am I operating at?"
- "What's one level higher I could try?"
- "Why hasn't this parameter tuning fixed the problem?"
- "What information is missing that would change behavior?"
- "What rule change would make this unnecessary?"
- "What goal are we actually optimizing for?"
- "What paradigm is constraining our thinking?"

## Meadows' Wisdom

"People who manage to intervene in systems at the level of paradigm hit a leverage point that totally transforms systems."

"Magical leverage points are not easily accessible, even if we know where they are. There are no cheap tickets to mastery."

The highest leverage requires the most skill and often the most patience. But knowing where leverage exists helps you stop wasting effort at the bottom of the hierarchy.
