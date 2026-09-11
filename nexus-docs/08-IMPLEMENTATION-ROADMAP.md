# Implementation and Learning Roadmap

## Phase 0 --- Project setup

Learn:

-   Git workflow
-   Python virtual environments
-   project structure
-   environment variables
-   Docker basics

Deliverable:

-   Git repository
-   README
-   Python app
-   tests running
-   Docker Compose skeleton

------------------------------------------------------------------------

## Phase 1 --- NovaCart data foundation

Learn:

-   relational modeling
-   SQL
-   PostgreSQL
-   primary/foreign keys
-   indexes
-   transactions
-   SQLAlchemy

Build:

-   product model
-   customer model
-   supplier model
-   warehouse model
-   inventory model
-   order model
-   order item model

Then:

-   synthetic data generator
-   data validation tests

Checkpoint:

> Can I explain every relationship without looking at the schema?

------------------------------------------------------------------------

## Phase 2 --- FastAPI backend

Learn:

-   HTTP
-   REST
-   request/response lifecycle
-   Pydantic
-   dependency injection
-   service layer

Build:

-   health endpoint
-   product endpoints
-   inventory endpoints
-   order endpoints

Add:

-   validation
-   errors
-   tests

------------------------------------------------------------------------

## Phase 3 --- Digital twin

Learn:

-   state representation
-   derived metrics
-   reproducibility
-   data snapshots

Build:

``` text
GET /digital-twin
```

Return:

-   revenue
-   profit
-   inventory
-   orders
-   customer metrics
-   supplier metrics

------------------------------------------------------------------------

## Phase 4 --- First simulation

Do NOT use an LLM yet.

Learn:

-   probability
-   distributions
-   Monte Carlo simulation
-   sensitivity analysis
-   statistical summaries

Build:

``` text
simulate_price_change()
```

Input:

``` text
product
price change
simulation count
time horizon
```

Output:

``` text
revenue
profit
stockout probability
risk
```

This is one of the most important learning phases.

------------------------------------------------------------------------

## Phase 5 --- RAG

Learn:

-   embeddings
-   vector search
-   chunking
-   retrieval
-   reranking
-   context construction

Build:

``` text
documents
   ↓
chunks
   ↓
embeddings
   ↓
vector DB
   ↓
retriever
```

Then ask questions about NovaCart policies.

------------------------------------------------------------------------

## Phase 6 --- LLM structured outputs

Learn:

-   prompts
-   structured outputs
-   JSON schema
-   tool calling
-   hallucination
-   context limits

Build a decision planner that turns:

> "Should we reduce P-172 by 10%?"

into a structured plan.

------------------------------------------------------------------------

## Phase 7 --- Agents

Start with:

``` text
Manager
Finance
Operations
```

Do not add more agents until necessary.

Build:

``` text
Manager
   ↓
Finance + Operations
   ↓
Simulation
   ↓
Manager
```

------------------------------------------------------------------------

## Phase 8 --- MCP

Learn:

-   MCP architecture
-   client/server
-   tools
-   schemas
-   authorization
-   transport
-   errors
-   stateless architecture

Build first:

``` text
nexus-data-mcp
```

Then:

``` text
nexus-compute-mcp
```

Then:

``` text
nexus-action-mcp
```

------------------------------------------------------------------------

## Phase 9 --- Redis and workers

Learn:

-   caching
-   queues
-   background jobs
-   job state
-   retries

Move long simulations into workers.

Example:

``` text
POST /simulations
       ↓
job created
       ↓
Redis queue
       ↓
worker
       ↓
simulation
       ↓
result
```

------------------------------------------------------------------------

## Phase 10 --- WebSockets

Learn:

-   WebSocket lifecycle
-   connection management
-   events

Display:

``` text
Manager Agent started
Finance Agent running
Inventory data retrieved
Simulation started
Simulation 43% complete
Simulation completed
Recommendation ready
```

------------------------------------------------------------------------

## Phase 11 --- Frontend

Build the dashboard.

Do not spend weeks making it visually perfect.

Prioritize:

-   decision workflow
-   scenario comparison
-   traceability
-   charts
-   approval flow

------------------------------------------------------------------------

## Phase 12 --- Evaluation

Build deterministic tests for:

-   data tools
-   calculations
-   simulation
-   retrieval
-   agent outputs
-   tool arguments

Create evaluation datasets.

Example:

``` text
Question:
Should Product P-172 be reordered?

Expected evidence:
inventory + demand + supplier lead time

Forbidden:
invented numbers
```

------------------------------------------------------------------------

## Phase 13 --- Observability

Learn:

-   structured logs
-   traces
-   metrics
-   latency
-   token/cost tracking

Every decision should have a trace.

------------------------------------------------------------------------

## Phase 14 --- AMD ROCm

Only after CPU correctness.

Learn:

-   GPU architecture basics
-   ROCm
-   PyTorch on ROCm
-   GPU memory
-   batching
-   profiling
-   inference serving

Move an appropriate workload to AMD GPU.

Candidate:

``` text
large scenario simulation
```

or:

``` text
embedding / model inference
```

or:

``` text
local LLM inference with vLLM
```

Benchmark:

``` text
CPU time
GPU time
throughput
memory
```

Do not claim acceleration without measurements.

------------------------------------------------------------------------

## Phase 15 --- Production hardening

Add:

-   authentication
-   RBAC
-   rate limiting
-   input validation
-   secrets management
-   audit logging
-   Docker
-   CI
-   migrations
-   backups
-   error handling

------------------------------------------------------------------------

## Phase 16 --- Final demo

The demo should tell one story:

> "NovaCart is considering a 10% price reduction."

Then show:

1.  Current business state.
2.  NEXUS understands the question.
3.  Agents collect evidence.
4.  Candidate strategies are generated.
5.  Thousands of futures are simulated.
6.  Results are compared.
7.  Risks are explained.
8.  NEXUS recommends a strategy.
9.  Human approves.
10. Simulated action executes.
11. Full trace remains available.

That is the product.
