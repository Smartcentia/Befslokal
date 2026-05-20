from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ComplianceProvider(ABC):
    """
    Abstract Base Class for external compliance checks.
    Examples: Tax (Skatteetaten), Credit (Dun & Bradstreet), Sanctions.
    """

    @abstractmethod
    async def check_compliance(self, org_nr: str) -> Dict[str, Any]:
        """
        Returns a standardized compliance report.
        
        Return format:
        {
            "status": "OK" | "WARNING" | "FAIL" | "UNKNOWN",
            "score_modifier": int, # Points to add to Risk Score
            "details": str,
            "source": str
        }
        """
        pass

class TaxService(ComplianceProvider):
    """
    Integration with Skatteetaten (eBevis/A-ordningen).
    Requires 'Samtykke' or legal basis.
    """
    async def check_compliance(self, org_nr: str) -> Dict[str, Any]:
        # TODO: Implement eBevis API call
        # Mock for now
        return {
            "status": "UNKNOWN",
            "score_modifier": 0,
            "details": "Tax check requires eBevis integration.",
            "source": "Skatteetaten"
        }

class CreditService(ComplianceProvider):
    """
    Integration with Credit Agencies (D&B, Creditsafe).
    """
    async def check_compliance(self, org_nr: str) -> Dict[str, Any]:
        # TODO: Implement Credit API
        return {
            "status": "UNKNOWN", 
            "score_modifier": 0,
            "details": "Credit rating not configured.",
            "source": "CreditAgency"
        }
        
class SanctionService(ComplianceProvider):
    """
    Checks against EU/UN/OFAC sanction lists.
    """
    async def check_compliance(self, org_nr: str) -> Dict[str, Any]:
        # TODO: Implement Sanctions API
        return {
            "status": "OK", # Default to OK to avoid noise 
            "score_modifier": 0, 
            "details": "No generic sanctions found (Mock).",
            "source": "SanctionList"
        }
