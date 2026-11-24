# Probabilistic — worked examples and seminar material

> Read this when studying the method or when a plan asks for a walkthrough ("teach me"). `SKILL.md` is the
> procedure /plan loads; this file is the correctness reference for it and keeps everything the short
> procedure left out: origin, worked examples, facilitation steps, templates, and key questions.
> Source: the April 2026 snapshot of tjboudreaux/cc-thinking-skills (MIT). Retained 2026-09-08.

---

# Probabilistic Thinking

## Overview

Probabilistic thinking, informed by the research of Philip Tetlock's "Superforecasting," treats beliefs as probabilities rather than certainties. Good probabilistic thinkers express confidence in ranges, update beliefs when evidence changes, and track their accuracy to improve calibration over time.

**Core Principle:** Express beliefs as probabilities. Track predictions. Update when wrong. Calibrate over time.

## When to Use

- Project timeline estimation
- Risk assessment
- Predicting outcomes (launches, decisions, events)
- Evaluating uncertain technical choices
- Making decisions without complete information
- Any forecast or prediction

Decision flow:

```
Making a prediction?
  → Is outcome uncertain? → yes → EXPRESS AS PROBABILITY
  → Can you track the outcome? → yes → RECORD AND CALIBRATE
  → New information available? → yes → UPDATE PROBABILITY
```

## Core Concepts

### Probability as Confidence

Convert vague language to numbers:

| Vague Statement | Probability Range |
|-----------------|-------------------|
| "Certain" | 99%+ |
| "Almost certain" | 90-99% |
| "Very likely" | 80-90% |
| "Likely" / "Probable" | 65-80% |
| "Better than even" | 55-65% |
| "Toss-up" | 45-55% |
| "Unlikely" | 20-35% |
| "Very unlikely" | 10-20% |
| "Almost impossible" | 1-10% |
| "Impossible" | <1% |

### Confidence Intervals

Express estimates as ranges, not points:

```
BAD: "The project will take 6 weeks"
GOOD: "I'm 80% confident the project will take 4-8 weeks"
BETTER: "50% confidence: 5-7 weeks; 90% confidence: 3-10 weeks"
```

### Base Rates

Start with how often similar things happen:

```
Question: Will this feature launch on time?
Base rate: What % of similar features launched on time? ~40%
Adjustment: This team is experienced (+10%), scope is clear (+10%)
Estimate: ~60% probability of on-time launch
```

## The Probabilistic Process

### Step 1: Express Initial Probability

State your belief as a number:

```markdown
## Prediction: Will we hit Q2 revenue target?

Initial estimate: 65%
Reasoning:
- Last 4 quarters: Hit 3/4 targets (75% base rate)
- Current pipeline: Slightly below historical (-10%)
- New product launching: Uncertain impact
```

### Step 2: Identify Key Uncertainties

What could change the probability?

```markdown
Key uncertainties:
1. Will Enterprise deal close? (+15% if yes)
2. Will new product cannibalize existing? (-10% if significant)
3. Will competitor launch disrupt? (-20% if aggressive)
```

### Step 3: Create Probability Tree

For complex predictions, branch scenarios:

```
Project success: ?
├── Technical risk resolves well (60%)
│   ├── Team stays intact (80%) → 0.60 × 0.80 = 48% → SUCCESS
│   └── Key person leaves (20%) → 0.60 × 0.20 × 0.50 = 6% → PARTIAL
├── Technical risk causes delays (30%)
│   ├── Scope reduced (60%) → 0.30 × 0.60 × 0.70 = 12.6% → SUCCESS
│   └── Scope maintained (40%) → 0.30 × 0.40 = 12% → FAILURE
└── Technical risk blocks project (10%) → 10% → FAILURE

P(Success) = 48% + 12.6% = 60.6% ≈ 60%
```

### Step 4: Update with New Information

When new evidence arrives, update:

```markdown
Original estimate: 65% hit revenue target

New information: Enterprise deal delayed to Q3
Impact: -15% (was +15% if closed, now neutral)
Updated estimate: 50%

New information: Competitor launch was weak
Impact: +10% (was -20% if aggressive)
Updated estimate: 60%
```

