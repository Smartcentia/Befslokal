import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Unit4Service:
    """
    Service for interacting with Unit4 / ERP system.
    Used for:
    - Checking invoice anomalies
    - Checking sensitive changes (Bank account numbers)
    - Blocking suppliers
    """
    
    async def check_bank_change(self, supplier_id: str, days: int = 30) -> bool:
        """Check if bank account has changed recently."""
        # Mock implementation: Returns False (No change) by default
        return False

    async def check_invoice_anomaly(self, supplier_id: str) -> float:
        """
        Returns anomaly score (0.0 - 1.0) based on invoice patterns.
        > 0.8 is considered suspicious.
        """
        # Mock implementation
        return 0.1

    async def block_supplier(self, supplier_id: str, reason: str) -> bool:
        """
        Sets supplier status to 'P' (Parked) in Unit4.
        """
        logger.info(f"UNIT4: Blocking supplier {supplier_id}. Reason: {reason}")
        return True

# Singleton instance
unit4_service = Unit4Service()
