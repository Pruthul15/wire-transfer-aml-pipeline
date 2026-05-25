# ============================================
# SCRIPT 1: Explore the IBM AML Dataset
# Wells Fargo Wire Transfer AML Pipeline
# ============================================

import pandas as pd
import os

# We'll point this to our data folder
DATA_FOLDER = "../data/"

def explore_dataset():
    # List all CSV files in the data folder
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
    print("Files found in data folder:")
    for f in files:
        print(f"  → {f}")

    # Load the small transactions file first
    # (HI-Small_Trans.csv is the one we want)
    trans_file = DATA_FOLDER + "HI-Small_Trans.csv"
    
    print("\nLoading transactions...")
    df = pd.read_csv(trans_file)
    
    print(f"\nTotal rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumn names:")
    for col in df.columns:
        print(f"  → {col}")
    
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    print(f"\nAny fraud in this data?")
    print(df['Is Laundering'].value_counts())

explore_dataset()