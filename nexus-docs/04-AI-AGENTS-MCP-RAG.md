# AI Agents, RAG and MCP

## 1. Agent philosophy

Avoid creating ten agents just to say "multi-agent."

Each agent needs a clear responsibility.

Initial agents:

### Manager Agent

Responsibilities:

-   understand the user's decision
-   create an analysis plan
-   delegate work
-   combine results
-   request simulation
-   prepare recommendation

### Finance Agent

Responsibilities:

-   revenue
-   cost
-   margin
-   profit
-   financial impact

### Operations Agent

Responsibilities:

-   inventory
-   warehouses
-   suppliers
-   fulfillment

### Research Agent

Responsibilities:

-   company documents
-   external information when enabled
-   evidence gathering

### Risk/Critic Agent

Responsibilities:

-   challenge assumptions
-   identify missing information
-   identify downside cases
-   detect unsupported conclusions

Start with 2--3 agents. Add others only when they solve a real problem.

## 2. Structured outputs

Agents should return typed objects.

Example conceptual schema:

``` python
class Evidence(BaseModel):
    source: str
    claim: str
    confidence: float

class AnalysisResult(BaseModel):
    findings: list[str]
    evidence: list[Evidence]
    assumptions: list[str]
    uncertainties: list[str]
```

Do not rely on parsing arbitrary prose.

## 3. RAG

RAG is for company knowledge.

Pipeline:

``` text
Document
   ↓
Parser
   ↓
Chunker
   ↓
Embedding model
   ↓
Vector DB
   ↓
Retriever
   ↓
Relevant chunks
   ↓
Agent
```

Important distinction:

``` text
PostgreSQL → facts and transactional state
Vector DB  → semantic document retrieval
LLM        → reasoning/synthesis
Simulator  → quantitative futures
```

Do not ask the LLM to calculate everything from retrieved prose.

## 4. MCP

MCP is the tool interface between agents and external capabilities.

NEXUS should implement both:

-   MCP client
-   custom MCP servers

Potential servers:

### nexus-data-mcp

Tools:

``` text
get_customer()
get_product()
get_product_sales()
get_inventory()
get_supplier()
query_orders()
get_financial_metrics()
```

### nexus-research-mcp

Tools:

``` text
search_company_documents()
search_external_information()
```

### nexus-compute-mcp

Tools:

``` text
run_simulation()
forecast_demand()
calculate_strategy_metrics()
```

### nexus-action-mcp

Tools:

``` text
create_purchase_order()
update_price()
create_campaign()
```

For the hackathon, action tools should be simulated or sandboxed.

## 5. Tool design

Tools must have:

-   clear name
-   typed input
-   typed output
-   validation
-   authorization
-   audit logging
-   timeout
-   error handling

Bad:

``` text
run_sql(query: str)
```

Better:

``` text
get_product_sales(
    product_id: UUID,
    start_date: date,
    end_date: date
)
```

Do not give an LLM unrestricted SQL or shell access.

## 6. Human approval

Side effects require approval.

``` text
Agent proposes action
       ↓
Policy check
       ↓
Human approval
       ↓
Action tool
       ↓
Audit log
```

Never let an LLM silently perform consequential actions.

## 7. MCP learning goal

When implementing MCP, first learn:

1.  Why tool protocols exist.
2.  Client/server architecture.
3.  Tool discovery.
4.  JSON schemas.
5.  Request/response flow.
6.  Authorization.
7.  Timeouts and failures.
8.  Stateless/scalable server design.

The current MCP specification has evolved toward a stateless protocol
core and updated authorization/scalability behavior, so pin the
implementation to the version used by the project rather than assuming
older tutorials are current.
