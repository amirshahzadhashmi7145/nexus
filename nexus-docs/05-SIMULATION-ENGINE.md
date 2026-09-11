# Digital Twin and Simulation Engine

## 1. Purpose

The simulation engine is the feature that differentiates NEXUS from a
normal AI assistant.

Input:

``` text
Current business state
+
Candidate strategy
+
Assumptions
+
Time horizon
```

Output:

``` text
Possible future outcomes
```

## 2. First simulation

Start simple.

For a product:

``` text
base demand
price
price elasticity
inventory
supplier lead time
conversion rate
margin
```

A pricing strategy modifies price.

Demand changes according to a model.

Example conceptual relationship:

``` text
new_demand = base_demand * demand_multiplier(price_change)
```

Do not initially claim this is a scientifically perfect market model.

It is a transparent simulation model.

## 3. Monte Carlo-style simulation

For each scenario:

1.  sample uncertain variables
2.  apply strategy
3.  simulate demand
4.  update inventory
5.  calculate revenue
6.  calculate costs
7.  calculate profit
8.  record outcome

Repeat many times.

``` text
Scenario
   │
   ├── Run 1
   ├── Run 2
   ├── Run 3
   ├── ...
   └── Run N
          ↓
   Outcome distribution
```

## 4. Example outputs

``` text
Expected revenue
Expected profit
Profit standard deviation
Probability of loss
Probability of stockout
Expected inventory
Worst 5% outcome
Best 5% outcome
```

## 5. Strategy comparison

Every strategy should produce comparable metrics.

Example:

``` text
Strategy A
Strategy B
Strategy C
```

Then rank them according to a configurable objective.

Example:

``` text
score =
    profit_weight * normalized_profit
    - risk_weight * normalized_risk
    - stockout_weight * stockout_probability
```

The weights should be visible to the user.

## 6. GPU path

Do not force GPU usage before the CPU implementation is correct.

First:

``` text
CPU simulation
   ↓
correctness tests
   ↓
benchmark
   ↓
vectorize/parallelize
   ↓
AMD GPU experiment
```

Possible GPU workloads:

-   large scenario simulation
-   demand model inference
-   embeddings
-   LLM inference

Use ROCm-compatible frameworks when the AMD environment is available.

## 7. Explainability

Every simulation should expose:

-   assumptions
-   parameters
-   strategy
-   number of runs
-   model version
-   dataset version
-   random seed
-   execution environment
-   timestamp

This makes results reproducible.

## 8. Simulation must not pretend to predict the future

The UI should use language such as:

> "Under these assumptions, simulated outcomes suggest..."

Not:

> "This will definitely happen."

That distinction is important for trust.
