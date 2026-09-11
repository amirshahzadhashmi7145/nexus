# NEXUS --- Autonomous Future Intelligence

## Product vision

NEXUS is an AI-powered digital-twin and decision-intelligence platform
for organizations.

**Core promise:**

> Simulate decisions. Discover better strategies. Act with confidence.

NEXUS does not primarily answer questions like a chatbot. It connects
business data, company knowledge, AI agents, simulation, evaluation, and
controlled tool execution into one decision loop:

**Observe → Reason → Simulate → Evaluate → Recommend → Human approval →
Act → Monitor**

## Hackathon implementation strategy

We will build a fictional but realistic e-commerce company called
**NovaCart**.

NovaCart is our controlled digital twin. We do not need access to a real
store.

The MVP will demonstrate strategic decisions such as:

-   Should we reduce the price of a product?
-   Should we reorder inventory now?
-   Which products should receive marketing budget?
-   What happens if a supplier is delayed?
-   Which strategy maximizes expected profit while controlling risk?

The synthetic data must be relational and internally consistent, not
random CSV rows.

## Core technology stack

### Backend

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy
-   PostgreSQL
-   Redis
-   Background workers
-   WebSockets

### AI

-   LLM provider abstraction
-   Open-source model support
-   RAG
-   Embeddings
-   Vector database
-   Multi-agent orchestration
-   Structured outputs
-   Tool calling
-   MCP client/server
-   Guardrails
-   Evaluation
-   Observability/tracing

### Simulation

-   Python simulation engine
-   Demand model
-   Inventory model
-   Pricing model
-   Financial model
-   Scenario generation
-   Monte Carlo-style experimentation
-   Strategy ranking

### Frontend

-   Next.js / React
-   TypeScript
-   Dashboard
-   Scenario comparison
-   Agent activity
-   Charts
-   WebSockets

### Infrastructure

-   Docker / Docker Compose
-   GitHub Actions
-   Tests
-   Linux
-   AMD Developer Cloud
-   ROCm
-   AMD GPU inference/compute
-   Optional vLLM deployment

## Important learning rule

This repository is intentionally built as a learning project.

Cursor must NOT be treated as an autonomous programmer.

The developer must understand each subsystem before implementing it.

The preferred loop is:

1.  Learn the concept.
2.  Design the small component.
3.  Attempt implementation yourself.
4.  Ask Cursor to review/debug.
5.  Run tests.
6.  Explain the implementation back in your own words.
7.  Commit a checkpoint.
8.  Move to the next concept.

See `07-CURSOR-LEARNING-PROTOCOL.md`.

## Repository documentation

-   `01-PRODUCT-REQUIREMENTS.md` --- product requirements and MVP scope
-   `02-SYSTEM-ARCHITECTURE.md` --- complete architecture
-   `03-DATA-MODEL.md` --- database schema and synthetic dataset
-   `04-AI-AGENTS-MCP-RAG.md` --- agents, RAG, MCP and tool architecture
-   `05-SIMULATION-ENGINE.md` --- digital twin and scenario simulation
-   `06-API-FRONTEND-INFRA.md` --- APIs, frontend and infrastructure
-   `07-CURSOR-LEARNING-PROTOCOL.md` --- rules for using Cursor without
    outsourcing learning
-   `08-IMPLEMENTATION-ROADMAP.md` --- phased build and learning roadmap
-   `09-TESTING-EVALUATION.md` --- testing, AI evaluation and
    observability
-   `10-AMD-ROCM-PLAN.md` --- AMD/ROCm integration plan
-   `11-SECURITY-GUARDRAILS.md` --- security and safe execution
-   `12-DEMO-STORY.md` --- final hackathon demo narrative
-   `13-DECISION-LOG.md` --- architectural decisions to record during
    development

## Definition of success

A successful MVP should let a user:

1.  Log in.
2.  Open the NovaCart organization.
3.  Inspect the current digital twin.
4.  Ask a strategic question.
5.  Watch the manager agent decompose the problem.
6.  See agents retrieve relevant data and documents.
7.  Generate several candidate strategies.
8.  Simulate many possible futures.
9.  Compare outcomes.
10. Receive a recommendation with evidence, uncertainty and risks.
11. Approve an action.
12. Execute a safe simulated business action.
13. Inspect the complete trace afterward.

The goal is not to build every possible feature.

The goal is to build one **deep, technically credible vertical** and
expose a larger platform architecture around it.
