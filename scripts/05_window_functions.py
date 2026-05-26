# ============================================
# SCRIPT 5: Window Functions for AML Detection
# These are the most powerful SQL queries
# Wells Fargo analysts use daily
# Window functions let us compare each
# transaction to its own history
# ============================================

import sqlite3
import pandas as pd

DB_PATH = "../output/aml_database.db"

def run_query(title, query, conn):
    print(f"\n{'='*55}")
    print(f"{title}")
    print(f"{'='*55}")
    df = pd.read_sql_query(query, conn)
    print(f"Results: {len(df)} rows")
    print(df.to_string(index=False))
    return df

def window_function_analysis():
    conn = sqlite3.connect(DB_PATH)
    print("Running Window Function Analysis...")
    print("This is senior-level SQL used at Wells Fargo\n")

    # ----------------------------------------
    # QUERY 1: ROW_NUMBER
    # Rank every wire per account by amount
    # Find each account's BIGGEST wire ever
    # ----------------------------------------
    query1 = """
        SELECT
            from_account,
            from_bank,
            amount_paid,
            payment_format,
            timestamp,
            ROW_NUMBER() OVER (
                PARTITION BY from_account
                ORDER BY amount_paid DESC
            ) as rank_by_amount
        FROM wire_transactions
        WHERE is_laundering = 1
        LIMIT 20
    """
    run_query(
        "QUERY 1: ROW_NUMBER — Rank fraud transactions by amount",
        query1, conn
    )

    # ----------------------------------------
    # QUERY 2: LAG() — Compare to previous wire
    # This catches sudden spikes
    # Criminal sends normal wires then suddenly
    # sends a massive one — classic red flag
    # ----------------------------------------
    query2 = """
        WITH account_history AS (
            SELECT
                from_account,
                from_bank,
                amount_paid,
                timestamp,
                is_laundering,
                LAG(amount_paid) OVER (
                    PARTITION BY from_account
                    ORDER BY timestamp
                ) as previous_amount
            FROM wire_transactions
            LIMIT 500000
        )
        SELECT
            from_account,
            from_bank,
            previous_amount,
            amount_paid as current_amount,
            ROUND(amount_paid - previous_amount, 2)
                as amount_increase,
            ROUND(amount_paid * 100.0 /
                NULLIF(previous_amount, 0), 1)
                as pct_of_previous,
            is_laundering
        FROM account_history
        WHERE previous_amount IS NOT NULL
          AND amount_paid > previous_amount * 5
          AND previous_amount > 1000
          AND is_laundering = 1
        ORDER BY pct_of_previous DESC
        LIMIT 15
    """
    run_query(
        "QUERY 2: LAG() — Detect sudden amount spikes (5x jumps)",
        query2, conn
    )

    # ----------------------------------------
    # QUERY 3: Running Total per account
    # See cumulative money moved by each account
    # Helps catch accounts slowly building up
    # to large amounts over time
    # ----------------------------------------
    query3 = """
        SELECT
            from_account,
            from_bank,
            timestamp,
            amount_paid,
            SUM(amount_paid) OVER (
                PARTITION BY from_account
                ORDER BY timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING
                AND CURRENT ROW
            ) as running_total,
            is_laundering
        FROM wire_transactions
        WHERE is_laundering = 1
        ORDER BY from_account, timestamp
        LIMIT 20
    """
    run_query(
        "QUERY 3: Running Total — Cumulative amount per fraud account",
        query3, conn
    )

    # ----------------------------------------
    # QUERY 4: LEAD() — Look AHEAD
    # After a large suspicious wire,
    # what happens next?
    # Criminals often move money quickly
    # after placement
    # ----------------------------------------
    query4 = """
        WITH next_wire AS (
            SELECT
                from_account,
                from_bank,
                amount_paid,
                timestamp,
                is_laundering,
                LEAD(amount_paid) OVER (
                    PARTITION BY from_account
                    ORDER BY timestamp
                ) as next_amount,
                LEAD(timestamp) OVER (
                    PARTITION BY from_account
                    ORDER BY timestamp
                ) as next_timestamp
            FROM wire_transactions
            WHERE is_laundering = 1
            LIMIT 500000
        )
        SELECT
            from_account,
            from_bank,
            timestamp as current_time,
            amount_paid as current_amount,
            next_timestamp,
            next_amount,
            ROUND(next_amount - amount_paid, 2)
                as change_in_amount
        FROM next_wire
        WHERE next_amount IS NOT NULL
        ORDER BY amount_paid DESC
        LIMIT 15
    """
    run_query(
        "QUERY 4: LEAD() — What happens AFTER a fraud transaction?",
        query4, conn
    )

    # ----------------------------------------
    # QUERY 5: RANK accounts by fraud risk
    # Combine everything into one risk score
    # This is what gets presented to management
    # ----------------------------------------
    query5 = """
        WITH account_stats AS (
            SELECT
                from_account,
                from_bank,
                COUNT(*) as total_wires,
                SUM(amount_paid) as total_amount,
                AVG(amount_paid) as avg_amount,
                SUM(is_laundering) as fraud_count,
                MAX(amount_paid) as max_wire
            FROM wire_transactions
            GROUP BY from_account, from_bank
            HAVING SUM(is_laundering) > 0
        )
        SELECT
            from_account,
            from_bank,
            total_wires,
            fraud_count,
            ROUND(total_amount, 2) as total_amount,
            ROUND(avg_amount, 2) as avg_amount,
            ROUND(max_wire, 2) as max_wire,
            RANK() OVER (
                ORDER BY fraud_count DESC
            ) as risk_rank
        FROM account_stats
        ORDER BY risk_rank
        LIMIT 15
    """
    run_query(
        "QUERY 5: RANK() — Top 15 highest risk accounts",
        query5, conn
    )

    conn.close()
    print(f"\n{'='*55}")
    print("WINDOW FUNCTION ANALYSIS COMPLETE")
    print("These queries = senior analyst level SQL")
    print(f"{'='*55}")

window_function_analysis()