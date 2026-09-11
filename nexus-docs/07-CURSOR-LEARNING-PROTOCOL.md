# Cursor Learning Protocol

## The most important document in this repository

Cursor is an assistant, not your replacement.

The goal of NEXUS is not merely to finish the application.

The goal is for you to become capable of explaining, modifying,
debugging and extending the application without Cursor.

## 1. Golden rule

**Never paste a large feature request into Cursor and accept everything
it generates.**

Instead use:

``` text
Learn → Design → Attempt → Review → Test → Explain → Commit
```

## 2. Three Cursor modes

### Mode A --- Teacher

Use Cursor when you do not understand a concept.

Prompt style:

> Explain SQLAlchemy sessions and transactions for this project. Do not
> write code yet. Give me a small example and then ask me to implement
> it.

### Mode B --- Reviewer

You write the code first.

Then:

> Review this implementation. Do not rewrite it. Identify bugs, design
> problems and missing tests. Explain why each issue matters.

### Mode C --- Debugger

When tests fail:

> Here is the failing test and error. Help me reason about the root
> cause. Give me hints first. Do not provide the final fix unless I ask.

## 3. Forbidden default behavior

Do not ask Cursor:

> Build the entire backend.

Do not ask:

> Implement authentication, agents, MCP and simulation.

Do not allow a generated feature to introduce dependencies you cannot
explain.

## 4. Before every feature

Write a short note:

``` text
Feature:
Why:
Inputs:
Outputs:
Dependencies:
Failure cases:
Tests:
```

Then learn the required concepts.

## 5. Implementation ladder

For each component:

### Level 1 --- Understand

Explain:

-   what it does
-   why it exists
-   alternatives
-   failure modes

### Level 2 --- Design

Draw:

``` text
input → component → output
```

### Level 3 --- Implement

You write the first version.

Cursor can help with syntax and review.

### Level 4 --- Test

Write tests before trusting the component.

### Level 5 --- Explain

Close Cursor and explain the code aloud.

If you cannot explain it, you do not own the implementation yet.

## 6. Ask Cursor to quiz you

At the end of each milestone:

> Quiz me on the concepts and implementation from this milestone. Ask
> one question at a time. Do not reveal answers immediately.

## 7. Required learning journal

Maintain:

``` text
docs/learning/
    python.md
    fastapi.md
    postgres.md
    sqlalchemy.md
    redis.md
    rag.md
    agents.md
    mcp.md
    simulation.md
    rocm.md
    docker.md
    testing.md
```

Each topic should contain:

``` text
What I learned
Why NEXUS uses it
Small example
Common mistakes
Questions I still have
```

## 8. Checkpoint rule

At the end of each milestone:

1.  Run tests.
2.  Run lint/type checks.
3.  Manually test the feature.
4.  Explain it without looking at code.
5.  Commit to Git.

Example commits:

``` text
feat: add NovaCart product model
feat: add synthetic data generator
test: validate generated business data
feat: add inventory service
feat: add decision API
```

## 9. When Cursor writes code

Ask:

> Explain every new file and every important function before I accept
> it.

Then ask:

> What assumptions does this implementation make?

Then:

> What tests would prove this implementation is correct?

## 10. Dependency discipline

Before installing a package:

1.  Why do we need it?
2.  Is Python standard library enough?
3.  Is there an existing dependency already solving it?
4.  Is the package maintained?
5.  Does it make the architecture harder to understand?

Do not accumulate libraries.

## 11. AI-generated code verification

For every important AI-generated function:

-   read it
-   predict its behavior
-   run tests
-   create an edge case
-   inspect failure behavior
-   explain it

## 12. Learning priority

Do not learn everything simultaneously.

Order:

``` text
Python
↓
PostgreSQL / SQL
↓
FastAPI
↓
SQLAlchemy
↓
Testing
↓
Redis / background jobs
↓
React / Next.js
↓
RAG
↓
LLM structured outputs
↓
Agents
↓
Tool calling
↓
MCP
↓
Simulation
↓
Observability
↓
Docker / CI
↓
ROCm / GPU
↓
Optimization
```

## 13. Personal rule

If a feature can be learned by implementing a small version yourself, do
that before asking Cursor to generate the production version.

The project should stretch your skills, not hide your gaps.
