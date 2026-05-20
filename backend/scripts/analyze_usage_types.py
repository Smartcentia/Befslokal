#!/usr/bin/env python3
"""
Analyze property usage types and prepare for update.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

CSV_PATH = "/Volumes/KINGSTON/csv/Bufetat_leiedata_renset.csv"

async def analyze_usage_types():
    print("🏢 Analyzing Property Usage Types")
    print("=" * 60)
    
    # Load CSV
    print("\n📊 Loading CSV data...")
    df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8-sig')
    print(f"  Loaded {len(df)} rows")
    
    # Check column names
    print(f"\n📋 CSV Columns:")
    for i, col in enumerate(df.columns[:20], 1):
        print(f"  {i}. {col}")
    
    # Analyze Type lokasjon
    if 'Type lokasjon' in df.columns:
        print(f"\n📊 Type lokasjon distribution:")
        type_counts = df['Type lokasjon'].value_counts()
        for type_val, count in type_counts.items():
            print(f"  {type_val}: {count}")
    
    # Get current property usage in database
    print(f"\n🗄️  Current database property usage:")
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        usage_counts = {}
        for p in properties:
            usage = p.usage or "NULL"
            usage_counts[usage] = usage_counts.get(usage, 0) + 1
        
        for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
            print(f"  {usage}: {count}")
        
        # Check if we have external_data with institution info
        print(f"\n🔍 Properties with institution data:")
        with_inst_data = 0
        for p in properties:
            if p.external_data and 'bufdir_institution' in p.external_data:
                with_inst_data += 1
        print(f"  {with_inst_data} properties have Bufdir institution data")

if __name__ == "__main__":
    asyncio.run(analyze_usage_types())
