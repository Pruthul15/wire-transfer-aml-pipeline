# Wire Transfer AML Analysis Pipeline

> An end-to-end Anti-Money Laundering (AML) detection system built on 5 million real synthetic wire transactions from IBM's AML research dataset — simulating the exact work done by Payments Risk and Financial Crimes analysts at major financial institutions.

---

## Why This Project Exists

In 2024, the OCC (Office of the Comptroller of the Currency) identified serious gaps in wire transfer monitoring at major US banks. This project builds the kind of detection pipeline that addresses those gaps — comparing wire messages against initiation instructions, flagging anomalies, and generating compliance reports aligned with FATF guidelines and the Bank Secrecy Act.

---

## Project Structure

```
wire-transfer-aml-pipeline/
│
├── data/                         # IBM AML dataset (local only, not tracked)
│   ├── HI-Small_Trans.csv        # 5M wire transactions
│   └── HI-Small_accounts.csv    # Account reference data
│
├── scripts/                      # Pipeline scripts (run in order)
│   ├── 01_explore_data.py        # Data exploration and profiling
│   ├── 02_setup_database.py      # Load CSV into SQLite database
│   ├── 03_fraud_detection.py     # Core AML fraud detection SQL
│   ├── 04_xml_parser.py          # SWIFT XML wire message parser
│   ├── 05_window_functions.py    # Advanced SQL window functions
│   └── 06_report_generator.py   # Executive AML report output
│
├── output/                       # Generated outputs
│   ├── aml_risk_report.txt       # Daily AML risk report
│   └── wire_messages.xml         # Sample SWIFT MT103 XML messages
│
└── README.md
```

---

## Dataset

**IBM Transactions for Anti-Money Laundering (AML)** — NeurIPS 2023

| Metric | Value |
|--------|-------|
| Total Transactions | 5,078,345 |
| Confirmed Fraud Cases | 5,177 |
| Fraud Rate | 0.10% |
| Unique Accounts | 496,995 |
| Unique Banks | 30,470 |
| Total Wire Volume | $22.9 Trillion |

Source: [Kaggle — IBM AML Dataset](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)

---

## Scripts Overview

### Script 01 — Data Exploration
Loads and profiles the IBM AML dataset. Reveals the 11 key columns, transaction distribution, and the fraud/legitimate split across 5 million records.

### Script 02 — Database Setup
Creates a SQLite database, loads all 5,078,345 transactions, and verifies data integrity. This is the foundation all other scripts query against.

### Script 03 — Fraud Detection SQL

Implements 4 production-level AML detection queries:

**Structuring Detection**
Finds accounts sending multiple wires between $9,000–$9,999 to avoid the $10,000 BSA mandatory reporting threshold (a federal crime under 31 U.S.C. 5324).

```
Top Finding: Account 100428660 sent 1,581 wires
all between $9,002–$9,998 — totaling $14.9 million.
ACTION: Immediate SAR filing required.
```

**High Velocity Detection**
Flags accounts with abnormally high wire frequency — a signal of automated money laundering operations.

```
Top Finding: Account 100428660 sent 168,672 wires
in 10 days — one wire every 5 seconds, 24/7.
ACTION: Account freeze + enhanced due diligence.
```

**Currency Mismatch (Layering)**
Detects FX conversion patterns used in Stage 2 money laundering (Layering) — converting through multiple currencies to obscure the money trail.

```
Top Finding: Account 8046CA880 converted
Yen → Ruble across 14 transactions worth $32B.
ACTION: Review for cross-border layering activity.
```

**Fraud Rate by Payment Format**

| Payment Format | Fraud Rate | Total Transactions |
|---------------|-----------|-------------------|
| ACH | 0.746% | 600,797 |
| Bitcoin | 0.038% | 146,091 |
| Cash | 0.022% | 490,891 |
| Cheque | 0.017% | 1,864,331 |
| Credit Card | 0.016% | 1,323,324 |
| Wire | 0.000% | 171,855 |

**Key Insight:** ACH is 37x more fraud-prone than Wire transfers — critical input for channel risk strategy.

---

### Script 04 — XML Parser (SWIFT MT103)

Converts wire transaction data into SWIFT MT103-style XML format — the international standard used for bank-to-bank wire messages — then parses it back into the database.

```xml
<WireTransfer id="WT-000001">
  <Timestamp>2022/09/01 00:20</Timestamp>
  <FromBank>10</FromBank>
  <FromAccount>80D49E000</FromAccount>
  <ToBank>10</ToBank>
  <AmountPaid>9466.45</AmountPaid>
  <PaymentCurrency>US Dollar</PaymentCurrency>
  <PaymentFormat>Reinvestment</PaymentFormat>
  <IsLaundering>0</IsLaundering>
</WireTransfer>
```

Handles: missing fields, malformed data, encoding errors, and duplicate records.

---

### Script 05 — Window Functions

Implements senior-level SQL analytics using window functions — the most powerful tool in a financial crimes analyst's toolkit.

| Function | Purpose | Finding |
|----------|---------|---------|
| `ROW_NUMBER()` | Rank transactions by amount per account | Identified top fraud transactions per criminal |
| `LAG()` | Compare each wire to the previous one | Caught 18,000,000% amount spikes |
| `LEAD()` | Analyze behavior after a fraud transaction | Confirmed rapid fund dispersal post-fraud |
| `SUM OVER` | Running cumulative total per account | Tracked $13M moved in first hour of activity |
| `RANK()` | Risk-rank all accounts by fraud count | Produced top 15 highest risk account list |

