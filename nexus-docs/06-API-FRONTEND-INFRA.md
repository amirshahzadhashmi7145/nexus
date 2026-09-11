# API, Frontend and Infrastructure

## 1. Suggested repository

``` text
nexus/
├── apps/
│   ├── api/
│   └── web/
│
├── services/
│   ├── orchestrator/
│   ├── simulation/
│   ├── ingestion/
│   └── mcp/
│
├── packages/
│   ├── schemas/
│   └── client/
│
├── data/
│   ├── seed/
│   └── generated/
│
├── docs/
├── tests/
├── docker/
├── scripts/
├── .github/
├── docker-compose.yml
└── README.md
```

Do not create all of this immediately.

Start as a modular monolith if that makes development easier.

Split services only when the boundary is justified.

## 2. FastAPI endpoints

Initial endpoints:

``` text
GET  /health

GET  /api/v1/products
GET  /api/v1/inventory
GET  /api/v1/orders

POST /api/v1/decisions
GET  /api/v1/decisions/{id}

POST /api/v1/simulations
GET  /api/v1/simulations/{id}

POST /api/v1/approvals/{id}

GET  /api/v1/audit
```

Later:

``` text
POST /api/v1/documents
POST /api/v1/ingestion
GET  /api/v1/agents/runs/{id}
```

## 3. API principles

Use:

-   Pydantic schemas
-   dependency injection
-   service layer
-   repository/data-access layer
-   centralized error handling
-   structured logging
-   request IDs
-   authentication
-   authorization

Avoid putting business logic directly in route functions.

## 4. Frontend pages

Initial:

``` text
/login
/dashboard
/decisions
/decisions/[id]
/simulations/[id]
/data
/audit
/settings
```

## 5. Main dashboard

Show:

``` text
Revenue
Profit
Inventory value
Orders
Stockout risk
Active simulations
Recent decisions
```

## 6. Decision workspace

Example:

``` text
┌─────────────────────────────────────────────┐
│ Ask NEXUS                                   │
│                                             │
│ What happens if we reduce Product P-172    │
│ by 10%?                                     │
│                                  [Analyze]  │
└─────────────────────────────────────────────┘
```

Then display:

-   analysis plan
-   evidence
-   agent activity
-   simulation progress
-   strategy comparison
-   recommendation
-   assumptions
-   risks
-   approval button

## 7. Infrastructure

Local development:

``` text
Docker Compose
├── postgres
├── redis
├── api
├── worker
├── web
└── vector-db
```

Production/hackathon cloud can be introduced later.

## 8. Observability

Capture:

-   request ID
-   user ID
-   decision ID
-   agent run ID
-   tool call
-   tool duration
-   model
-   token usage when available
-   simulation duration
-   errors
-   final outcome

Never log secrets or sensitive credentials.
