import pandas as pd
import numpy as np
import os
import time
from dotenv import load_dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

# Load environment variables from .env file
load_dotenv()

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("docs/quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("docs/quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.

                quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
model = OpenAIServerModel(
    model_id='gpt-5.4-mini',
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("BASE_URL"),
)

# ---------------------------------------------------------------------------
# INVENTORY AGENT TOOLS
# ---------------------------------------------------------------------------

@tool
def check_inventory(item_name: str, as_of_date: str) -> str:
    """
    Look up the current stock level for a specific paper product as of a given date.
    Use this tool when a customer asks whether an item is available or how much stock remains.
    Returns the item name, current stock quantity, and whether stock is sufficient for a typical order.

    Args:
        item_name: The exact name of the paper product to look up (e.g. 'A4 paper').
        as_of_date: The date to check inventory for, in ISO format YYYY-MM-DD.

    Returns:
        A plain-text summary of the item's current stock level and availability status.
    """
    current_stock_df = get_stock_level(item_name, as_of_date)
    current_stock = current_stock_df["current_stock"].iloc[0] if not current_stock_df.empty else 0
    min_stock_level_df = pd.read_sql("SELECT min_stock_level FROM inventory WHERE item_name = :n", db_engine, params={"n": item_name})
    min_stock_level = min_stock_level_df["min_stock_level"].iloc[0] if not min_stock_level_df.empty else 0

    if current_stock == 0:
        status = "out of stock"
    elif current_stock <= min_stock_level:
        status = "low stock"
    else:        
        status = "in stock"
    return f"{item_name}: {current_stock} units available (min stock level: {min_stock_level}) - Status: {status}"
    


@tool
def reorder_stock(item_name: str, quantity: int, order_date: str) -> str:
    """
    Place a stock replenishment order for a paper product and record it in the database.
    Use this tool when inventory falls below the minimum stock level and a reorder is needed.
    Returns the estimated supplier delivery date and the transaction ID of the order.

    Args:
        item_name: The exact name of the paper product to reorder (e.g. 'Cardstock').
        quantity: The number of units to order from the supplier.
        order_date: The date the order is placed, in ISO format YYYY-MM-DD.

    Returns:
        A plain-text confirmation including the transaction ID and estimated delivery date.
    """
    item_unit_price_df = pd.read_sql("SELECT unit_price FROM inventory WHERE item_name = :n", db_engine, params={"n": item_name})
    if item_unit_price_df.empty:
        return f"Error: Item '{item_name}' not found in inventory. Cannot place reorder."
    unit_price = item_unit_price_df["unit_price"].iloc[0]

    total_price = quantity * unit_price
    delivery_date = get_supplier_delivery_date(order_date, quantity)
    transaction_id = create_transaction(item_name, 'stock_orders', quantity, total_price, order_date)

    return f"Reorder placed: Transaction ID {transaction_id}, Item: {item_name}, Quantity: {quantity}, Estimated Delivery: {delivery_date}"


# ---------------------------------------------------------------------------
# QUOTE AGENT TOOLS
# ---------------------------------------------------------------------------

@tool
def get_quote_history(search_terms: str, limit: int = 5) -> str:
    """
    Retrieve historical quotes similar to a customer's current request.
    Use this tool to find comparable past quotes before generating a new one,
    so pricing is consistent with what has been offered before.

    Args:
        search_terms: A comma-separated string of keywords describing the request
                      (e.g. 'glossy, wedding, bulk'). Will be split and matched against
                      past quote requests and explanations.
        limit: Maximum number of historical quotes to return (default 5).

    Returns:
        A plain-text list of matching historical quotes including amounts and explanations.
    """
    search_terms_list = [term.strip() for term in search_terms.split(",") if term.strip()]
    previous_quotes = search_quote_history(search_terms_list, limit)
    if not previous_quotes:
        return "No historical quotes found matching the search terms."
    
    formatted_quotes = []
    for quote in previous_quotes:
        formatted_quotes.append(
            f"Quote for {quote['job_type']} ({quote['order_size']}): ${quote['total_amount']:.2f}\n"
            f"Explanation: {quote['quote_explanation']}\n"
            f"Event Type: {quote['event_type']}\n"
            f"Order Date: {quote['order_date']}\n"
        )
    return "\n---\n".join(formatted_quotes) 


@tool
def calculate_quote(item_name: str, quantity: int, as_of_date: str) -> str:
    """
    Generate a price quote for a customer order, applying bulk discount tiers automatically.
    Use this tool after confirming stock availability to produce a final quoted price.

    Discount tiers:
        - < 100 units  : no discount (0%)
        - 100–499 units: 5% discount
        - 500–999 units: 10% discount
        - 1000+ units  : 15% discount

    Args:
        item_name: The exact name of the paper product being quoted.
        quantity: The number of units the customer wants to purchase.
        as_of_date: The date of the quote request in ISO format YYYY-MM-DD.

    Returns:
        A plain-text quote summary showing unit price, discount applied, and total amount due.
    """
    
    unit_price_df = pd.read_sql("SELECT unit_price FROM inventory WHERE item_name = :n", db_engine, params={"n": item_name})
    if unit_price_df.empty:
        return f"Error: Item '{item_name}' not found in inventory. Cannot calculate quote."
    unit_price = unit_price_df["unit_price"].iloc[0]

    item_stock_df = get_stock_level(item_name, as_of_date)
    current_stock = item_stock_df["current_stock"].iloc[0] if not item_stock_df.empty else 0
    if current_stock < quantity:
        return f"Quote cannot be generated: Only {current_stock} units of '{item_name}' are available as of {as_of_date}."

    # Apply the bulk discount tier based on quantity (see tiers in docstring above)
    if quantity < 100:
        discount_rate = 0.0
    elif 100 <= quantity <= 499:
        discount_rate = 0.05
    elif 500 <= quantity <= 999:
        discount_rate = 0.10
    else:  # quantity >= 1000
        discount_rate = 0.15

    # Calculate: subtotal = quantity * unit_price, discount_amount, total = subtotal - discount_amount
    subtotal = quantity * unit_price
    discount_amount = subtotal * discount_rate
    total = subtotal - discount_amount

    # Return a formatted quote string: item, qty, unit_price, discount %, total
    return (
        f"Quote for {item_name}:\n"
        f"Quantity: {quantity}\n"
        f"Unit Price: ${unit_price:.2f}\n"
        f"Discount: {discount_rate*100:.0f}%\n"
        f"Total: ${total:.2f}"
    )


# ---------------------------------------------------------------------------
# SALES AGENT TOOLS
# ---------------------------------------------------------------------------

@tool
def check_delivery_timeline(quantity: int, order_date: str) -> str:
    """
    Estimate the delivery date for a customer order based on quantity and order date.
    Use this tool before finalising a sale so the customer is informed of the expected timeline.

    Delivery lead times (from supplier):
        - ≤10 units   : same day
        - 11–100 units: 1 business day
        - 101–1000    : 4 business days
        - >1000 units : 7 business days

    Args:
        quantity: The number of units in the customer's order.
        order_date: The date the order would be placed, in ISO format YYYY-MM-DD.

    Returns:
        A plain-text string stating the estimated delivery date and lead-time reason.
    """
    # Call get_supplier_delivery_date(order_date, quantity) to compute the delivery date
    super_delivery_date = get_supplier_delivery_date(order_date, quantity)

    # Determine the lead-time band label (same day / 1 day / 4 days / 7 days)
    if quantity <= 10:
        lead_time_label = "same day"
    elif quantity <= 100:
        lead_time_label = "1 business day"
    elif quantity <= 1000:
        lead_time_label = "4 business days"
    else:        
        lead_time_label = "7 business days"
    
    return f"Estimated delivery date: {super_delivery_date} (Lead time: {lead_time_label} for quantity of {quantity})"


@tool
def fulfill_order(item_name: str, quantity: int, unit_price: float, sale_date: str) -> str:
    """
    Finalise a sale by recording it in the database. Validates that sufficient stock exists
    before completing the transaction. Use this tool only after the customer has agreed to
    the quoted price.

    Args:
        item_name: The exact name of the paper product being sold.
        quantity: The number of units being sold.
        unit_price: The agreed per-unit price (after any discount) to charge the customer.
        sale_date: The date of the sale in ISO format YYYY-MM-DD.

    Returns:
        A plain-text confirmation of the sale including transaction ID and updated stock level,
        or an error message if insufficient stock is available.
    """
    # Call get_stock_level(item_name, sale_date) to verify sufficient stock
    current_stock = get_stock_level(item_name, sale_date)["current_stock"].iloc[0] if not get_stock_level(item_name, sale_date).empty else 0

    #       If current_stock < quantity, return an error string — do NOT create a transaction
    if current_stock < quantity:
        return f"Sale cannot be completed: Only {current_stock} units of '{item_name}' are available as of {sale_date}."
    
    # Calculate total_price = quantity * unit_price
    total_price = quantity * unit_price
    # Call create_transaction(item_name, 'sales', quantity, total_price, sale_date)
    transaction_id = create_transaction(item_name, 'sales', quantity, total_price, sale_date)
    # Call get_stock_level(item_name, sale_date) again to get the post-sale stock level
    post_sale_stock = get_stock_level(item_name, sale_date)["current_stock"].iloc[0] if not get_stock_level(item_name, sale_date).empty else 0
    # Return a confirmation string: transaction_id, item_name, qty sold, total charged,
    #       and remaining stock
    return f"Sale completed: Transaction ID {transaction_id}, Item '{item_name}', Quantity {quantity}, Total ${total_price:.2f}, Remaining Stock {post_sale_stock}"


# ---------------------------------------------------------------------------
# AGENT DEFINITIONS
# ---------------------------------------------------------------------------

inventory_agent = ToolCallingAgent(
    tools=[check_inventory, reorder_stock],
    model=model,
    instructions=(
        "You are an inventory specialist for Beaver's Choice Paper Company.\n"
        "Your job is to check stock levels and place restock orders when needed.\n\n"
        "Rules:\n"
        "- Always call check_inventory BEFORE deciding to reorder.\n"
        "- Only call reorder_stock when current stock is at or below the minimum stock level.\n"
        "- When restocking, order enough to comfortably exceed the minimum level.\n"
        "- Always return clear, structured text so the orchestrator can interpret your result."
    ),
    name="inventory_agent",
    description="Checks inventory levels and places restock orders when supplies run low.",
)

quote_agent = ToolCallingAgent(
    tools=[get_quote_history, calculate_quote],
    model=model,
    instructions=(
        "You are a pricing and quoting specialist for Beaver's Choice Paper Company.\n"
        "Your job is to generate accurate, competitive quotes for customer orders.\n\n"
        "Rules:\n"
        "- Always call get_quote_history first to check how similar orders were priced before.\n"
        "- Apply bulk discount tiers exactly as defined in calculate_quote.\n"
        "- Never quote a quantity greater than what is currently in stock.\n"
        "- Return the unit price, discount percentage, and final total clearly in your response."
    ),
    name="quote_agent",
    description="Generates competitive price quotes and applies bulk discount tiers.",
)

sales_agent = ToolCallingAgent(
    tools=[check_delivery_timeline, fulfill_order],
    model=model,
    instructions=(
        "You are a sales and fulfilment specialist for Beaver's Choice Paper Company.\n"
        "Your job is to close sales and advise customers on when their order will arrive.\n\n"
        "Rules:\n"
        "- Always call check_delivery_timeline before confirming a sale so the customer knows the ETA.\n"
        "- Only call fulfill_order after the customer has agreed to the quoted price.\n"
        "- fulfill_order will reject the transaction if stock is insufficient — report that clearly if it happens.\n"
        "- Always include the transaction ID and delivery date in your final response."
    ),
    name="sales_agent",
    description="Finalises sales transactions and advises customers on delivery timelines.",
)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    instructions=(
        "You are the customer-facing representative of Beaver's Choice Paper Company.\n"
        "Your job is to handle incoming customer requests about paper products and coordinate specialist agents to fulfil them.\n\n"
        "Workflow:\n"
        "1. Understand the customer's need: stock inquiry, quote request, or purchase.\n"
        "2. For stock questions: delegate to inventory_agent.\n"
        "3. For quotes: delegate to quote_agent (it will check history and calculate a price).\n"
        "4. For purchases: delegate to sales_agent to confirm delivery timeline and complete the transaction.\n"
        "5. For a full sales flow, follow this order: inventory_agent → quote_agent → sales_agent.\n"
        "6. Synthesise all specialist responses into a single, friendly, professional reply to the customer.\n\n"
        "Always be concise, helpful, and accurate. Do not invent prices or stock levels."
    ),
    managed_agents=[inventory_agent, quote_agent, sales_agent],
)


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("docs/quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############
    # TODO: Re-initialize any stateful context the orchestrator needs before the run loop.
    #       The agents and tools are already instantiated at module level above.
    #       If your orchestrator or agents need a fresh memory/history, reset it here.

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############
        # Run the request through the orchestrator
        response = orchestrator.run(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
