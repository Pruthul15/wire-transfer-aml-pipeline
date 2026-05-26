# ============================================
# SCRIPT 6: Executive Report Generator
# This is what Wells Fargo managers read
# every morning — a clean summary of all
# suspicious wire activity from the night
# ============================================

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "../output/aml_database.db"
REPORT_PATH = "../output/aml_risk_report.txt"

def generate_report():
    conn = sqlite3.connect(DB_PATH)
    report = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def section(title):
        report.append("\n" + "="*60)
        report.append(f"  {title}")
        report.append("="*60)

    def line(text=""):
        report.append(text)

    # ----------------------------------------
    # HEADER
    # ----------------------------------------
    report.append("="*60)
    report.append("   WELLS FARGO - AML WIRE MONITORING REPORT")
    report.append(f"   Generated : {now}")
    report.append(f"   Prepared by: Payments Risk & Financial Crimes")
    report.append(f"   Classification: CONFIDENTIAL")
    report.append("="*60)

    # ----------------------------------------
    # SECTION 1: PORTFOLIO OVERVIEW
    # ----------------------------------------
    section("SECTION 1: PORTFOLIO OVERVIEW")

    overview = pd.read_sql_query("""
        SELECT
            COUNT(*) as total_transactions,
            SUM(is_laundering) as confirmed_fraud,
            ROUND(SUM(amount_paid), 2) as total_volume,
            ROUND(AVG(amount_paid), 2) as avg_transaction,
            COUNT(DISTINCT from_account) as unique_accounts,
            COUNT(DISTINCT from_bank) as unique_banks
        FROM wire_transactions
    """, conn)

    row = overview.iloc[0]
    line(f"  Total Transactions  : {int(row['total_transactions']):,}")
    line(f"  Confirmed Fraud     : {int(row['confirmed_fraud']):,}")
    line(f"  Total Volume        : ${row['total_volume']:,.2f}")
    line(f"  Avg Transaction     : ${row['avg_transaction']:,.2f}")
    line(f"  Unique Accounts     : {int(row['unique_accounts']):,}")
    line(f"  Unique Banks        : {int(row['unique_banks']):,}")
    line(f"  Fraud Rate          : {row['confirmed_fraud']/row['total_transactions']*100:.3f}%")

    # ----------------------------------------
    # SECTION 2: STRUCTURING ALERTS
    # ----------------------------------------
    section("SECTION 2: STRUCTURING ALERTS (Bank Secrecy Act)")
    line("  Accounts sending multiple wires between $9,000-$9,999")
    line("  ACTION REQUIRED: File SAR report for each account")
    line()

    structuring = pd.read_sql_query("""
        SELECT
            from_account,
            from_bank,
            COUNT(*) as wire_count,
            ROUND(SUM(amount_paid), 2) as total_amount
        FROM wire_transactions
        WHERE amount_paid BETWEEN 9000 AND 9999
        GROUP BY from_account, from_bank
        HAVING COUNT(*) >= 3
        ORDER BY wire_count DESC
        LIMIT 5
    """, conn)

    for _, r in structuring.iterrows():
        line(f"  [ALERT] Account {r['from_account']} | "
             f"Bank {int(r['from_bank'])} | "
             f"{int(r['wire_count'])} wires | "
             f"${r['total_amount']:,.2f}")

    # ----------------------------------------
    # SECTION 3: HIGH VELOCITY ALERTS
    # ----------------------------------------
    section("SECTION 3: HIGH VELOCITY ALERTS")
    line("  Accounts with abnormally high transaction frequency")
    line("  ACTION REQUIRED: Enhanced due diligence review")
    line()

    velocity = pd.read_sql_query("""
        SELECT
            from_account,
            from_bank,
            COUNT(*) as total_wires,
            ROUND(SUM(amount_paid), 2) as total_amount
        FROM wire_transactions
        GROUP BY from_account, from_bank
        HAVING COUNT(*) > 50
        ORDER BY total_wires DESC
        LIMIT 5
    """, conn)

    for _, r in velocity.iterrows():
        line(f"  [ALERT] Account {r['from_account']} | "
             f"Bank {int(r['from_bank'])} | "
             f"{int(r['total_wires']):,} wires | "
             f"${r['total_amount']:,.2f}")

    # ----------------------------------------
    # SECTION 4: CURRENCY MISMATCH ALERTS
    # ----------------------------------------
    section("SECTION 4: CURRENCY MISMATCH ALERTS (Layering)")
    line("  Accounts converting currencies suspiciously")
    line("  ACTION REQUIRED: Review for layering activity")
    line()

    currency = pd.read_sql_query("""
        SELECT
            from_account,
            from_bank,
            payment_currency,
            receiving_currency,
            COUNT(*) as mismatch_count,
            ROUND(SUM(amount_paid), 2) as total_amount
        FROM wire_transactions
        WHERE payment_currency != receiving_currency
        GROUP BY from_account, payment_currency, receiving_currency
        HAVING COUNT(*) > 5
        ORDER BY total_amount DESC
        LIMIT 5
    """, conn)

    for _, r in currency.iterrows():
        line(f"  [ALERT] Account {r['from_account']} | "
             f"{r['payment_currency']} -> {r['receiving_currency']} | "
             f"{int(r['mismatch_count'])} times | "
             f"${r['total_amount']:,.2f}")

    # ----------------------------------------
    # SECTION 5: HIGHEST RISK ACCOUNTS
    # ----------------------------------------
    section("SECTION 5: TOP 5 HIGHEST RISK ACCOUNTS")
    line("  Ranked by confirmed fraud transaction count")
    line("  ACTION REQUIRED: Immediate account review + freeze")
    line()

    risk = pd.read_sql_query("""
        SELECT
            from_account,
            from_bank,
            COUNT(*) as total_wires,
            SUM(is_laundering) as fraud_count,
            ROUND(SUM(amount_paid), 2) as total_amount,
            ROUND(SUM(is_laundering)*100.0/COUNT(*), 2)
                as fraud_rate_pct
        FROM wire_transactions
        GROUP BY from_account, from_bank
        HAVING SUM(is_laundering) > 0
        ORDER BY fraud_count DESC
        LIMIT 5
    """, conn)

    for i, r in risk.iterrows():
        line(f"  #{i+1} Account {r['from_account']} | "
             f"Bank {int(r['from_bank'])} | "
             f"Fraud: {int(r['fraud_count'])} | "
             f"Total: ${r['total_amount']:,.2f} | "
             f"Risk: {r['fraud_rate_pct']}%")

    # ----------------------------------------
    # SECTION 6: PAYMENT FORMAT RISK
    # ----------------------------------------
    section("SECTION 6: FRAUD RATE BY PAYMENT FORMAT")
    line()

    formats = pd.read_sql_query("""
        SELECT
            payment_format,
            COUNT(*) as total,
            SUM(is_laundering) as fraud,
            ROUND(SUM(is_laundering)*100.0/COUNT(*), 3)
                as fraud_pct
        FROM wire_transactions
        GROUP BY payment_format
        ORDER BY fraud_pct DESC
    """, conn)

    for _, r in formats.iterrows():
        bar = "#" * int(r['fraud_pct'] * 10)
        line(f"  {r['payment_format']:<15} | "
             f"{bar:<10} | "
             f"{r['fraud_pct']}% fraud | "
             f"{int(r['total']):,} total")

    # ----------------------------------------
    # FOOTER
    # ----------------------------------------
    report.append("\n" + "="*60)
    report.append("  END OF REPORT")
    report.append(f"  Next report: Tomorrow 06:00 AM EST")
    report.append(f"  Questions: aml-monitoring@wellsfargo.com")
    report.append("="*60)

    conn.close()

    # Save to file — utf-8 fixes Windows encoding
    full_report = "\n".join(report)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(full_report)
    print(f"\n✓ Report saved to: {REPORT_PATH}")

generate_report()