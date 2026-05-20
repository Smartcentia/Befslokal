#!/usr/bin/env python3
"""Export prediction data for Excel generation."""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.db.session import SessionLocal
from sqlalchemy import text


async def main():
    async with SessionLocal() as db:
        # GL 2025 total (ar = year column in Agresso data, belop > 0 = expenses only)
        r = await db.execute(text("SELECT SUM(belop) FROM gl_transactions WHERE ar=2025 AND belop > 0"))
        gl25_total = float(r.scalar() or 0)
        print(f"GL 2025 total (expenses): {gl25_total/1e6:.1f}M")

        # Count predictions
        r = await db.execute(text("SELECT COUNT(DISTINCT property_id) FROM budget WHERE year=2027 AND is_synthetic=true"))
        print(f"Properties in prediction: {r.scalar()}")

        # All prediction rows with GL history
        r3 = await db.execute(text("""
            SELECT p.name, p.region, p.municipality,
                   SUM(b.amount) as pred,
                   COALESCE(gl25.tot, 0) as gl25,
                   COALESCE(gl24.tot, 0) as gl24,
                   COALESCE(gl23.tot, 0) as gl23,
                   COALESCE(gl22.tot, 0) as gl22,
                   COALESCE(gl21.tot, 0) as gl21
            FROM budget b
            JOIN properties p ON p.property_id = b.property_id
            LEFT JOIN (SELECT property_id, SUM(belop) as tot FROM gl_transactions WHERE ar=2025 AND belop>0 GROUP BY property_id) gl25 ON gl25.property_id = b.property_id
            LEFT JOIN (SELECT property_id, SUM(belop) as tot FROM gl_transactions WHERE ar=2024 AND belop>0 GROUP BY property_id) gl24 ON gl24.property_id = b.property_id
            LEFT JOIN (SELECT property_id, SUM(belop) as tot FROM gl_transactions WHERE ar=2023 AND belop>0 GROUP BY property_id) gl23 ON gl23.property_id = b.property_id
            LEFT JOIN (SELECT property_id, SUM(belop) as tot FROM gl_transactions WHERE ar=2022 AND belop>0 GROUP BY property_id) gl22 ON gl22.property_id = b.property_id
            LEFT JOIN (SELECT property_id, SUM(belop) as tot FROM gl_transactions WHERE ar=2021 AND belop>0 GROUP BY property_id) gl21 ON gl21.property_id = b.property_id
            WHERE b.year = 2027 AND b.is_synthetic = true
            GROUP BY p.name, p.region, p.municipality,
                     gl25.tot, gl24.tot, gl23.tot, gl22.tot, gl21.tot
            ORDER BY pred DESC
        """))
        all_rows = r3.fetchall()
        all_data = []
        for row in all_rows:
            pred = float(row[3] or 0)
            gl25 = float(row[4] or 0)
            gl24 = float(row[5] or 0)
            gl23 = float(row[6] or 0)
            gl22 = float(row[7] or 0)
            gl21 = float(row[8] or 0)
            all_data.append({
                "name": str(row[0] or "?"),
                "region": str(row[1] or ""),
                "municipality": str(row[2] or ""),
                "pred_2027": pred,
                "gl_2025": gl25,
                "gl_2024": gl24,
                "gl_2023": gl23,
                "gl_2022": gl22,
                "gl_2021": gl21,
                "ratio_vs_2025": round(pred / gl25, 3) if gl25 > 0 else None,
            })

        result = {
            "gl_2025_total": gl25_total,
            "pred_2027_total": sum(d["pred_2027"] for d in all_data),
            "n_properties": len(all_data),
            "properties": all_data,
        }
        with open("/tmp/prediction_data_v2.json", "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_data)} properties to /tmp/prediction_data_v2.json")
        print(f"Prediction total: {result['pred_2027_total']/1e6:.1f}M")


if __name__ == "__main__":
    asyncio.run(main())