### Step 5: Record and Track

Keep a prediction log:

```markdown
## Prediction Log

| Date | Prediction | Probability | Actual | Brier Score |
|------|------------|-------------|--------|-------------|
| 2024-01-01 | Q1 launch | 70% | Yes | 0.09 |
| 2024-01-15 | Deal closes | 60% | No | 0.36 |
| 2024-02-01 | Bug resolved in 1 week | 80% | Yes | 0.04 |
```

### Step 6: Calibrate Over Time

Review your accuracy:

```markdown
## Calibration Review

For predictions I rated 70%:
- Total predictions: 20
- Actual outcomes "Yes": 12 (60%)
- I'm overconfident by 10% at this level

Adjustment: When I feel "70%", actual is closer to 60%
```

## Calibration Techniques

### The Equivalent Bet Test

"Would I bet at these odds?"

```
Prediction: 80% confident project finishes on time
Equivalent: Would I bet $4 to win $1?
If that feels wrong, adjust the probability.
```

### The Outside View

Always check base rates:

```
Inside view: "Our team is great, we'll definitely finish on time"
Outside view: "What % of similar projects finished on time?"

Inside tends toward overconfidence
Outside provides calibration anchor
```

### The Pre-Mortem Adjustment

Imagine failure, then adjust:

```
Initial estimate: 85% success
After pre-mortem: Identified 5 failure modes I hadn't considered
Adjusted estimate: 70%
```

### The Confidence Interval Check

Are your intervals too narrow?

```
Test: Of your 90% confidence intervals, do 90% contain the actual?
Common finding: Only 60-70% do
Fix: Widen intervals by 50%
```

## Application Examples

### Project Estimation

```markdown
## Project: Payment System Rewrite

Timeline estimate:
- 50% confidence: 8-12 weeks
- 80% confidence: 6-16 weeks
- 95% confidence: 4-24 weeks

Key variables:
- API complexity: High uncertainty (+/- 3 weeks)
- Team availability: Medium uncertainty (+/- 2 weeks)
- Integration testing: High uncertainty (+/- 4 weeks)

Commitment: "We're 80% confident we'll deliver in Q2"
```

### Risk Assessment

```markdown
## Risk: Database migration causes extended downtime

Probability assessment:
- Base rate for similar migrations: 20% have issues
- Our preparation level: Above average (-5%)
- Complexity of our schema: Above average (+5%)
- Rollback plan quality: Strong (-5%)

Estimate: 15% probability of extended downtime

Mitigation value:
- If issue occurs: 4 hours downtime × $10K/hour = $40K
- Expected loss: 15% × $40K = $6K
- Mitigation cost: $3K for additional testing
- Decision: Mitigation worth it (ROI positive)
```

### Technical Decision

```markdown
## Decision: Adopt new framework

Success probability factors:
| Factor | Probability | Weight |
|--------|-------------|--------|
| Team learns quickly | 70% | 0.3 |
| Framework matures | 80% | 0.2 |
| Performance meets needs | 60% | 0.3 |
| Integration works | 75% | 0.2 |

Combined probability (simplified):
0.70 × 0.80 × 0.60 × 0.75 = 25% (if all must succeed)
OR weighted average: 70% (if partial success acceptable)

Decision: High uncertainty suggests pilot first
```

## Brier Score for Calibration

Track prediction accuracy with Brier Score:

```
Brier Score = (probability - outcome)²

Where outcome = 1 if happened, 0 if not

Example:
Predicted 70% (0.70), it happened (1)
Brier = (0.70 - 1)² = 0.09

Predicted 70% (0.70), it didn't happen (0)
Brier = (0.70 - 0)² = 0.49

Lower is better. Perfect = 0, Random = 0.25
```

## Probabilistic Thinking Template

