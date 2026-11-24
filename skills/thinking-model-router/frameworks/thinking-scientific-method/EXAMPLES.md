# Scientific Method — worked examples and seminar material

> Read this when studying the method or when a plan asks for a walkthrough ("teach me"). `SKILL.md` is the
> procedure /plan loads; this file is the correctness reference for it and keeps everything the short
> procedure left out: origin, worked examples, facilitation steps, templates, and key questions.
> Source: the April 2026 snapshot of tjboudreaux/cc-thinking-skills (MIT). Retained 2026-09-08.

---

# Scientific Method

## Overview

The scientific method is a systematic approach to understanding through observation, hypothesis formation, prediction, testing, and revision. In engineering, it provides rigor to debugging, experimentation, and investigation. The key insight: good hypotheses must be falsifiable—you must be able to prove them wrong.

**Core Principle:** Form hypotheses that could be proven false. Design experiments that could falsify them. Update beliefs based on evidence.

## When to Use

- Debugging (systematic cause identification)
- Performance investigation
- A/B test design
- Feature experimentation
- Root cause analysis
- Data analysis
- Any investigation where you're testing theories

Decision flow:

```
Investigating something?
  → Do you have a clear hypothesis? → no → FORM A HYPOTHESIS
  → Can your hypothesis be proven false? → no → MAKE IT FALSIFIABLE
  → Have you designed a test? → no → DESIGN AN EXPERIMENT
  → Did you update beliefs based on results? → no → REVISE AND ITERATE
```

## The Scientific Method Process

### Step 1: Observe

Gather data about the phenomenon:

```markdown
## Observation

What I'm seeing:
- API latency increased from 200ms to 800ms
- Started approximately Monday 9 AM
- Affects /checkout endpoint
- Other endpoints are normal
- Error rate is normal

Initial data:
- P50: 400ms (was 150ms)
- P99: 2.5s (was 500ms)
- Traffic: Normal levels
```

### Step 2: Question

What do you want to understand?

```markdown
## Question

Central question: Why did /checkout latency increase 4x on Monday?

Sub-questions:
- What changed on/around Monday 9 AM?
- Why only /checkout and not other endpoints?
- Why is P99 more affected than P50?
```

### Step 3: Hypothesize

Form a testable explanation:

```markdown
## Hypothesis

Primary hypothesis:
"The latency increase is caused by the payment provider SDK update
deployed Sunday night, which changed from async to sync API calls."

Why this hypothesis:
- SDK was updated Sunday (timing matches)
- /checkout is the only endpoint using payment SDK (scope matches)
- Sync calls would increase variance (P99 impact matches)
```

**Good hypothesis characteristics:**
- **Testable:** Can design an experiment
- **Falsifiable:** Can be proven wrong
- **Specific:** Not vague or unfalsifiable
- **Explanatory:** Accounts for observations

### Step 4: Predict

What would you expect IF the hypothesis is true?

```markdown
## Predictions

If hypothesis is true:
1. Rolling back the SDK should restore previous latency
2. Traffic to payment provider should show increased duration
3. Thread utilization should be higher (blocking calls)
4. Adding async wrapper should reduce latency

If hypothesis is false:
1. Rollback won't change latency
2. Payment provider call duration is unchanged
3. Thread utilization is normal
```

**Prediction requirement:**
Predictions must differentiate hypothesis-true from hypothesis-false. If both would produce the same observation, the prediction is useless.

### Step 5: Experiment

Design and run a test:

```markdown
## Experiment Design

Test: Deploy SDK rollback to canary group

Setup:
- Control: 90% traffic, new SDK
- Treatment: 10% traffic, old SDK
- Duration: 1 hour
- Metric: P50 and P99 latency

Success criteria:
- If P50 < 200ms in treatment → Hypothesis SUPPORTED
- If P50 > 350ms in treatment → Hypothesis FALSIFIED

Confounds controlled:
- Same time of day as original issue
- Same traffic routing rules
- Same downstream dependencies
```

### Step 6: Analyze

Examine the results:

```markdown
## Results

Control (new SDK):
- P50: 410ms
- P99: 2.4s
- n: 45,000 requests

Treatment (old SDK):
- P50: 155ms
- P99: 480ms
- n: 5,000 requests

Statistical significance: p < 0.001
Effect size: 62% reduction in P50

Analysis:
Hypothesis SUPPORTED. Old SDK shows pre-incident latency levels.
```

### Step 7: Conclude and Iterate

Update beliefs and act:

```markdown
## Conclusion

Finding: Payment SDK update caused latency regression
Confidence: High (controlled experiment, clear signal)

Action:
1. Roll back SDK immediately
2. File bug with payment provider
3. Add latency monitoring for SDK calls
4. Evaluate SDK changes before future updates

Next investigation:
Why didn't we catch this in staging?
Hypothesis: Staging doesn't have realistic payment provider latency
```

## Scientific Debugging

### The Debugging Scientific Method

```markdown
## Bug: Users sometimes see stale data

### Observation
- Reports of stale data from support tickets
- No clear pattern in who/when
- Estimated 5% of users affected

### Hypotheses (Multiple)
| # | Hypothesis | Falsification Test |
|---|------------|-------------------|
| 1 | Cache not invalidating | Check cache hits with stale data |
| 2 | Read replica lag | Check replica lag at time of reports |
| 3 | Browser caching | Check with cache-busted requests |
| 4 | CDN serving old content | Check CDN cache status |

### Testing Strategy
Test in order of: (ease × likelihood)
1. CDN cache status (easy to check)
2. Browser caching (easy to check)
3. Read replica lag (need to correlate times)
4. Cache invalidation (needs instrumentation)

### Test 1: CDN Cache Status
Prediction: If CDN is serving stale content,
            cache headers will show old timestamps
Result: CDN timestamps are fresh
Conclusion: CDN ruled out

### Test 2: Browser Caching
Prediction: If browser caching,
            force-refresh will show correct data
Result: Force-refresh still shows stale data sometimes
Conclusion: Browser caching ruled out

### Test 3: Read Replica Lag
Prediction: If replica lag,
            reports will correlate with lag spikes
Result: Strong correlation (r=0.84) between reports and lag spikes
Conclusion: SUPPORTED - read replica lag is the cause
```

## A/B Test Design

```markdown
## A/B Test: New Checkout Flow

### Hypothesis
"The simplified 2-step checkout will increase conversion rate
compared to current 4-step checkout."

### Predictions
If hypothesis is true:
- Conversion rate increases by >5%
- Time to complete decreases
- Abandonment rate decreases

If hypothesis is false:
- Conversion rate unchanged or decreases
- Potential confusion (errors increase)

### Experiment Design
Control: Current 4-step checkout
Treatment: New 2-step checkout
Traffic split: 50/50
Duration: 2 weeks (for statistical power)
Primary metric: Conversion rate
Guardrail metrics: Error rate, support tickets

### Sample Size Calculation
Baseline conversion: 3.2%
Minimum detectable effect: 5% relative (0.16% absolute)
Required n per group: 150,000 users

### Stopping Criteria
Stop early if:
- Treatment errors > 2x control
- Support tickets > 2x baseline
- p < 0.01 AND effect > 10%
```

## Scientific Method Template

```markdown
# Scientific Investigation: [Topic]

## Observation
What I'm seeing:
- [Observation 1]
- [Observation 2]

Data:
- [Metric]: [Value]

## Question
[Central question to answer]

## Hypotheses
| # | Hypothesis | How to Test | How to Falsify |
|---|------------|-------------|----------------|
| 1 | | | |
| 2 | | | |

## Predictions
If H1 is true:
- [Prediction 1]
- [Prediction 2]

If H1 is false:
- [Counter-prediction 1]

## Experiment
Design: [How to test]
Control: [Baseline]
Treatment: [Intervention]
Metric: [What to measure]
Duration: [How long]
Success criteria: [What constitutes support/falsification]

## Results
[Data from experiment]

## Analysis
Hypothesis [SUPPORTED/FALSIFIED]
Confidence: [High/Medium/Low]
Reasoning: [Why]

## Conclusion
Finding: [What I learned]
Action: [What to do]
Next: [Follow-up investigation]
```

## Verification Checklist

- [ ] Observations documented with data
- [ ] Hypothesis is falsifiable (can be proven wrong)
- [ ] Predictions differentiate true vs. false
- [ ] Experiment controls for confounding variables
- [ ] Results analyzed objectively
- [ ] Conclusion follows from evidence
- [ ] Updated beliefs based on evidence

## Key Questions

- "What would I expect to see if my hypothesis is true?"
- "What would I expect to see if my hypothesis is false?"
- "Can this hypothesis be proven wrong?"
- "Am I testing my hypothesis or confirming my beliefs?"
- "What's the simplest explanation that fits the data?"
- "What evidence would change my mind?"

## Feynman's Wisdom

"The first principle is that you must not fool yourself—and you are the easiest person to fool."

