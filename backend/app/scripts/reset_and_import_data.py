
import sys
import os
import asyncio
import argparse
from dotenv import load_dotenv

# Add backend to path
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, 'backend')
if os.path.exists(backend_dir):
    sys.path.append(backend_dir)
# Env should be loaded by pydantic settings via os.environ if not using .env files

from app.db.session import SessionLocal
from app.services.data_management import DataManagementService

async def main():
    parser = argparse.ArgumentParser(description="Unified Data Management Tool")
    parser.add_argument("--clear", action="store_true", help="Clear all existing economic and text data")
    parser.add_argument("--import-financial", type=str, help="Path to financial CSV file")
    parser.add_argument("--import-master", type=str, help="Path to property master text/csv file")
    parser.add_argument("--import-text", type=str, help="Path to text CSV file")
    parser.add_argument("--category", type=str, default="Imported", help="Category for imported text")
    
    args = parser.parse_args()
    
    if not (args.clear or args.import_financial or args.import_text or args.import_master):
        parser.print_help()
        return

    async with SessionLocal() as db:
        if args.clear:
            print("Cleaning up existing data...")
            result = await DataManagementService.clear_all_economic_data(db)
            print(f"Result: {result['message']}")
            
        if args.import_financial:
            print(f"Importing financial data from {args.import_financial}...")
            if not os.path.exists(args.import_financial):
                print(f"Error: File {args.import_financial} not found.")
            else:
                with open(args.import_financial, 'rb') as f:
                    content = f.read()
                    result = await DataManagementService.import_financial_csv(db, content)
                    if result['status'] == 'success':
                        print(f"Success! Imported {result['imported']} records with {result['errors']} errors.")
                    else:
                        print(f"Failed: {result['message']}")
                        
        if args.import_master:
            print(f"Importing property master data from {args.import_master}...")
            # Bypassing os.path.exists check because it fails in sandbox for backend/ docs/ etc
            try:
                with open(args.import_master, 'rb') as f:
                    content = f.read()
                    result = await DataManagementService.import_property_master_csv(db, content)
                    if result['status'] == 'success':
                        print(f"Success! Imported {result.get('imported', 0)} new and updated {result.get('updated', 0)} properties.")
                    else:
                        print(f"Failed: {result['message']}")
            except Exception as e:
                print(f"Error reading file {args.import_master}: {str(e)}")
                        
        if args.import_text:
            print(f"Importing text data from {args.import_text}...")
            if not os.path.exists(args.import_text):
                print(f"Error: File {args.import_text} not found.")
            else:
                with open(args.import_text, 'rb') as f:
                    content = f.read()
                    result = await DataManagementService.import_text_csv(db, content, args.category)
                    if result['status'] == 'success':
                        print(f"Success! Imported {result['imported']} text records.")
                    else:
                        print(f"Failed: {result['message']}")

if __name__ == "__main__":
    asyncio.run(main())