```markdown
# Probabilistic Assessment: [Prediction]

## Prediction
[Clear, falsifiable statement with timeframe]

## Initial Probability
Estimate: [X]%
Base rate: [Similar events: Y%]
Adjustment rationale: [Why different from base rate]

## Confidence Interval
- 50% CI: [Range]
- 80% CI: [Range]
- 95% CI: [Range]

## Key Uncertainties
| Uncertainty | If positive | If negative |
|-------------|-------------|-------------|
| [Factor 1] | +X% | -Y% |
| [Factor 2] | +X% | -Y% |

## Update Log
| Date | New Information | Old P | New P |
|------|-----------------|-------|-------|
| | | | |

## Resolution
Date: [When known]
Outcome: [What happened]
Brier Score: [Calculation]
Lessons: [What to learn]
```

## Verification Checklist

- [ ] Expressed prediction as specific probability
- [ ] Checked base rate for similar events
- [ ] Created appropriate confidence intervals
- [ ] Identified key uncertainties and their impacts
- [ ] Recorded prediction for future calibration
- [ ] Applied equivalent bet test for sanity check
- [ ] Willing to update when new information arrives

## Key Questions

- "What probability would I assign to this?"
- "What's the base rate for similar things?"
- "What would change my estimate up or down?"
- "Am I being overconfident? (Usually yes)"
- "What's my track record at this confidence level?"
- "Would I bet at these odds?"

## Tetlock's Superforecaster Traits

1. **Update often:** Change predictions when evidence changes
2. **Granular probabilities:** Use 65% not "likely"
3. **Outside view:** Start with base rates
4. **Seek disconfirming evidence:** Look for reasons you're wrong
5. **Track record:** Keep score, learn from errors
6. **Intellectual humility:** Know you're often wrong

## Tetlock's Wisdom

"The fox knows many things, but the hedgehog knows one big thing."

Superforecasters are foxes—they integrate many perspectives, update frequently, and avoid ideological certainty. They're not smarter; they're more calibrated.

"Beliefs are hypotheses to be tested, not treasures to be protected."

Your predictions should change as evidence changes. Holding steady when you should update is a calibration failure.


---

# Absorbed framework: Bayesian

> Upstream folded this framework's mechanism into `probabilistic` (see SKILL.md). The original lesson is kept here in full.

# Bayesian Reasoning

## Overview
Bayesian thinking provides a framework for updating beliefs based on new evidence. Rather than treating beliefs as binary (true/false), it recognizes degrees of confidence that should shift as evidence accumulates. This approach, rooted in Bayes' Theorem, helps avoid both overconfidence and underreaction to new information.

**Core Principle:** Beliefs are probabilities that should update incrementally as evidence arrives. Strong priors require strong evidence to shift.

## When to Use
- Estimating probabilities or likelihoods
- Interpreting test results or metrics
- Making decisions with incomplete information
- Evaluating competing hypotheses
- Learning from experiments or A/B tests
- Diagnosing problems with uncertain causes
- Predicting outcomes based on historical data

Decision flow:
```
Uncertain about something? → yes → Have prior belief? → yes → New evidence? → APPLY BAYESIAN UPDATE
                                                      ↘ no → Establish base rate first
                         ↘ no → Standard analysis may suffice
```

## Key Concepts

### Prior Probability
Your belief BEFORE seeing new evidence:
```
P(H) = probability that hypothesis H is true

Example: Before any symptoms, what's the probability someone has disease X?
         Use base rate: If 1 in 1000 people have it, P(disease) = 0.001
```

### Likelihood
How probable is the evidence IF the hypothesis is true?
```
P(E|H) = probability of seeing evidence E, given H is true

Example: If someone HAS the disease, what's the probability of a positive test?
         If test is 99% sensitive: P(positive|disease) = 0.99
```

### Posterior Probability
Your belief AFTER seeing the evidence:
```
P(H|E) = updated probability of H, given you observed E

This is what Bayes' Theorem calculates.
```

## Bayes' Theorem

```
                P(E|H) × P(H)
P(H|E) = ─────────────────────────
                   P(E)

Where:
  P(H|E) = posterior (what we want)
  P(E|H) = likelihood (how expected is evidence if H true)
  P(H)   = prior (initial belief)
  P(E)   = total probability of evidence
```