"It doesn't matter how beautiful your theory is, it doesn't matter how smart you are. If it doesn't agree with experiment, it's wrong."

The scientific method protects you from yourself. Your intuition generates hypotheses; the method tests them ruthlessly. When the experiment disagrees with your expectation, the experiment wins.


---

# Absorbed framework: Occams Razor

> Upstream folded this framework's mechanism into `scientific-method` (see SKILL.md). The original lesson is kept here in full.

# Occam's Razor (Parsimony Principle)

## Overview

Occam's Razor, attributed to 14th-century philosopher William of Ockham, states: "Entities should not be multiplied beyond necessity" (entia non sunt multiplicanda praeter necessitatem). When multiple explanations fit the evidence equally well, prefer the simplest one—the one with the fewest assumptions.

**Core Principle:** Among competing hypotheses that explain the data equally well, select the one with the fewest assumptions.

**Einstein's Corollary:** "Everything should be made as simple as possible, but no simpler."

## When to Use

- Debugging: Multiple hypotheses could explain a bug
- Architecture: Choosing between design approaches
- Root cause analysis: Several causes seem plausible
- Code review: Evaluating implementation complexity
- Technical decisions: Selecting between tools or patterns
- Incident response: Narrowing down failure causes

Decision flow:

```
Multiple explanations exist? → yes → Do they explain the evidence equally? → yes → APPLY OCCAM'S RAZOR
                                                                          ↘ no → Prefer better explanation
                           ↘ no → Use available explanation
```

## The Process

### Step 1: Enumerate Competing Hypotheses

List all plausible explanations for the observed behavior:

```
Bug: Users intermittently can't log in

Hypotheses:
A. Session token expiration edge case
B. Race condition in auth service
C. Database connection pool exhaustion
D. Cosmic rays flipping bits in memory
E. Complex interaction between CDN cache, load balancer, and session service
```

### Step 2: Count the Assumptions

For each hypothesis, list required assumptions:

| Hypothesis | Assumptions Required |
|------------|---------------------|
| A. Token expiration | 1. Token validation has edge case |
| B. Race condition | 1. Concurrent requests possible, 2. Shared mutable state exists |
| C. DB pool exhaustion | 1. Pool is undersized, 2. Connections are leaking |
| D. Cosmic rays | 1. Hardware failure, 2. No ECC memory, 3. Perfect timing |
| E. Complex interaction | 1. CDN caches auth, 2. LB sticky sessions fail, 3. Session sync delayed |

### Step 3: Verify Explanatory Power

Ensure simpler hypotheses actually explain the evidence:

```
Evidence: Failures correlate with high traffic periods

Hypothesis A (token edge case): 
  - Doesn't explain traffic correlation ❌
  
Hypothesis C (DB pool exhaustion):
  - Explains traffic correlation ✓
  - Fewer assumptions than E
  - PREFERRED by Occam's Razor ✓
```

### Step 4: Test Simplest First

Investigate hypotheses in order of simplicity:

```
1. Check DB connection pool metrics (simplest)
2. Review token validation code (simple)
3. Analyze race condition potential (moderate)
4. Instrument complex service interactions (complex)
5. Check for hardware issues (last resort)
```

### Step 5: Escalate Complexity Only When Needed

If simple explanations are ruled out, move to complex ones with new evidence.

## Complexity Assessment Framework

### Counting Complexity

| Factor | Complexity Cost |
|--------|-----------------|
| Each independent assumption | +1 |
| Each component involved | +1 |
| Each external dependency | +2 |
| Timing-dependent behavior | +2 |
| Requires rare conditions | +3 |
| "Perfect storm" scenarios | +5 |

### Example Comparison

```
Solution A: Add caching layer
- New component (Redis): +1
- Cache invalidation logic: +1  
- New failure mode: +1
Total: 3

Solution B: Optimize existing query
- Query modification: +1
Total: 1

→ Prefer Solution B unless evidence shows it's insufficient
```

## When Simplicity Yields to Complexity

Occam's Razor is a heuristic, not an absolute law. Prefer complexity when:

### 1. Evidence Demands It

```
Simple hypothesis: Single bug in auth service
Evidence: Failures only occur when Feature X AND Feature Y are both enabled

→ Complex interaction hypothesis now has supporting evidence
→ Accept complexity that explains the evidence
```

### 2. Domain Complexity Is Irreducible

```
Problem: Distributed consensus
Simple solution: Single leader (but single point of failure)
Reality: Distributed systems require complex solutions (Raft, Paxos)

→ Some domains have irreducible complexity
→ Don't oversimplify beyond what's correct
```

