# Architectural Decision Log

Record important decisions here.

## Template

``` text
Date:
Decision:
Context:
Options:
Chosen:
Why:
Trade-offs:
Consequences:
Revisit when:
```

## Initial decisions

### ADR-001 --- Synthetic NovaCart dataset

Decision:

Use a synthetic e-commerce organization as the initial digital twin.

Reason:

-   no real business data required
-   reproducible
-   safe
-   controllable
-   easy to test
-   ideal for simulations

### ADR-002 --- PostgreSQL as source of truth

Decision:

Structured business state lives in PostgreSQL.

Reason:

Relational business entities require consistency and transactions.

### ADR-003 --- RAG does not replace structured data

Decision:

Use RAG for documents and policies, PostgreSQL for transactional facts.

Reason:

Semantic retrieval and transactional queries solve different problems.

### ADR-004 --- Human approval for side effects

Decision:

Agent actions that change state require approval.

Reason:

Safety, auditability and predictable behavior.

### ADR-005 --- CPU before GPU

Decision:

Implement and benchmark simulation on CPU before moving to AMD GPU.

Reason:

GPU optimization without a correct baseline is difficult to validate.

### ADR-006 --- Modular monolith first

Decision:

Do not begin with dozens of microservices.

Reason:

The project is being built by one developer and is also a learning
project.

Split services only when there is a concrete architectural reason.
