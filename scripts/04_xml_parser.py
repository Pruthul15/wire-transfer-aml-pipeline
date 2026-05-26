# ============================================
# SCRIPT 4: XML Wire Transfer Parser
# In real banking, wire messages travel
# between banks in XML format (SWIFT standard)
# This script:
# 1. Takes our CSV data
# 2. Converts it to XML (like real wire messages)
# 3. Parses the XML back
# 4. Loads into database
# This is exactly what Wells Fargo does when
# receiving wire messages from other banks
# ============================================

import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
import os

DB_PATH = "../output/aml_database.db"
DATA_PATH = "../data/HI-Small_Trans.csv"
XML_OUTPUT = "../output/wire_messages.xml"

# ============================================
# STEP 1: Convert CSV rows to XML format
# This simulates real SWIFT wire messages
# ============================================
def convert_to_xml(num_records=200):
    print("=" * 50)
    print("STEP 1: Converting wire data to XML format")
    print("This simulates real SWIFT bank messages")
    print("=" * 50)

    # Load first 200 rows from CSV
    df = pd.read_csv(DATA_PATH, nrows=num_records)

    # Create XML root element
    root = ET.Element("WireTransferBatch")
    root.set("bank", "Wells Fargo")
    root.set("date", "2022-09-01")
    root.set("total_messages", str(num_records))

    # Convert each row to XML element
    for index, row in df.iterrows():
        # Create one wire message
        wire = ET.SubElement(root, "WireTransfer")
        wire.set("id", f"WT-{index+1:06d}")

        # Add all fields as child elements
        ET.SubElement(wire, "Timestamp").text      = str(row['Timestamp'])
        ET.SubElement(wire, "FromBank").text       = str(row['From Bank'])
        ET.SubElement(wire, "FromAccount").text    = str(row['Account'])
        ET.SubElement(wire, "ToBank").text         = str(row['To Bank'])
        ET.SubElement(wire, "ToAccount").text      = str(row['Account.1'])
        ET.SubElement(wire, "AmountPaid").text     = str(row['Amount Paid'])
        ET.SubElement(wire, "PaymentCurrency").text= str(row['Payment Currency'])
        ET.SubElement(wire, "AmountReceived").text = str(row['Amount Received'])
        ET.SubElement(wire, "ReceivingCurrency").text = str(row['Receiving Currency'])
        ET.SubElement(wire, "PaymentFormat").text  = str(row['Payment Format'])
        ET.SubElement(wire, "IsLaundering").text   = str(row['Is Laundering'])

    # Save XML file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(XML_OUTPUT, encoding="unicode", xml_declaration=True)

    print(f"✓ Created XML file: {XML_OUTPUT}")
    print(f"✓ Total wire messages: {num_records}")
    print(f"\nSample of what one wire message looks like:")
    print("""
  <WireTransfer id="WT-000001">
    <Timestamp>2022/09/01 00:20</Timestamp>
    <FromBank>10</FromBank>
    <FromAccount>80D49E000</FromAccount>
    <ToBank>10</ToBank>
    <ToAccount>80D49EAC8</ToAccount>
    <AmountPaid>9466.45</AmountPaid>
    <PaymentCurrency>US Dollar</PaymentCurrency>
    <AmountReceived>9466.45</AmountReceived>
    <ReceivingCurrency>US Dollar</ReceivingCurrency>
    <PaymentFormat>Reinvestment</PaymentFormat>
    <IsLaundering>0</IsLaundering>
  </WireTransfer>
    """)

# ============================================
# STEP 2: Parse the XML back
# This is what Wells Fargo does when they
# RECEIVE wire messages from other banks
# ============================================
def parse_xml_to_database():
    print("=" * 50)
    print("STEP 2: Parsing XML wire messages")
    print("Simulates receiving wires from other banks")
    print("=" * 50)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create separate table for XML-parsed wires
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xml_wire_messages (
            wire_id             TEXT PRIMARY KEY,
            timestamp           TEXT,
            from_bank           TEXT,
            from_account        TEXT,
            to_bank             TEXT,
            to_account          TEXT,
            amount_paid         REAL,
            payment_currency    TEXT,
            amount_received     REAL,
            receiving_currency  TEXT,
            payment_format      TEXT,
            is_laundering       INTEGER,
            parsed_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created table: xml_wire_messages")

    # Parse the XML file
    print("✓ Reading XML wire messages...")
    tree = ET.parse(XML_OUTPUT)
    root = tree.getroot()

    total = 0
    fraud_found = 0
    errors = 0

    for wire in root.findall('WireTransfer'):
        try:
            wire_id     = wire.get('id')
            timestamp   = wire.find('Timestamp').text
            from_bank   = wire.find('FromBank').text
            from_acct   = wire.find('FromAccount').text
            to_bank     = wire.find('ToBank').text
            to_acct     = wire.find('ToAccount').text
            amt_paid    = float(wire.find('AmountPaid').text)
            pay_curr    = wire.find('PaymentCurrency').text
            amt_recv    = float(wire.find('AmountReceived').text)
            recv_curr   = wire.find('ReceivingCurrency').text
            pay_format  = wire.find('PaymentFormat').text
            is_laund    = int(wire.find('IsLaundering').text)

            cursor.execute("""
                INSERT OR REPLACE INTO xml_wire_messages
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            """, (wire_id, timestamp, from_bank, from_acct,
                  to_bank, to_acct, amt_paid, pay_curr,
                  amt_recv, recv_curr, pay_format, is_laund))

            total += 1
            if is_laund == 1:
                fraud_found += 1

        except Exception as e:
            errors += 1
            print(f"  Error parsing wire {wire_id}: {e}")

    conn.commit()

    print(f"\n{'='*50}")
    print(f"XML PARSING COMPLETE")
    print(f"{'='*50}")
    print(f"Messages parsed  : {total}")
    print(f"Fraud detected   : {fraud_found}")
    print(f"Parse errors     : {errors}")
    print(f"{'='*50}")

    # Quick verification query
    print("\nVerification — checking database:")
    df = pd.read_sql_query("""
        SELECT
            payment_format,
            COUNT(*) as count,
            SUM(is_laundering) as fraud_count
        FROM xml_wire_messages
        GROUP BY payment_format
    """, conn)
    print(df.to_string(index=False))

    conn.close()
    print("\n✓ XML wire messages saved to database!")

# ============================================
# RUN BOTH STEPS
# ============================================
convert_to_xml(200)
print()
parse_xml_to_database()