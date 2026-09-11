# Testing, Evaluation and Observability

## 1. Testing layers

### Unit tests

Test:

-   demand calculations
-   inventory calculations
-   financial calculations
-   validators
-   data generator
-   simulation functions

### Integration tests

Test:

``` text
FastAPI → PostgreSQL
FastAPI → Redis
Agent → MCP
MCP → PostgreSQL
Worker → Simulation
```

### End-to-end tests

Test:

``` text
user question
→ decision
→ agent plan
→ tools
→ simulation
→ recommendation
→ approval
→ action
```

## 2. AI evaluation

LLM output should not be evaluated only by "looks good."

Create evaluation cases.

Dimensions:

-   factual grounding
-   tool selection
-   correct parameters
-   completeness
-   refusal when evidence is insufficient
-   risk identification
-   consistency
-   recommendation quality

## 3. Simulation evaluation

Compare the simulation against known synthetic ground truth.

Because we control NovaCart, we can create situations where the expected
result is known.

Example:

If inventory is already extremely high and demand is low, a strategy
that increases purchasing should generally score poorly.

## 4. Regression tests

Keep a fixed evaluation set.

Every meaningful change runs it.

Track:

``` text
baseline
new version
difference
```

## 5. Observability

A decision trace should look like:

``` text
Decision ID
   ↓
Manager Agent
   ↓
Tool call 1
Tool call 2
Tool call 3
   ↓
Strategy generation
   ↓
Simulation
   ↓
Critic
   ↓
Recommendation
   ↓
Approval
   ↓
Action
```

Record:

-   latency
-   errors
-   tool arguments
-   tool results
-   model name
-   simulation seed
-   simulation count
-   final recommendation

## 6. Security rule

Never store:

-   API keys
-   passwords
-   private credentials
-   raw secrets

in logs or prompts.