### 3. Future Requirements Are Known

```
Current need: Store user preferences
Simple: JSON file
Future need: Multi-device sync, conflict resolution

→ Database is more complex but necessary
→ Known future needs justify upfront complexity
```

### 4. Simplicity Introduces Technical Debt

```
Simple now: Copy-paste code in 5 places
Simpler long-term: Extract shared function

→ Local simplicity vs. systemic simplicity
→ Prefer systemic simplicity
```

## Application Examples

### Debugging Example

```
Bug: API returns 500 errors sporadically

Hypothesis A: Null pointer in rare code path
  Assumptions: 1
  
Hypothesis B: Memory pressure causes GC pauses that timeout requests
  Assumptions: 3 (memory issues + GC behavior + timeout settings)
  
Hypothesis C: Race condition between cache refresh and request handling
  Assumptions: 4 (concurrent access + shared state + timing + cache implementation)

Occam's Razor: Start with Hypothesis A
Action: Search logs for null pointer exceptions
Result: Found! NPE in user profile edge case
```

### Architecture Example

```
Requirement: Service needs to call another service

Option A: Direct HTTP call
  Components: 1 (HTTP client)
  Assumptions: Target available, network reliable
  
Option B: Message queue with retry
  Components: 3 (queue, producer, consumer)
  Assumptions: Need async, need retry, need decoupling
  
Option C: Service mesh with circuit breaker, retry, timeout
  Components: 5+ (sidecar, control plane, observability)
  Assumptions: At scale, need observability, need traffic management

Occam's Razor: Start with Option A
Escalate to B/C only when evidence shows need for resilience
```

### Code Implementation Example

```python
# Complex (unnecessary assumptions)
def is_even(n):
    binary = bin(n)
    last_bit = binary[-1]
    return last_bit == '0'

# Simple (minimal assumptions)  
def is_even(n):
    return n % 2 == 0

# Occam's Razor: Prefer the modulo approach
# Fewer concepts, fewer operations, same result
```

### Root Cause Analysis Example

```
Symptom: Deployment failed

Complex hypothesis:
"The CI server's Docker daemon ran out of disk space because 
a cron job that cleans old images was disabled when we upgraded 
the server OS last month, and nobody noticed because the monitoring 
alert was routed to a deprecated Slack channel."

Simple hypothesis:
"The build script has a typo in the new environment variable name."

Occam's Razor: Check the build script first
Result: Typo found. DATABSE_URL instead of DATABASE_URL
```

## Common Anti-Patterns

| Anti-Pattern | Description | Correction |
|--------------|-------------|------------|
| Rube Goldberg | Complex solution to simple problem | Ask "what's the minimum needed?" |
| Premature abstraction | Abstracting for hypothetical cases | Wait for evidence of need |
| Resume-driven development | Using complex tech to learn it | Match tool to problem |
| Cargo culting | Copying complex patterns blindly | Understand why patterns exist |
| Conspiracy thinking | Assuming coordinated complex causes | Check simple causes first |

## Verification Checklist

- [ ] Listed all plausible hypotheses/solutions
- [ ] Counted assumptions required for each
- [ ] Verified simpler options have equal explanatory power
- [ ] Investigated in order of simplicity
- [ ] Escalated to complexity only with evidence
- [ ] Confirmed solution is "as simple as possible, but no simpler"
- [ ] Checked for domain-irreducible complexity
- [ ] Considered systemic vs. local simplicity

## Combining with Other Models

- **First Principles**: Reduce to fundamentals, then apply Occam's to solutions
- **Inversion**: "What would make this unnecessarily complex?"
- **Debiasing**: Watch for complexity bias (assuming complex = sophisticated)
- **Pre-Mortem**: Would a simpler approach have fewer failure modes?

## Key Questions

- "What's the simplest explanation that fits all the evidence?"
- "How many things have to be true for this hypothesis to hold?"
- "Am I adding complexity to handle cases I haven't seen?"
- "Would a junior engineer understand this solution?"
- "If I explained this to a non-technical person, how many steps would it take?"
- "What's the minimum change that could fix this?"
- "Am I solving the problem I have, or a problem I might have?"

## Ockham's Warning

"Plurality must never be posited without necessity."

The simplest solution isn't always correct, but it should always be tested first. Complexity should be earned through evidence, not assumed through speculation. When you find yourself building elaborate explanations, step back and ask: "What's the minimum hypothesis that explains what I'm seeing?"
