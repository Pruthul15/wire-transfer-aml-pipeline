# ============================================
# SCRIPT 7: AI Anomaly Detection
# Uses Isolation Forest — same AI technique
# used by JPMorgan, HSBC, and major banks
# to detect unusual wire transfer behavior
#
# Simple explanation:
# AI learns what NORMAL looks like
# Then flags anything that doesn't fit
# No rules needed — AI figures it out
# ============================================

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

DB_PATH = "../output/aml_database.db"

def run_anomaly_detection():
    print("="*55)
    print("AI ANOMALY DETECTION — Isolation Forest")
    print("Same technique used by major banks worldwide")
    print("="*55)

    # ----------------------------------------
    # STEP 1: Load data from database
    # ----------------------------------------
    print("\nStep 1: Loading wire transactions...")
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT
            from_account,
            from_bank,
            to_bank,
            amount_paid,
            amount_received,
            payment_currency,
            receiving_currency,
            payment_format,
            is_laundering
        FROM wire_transactions
        LIMIT 500000
    """, conn)
    conn.close()

    print(f"✓ Loaded {len(df):,} transactions")
    print(f"✓ Known fraud cases: {df['is_laundering'].sum():,}")

    # ----------------------------------------
    # STEP 2: Prepare features for AI
    # ----------------------------------------
    print("\nStep 2: Preparing data for AI...")

    le = LabelEncoder()

    df['payment_currency_code'] = le.fit_transform(
        df['payment_currency']
    )
    df['receiving_currency_code'] = le.fit_transform(
        df['receiving_currency']
    )
    df['payment_format_code'] = le.fit_transform(
        df['payment_format']
    )

    # Currency mismatch flag
    df['currency_mismatch'] = (
        df['payment_currency'] != df['receiving_currency']
    ).astype(int)

    # Amount difference
    df['amount_difference'] = abs(
        df['amount_paid'] - df['amount_received']
    )

    # Log of amount — handles huge value ranges better
    df['log_amount'] = np.log1p(df['amount_paid'])

    features = [
        'log_amount',
        'amount_paid',
        'amount_received',
        'amount_difference',
        'currency_mismatch',
        'payment_currency_code',
        'receiving_currency_code',
        'payment_format_code',
        'from_bank',
        'to_bank'
    ]

    X = df[features].fillna(0)
    print(f"✓ Features prepared: {len(features)} features")

    # ----------------------------------------
    # STEP 3: Train Isolation Forest
    # contamination=0.01 means we expect
    # about 1% suspicious transactions
    # ----------------------------------------
    print("\nStep 3: Training AI model...")
    print("AI is learning what NORMAL looks like...")

    model = IsolationForest(
        contamination=0.01,
        random_state=42,
        n_estimators=100,
        n_jobs=-1
    )
    model.fit(X)
    print("✓ AI model trained!")

    # ----------------------------------------
    # STEP 4: Predict anomalies
    # -1 = anomaly (suspicious)
    #  1 = normal
    # ----------------------------------------
    print("\nStep 4: AI scanning all transactions...")
    df['anomaly_score'] = model.decision_function(X)
    df['ai_prediction'] = model.predict(X)

    df['ai_flag'] = df['ai_prediction'].map({
        -1: 'SUSPICIOUS',
         1: 'NORMAL'
    })

    # ----------------------------------------
    # STEP 5: Results
    # ----------------------------------------
    print("\n" + "="*55)
    print("AI DETECTION RESULTS")
    print("="*55)

    total = len(df)
    ai_flagged = (df['ai_prediction'] == -1).sum()
    known_fraud = df['is_laundering'].sum()

    print(f"Total transactions scanned : {total:,}")
    print(f"AI flagged as suspicious   : {ai_flagged:,}")
    print(f"Known fraud cases          : {known_fraud:,}")
    print(f"AI flag rate               : {ai_flagged/total*100:.2f}%")

    # ----------------------------------------
    # STEP 6: Accuracy check
    # ----------------------------------------
    print("\n" + "="*55)
    print("AI ACCURACY CHECK")
    print("="*55)

    tp = ((df['ai_prediction'] == -1) &
          (df['is_laundering'] == 1)).sum()
    fp = ((df['ai_prediction'] == -1) &
          (df['is_laundering'] == 0)).sum()
    tn = ((df['ai_prediction'] == 1) &
          (df['is_laundering'] == 0)).sum()
    fn = ((df['ai_prediction'] == 1) &
          (df['is_laundering'] == 1)).sum()

    print(f"✅ Caught real fraud        : {tp:,}")
    print(f"❌ Missed real fraud        : {fn:,}")
    print(f"⚠  False alarms            : {fp:,}")
    print(f"✅ Correctly cleared        : {tn:,}")

    if tp + fn > 0:
        recall = tp / (tp + fn) * 100
        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        print(f"\nFraud Recall Rate          : {recall:.1f}%")
        print(f"Precision Rate             : {precision:.1f}%")
        print(f"(AI caught {recall:.1f}% of all known fraud)")

    # ----------------------------------------
    # STEP 7: Top suspicious transactions
    # ----------------------------------------
    print("\n" + "="*55)
    print("TOP 10 MOST SUSPICIOUS TRANSACTIONS")
    print("(Lowest anomaly score = most suspicious)")
    print("="*55)

    top_suspicious = df.nsmallest(10, 'anomaly_score')[[
        'from_account', 'from_bank', 'to_bank',
        'amount_paid', 'payment_format',
        'currency_mismatch', 'anomaly_score',
        'is_laundering'
    ]]
    print(top_suspicious.to_string(index=False))

    # ----------------------------------------
    # STEP 8: Breakdown by payment format
    # ----------------------------------------
    print("\n" + "="*55)
    print("AI FLAGS BY PAYMENT FORMAT")
    print("="*55)

    format_summary = df[
        df['ai_prediction'] == -1
    ].groupby('payment_format').agg(
        ai_flagged=('ai_flag', 'count'),
        actual_fraud=('is_laundering', 'sum')
    ).sort_values('ai_flagged', ascending=False)

    print(format_summary.to_string())

    # ----------------------------------------
    # STEP 9: Show fraud the AI caught
    # ----------------------------------------
    print("\n" + "="*55)
    print("ACTUAL FRAUD CASES AI CAUGHT")
    print("="*55)

    caught = df[
        (df['ai_prediction'] == -1) &
        (df['is_laundering'] == 1)
    ][[
        'from_account', 'from_bank',
        'amount_paid', 'payment_format',
        'anomaly_score'
    ]]

    if len(caught) > 0:
        print(caught.to_string(index=False))
    else:
        print("None caught in this sample")
        print("Try running with full dataset")

    print("\n" + "="*55)
    print("ANOMALY DETECTION COMPLETE")
    print("="*55)
    print("\nWhat this means in plain English:")
    print(f"→ AI scanned {total:,} wires without any rules")
    print(f"→ Flagged {ai_flagged:,} as suspicious")
    print(f"→ Caught {tp:,} confirmed fraud cases")
    print(f"→ This is how real banks use AI for AML")

run_anomaly_detection()