### Intuitive Form

```
Posterior odds = Prior odds × Likelihood ratio

If evidence is 10x more likely under H than under not-H,
your odds should shift by factor of 10.
```

## The Process

### Step 1: Establish Your Prior
What did you believe before this evidence?
- Use base rates when available
- Be explicit about uncertainty
- Don't anchor on 50% just because you're unsure

```
Question: Will this feature increase conversion?
Prior: Based on similar features, ~30% succeed significantly
       P(success) = 0.30
```

### Step 2: Assess the Evidence
How strong is this evidence? Consider:
- How likely is this evidence if hypothesis is TRUE?
- How likely is this evidence if hypothesis is FALSE?
- What's the ratio?

```
Evidence: Early A/B test shows 5% lift (p=0.08)
P(this result | feature works) = 0.60 (moderately expected)
P(this result | feature doesn't work) = 0.15 (possible but less likely)
Likelihood ratio = 0.60 / 0.15 = 4x
```

### Step 3: Update Your Belief
Apply the likelihood ratio to your prior:

```
Prior odds: 0.30 / 0.70 = 0.43
Likelihood ratio: 4x
Posterior odds: 0.43 × 4 = 1.72
Posterior probability: 1.72 / (1 + 1.72) = 0.63

Updated belief: 63% confidence feature will succeed
(up from 30% prior)
```

### Step 4: Iterate as More Evidence Arrives
Yesterday's posterior becomes today's prior:

```
New evidence: Week 2 shows lift holding at 4.5%
Prior (from step 3): 0.63
[Repeat update process]
New posterior: 0.78
```

## Common Applications

### Interpreting Test Results
```
Scenario: Test for rare disease (1 in 10,000 prevalence)
Test: 99% sensitive, 99% specific

Prior: P(disease) = 0.0001
If positive test:
  P(positive|disease) = 0.99
  P(positive|no disease) = 0.01
  P(positive) = 0.99 × 0.0001 + 0.01 × 0.9999 ≈ 0.0101

Posterior: P(disease|positive) = (0.99 × 0.0001) / 0.0101 ≈ 0.0098

Even with 99% accurate test, positive result only means ~1% chance of disease!
Base rate dominates when condition is rare.
```

### Debugging
```
Bug report: Users see error X
Prior beliefs:
  P(database issue) = 0.20
  P(network issue) = 0.30
  P(code bug) = 0.40
  P(user error) = 0.10

Evidence: Error happens only on mobile
  P(mobile-only | database) = 0.05
  P(mobile-only | network) = 0.30
  P(mobile-only | code bug) = 0.60
  P(mobile-only | user error) = 0.40

Update: Code bug becomes most likely (posterior ~0.55)
Next step: Investigate mobile-specific code paths
```

### Project Estimation
```
Prior: Based on similar projects, P(on-time) = 0.40

Evidence 1: Team is experienced with this stack
  Likelihood ratio: 1.5x → Posterior: 0.50

Evidence 2: Requirements are unclear
  Likelihood ratio: 0.6x → Posterior: 0.38

Evidence 3: Critical dependency has risk
  Likelihood ratio: 0.7x → Posterior: 0.30

Final estimate: 30% chance of on-time delivery
```

## Mental Shortcuts

### Strong vs Weak Evidence
| Evidence Type | Typical Likelihood Ratio |
|---------------|-------------------------|
| Definitive proof | 100x+ |
| Strong evidence | 10-100x |
| Moderate evidence | 3-10x |
| Weak evidence | 1.5-3x |
| Noise | ~1x (no update) |

### When to Update Significantly
Update strongly when:
- Evidence is surprising under your current belief
- Evidence comes from reliable source
- Evidence is specific to your hypothesis

Update weakly when:
- Evidence is expected regardless of hypothesis
- Source has unknown reliability
- Evidence is circumstantial