---

### Script 06 — Executive Report Generator

Produces a daily AML risk report in the format used by compliance teams and presented to bank executives and regulators.

```
============================================================
   XYZ BANK - AML WIRE MONITORING REPORT
   Classification: CONFIDENTIAL
============================================================
  Total Transactions  : 5,078,345
  Confirmed Fraud     : 5,177
  Fraud Rate          : 0.102%

  [ALERT] STRUCTURING
  Account 100428660 | Bank 70 | 1,581 wires | $14.9M
  ACTION REQUIRED: File SAR report immediately

  [ALERT] HIGH VELOCITY
  Account 100428660 | 168,672 wires in 10 days
  ACTION REQUIRED: Enhanced due diligence review
============================================================
```

---

## Key Skills Demonstrated

| Skill | Scripts |
|-------|---------|
| Complex SQL (JOINs, CTEs, subqueries) | 03, 05 |
| Window Functions (LAG, LEAD, RANK, ROW_NUMBER) | 05 |
| XML Parsing (SWIFT MT103 format) | 04 |
| Data Pipeline (CSV → Python → SQLite → Report) | 02, 04 |
| AML Domain Knowledge | All |
| Python / Pandas | All |
| SQLite Database Management | 02–06 |
| Git / GitHub Version Control | Full project |

---

## AML Concepts Covered

- **Structuring** — Deliberately breaking transactions below $10,000 to avoid BSA reporting
- **Layering** — Using currency conversions to obscure the origin of funds
- **High Velocity** — Abnormal transaction frequency as a fraud signal
- **SAR** — Suspicious Activity Report — mandatory filing with FinCEN
- **BSA** — Bank Secrecy Act — US federal AML law
- **FATF** — Financial Action Task Force — global AML standards
- **OCC** — Office of the Comptroller of the Currency — US bank regulator

---

## How To Run

```bash
# 1. Clone the repo
git clone https://github.com/Pruthul15/wire-transfer-aml-pipeline.git
cd wire-transfer-aml-pipeline

# 2. Install dependencies
pip install pandas

# 3. Download dataset from Kaggle
# kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml
# Place these files in data/:
#   - HI-Small_Trans.csv
#   - HI-Small_accounts.csv

# 4. Run pipeline in order
python scripts/01_explore_data.py
python scripts/02_setup_database.py
python scripts/03_fraud_detection.py
python scripts/04_xml_parser.py
python scripts/05_window_functions.py
python scripts/06_report_generator.py
```

---

## References

- [IBM AML Research Dataset — NeurIPS 2023](https://research.ibm.com/publications/realistic-synthetic-financial-transactions-for-anti-money-laundering-models)
- [FATF 40 Recommendations](https://www.fatf-gafi.org/recommendations.html)
- [Bank Secrecy Act — 31 U.S.C. 5311](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)
- [OCC AML Enforcement Guidelines 2024](https://www.occ.gov)

---

*Built as a portfolio project demonstrating financial crimes analytics skills aligned with Payments Risk and AML monitoring roles at major financial institutions.*

---

## AI Features (Days 4-8)

### Script 07 - Anomaly Detection (Isolation Forest)
Uses unsupervised machine learning to detect unusual wire
transfer behavior without any predefined rules.

**How it works:**
- AI learns what NORMAL transactions look like
- Flags anything that doesnt fit the pattern
- No rules needed - AI figures it out automatically
- Same technique used by JPMorgan, HSBC worldwide

**Results on 500,000 transactions:**

| Metric | Value |
|--------|-------|
| Transactions Scanned | 500,000 |
| AI Flagged Suspicious | 5,000 (1%) |
| Known Fraud Cases | 193 |
| Fraud Caught | 1 |
| Top Suspicious Format | ACH with currency mismatch |

**Key Finding:** AI independently discovered that ACH
transactions with currency mismatches are the most
anomalous - matching our SQL findings from Script 03.
This validates both approaches.

**Why low recall is realistic:**
Money launderers deliberately make transactions look
normal. Even AI gets fooled - improving recall is
exactly what a Wells Fargo analyst works on daily.

**Tech used:** scikit-learn IsolationForest,
LabelEncoder, numpy log transformation


### Script 08 - ML Risk Scoring (Random Forest)
Builds behavioral profiles for all 496,995 accounts
and assigns each a risk score from 0-100.

**Results:**

| Risk Level | Accounts | Action |
|------------|----------|--------|
| CRITICAL (70-100) | 1,522 | Immediate investigation |
| HIGH (40-70) | 1,518 | Investigate this week |
| MEDIUM (20-40) | 474 | Monitor closely |
| LOW (0-20) | 493,481 | Auto-cleared |

**Model Accuracy:** 100% overall, 81% fraud precision

**Top features the AI uses:**
- unique_banks: criminals send to many different banks
- std_amount: criminals vary amounts unpredictably
- mismatch_rate: currency conversion patterns

**Tech used:** scikit-learn RandomForestClassifier,
train_test_split, classification_report
