#!/usr/bin/env python3
"""
Fix negative amounts that are clearly import errors while preserving legitimate credits.

Strategy:
1. Remove negatives in "Leie lokaler" categories (likely import errors - should never be negative)
2. Keep small negatives in utility categories (likely legitimate credits/adjustments)
3. Flag suspicious large negatives for manual review
"""

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import attributes

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

# Categories where negatives are ALWAYS errors (rent should never be negative)
ERROR_CATEGORIES = {
    'Leie lokaler andre utleiere',
    'Leie lokaler fra Statsbygg',
    'Fast bygningsinventar over kr 50 000',
}

# Categories where small negatives might be legitimate (credits/adjustments)
CREDIT_OK_CATEGORIES = {
    'Strøm og oppvarming',  # Credit from usage estimates
    'Renovasjon, vann, avløp o.l.',  # Usage adjustments
    'Reparasjon og vedlikehold leide lokaler',  # Refunds
    'Annen kostnad lokaler',  # Various adjustments
}

async def fix_negative_amounts():
    print("=" * 80)
    print("FIXING NEGATIVE AMOUNTS - IMPORT ERRORS")
    print("=" * 80)
    
    async with SessionLocal() as db:
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        removed_errors = 0
        kept_legitimate = 0
        flagged_review = []
        properties_modified = 0
        
        for prop in properties:
            ext = prop.external_data or {}
            fin = ext.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            original_count = len(expenses)
            cleaned_expenses = []
            property_had_changes = False
            
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                except (ValueError, TypeError):
                    amount = 0.0
                
                category = exp.get('type', 'Ukjent')
                provider = exp.get('provider', 'Ukjent')
                
                # Decision logic
                if amount >= 0:
                    # Positive - keep it
                    cleaned_expenses.append(exp)
                elif category in ERROR_CATEGORIES:
                    # Negative in error category - REMOVE
                    print(f"❌ Removing: {prop.name} - {category}: {amount:,.0f} kr ({provider})")
                    removed_errors += 1
                    property_had_changes = True
                elif category in CREDIT_OK_CATEGORIES and amount > -10000:
                    # Small negative in ok category - KEEP
                    cleaned_expenses.append(exp)
                    kept_legitimate += 1
                else:
                    # Large negative or unknown category - FLAG but keep for now
                    flagged_review.append({
                        'property': prop.name,
                        'amount': amount,
                        'category': category,
                        'provider': provider
                    })
                    cleaned_expenses.append(exp)
            
            # Update if changes were made
            if property_had_changes:
                new_ext = dict(ext)
                new_fin = dict(new_ext.get('financials', {}))
                new_fin['manual_expenses'] = cleaned_expenses
                
                # Recalculate total
                total = sum(float(e.get('amount', 0) or 0) for e in cleaned_expenses)
                new_fin['total_manual_expenses'] = total
                
                new_ext['financials'] = new_fin
                prop.external_data = new_ext
                attributes.flag_modified(prop, 'external_data')
                
                properties_modified += 1
                print(f"   Property updated: {original_count} → {len(cleaned_expenses)} transactions")
        
        # Commit changes
        await db.commit()
        
        print("\n" + "=" * 80)
        print("FIX SUMMARY")
        print("=" * 80)
        print(f"✅ Properties modified: {properties_modified}")
        print(f"✅ Import errors removed: {removed_errors}")
        print(f"✅ Legitimate credits kept: {kept_legitimate}")
        print(f"⚠️  Transactions flagged for manual review: {len(flagged_review)}")
        
        if flagged_review:
            print("\n📋 TOP 10 FLAGGED FOR MANUAL REVIEW:")
            sorted_flagged = sorted(flagged_review, key=lambda x: x['amount'])
            for entry in sorted_flagged[:10]:
                print(f"  {entry['property'][:50]:<50} {entry['amount']:>12,.0f} kr")
                print(f"    Category: {entry['category']}")
                print(f"    Provider: {entry['provider']}")
        
        print(f"\n🎉 Database updated successfully!")

if __name__ == "__main__":
    asyncio.run(fix_negative_amounts())