### Base Rate Neglect (Avoid This)
Common error: Ignoring prior probability when evidence arrives
```
Wrong: "Positive test = probably have disease"
Right: "Positive test shifts probability, but base rate matters"
```

## Calibration Check

### Are You Well-Calibrated?
Track predictions and outcomes:
- Of things you said were "70% likely," did ~70% happen?
- If you're always overconfident, widen your uncertainty
- If you're always underconfident, trust your assessments more

### Confidence Levels
| Stated Confidence | Should Mean |
|-------------------|-------------|
| 50% | Coin flip |
| 70% | Would bet 2:1 |
| 90% | Would bet 9:1 |
| 99% | Would bet 99:1 |

## Verification Checklist
- [ ] Established explicit prior probability (not just "I think...")
- [ ] Assessed likelihood ratio of evidence
- [ ] Applied update mathematically (not just "more/less likely")
- [ ] Considered base rates for rare events
- [ ] Checked for base rate neglect
- [ ] Documented reasoning for future calibration

## Key Questions
- "What was my belief before this evidence?"
- "How likely is this evidence if my belief is true? If false?"
- "What's the likelihood ratio?"
- "Am I anchoring on the evidence and ignoring base rates?"
- "How would I bet on this? At what odds?"

## Kahneman's Warning
"People tend to assess the relative importance of issues by the ease with which they are retrieved from memory—and this is largely determined by the extent of coverage in the media."

Don't let vivid evidence override base rates. A plane crash doesn't make flying more dangerous than driving, even though it feels that way.


---

# Absorbed framework: Fermi Estimation

> Upstream folded this framework's mechanism into `probabilistic` (see SKILL.md). The original lesson is kept here in full.

# Fermi Estimation

## Overview

Fermi estimation, named after physicist Enrico Fermi, is the art of making reasonable estimates for quantities that seem impossible to know without direct measurement. By decomposing a question into factors you can estimate, then multiplying, you often get surprisingly accurate order-of-magnitude results.

**Core Principle:** Break the unknown into known (or estimable) pieces. Even rough estimates combine to reasonable accuracy due to errors canceling out.

## When to Use

- Capacity planning ("How much storage will we need?")
- Cost estimation ("What will this infrastructure cost?")
- Market sizing ("How many potential users exist?")
- Feasibility assessment ("Is this even plausible?")
- Sanity checking ("Does this number make sense?")
- Interview questions ("How many piano tuners in Chicago?")
- Quick prioritization ("Is this worth pursuing?")

Decision flow:

```
Need a number you don't have? → yes → Can you measure it directly? → no → FERMI ESTIMATE
                                                                   ↘ yes → Measure
                              ↘ no → You might not need it
```

## The Fermi Process

### Step 1: Clarify What You're Estimating

Be precise about the quantity:

```
Vague: "How big is the market?"
Precise: "How many SaaS companies with 50-500 employees in the US
         would pay $1000/month for our product?"
```

### Step 2: Decompose into Estimable Factors

Break into pieces you can estimate:

```
Storage needs for user data:
= (Number of users)
  × (Data per user per day)
  × (Days of retention)
  × (Overhead factor)
```

**Decomposition strategies:**

| Strategy | Example |
|----------|---------|
| By component | Total = Sum of parts |
| By rate × time | Total = Rate × Duration |
| By population × fraction | Target = Base × Percentage |
| By analogy × adjustment | New ≈ Similar × Ratio |

### Step 3: Estimate Each Factor

For each factor, estimate based on:

| Source | Example |
|--------|---------|
| Known data | "We have 10,000 DAU" |
| Industry benchmarks | "Average SaaS churn is 5%" |
| Physical constraints | "A human can make ~50 decisions/day" |
| Logical bounds | "At least 1, at most 1 million" |
| Personal experience | "I've seen systems handle 1000 req/s" |

**When estimating:**
- Use ranges, not point estimates: "10,000 to 50,000"
- Prefer geometric mean for order-of-magnitude: √(10,000 × 50,000) = 22,360
- Round to one significant figure: ~20,000

### Step 4: Combine Factors

Multiply (or add) factors together:

