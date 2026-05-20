
import os
import pandas as pd

def try_read(path):
    print(f"Trying to read: {path}")
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            print(f"SUCCESS (open): {f.readline()}")
    except Exception as e:
        print(f"FAILED (open): {e}")
    
    try:
        df = pd.read_csv(path, nrows=5)
        print("SUCCESS (pandas):")
        print(df.head())
    except Exception as e:
        print(f"FAILED (pandas): {e}")

path = "/Users/frank/Documents/BEFS_CLEAN/backend/docs/datafiler/Leveringsadresser til Frank Vevle(Midt).csv"
try_read(path)
