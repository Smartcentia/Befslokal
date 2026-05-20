#!/usr/bin/env python3
"""
Import General Ledger data from ok1.csv into gl_transactions table.
Processes 35,818 accounting transactions.
"""

import csv
import psycopg2
from uuid import uuid4
import re

# Configuration
# Configuration
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠️  DATABASE_URL environment variable is not set.")
    exit(1)
CSV_FILE = "/Users/frank/BEFS3/KNOWME/docs/ok1.csv"

def parse_norwegian_amount(amount_str):
    """Parse Norwegian number format (comma as decimal separator)."""
    if not amount_str or amount_str.strip() == '':
        return 0.0
    
    # Remove spaces and replace comma with dot
    cleaned = amount_str.strip().replace(' ', '').replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        print(f"   ⚠️  Could not parse amount: '{amount_str}'")
        return 0.0

def match_supplier_to_property(conn, supplier_name):
    """Try to match supplier name to a property via parties table."""
    if not supplier_name:
        return None
    
    cursor = conn.cursor()
    
    try:
        # Try exact match on party name
        cursor.execute("""
            SELECT DISTINCT p.property_id
            FROM parties pa
            JOIN contracts c ON pa.party_id = c.party_id
            JOIN units u ON c.unit_id = u.unit_id
            JOIN properties p ON u.property_id = p.property_id
            WHERE LOWER(pa.name) = LOWER(%s)
            LIMIT 1
        """, (supplier_name,))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        return None
    finally:
        cursor.close()

def main():
    """Main import function."""
    print("\n" + "="*80)
    print("IMPORTING GL DATA FROM ok1.csv")
    print("="*80 + "\n")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'gl_transactions'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("❌ Error: gl_transactions table does not exist!")
            print("   Run the CREATE TABLE script first.")
            return
        
        # Clear existing data
        cursor.execute("DELETE FROM gl_transactions;")
        print(f"🗑️  Cleared existing GL data\n")
        
        # Read and import CSV
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            transactions = []
            property_matches = 0
            total = 0
            
            print("📖 Reading CSV file...")
            
            for row in reader:
                total += 1
                
                # Parse amount
                amount = parse_norwegian_amount(row.get('Kontantbeløp', '0'))
                
                # Try to match property
                property_id = match_supplier_to_property(conn, row.get('Resk.nr(T)', ''))
                if property_id:
                    property_matches += 1
                
                transaction = (
                    str(uuid4()),  # transaction_id
                    property_id,   # property_id (may be None)
                    row.get('Regioner', ''),
                    row.get('Regioner(T)', ''),
                    row.get('Avdeling', ''),
                    row.get('Avdeling(T)', ''),
                    row.get('Dim 2', ''),
                    row.get('Dim 2(T)', ''),
                    row.get('Formål', ''),
                    row.get('Formål(T)', ''),
                    row.get('Konto', ''),
                    row.get('Konto(T)', ''),
                    row.get('BA', ''),
                    row.get('BA(T)', ''),
                    row.get('Resk.nr', ''),
                    row.get('Resk.nr(T)', ''),
                    row.get('Bilagsnr', ''),
                    amount,
                    row.get('Kont.periode', ''),
                    row.get('Kont.periode', ''),
                    row.get('Statskonto', ''),
                    False,          # is_synthetic
                    'import_csv'    # data_source
                )
                
                transactions.append(transaction)
                
                # Batch insert every 1000 rows
                if len(transactions) >= 1000:
                    cursor.executemany("""
                        INSERT INTO gl_transactions (
                            transaction_id, property_id, region_code, region_name,
                            department_code, department_name, dim2_code, dim2_name,
                            purpose_code, purpose_name, account_code, account_name,
                            ba_code, ba_name, supplier_id, supplier_name,
                            invoice_number, amount, period, state_account,
                            is_synthetic, data_source
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s
                        )
                    """, transactions)
                    
                    conn.commit()
                    print(f"   💾 Imported {total} transactions ({property_matches} matched to properties)")
                    transactions = []
            
            # Insert remaining transactions
            if transactions:
                cursor.executemany("""
                    INSERT INTO gl_transactions (
                        transaction_id, property_id, region_code, region_name,
                        department_code, department_name, dim2_code, dim2_name,
                        purpose_code, purpose_name, account_code, account_name,
                        ba_code, ba_name, supplier_id, supplier_name,
                        invoice_number, amount, period, state_account,
                        is_synthetic, data_source
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                """, transactions)
                conn.commit()
        
        # Get summary statistics
        cursor.execute("SELECT COUNT(*), SUM(amount) FROM gl_transactions;")
        count, total_amount = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM gl_transactions WHERE property_id IS NOT NULL;")
        matched_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT period) FROM gl_transactions;")
        period_count = cursor.fetchone()[0]
        
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"✅ Total transactions imported: {count:,}")
        print(f"🔗 Matched to properties: {matched_count:,} ({matched_count/count*100:.1f}%)")
        print(f"📅 Unique periods: {period_count}")
        print(f"💰 Total amount: {total_amount:,.2f} NOK")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
