#!/usr/bin/env python3
import os
import sys
import asyncio
import json
import argparse
from typing import Dict, Any

# Add parent directory to path to allow imports from 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import app.db.base # Ensure models are loaded in correct order for relationships
from app.db.session import SessionLocal
from app.services.analytics.financial_analytics import financial_analytics_service
from app.services.analytics.financial_analysis_service import FinancialAnalysisService
from app.domains.core.models.property import Property
from sqlalchemy import select

async def get_property_id_by_name(db, name: str) -> str:
    if not name:
        return None
    stmt = select(Property).where(Property.name.ilike(f"%{name}%"))
    result = await db.execute(stmt)
    prop = result.scalars().first()
    return prop.property_id if prop else None

async def run_analysis(args):
    async with SessionLocal() as db:
        target = args.target
        property_id = None
        
        # Sjekk om target er en UUID (ID)
        is_id = False
        if target and len(target) > 30 and "-" in target:
            is_id = True
            property_id = target
        
        if target and not is_id:
            property_id = await get_property_id_by_name(db, target)
            
        result = {}
        if args.type == "forecast":
            if not property_id:
                print(json.dumps({"error": "Fant ikke eiendom for prognose. Oppgi navn eller ID."}))
                return
            result = await financial_analytics_service.forecast_future_costs(db, property_id, years_ahead=args.years)
        elif args.type == "anomalies":
            if not property_id:
                print(json.dumps({"error": "Fant ikke eiendom for avviksanalyse. Oppgi navn eller ID."}))
                return
            result = await financial_analytics_service.detect_spending_anomalies(db, property_id)
        elif args.type == "patterns":
            # Patterns kan være generelle (hele porteføljen) eller per eiendom
            # Men per nå er get_common_patterns global
            result = await FinancialAnalysisService.get_common_patterns(db)
        else:
            # Run both forecast and anomalies for a property
            if not property_id:
                print(json.dumps({"error": "Må oppgi eiendom for 'both'."}))
                return
            forecast = await financial_analytics_service.forecast_future_costs(db, property_id, years_ahead=args.years)
            anomalies = await financial_analytics_service.detect_spending_anomalies(db, property_id)
            result = {
                "forecast": forecast,
                "anomalies": anomalies
            }

        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ML-basert økonomisk analyse og mønstergjenkjenning")
    parser.add_argument("target", nargs="?", help="Navn eller ID på eiendommen (valgfri for mønstre)")
    parser.add_argument("--type", choices=["forecast", "anomalies", "patterns", "both"], default="both")
    parser.add_argument("--years", type=int, default=3, help="Antall år frem i tid for prognose")
    
    args = parser.parse_args()
    
    asyncio.run(run_analysis(args))
