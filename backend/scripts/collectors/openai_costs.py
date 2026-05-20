"""
OpenAI Cost Collector

Collects usage metrics from database logs (ApiCallLog).
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import json

class OpenAICostCollector:
    """Collects and aggregates OpenAI costs from the database."""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")

    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Aggregates OpenAI costs for the past 24 hours (or since last collection).
        For simplicity, we just aggregate the last 30 days to check total usage trend,
        but for the cost monitor snapshot, we capture the 'current state' which is typically a daily snapshot.
        
        However, infrastructure_costs table is designed for snapshots. 
        We should calculate the total usage within the last 24 hours to represent 'daily cost' 
        OR cumulative cost if that's what other collectors do.
        
        Database collector returns projected monthly cost based on usage.
        Here we will return the ACTUAL cost incurred in the last 30 days to represent 'monthly run rate'
        so it's comparable to the other monthly estimates.
        """
        if not self.db_url:
            print("OpenAICostCollector: No database URL provided.")
            return None
            
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Aggregate last 30 days
                query = text("""
                    SELECT 
                        count(*) as request_count,
                        sum(cost_estimate) as total_cost,
                        sum(response_time_ms) as total_duration
                    FROM api_call_logs 
                    WHERE service_name = 'openai'
                    AND timestamp >= (now() - interval '30 days')
                """)
                
                result = conn.execute(query).fetchone()
                
                request_count = result[0] or 0
                total_cost = float(result[1] or 0.0)
                total_duration_ms = result[2] or 0
                
                active_time_seconds = int(total_duration_ms / 1000)
                
                return {
                    "service_name": "openai",
                    "collection_date": datetime.utcnow().isoformat(),
                    "raw_metrics": {
                        "request_count": request_count, 
                        "period": "last_30_days"
                    },
                    "estimated_cost_usd": round(total_cost, 4),
                    "active_time_seconds": active_time_seconds,
                    "cpu_used_seconds": None, # Not applicable
                    "storage_gb": None,
                    "bandwidth_gb": None,
                    "notes": f"Requests (30d): {request_count}"
                }
                
        except Exception as e:
            print(f"OpenAICostCollector Error: {e}")
            return None

if __name__ == "__main__":
    collector = OpenAICostCollector()
    print(json.dumps(collector.collect(), indent=2, default=str))