```
Storage = 50,000 users × 10 KB/user/day × 365 days × 1.5 overhead
        = 50,000 × 10,000 × 365 × 1.5 bytes
        = 274 billion bytes
        ≈ 270 GB/year
```

### Step 5: Sanity Check

Verify reasonableness:
- Does the order of magnitude make sense?
- Is it physically possible?
- Does it match any known data points?
- Would a 10x error change the decision?

### Step 6: State Confidence and Implications

```
Estimate: ~270 GB/year
Confidence: Within 3-5x (80-1,500 GB)
Implication: Standard database tier sufficient; no special infrastructure needed
```

## Fermi Estimation Template

```markdown
# Fermi Estimate: [Question]

## Question (Precise)
[Exactly what we're estimating]

## Decomposition
[Quantity] = [Factor 1] × [Factor 2] × ... × [Factor N]

## Factor Estimates

### Factor 1: [Name]
- Estimate: [Value]
- Source/Reasoning: [Why this number]
- Confidence: High / Medium / Low

### Factor 2: [Name]
- Estimate: [Value]
- Source/Reasoning: [Why this number]
- Confidence: High / Medium / Low

[Continue for all factors...]

## Calculation
[Show the math]

## Result
- Point estimate: [Value]
- Range: [Low] to [High] (representing Xx uncertainty)

## Sanity Check
- Physical plausibility: [Check]
- Comparison to known data: [Check]
- Order of magnitude reasonable: [Check]

## Implications
[What does this estimate mean for the decision?]
```

## Example 1: Data Storage Needs

**Question:** How much storage will our new feature need in Year 1?

```markdown
## Decomposition
Storage = Users × Events/User/Day × Event Size × Days × Replication

## Factor Estimates

### Users (DAU)
- Estimate: 100,000 (current) growing to 200,000 (end of year)
- Average over year: ~150,000
- Confidence: High (we have current data)

### Events per User per Day
- Estimate: 50 events (based on current feature usage patterns)
- Confidence: Medium (new feature might differ)

### Event Size
- Estimate: 500 bytes (JSON with typical payload)
- Confidence: High (we can measure similar events)

### Days in Year
- Estimate: 365
- Confidence: Certain

### Replication Factor
- Estimate: 3x (standard for durability)
- Confidence: High (architectural requirement)

## Calculation
Storage = 150,000 × 50 × 500 × 365 × 3
        = 150,000 × 50 × 500 × 365 × 3
        = 4.1 × 10^12 bytes
        = 4.1 TB

## Result
- Point estimate: ~4 TB
- Range: 1 TB (pessimistic assumptions) to 15 TB (growth beats expectations)

## Sanity Check
- 4 TB for 150K users = ~27 MB/user/year = reasonable
- Similar feature at other company uses "several TB" = consistent
- Standard database can handle 4 TB = feasible

## Implications
- Standard managed database tier sufficient
- No need for sharding or special storage architecture in Year 1
- Budget ~$500/month for storage costs
```

## Example 2: API Rate Capacity

**Question:** Can our API handle Black Friday traffic?

```markdown
## Decomposition
Required RPS = Peak Daily Users × Requests/User/Session × Sessions/Day × Peak Multiplier / Seconds in Peak Hour

## Factor Estimates

### Peak Daily Users
- Estimate: 500,000 (3x normal 170K)
- Source: Last year's Black Friday
- Confidence: Medium

### Requests per Session
- Estimate: 30 API calls (measured)
- Confidence: High

### Sessions per Day
- Estimate: 2 (mobile + desktop)
- Confidence: Medium

### Peak Multiplier
- Estimate: 5x (traffic concentrated in 4-hour window, spiky within that)
- Confidence: Medium

### Seconds in Peak Hour
- Estimate: 3,600
- Confidence: Certain

## Calculation
Required RPS = (500,000 × 30 × 2 × 5) / 3,600
             = 150,000,000 / 3,600
             = 41,667 RPS
             ≈ 40,000 RPS peak

## Result
- Point estimate: 40,000 RPS
- Range: 15,000 to 100,000 RPS

## Sanity Check
- Current capacity: 10,000 RPS
- Gap: 4x capacity needed
- Similar scale companies report 20-50K RPS on peak days = consistent

## Implications
- Need 4x capacity increase
- Auto-scaling must handle 40K+ RPS
- Load test to 60K RPS (1.5x safety margin)
```

