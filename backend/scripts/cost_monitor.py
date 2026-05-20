#!/usr/bin/env python3
"""
Cost Monitor - Main Orchestration Script

Collects cost data from all infrastructure services and stores in database.
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import argparse

# Add parent directory to path to import app modules
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


from collectors.flyio_costs import FlyioCostCollector
from collectors.vercel_costs import VercelCostCollector
from collectors.openai_costs import OpenAICostCollector
# from collectors.mapbox_costs import MapboxCostCollector  # FJERNET


class CostMonitor:
    """Main cost monitoring orchestrator."""
    
    def __init__(self, db_url: str = None):
        """
        Initialize cost monitor.
        
        Args:
            db_url: Database URL for storing cost data
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.collectors = [
            # FlyioCostCollector(),
            FlyioCostCollector(app_name="knowme-backend-prod"),
            VercelCostCollector(),
            OpenAICostCollector(db_url=self.db_url),
            # MapboxCostCollector(db_url=self.db_url)  # FJERNET
        ]
    
    def collect_all(self) -> List[Dict[str, Any]]:
        """
        Collect cost data from all services.
        
        Returns:
            List of cost data dictionaries
        """
        results = []
        
        print("=" * 60)
        print("Starting cost collection...")
        print("=" * 60)
        
        for collector in self.collectors:
            try:
                data = collector.collect()
                if data:
                    results.append(data)
                    print(f"✓ {data['service_name']}: ${data['estimated_cost_usd']:.2f}")
                else:
                    print(f"✗ Failed to collect from {collector.__class__.__name__}")
            except Exception as e:
                print(f"✗ Error collecting from {collector.__class__.__name__}: {e}")
        
        print("=" * 60)
        
        return results
    
    def calculate_total(self, cost_data: List[Dict[str, Any]]) -> float:
        """Calculate total estimated cost."""
        return sum(item.get("estimated_cost_usd", 0.0) for item in cost_data)
    
    def save_to_database(self, cost_data: List[Dict[str, Any]]) -> bool:
        """
        Save cost data to database.
        
        Args:
            cost_data: List of cost data dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_url:
            print("Warning: No database URL provided, skipping database save")
            return False
        
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            import json
            
            engine = create_engine(self.db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            for data in cost_data:
                # Insert into database
                query = text("""
                    INSERT INTO infrastructure_costs (
                        service_name,
                        collection_date,
                        raw_metrics,
                        estimated_cost_usd,
                        active_time_seconds,
                        cpu_used_seconds,
                        storage_gb,
                        bandwidth_gb,
                        notes
                    ) VALUES (
                        :service_name,
                        :collection_date,
                        :raw_metrics,
                        :estimated_cost_usd,
                        :active_time_seconds,
                        :cpu_used_seconds,
                        :storage_gb,
                        :bandwidth_gb,
                        :notes
                    )
                """)
                
                session.execute(query, {
                    "service_name": data["service_name"],
                    "collection_date": data["collection_date"],
                    "raw_metrics": json.dumps(data.get("raw_metrics", {})),
                    "estimated_cost_usd": data.get("estimated_cost_usd"),
                    "active_time_seconds": data.get("active_time_seconds"),
                    "cpu_used_seconds": data.get("cpu_used_seconds"),
                    "storage_gb": data.get("storage_gb"),
                    "bandwidth_gb": data.get("bandwidth_gb"),
                    "notes": data.get("notes", "")
                })
            
            session.commit()
            session.close()
            
            print(f"\n✓ Successfully saved {len(cost_data)} records to database")
            return True
            
        except Exception as e:
            print(f"\n✗ Error saving to database: {e}")
            return False
    
    def print_summary(self, cost_data: List[Dict[str, Any]]):
        """Print cost summary."""
        total = self.calculate_total(cost_data)
        
        print("\n" + "=" * 60)
        print("COST SUMMARY")
        print("=" * 60)
        
        for data in cost_data:
            service = data['service_name'].upper().ljust(10)
            cost = f"${data['estimated_cost_usd']:.2f}".rjust(10)
            notes = data.get('notes', '')
            print(f"{service} {cost}   {notes}")
        
        print("-" * 60)
        print(f"{'TOTAL'.ljust(10)} ${total:.2f}".rjust(21))
        print("=" * 60)
        
        # Additional insights
        if any(d.get('metadata', {}).get('free_tier_limit_reached') for d in cost_data):
            print("\n⚠️  Warning: Free tier limits exceeded on some services")
    
    def run(self, save_to_db: bool = True, output_json: bool = False):
        """
        Run the cost collection process.
        
        Args:
            save_to_db: Whether to save results to database
            output_json: Whether to output results as JSON
        """
        # Collect data
        cost_data = self.collect_all()
        
        if not cost_data:
            print("\n✗ No cost data collected")
            return 1
        
        # Save to database
        if save_to_db:
            self.save_to_database(cost_data)
        
        # Print summary
        if not output_json:
            self.print_summary(cost_data)
        else:
            import json
            print(json.dumps({
                "collection_date": datetime.utcnow().isoformat(),
                "total_cost_usd": self.calculate_total(cost_data),
                "services": cost_data
            }, indent=2, default=str))
        
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect infrastructure cost data from Cloud Providers"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Don't save to database"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL (overrides DATABASE_URL env var)"
    )
    
    args = parser.parse_args()
    
    monitor = CostMonitor(db_url=args.db_url)
    sys.exit(monitor.run(save_to_db=not args.no_db, output_json=args.json))


if __name__ == "__main__":
    main()
