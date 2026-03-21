# Beaver's Choice Paper Company — Inventory & Quoting Agent System

A multi-agent AI system built to streamline inventory management, quote generation, and sales transactions for the Beaver's Choice Paper Company.

## Overview

The Beaver's Choice Paper Company was losing potential sales due to slow, manual processes for handling customer inquiries, checking inventory, and generating quotes. This project delivers a multi-agent solution (at most five agents) that automates these workflows end-to-end using Python and the `smolagents` framework.

## What the System Does

The agents work together to:

- **Inventory Management** — Answer questions about current stock levels and automatically reorder supplies when inventory falls below threshold, using a `sqlite3` database as the source of truth.
- **Quote Generation** — Produce accurate, competitive quotes for customers by consulting historical quote data and applying appropriate pricing strategies.
- **Sales Transactions** — Finalize sales based on available inventory and estimated delivery timelines.

## Agent Workflow

```mermaid
flowchart TD
    Customer(["👤 Customer"])

    subgraph Orchestrator["🧠 Orchestrator Agent\nRoutes inquiry · Holds conversation state · Synthesizes final reply"]
        OA["Classify intent → delegate to specialist\nCollect specialist result → reply to customer"]
    end

    subgraph InventoryAgent["📦 Inventory Agent\nAnswers stock questions · Triggers reorders when stock is low"]
        T1["🔧 check_inventory\nPurpose: look up current stock for a paper type\nHelpers: get_stock_level(item_name, date)\n         get_all_inventory(as_of_date)"]
        T2["🔧 reorder_stock\nPurpose: place a supplier order and record it\nHelpers: get_supplier_delivery_date(date, qty)\n         create_transaction(item, 'stock_orders', qty, price, date)"]
    end

    subgraph QuoteAgent["💰 Quote Agent\nBuilds competitive quotes · Applies bulk discounts"]
        T3["🔧 get_quote_history\nPurpose: retrieve similar past quotes for context\nHelper: search_quote_history(search_terms, limit)"]
        T4["🔧 calculate_quote\nPurpose: compute total price with bulk discount tiers\nHelpers: get_stock_level(item_name, date)\n         get_cash_balance(as_of_date)"]
    end

    subgraph SalesAgent["🛒 Sales Agent\nFinalizes transactions · Advises delivery timelines"]
        T5["🔧 check_delivery_timeline\nPurpose: estimate supplier delivery date by order size\nHelper: get_supplier_delivery_date(date, quantity)"]
        T6["🔧 fulfill_order\nPurpose: deduct stock and record the sale\nHelpers: get_stock_level(item_name, date)\n         create_transaction(item, 'sales', qty, price, date)"]
    end

    DB[("🗄️ SQLite DB\ntransactions · inventory\nquotes · quote_requests")]

    Customer -- "Text inquiry" --> OA

    OA -- "item_name, as_of_date" --> T1
    OA -- "item_name, qty, date" --> T2
    OA -- "search_terms" --> T3
    OA -- "item_name, qty, date" --> T4
    OA -- "item_name, qty, date" --> T5
    OA -- "item_name, qty, price, date" --> T6

    T1 -- "current_stock, needs_reorder?" --> OA
    T2 -- "order_id, delivery_date" --> OA
    T3 -- "matching quotes list" --> OA
    T4 -- "unit_price, discount, total" --> OA
    T5 -- "estimated delivery date" --> OA
    T6 -- "transaction_id, confirmation" --> OA

    OA -- "Final response" --> Customer

    T1 & T2 <--> DB
    T3 & T4 <--> DB
    T5 & T6 <--> DB
```

## Project Structure

TODO

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.12+ |
| Agent Framework | `smolagents` |
| Database | `sqlite3` (built-in) |
| Input / Output | Text-based only |

## Deliverables

- [ ] Workflow diagram (image file) showing the multi-agent architecture
- [ ] `main.py` — complete multi-agent implementation
- [ ] This README / project documentation

## Project Steps

1. **Diagramming & Planning** — Design the agent workflow and interaction diagram.
2. **Implementation** — Build the multi-agent system in `main.py`.
3. **Testing & Debugging** — Validate all agents against the provided sample requests.
4. **Documentation** — Describe design decisions and how requirements are satisfied.

## Getting Started

```bash
TODO
```
