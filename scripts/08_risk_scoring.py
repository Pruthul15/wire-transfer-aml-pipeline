# ============================================
# SCRIPT 8: ML Risk Scoring
# Uses Random Forest to give every account
# a risk score from 0-100
#
# Simple explanation:
# Instead of saying "suspicious = yes/no"
# We say "this account is 94/100 risky"
# Banks use this to PRIORITIZE investigations
# Can't investigate 500k accounts — pick top 50
# ============================================

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

DB_PATH = "../output/aml_database.db"

def build_risk_scores():
    print("="*55)
    print("ML RISK SCORING — Random Forest Classifier")
    print("Gives every account a risk score 0-100")
    print("="*55)

    # ----------------------------------------
    # STEP 1: Load ALL data
    # ----------------------------------------
    print("\nStep 1: Loading all transactions...")
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
            timestamp,
            is_laundering
        FROM wire_transactions
    """, conn)
    conn.close()

    print(f"✓ Loaded {len(df):,} transactions")
    print(f"✓ Fraud cases: {df['is_laundering'].sum():,}")

    # ----------------------------------------
    # STEP 2: Build account-level features
    # Instead of per-transaction, we look at
    # each ACCOUNT's overall behavior pattern
    # This is how real banks do risk scoring
    # ----------------------------------------
    print("\nStep 2: Building account behavior profiles...")

    account_features = df.groupby('from_account').agg(
        total_wires        = ('amount_paid', 'count'),
        total_amount       = ('amount_paid', 'sum'),
        avg_amount         = ('amount_paid', 'mean'),
        max_amount         = ('amount_paid', 'max'),
        min_amount         = ('amount_paid', 'min'),
        std_amount         = ('amount_paid', 'std'),
        unique_banks       = ('to_bank', 'nunique'),
        unique_currencies  = ('payment_currency', 'nunique'),
        fraud_count        = ('is_laundering', 'sum'),
        total_received     = ('amount_received', 'sum'),
    ).reset_index()

    # Currency mismatch rate per account
    df['currency_mismatch'] = (
        df['payment_currency'] != df['receiving_currency']
    ).astype(int)

    mismatch_rate = df.groupby('from_account')[
        'currency_mismatch'
    ].mean().reset_index()
    mismatch_rate.columns = ['from_account', 'mismatch_rate']

    # Most common payment format per account
    common_format = df.groupby('from_account')[
        'payment_format'
    ].agg(lambda x: x.mode()[0]).reset_index()
    common_format.columns = ['from_account', 'common_format']

    # Merge everything together
    account_features = account_features.merge(
        mismatch_rate, on='from_account'
    )
    account_features = account_features.merge(
        common_format, on='from_account'
    )

    # Fill missing std values
    account_features['std_amount'] = account_features[
        'std_amount'
    ].fillna(0)

    # Is this account a fraudster?
    account_features['is_fraud'] = (
        account_features['fraud_count'] > 0
    ).astype(int)

    print(f"✓ Built profiles for {len(account_features):,} accounts")
    print(f"✓ Fraudulent accounts: {account_features['is_fraud'].sum():,}")

    # ----------------------------------------
    # STEP 3: Prepare for ML
    # ----------------------------------------
    print("\nStep 3: Preparing ML features...")

    le = LabelEncoder()
    account_features['format_code'] = le.fit_transform(
        account_features['common_format']
    )

    feature_cols = [
        'total_wires',
        'total_amount',
        'avg_amount',
        'max_amount',
        'min_amount',
        'std_amount',
        'unique_banks',
        'unique_currencies',
        'mismatch_rate',
        'format_code'
    ]

    X = account_features[feature_cols].fillna(0)
    y = account_features['is_fraud']

    print(f"✓ Features: {feature_cols}")
    print(f"✓ Fraud accounts: {y.sum():,} / {len(y):,}")

    # ----------------------------------------
    # STEP 4: Train Random Forest
    # ----------------------------------------
    print("\nStep 4: Training Random Forest model...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    print("✓ Model trained!")

    # ----------------------------------------
    # STEP 5: Generate risk scores 0-100
    # ----------------------------------------
    print("\nStep 5: Generating risk scores...")

    # Probability of being fraud = risk score
    risk_probs = model.predict_proba(X)[:, 1]
    account_features['risk_score'] = (
        risk_probs * 100
    ).round(1)

    # Risk category
    def categorize_risk(score):
        if score >= 70:
            return 'CRITICAL'
        elif score >= 40:
            return 'HIGH'
        elif score >= 20:
            return 'MEDIUM'
        else:
            return 'LOW'

    account_features['risk_category'] = account_features[
        'risk_score'
    ].apply(categorize_risk)

    # ----------------------------------------
    # STEP 6: Results
    # ----------------------------------------
    print("\n" + "="*55)
    print("RISK SCORE DISTRIBUTION")
    print("="*55)

    risk_dist = account_features.groupby(
        'risk_category'
    )['from_account'].count()

    for category in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if category in risk_dist.index:
            count = risk_dist[category]
            pct = count / len(account_features) * 100
            bar = "█" * int(pct / 2)
            print(f"  {category:<10} | {bar:<25} | "
                  f"{count:,} accounts ({pct:.1f}%)")

    # ----------------------------------------
    # STEP 7: Top 15 highest risk accounts
    # These are who Wells Fargo investigates first
    # ----------------------------------------
    print("\n" + "="*55)
    print("TOP 15 HIGHEST RISK ACCOUNTS")
    print("Priority investigation list")
    print("="*55)

    top_risk = account_features.nlargest(
        15, 'risk_score'
    )[[
        'from_account', 'total_wires', 'total_amount',
        'avg_amount', 'mismatch_rate', 'unique_banks',
        'risk_score', 'risk_category', 'is_fraud'
    ]]

    for _, r in top_risk.iterrows():
        fraud_label = "CONFIRMED FRAUD" if r['is_fraud'] == 1 else "unconfirmed"
        print(f"\n  Account  : {r['from_account']}")
        print(f"  Risk     : {r['risk_score']}/100 [{r['risk_category']}]")
        print(f"  Status   : {fraud_label}")
        print(f"  Wires    : {int(r['total_wires']):,}")
        print(f"  Volume   : ${r['total_amount']:,.2f}")
        print(f"  Mismatch : {r['mismatch_rate']*100:.1f}%")

    # ----------------------------------------
    # STEP 8: Model performance
    # ----------------------------------------
    print("\n" + "="*55)
    print("MODEL PERFORMANCE ON TEST DATA")
    print("="*55)

    y_pred = model.predict(X_test)
    print(classification_report(
        y_test, y_pred,
        target_names=['Legitimate', 'Fraud']
    ))

    # ----------------------------------------
    # STEP 9: Feature importance
    # What does the AI think matters most?
    # ----------------------------------------
    print("\n" + "="*55)
    print("WHAT FEATURES MATTER MOST TO THE AI?")
    print("="*55)

    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for _, row in importance.iterrows():
        bar = "█" * int(row['importance'] * 50)
        print(f"  {row['feature']:<20} | {bar}")

    print("\n" + "="*55)
    print("RISK SCORING COMPLETE")
    print("="*55)
    print("\nWhat this means in plain English:")
    print("→ Every account now has a risk score 0-100")
    print("→ CRITICAL accounts need immediate investigation")
    print("→ LOW risk accounts can be cleared automatically")
    print("→ This is how Wells Fargo prioritizes 500k accounts")

build_risk_scores()