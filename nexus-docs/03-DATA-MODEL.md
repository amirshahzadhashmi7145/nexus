# Data Model and Synthetic Dataset

## 1. Philosophy

We do not have a real store.

That is acceptable.

NovaCart is a synthetic organization whose data is generated with
deterministic relationships.

The dataset should feel like a real operational system.

## 2. PostgreSQL entities

Initial schema:

``` text
organizations
users
memberships

customers
customer_segments

products
categories
suppliers
supplier_products
warehouses

inventory
inventory_events

orders
order_items

payments
returns

marketing_campaigns
campaign_events

support_tickets

financial_records

decision_runs
strategies
simulation_runs
simulation_results

tool_calls
audit_logs
```

Do not implement every table on day one.

Start with:

``` text
customers
products
suppliers
warehouses
inventory
orders
order_items
financial_records
```

Then expand.

## 3. Relationships

``` text
Customer
   │
   └──< Order
          │
          └──< OrderItem >── Product
                               │
                               └── Supplier

Product
   │
   └──< Inventory >── Warehouse
```

## 4. Data generation

Build a Python CLI:

``` bash
python -m app.cli.generate_data --customers 10000 --products 500 --orders 50000
```

Generation should support:

-   deterministic random seed
-   configurable sizes
-   realistic distributions
-   referential integrity
-   date ranges
-   reproducibility

Example:

``` text
seed = 42
```

Running the same generator with the same seed should produce the same
dataset.

## 5. Realistic behavior

Do not make all products equally popular.

Example demand distribution:

-   10% high-demand products
-   60% normal products
-   30% slow-moving products

Customer behavior should also vary:

-   frequent buyers
-   occasional buyers
-   high-value customers
-   discount-sensitive customers
-   inactive customers

Supplier behavior should vary:

-   reliable
-   average
-   unreliable

## 6. Synthetic history

Generate at least several months of history.

The simulation engine can then use history to estimate:

-   demand
-   seasonality
-   price sensitivity
-   stockout effects
-   customer behavior

## 7. Documents for RAG

Create synthetic company documents:

``` text
docs/company/
    pricing_policy.md
    return_policy.md
    supplier_policy.md
    inventory_policy.md
    marketing_policy.md
    finance_policy.md
    management_report_q1.md
```

Later convert/add PDF versions.

The documents should contain information that matters to decisions.

Example:

> Products with inventory coverage below 14 days require manager
> approval for promotional campaigns.

That gives the RAG system something meaningful to retrieve.

## 8. Data quality checks

The generator must verify:

-   every order references an existing customer
-   every order item references an existing product
-   inventory references valid product/warehouse pairs
-   quantities are positive
-   prices are non-negative
-   dates are valid
-   financial totals reconcile
-   no impossible stock levels are produced

Build tests for these rules.

## 9. Why PostgreSQL?

PostgreSQL is the source of truth for structured business state.

The vector database is NOT the source of truth.

RAG should retrieve knowledge; business calculations should use
structured data.
