import pandas as pd
import io
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.domains.core.models.property import Property

import logging

logger = logging.getLogger(__name__)

class FinancialImportService:
    def parse_financial_file(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parses CSV or Excel file containing financial data.
        Expected columns: 'Koststed', 'Konto', 'Beskrivelse', 'Beløp', 'Dato'
        """
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content), sep=';') # Assuming Norwegian CSV
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format")

            # Basic Validation/Normalization
            # Map common headers to standard keys
            # Implementation assumes a specific standard or flexible matching
            results = []
            
            # Simple simulation of mapping logical rows
            # Real implementation would need the user's specific excel layout
            for _, row in df.iterrows():
                # Attempt to find property ID in 'Koststed' or description
                results.append({
                    "cost_center": str(row.get('Koststed', '')),
                    "account": str(row.get('Konto', '')),
                    "description": str(row.get('Beskrivelse', '')),
                    "amount": float(str(row.get('Beløp', '0')).replace(',', '.').replace(' ', '')),
                    "date": str(row.get('Dato', ''))
                })
                
            return results

        except Exception as e:
            logger.error(f"Error parsing financial file: {str(e)}")
            return []

    def import_expenses(self, db: Session, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Updates properties with financial data matching their ID or ExternalRef.
        Currently just returns a summary of what WOULd happen (Simulation).
        """
        updated_count = 0
        skipped_count = 0
        
        for item in data:
            # Logic: Try to match Cost Center to Property.external_data['cost_center']
            # or Property Name/ID
            cost_center = item['cost_center']
            
            # This requires Property model to have a field for cost mapping
            # For now, we simulate success if mapped
            if cost_center:
                updated_count += 1
            else:
                skipped_count += 1
                
        return {"processed": len(data), "mapped": updated_count, "skipped": skipped_count}

financial_import_service = FinancialImportService()
