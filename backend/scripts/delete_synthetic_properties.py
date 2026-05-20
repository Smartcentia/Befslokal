"""
Delete synthetic properties and all related data.

This script:
1. Identifies all synthetic properties (external_data.is_synthetic = true)
2. Deletes all related data in correct order (CASCADE)
3. Deletes the properties themselves
4. Provides detailed logging and statistics
5. Supports dry-run mode for testing

WARNING: This operation is IRREVERSIBLE. Always run with --dry-run first!
"""
import asyncio
import sys
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, '/Users/frank/Documents/BEFS_CLEAN/backend')
from app.db.session import SessionLocal


class DeletionStats:
    """Track deletion statistics"""
    def __init__(self):
        self.properties = 0
        self.units = 0
        self.contracts = 0
        self.gl_transactions = 0
        self.budgets = 0
        self.risk_assessments = 0
        self.internal_control_cases = 0
        self.scheduled_activities = 0
        self.expenses = 0
        self.proximity_services = 0
        self.proximity_data = 0
        self.environmental_data = 0
        self.geo_data = 0
        self.socioeconomic_data = 0
        self.building_components = 0
        self.text_content = 0
        self.start_time = datetime.now()
    
    def print_summary(self, dry_run: bool):
        duration = (datetime.now() - self.start_time).total_seconds()
        mode = "DRY RUN" if dry_run else "LIVE"
        
        print("\n" + "="*60)
        print(f"DELETION SUMMARY ({mode})")
        print("="*60)
        print(f"Properties deleted: {self.properties}")
        print(f"\nRelated data deleted:")
        print(f"  - Units: {self.units}")
        print(f"  - Contracts: {self.contracts}")
        print(f"  - GL Transactions: {self.gl_transactions}")
        print(f"  - Budgets: {self.budgets}")
        print(f"  - Risk Assessments: {self.risk_assessments}")
        print(f"  - Internal Control Cases: {self.internal_control_cases}")
        print(f"  - Scheduled Activities: {self.scheduled_activities}")
        print(f"  - Expenses: {self.expenses}")
        print(f"  - Proximity Services: {self.proximity_services}")
        print(f"  - Proximity Data: {self.proximity_data}")
        print(f"  - Environmental Data: {self.environmental_data}")
        print(f"  - Geo Data: {self.geo_data}")
        print(f"  - Socioeconomic Data: {self.socioeconomic_data}")
        print(f"  - Building Components: {self.building_components}")
        print(f"  - Text Content: {self.text_content}")
        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        
        if dry_run:
            print("\n🔍 DRY RUN - No changes committed")
        else:
            print("\n💾 Changes committed to database")


