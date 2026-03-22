# Reflection Report


## Agent workflow & Diagram

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

The current setup has four agents in total. We have an `Orchestrator` which is the main brain of the system. Main job is to figure out what the potential customer is after and to correctly route to the most qualified sub agent that could complete the task. Once the sub agent completes their task, the Orchestrator compiles and formulates a proper response. Since I am using smolagents, the Orchestrator is a toolcalling agents that has no tools but maintains a list of managed agents. The other agents are as follows, the `InventoryAgent`, `QuoteAgent` and `SalesAgent`. Inventory agent has tools to check the inventory and if necessary, restock. The Quote agent, can look up previous quote history and generate new quotes. This includes handling discounts. Finally the Sales agent is tasked with checking delivery timeline and making the sale. At a highlevel this is a very basic setup. The system maintains all the records in SQLite. The diagram below shows the tables and relations.

```mermaid
erDiagram
    inventory {
        string item_name PK
        string category
        float  unit_price
        int    current_stock
        int    min_stock_level
    }

    transactions {
        int    id PK
        string item_name FK
        string transaction_type
        int    units
        float  price
        string transaction_date
    }

    quote_requests {
        int    id PK
        string response
    }

    quotes {
        int    request_id PK "FK to quote_requests"
        float  total_amount
        string quote_explanation
        string order_date
        string job_type
        string order_size
        string event_type
    }

    inventory ||--o{ transactions : "item_name (stock orders & sales)"
    quote_requests ||--|| quotes : "id → request_id"
```



## Eval Results Discussion



## Future Improvements