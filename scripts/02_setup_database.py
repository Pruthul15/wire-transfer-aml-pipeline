# ============================================
# SCRIPT 2: Create our AML Database
# This is what Wells Fargo does — load wire
# transaction data into a queryable database
# ============================================

import sqlite3
import pandas as pd
import os

# Database will be saved in our project folder
DB_PATH = "../output/aml_database.db"
DATA_PATH = "../data/HI-Small_Trans.csv"

def create_database():
    print("Setting up AML Database...")
    print("This is exactly what a Wells Fargo data engineer does.\n")

    # Step 1: Connect to database (creates it if not exists)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"✓ Database created at: {DB_PATH}")

    # Step 2: Create the wire transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wire_transactions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT,
            from_bank           TEXT,
            from_account        TEXT,
            to_bank             TEXT,
            to_account          TEXT,
            amount_received     REAL,
            receiving_currency  TEXT,
            amount_paid         REAL,
            payment_currency    TEXT,
            payment_format      TEXT,
            is_laundering       INTEGER
        )
    """)
    print("✓ Table created: wire_transactions")

    # Step 3: Load the CSV data
    print("\nLoading IBM AML data...")
    df = pd.read_csv(DATA_PATH)
    print(f"✓ Loaded {len(df):,} transactions from CSV")

    # Step 4: Rename columns to match our table
    df.columns = [
        'timestamp', 'from_bank', 'from_account',
        'to_bank', 'to_account', 'amount_received',
        'receiving_currency', 'amount_paid',
        'payment_currency', 'payment_format', 'is_laundering'
    ]

    # Step 5: Insert into database
    print("Inserting into database (this takes a minute)...")
    df.to_sql('wire_transactions', conn,
              if_exists='replace', index=False)
    print(f"✓ {len(df):,} rows inserted into database")

    # Step 6: Quick check
    cursor.execute("SELECT COUNT(*) FROM wire_transactions")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM wire_transactions
        WHERE is_laundering = 1
    """)
    fraud = cursor.fetchone()[0]

    print(f"\n{'='*40}")
    print(f"DATABASE READY")
    print(f"{'='*40}")
    print(f"Total transactions : {total:,}")
    print(f"Fraud (laundering) : {fraud:,}")
    print(f"Legitimate         : {total - fraud:,}")
    print(f"Fraud rate         : {(fraud/total*100):.2f}%")
    print(f"{'='*40}")

    conn.commit()
    conn.close()
    print("\n✓ Database saved. Ready for SQL queries!")

create_database()