async def get_synthetic_property_ids(db: AsyncSession, limit: int = None) -> List[str]:
    """Get list of synthetic property IDs"""
    query = """
        SELECT property_id, name 
        FROM properties 
        WHERE external_data::text LIKE '%is_synthetic%true%'
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    result = await db.execute(text(query))
    properties = result.all()
    
    print(f"\n{'='*60}")
    print(f"SYNTHETIC PROPERTIES IDENTIFIED")
    print(f"{'='*60}")
    print(f"Total: {len(properties)}")
    
    if len(properties) <= 10:
        print("\nProperties to delete:")
        for prop in properties:
            print(f"  - {prop.name}")
    else:
        print(f"\nFirst 10 properties:")
        for prop in properties[:10]:
            print(f"  - {prop.name}")
        print(f"  ... and {len(properties) - 10} more")
    
    return [str(p.property_id) for p in properties]


async def delete_related_data(
    db: AsyncSession, 
    property_ids: List[str], 
    stats: DeletionStats
) -> None:
    """Delete all related data in correct order"""
    
    if not property_ids:
        print("\n⚠️  No properties to delete")
        return
    
    # Create comma-separated list for SQL IN clause
    ids_str = "', '".join(property_ids)
    ids_clause = f"'{ids_str}'"
    
    print(f"\n{'='*60}")
    print(f"DELETING RELATED DATA")
    print(f"{'='*60}")
    
    # 1. Delete contracts (depends on units)
    print("\n1. Deleting contracts...")
    result = await db.execute(text(f"""
        DELETE FROM contracts 
        WHERE unit_id IN (
            SELECT unit_id FROM units 
            WHERE property_id IN ({ids_clause})
        )
    """))
    stats.contracts = result.rowcount
    print(f"   ✅ Deleted {stats.contracts} contracts")
    
    # 2. Delete units (depends on properties)
    print("\n2. Deleting units...")
    result = await db.execute(text(f"""
        DELETE FROM units 
        WHERE property_id IN ({ids_clause})
    """))
    stats.units = result.rowcount
    print(f"   ✅ Deleted {stats.units} units")
    
    # 3. Delete financial data
    print("\n3. Deleting financial data...")
    result = await db.execute(text(f"""
        DELETE FROM gl_transactions 
        WHERE property_id IN ({ids_clause})
    """))
    stats.gl_transactions = result.rowcount
    print(f"   ✅ Deleted {stats.gl_transactions} GL transactions")
    
    result = await db.execute(text(f"""
        DELETE FROM budget 
        WHERE property_id IN ({ids_clause})
    """))
    stats.budgets = result.rowcount
    print(f"   ✅ Deleted {stats.budgets} budgets")
    
    # 4. Delete HMS/Risk data
    print("\n4. Deleting HMS/Risk data...")
    
    # Delete risk_factors first (depends on risk_assessments)
    result = await db.execute(text(f"""
        DELETE FROM risk_factors 
        WHERE assessment_id IN (
            SELECT assessment_id FROM risk_assessments 
            WHERE property_id IN ({ids_clause})
        )
    """))
    risk_factors_count = result.rowcount
    print(f"   ✅ Deleted {risk_factors_count} risk factors")
    
    result = await db.execute(text(f"""
        DELETE FROM risk_assessments 
        WHERE property_id IN ({ids_clause})
    """))
    stats.risk_assessments = result.rowcount
    print(f"   ✅ Deleted {stats.risk_assessments} risk assessments")
    
    result = await db.execute(text(f"""
        DELETE FROM internal_control_cases 
        WHERE property_id IN ({ids_clause})
    """))
    stats.internal_control_cases = result.rowcount
    print(f"   ✅ Deleted {stats.internal_control_cases} internal control cases")
    
    result = await db.execute(text(f"""
        DELETE FROM scheduled_activities 
        WHERE property_id IN ({ids_clause})
    """))
    stats.scheduled_activities = result.rowcount
    print(f"   ✅ Deleted {stats.scheduled_activities} scheduled activities")
    
    # 5. Delete other data
    print("\n5. Deleting other data...")
    
    # List of tables that might not exist
    optional_tables = [
        'expenses',  # Financial expenses
        'proximity_services',  # Must be deleted before proximity_data
        'proximity_data',
        'environmental_data',
        'geo_data',
        'socioeconomic_data',
        'building_components',
        'text_content'
    ]
    
    for table_name in optional_tables:
        try:
            # Use SAVEPOINT to prevent transaction abort on error
            await db.execute(text("SAVEPOINT before_optional_delete"))
            
            result = await db.execute(text(f"""
                DELETE FROM {table_name} 
                WHERE property_id IN ({ids_clause})
            """))
            count = result.rowcount
            setattr(stats, table_name, count)
            if count > 0:
                print(f"   ✅ Deleted {count} rows from {table_name}")
            
            await db.execute(text("RELEASE SAVEPOINT before_optional_delete"))
        except Exception:
            # Rollback to savepoint and continue
            await db.execute(text("ROLLBACK TO SAVEPOINT before_optional_delete"))
            setattr(stats, table_name, 0)

    
    # 6. Delete properties (last)
    print("\n6. Deleting properties...")
    result = await db.execute(text(f"""
        DELETE FROM properties 
        WHERE property_id IN ({ids_clause})
    """))
    stats.properties = result.rowcount
    print(f"   ✅ Deleted {stats.properties} properties")


async def delete_synthetic_properties(
    dry_run: bool = True,
    limit: int = None
):
    """
    Delete synthetic properties and all related data.
    
    Args:
        dry_run: If True, rollback changes (don't commit)
        limit: Maximum number of properties to delete (for testing)
    """
    stats = DeletionStats()
    
    async with SessionLocal() as db:
        try:
            # Get synthetic property IDs
            property_ids = await get_synthetic_property_ids(db, limit)
            
            if not property_ids:
                print("\n✅ No synthetic properties found!")
                return
            
            # Confirm deletion (unless dry-run or limit)
            if not dry_run and not limit:
                print(f"\n{'='*60}")
                print(f"⚠️  WARNING: About to delete {len(property_ids)} properties")
                print(f"{'='*60}")
                print("This operation is IRREVERSIBLE!")
                response = input("\nType 'DELETE' to confirm: ")
                
                if response != 'DELETE':
                    print("\n❌ Deletion cancelled")
                    return
            
            # Delete related data
            await delete_related_data(db, property_ids, stats)
            
            # Commit or rollback
            if not dry_run:
                await db.commit()
                print("\n💾 Changes committed to database")
            else:
                await db.rollback()
                print("\n🔍 Dry run - changes rolled back")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error occurred: {e}")
            print("🔄 Changes rolled back")
            raise
    
    # Print summary
    stats.print_summary(dry_run)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Delete synthetic properties and all related data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing changes (default: True)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually delete data (WARNING: IRREVERSIBLE!)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of properties to delete (for testing)"
    )
    
    args = parser.parse_args()
    
    # Default to dry-run unless --live is specified
    dry_run = not args.live
    
    if not dry_run:
        print("\n" + "="*60)
        print("⚠️  LIVE MODE - CHANGES WILL BE PERMANENT!")
        print("="*60)
    
    await delete_synthetic_properties(
        dry_run=dry_run,
        limit=args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())