## Example 3: Market Size

**Question:** How many potential customers for our developer tool?

```markdown
## Decomposition
TAM = Software Companies × Avg Developers × Adoption Rate × Price Tolerance

## Factor Estimates

### Software Companies (US)
- Estimate: ~500,000 (SBA data: tech companies)
- Confidence: Medium

### With 10+ Developers (our target)
- Estimate: 10% = 50,000 companies
- Confidence: Low (rough estimate)

### Developers per Target Company
- Estimate: 30 average
- Confidence: Medium

### Adoption Rate (would consider)
- Estimate: 20% (dev tools are crowded)
- Confidence: Low

### Price Point
- Estimate: $50/developer/month
- Confidence: Medium (based on similar tools)

## Calculation
Addressable Users = 50,000 × 30 × 20% = 300,000 developers
Revenue = 300,000 × $50 × 12 = $180M/year TAM

## Result
- TAM: ~$180M/year
- Realistic serviceable market: 5-10% = $10-20M/year

## Sanity Check
- Similar dev tools (Datadog, etc.) have $100M+ revenue = plausible ceiling
- 300K potential users in a niche = reasonable

## Implications
- Market size justifies investment if we can capture 5%+
- Need differentiation in crowded space
```

## Common Decomposition Patterns

### Capacity Planning
```
Needed = Users × Usage/User × Factor/Usage × Growth × Safety
```

### Cost Estimation
```
Cost = Resources × Unit Cost × Duration × Overhead
```

### Time Estimation
```
Time = Tasks × Time/Task × (1 + Risk Factor)
```

### Market Sizing
```
Market = Population × Segment% × Adoption% × Price × Frequency
```

## Tips for Better Estimates

### Use Multiple Approaches

Estimate the same thing different ways:

```
Website traffic estimate:
Method 1: Bottom-up from user base
Method 2: Top-down from market share
Method 3: Analogy to similar company

If methods agree within 3x, confidence increases
If they diverge wildly, investigate assumptions
```

### Bound First

Start with upper and lower bounds:

```
"Definitely more than 1,000, definitely less than 10 million"
"So somewhere in 10,000-1,000,000 range"
"Let me narrow from there..."
```

### Watch for Correlated Errors

If factors are correlated, errors don't cancel:

```
BAD: Users × Revenue/User (both depend on same growth assumption)
BETTER: Estimate revenue directly, or use independent factors
```

### One Significant Figure

Don't false precision:

```
Calculation: 47,832,519 bytes
Report: ~50 MB (not "47.8 MB")
```

## Verification Checklist

- [ ] Question stated precisely
- [ ] Decomposed into 3-6 estimable factors
- [ ] Each factor has reasoning/source
- [ ] Factors are relatively independent
- [ ] Calculation shown and checked
- [ ] Result sanity-checked against reality
- [ ] Uncertainty range stated
- [ ] Implications for decision clarified

## Key Questions

- "Can I break this into smaller, estimable pieces?"
- "What do I already know that constrains this?"
- "What's the upper bound? Lower bound?"
- "Does this number pass the smell test?"
- "Would being off by 10x change my decision?"
- "Can I estimate this a different way to cross-check?"

## Fermi's Wisdom

When asked how many piano tuners were in Chicago, Fermi didn't look it up—he estimated from population, households, pianos, tuning frequency, and tuner capacity. His estimate was reportedly within 20% of the actual number.

The lesson: You know more than you think. Decompose, estimate, combine. The errors often cancel, and you get surprisingly close to truth.

"Never make a calculation until you know the answer." — John Wheeler (Fermi's colleague)

Meaning: Estimate first to know what answer to expect, then calculate to verify.
