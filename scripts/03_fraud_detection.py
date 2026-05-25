# ============================================
# SCRIPT 3: Fraud Detection SQL Queries
# This is what Wells Fargo analysts run
# every single morning to find suspicious
# wire transfers
# ============================================

import sqlite3
import pandas as pd

DB_PATH = "../output/aml_database.db"

def run_query(title, query, conn):
    print(f"\n{'='*50}")
    print(f"QUERY: {title}")
    print(f"{'='*50}")
    df = pd.read_sql_query(query, conn)
    print(f"Found: {len(df)} suspicious cases")
    print(df.to_string(index=False))
    return df

def detect_fraud():
    conn = sqlite3.connect(DB_PATH)
    print("Connected to AML Database")
    print("Running fraud detection queries...\n")

    # ----------------------------------------
    # QUERY 1: STRUCTURING DETECTION
    # Criminals split large amounts into many
    # smaller transactions just under $10,000
    # to avoid bank reporting requirements
    # This is illegal under the Bank Secrecy Act
    # ----------------------------------------
    query1 = """
        SELECT
            from_account,
            from_bank,
            COUNT(*)        AS wire_count,
            SUM(amount_paid) AS total_sent,
            AVG(amount_paid) AS avg_amount,
            MIN(amount_paid) AS min_amount,
            MAX(amount_paid) AS max_amount
        FROM wire_transactions
        WHERE amount_paid BETWEEN 9000 AND 9999
        GROUP BY from_account, from_bank
        HAVING COUNT(*) >= 3
        ORDER BY wire_count DESC
        LIMIT 20
    """
    df1 = run_query("STRUCTURING DETECTION (multiple wires $9000-$9999)", query1, conn)

    # ----------------------------------------
    # QUERY 2: HIGH VELOCITY ACCOUNTS
    # Accounts sending unusually high number
    # of wires in a short period
    # Normal customer sends maybe 2-3 wires
    # a month. 50+ wires = red flag
    # ----------------------------------------
    query2 = """
        SELECT
            from_account,
            from_bank,
            COUNT(*)         AS total_wires,
            SUM(amount_paid) AS total_amount,
            MIN(timestamp)   AS first_wire,
            MAX(timestamp)   AS last_wire
        FROM wire_transactions
        GROUP BY from_account, from_bank
        HAVING COUNT(*) > 50
        ORDER BY total_wires DESC
        LIMIT 20
    """
    df2 = run_query("HIGH VELOCITY ACCOUNTS (50+ wires)", query2, conn)

    # ----------------------------------------
    # QUERY 3: CURRENCY MISMATCH
    # When payment currency differs from
    # receiving currency — could mean
    # layering money through FX conversions
    # ----------------------------------------
    query3 = """
        SELECT
            from_account,
            from_bank,
            to_bank,
            payment_currency,
            receiving_currency,
            COUNT(*)         AS mismatch_count,
            SUM(amount_paid) AS total_amount
        FROM wire_transactions
        WHERE payment_currency != receiving_currency
        GROUP BY from_account, from_bank,
                 payment_currency, receiving_currency
        HAVING COUNT(*) > 5
        ORDER BY total_amount DESC
        LIMIT 20
    """
    df3 = run_query("CURRENCY MISMATCH (possible FX layering)", query3, conn)

    # ----------------------------------------
    # QUERY 4: CONFIRMED FRAUD SUMMARY
    # Cross check our findings against
    # known laundering cases in the data
    # ----------------------------------------
    query4 = """
        SELECT
            payment_format,
            COUNT(*)         AS total_transactions,
            SUM(is_laundering) AS confirmed_fraud,
            ROUND(SUM(is_laundering) * 100.0 / COUNT(*), 2)
                             AS fraud_rate_pct
        FROM wire_transactions
        GROUP BY payment_format
        ORDER BY fraud_rate_pct DESC
    """
    df4 = run_query("FRAUD RATE BY PAYMENT FORMAT", query4, conn)

    conn.close()
    print(f"\n{'='*50}")
    print("DETECTION COMPLETE")
    print(f"{'='*50}")

detect_fraud()