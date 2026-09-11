# System Architecture

## 1. High-level architecture

``` text
                           ┌─────────────────────┐
                           │   Next.js Web App   │
                           │  Dashboard / Chat   │
                           └──────────┬──────────┘
                                      │ HTTPS / WS
                                      ▼
                           ┌─────────────────────┐
                           │      FastAPI        │
                           │ API + Auth + WS     │
                           └──────────┬──────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                │
                     ▼                ▼                ▼
              ┌────────────┐   ┌────────────┐   ┌─────────────┐
              │ PostgreSQL │   │   Redis    │   │ Vector DB   │
              │ business   │   │ cache/jobs │   │ embeddings  │
              │ data       │   │ state      │   │ + RAG       │
              └────────────┘   └────────────┘   └─────────────┘
                     │
                     ▼
             ┌──────────────────┐
             │ Digital Twin     │
             │ State Builder    │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │ NEXUS Orchestr.  │
             │ Manager Agent    │
             └────────┬─────────┘
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
     Research      Finance      Operations
       Agent        Agent          Agent
          │           │            │
          └───────────┼────────────┘
                      ▼
                MCP Client
                      │
       ┌──────────────┼─────────────────┐
       ▼              ▼                 ▼
  Data MCP       Research MCP      Compute MCP
       │              │                 │
       ▼              ▼                 ▼
 PostgreSQL      Web / RAG        Simulation Engine
                                      │
                                      ▼
                                  AMD GPU
                                   / ROCm
```

## 2. Core services

### Web application

Responsibilities:

-   authentication UI
-   organization selection
-   digital-twin overview
-   decision workspace
-   scenario comparison
-   agent trace
-   approval interface
-   audit history

### API service

FastAPI responsibilities:

-   REST API
-   authentication
-   authorization
-   request validation
-   orchestration endpoints
-   WebSocket connection
-   health checks

### Orchestrator

Responsibilities:

-   accept strategic question
-   create decision plan
-   select agents
-   manage tool calls
-   collect evidence
-   request simulations
-   combine results
-   ask evaluation/critic components
-   produce recommendation

The orchestrator should NOT directly perform unrestricted database
writes.

### Digital twin

A normalized representation of the current company state.

It should be reproducible from source data.

Conceptually:

``` text
DigitalTwin(t)
    = Customers
    + Products
    + Orders
    + Inventory
    + Suppliers
    + Financial state
    + Operational state
```

### Simulation engine

Receives:

-   current state
-   candidate strategy
-   assumptions
-   time horizon
-   number of scenarios

Returns:

-   outcome distribution
-   expected values
-   downside cases
-   confidence/uncertainty metrics
-   key drivers

## 3. Event flow

Example: pricing decision.

``` text
POST /decisions
        │
        ▼
Create decision
        │
        ▼
Manager Agent
        │
        ├── get_product_sales()
        ├── get_inventory()
        ├── search_documents()
        └── get_financial_metrics()
        │
        ▼
Generate candidate strategies
        │
        ▼
run_simulation()
        │
        ▼
Simulation results
        │
        ▼
Critic / Evaluator
        │
        ▼
Recommendation
        │
        ▼
Human approval
        │
        ▼
execute_action()
        │
        ▼
Audit log
```

## 4. Synchronous vs asynchronous

Use synchronous requests for:

-   simple reads
-   health checks
-   small calculations

Use background jobs for:

-   large simulations
-   document ingestion
-   embedding generation
-   long LLM workflows
-   large evaluations

Use WebSockets for:

-   job progress
-   agent activity
-   simulation status
-   completion notifications

## 5. Failure boundaries

Every major service should have an explicit failure state.

Examples:

-   LLM unavailable
-   database unavailable
-   MCP server unavailable
-   simulation timeout
-   malformed tool arguments
-   unsupported action
-   insufficient evidence

A failure should become a structured error, not a silent fallback to
invented information.
