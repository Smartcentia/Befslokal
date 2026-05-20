from typing import Dict, Any, List, Optional
import logging
from app.services.external.brreg_service import brreg_service

logger = logging.getLogger(__name__)

class RiskProfile:
    def __init__(self, score: int, level: str, red_flags: List[str], actions: List[str], liens: List[Dict] = None):
        self.score = score
        self.level = level
        self.red_flags = red_flags
        self.actions = actions
        self.liens = liens or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "red_flags": self.red_flags,
            "actions": self.actions,
            "liens": self.liens
        }

class RiskEngine:
    """
    Calculates a risk score (0-100) for a supplier based on available data.
    """

    async def calculate_risk_score(self, org_nr: str) -> RiskProfile:
        score = 0
        red_flags = []
        actions = []

        if not org_nr:
             return RiskProfile(0, "UNKNOWN", ["Missing OrgNr"], [])

        try:
            # 1. CRITICAL EVENTS (Kunngjøringer / Enhetsregisteret Status)
            # Weights: Konkurs/Tvangsoppløsning = 100 (Critical)
            announcements = await brreg_service.get_kunngjoringer(org_nr)
            
            for announcement in announcements:
                atype = announcement.get("type", "")
                if atype in ["Konkursåpning", "Tvangsoppløsning", "Oppbud / Avvikling"]:
                    score = 100
                    red_flags.append(f"CRITICAL: {atype} registered ({announcement.get('dato')})")
                    actions.append("BLOCK_PAYMENTS")
                    # Immediate critical return
                    return RiskProfile(score, "CRITICAL", red_flags, actions)

            # 2. FINANCIAL HEALTH (Regnskap)
            # Weights: Negative Equity = 40, Operating Loss = 20
            financials = await brreg_service.get_aarsregnskap(org_nr)
            if financials:
                latest = financials[0] # Newest year
                equity = latest.get("equity")
                op_profit = latest.get("operating_profit")
                
                if equity is not None and equity < 0:
                    score += 40
                    red_flags.append(f"Insolvent: Negative Equity ({latest.get('year')})")
                
                if op_profit is not None and op_profit < 0:
                    # Check usage of previous years for trend if needed
                    score += 20
                    red_flags.append(f"Operating Loss ({latest.get('year')})")
            
            # 3. MORTGAGES (Løsøreregisteret)
            # Fetch real data via Maskinporten
            liens = await brreg_service.get_losore(org_nr)
            risk_liens = []
            
            if liens:
                total_pledged = 0
                for lien in liens:
                    amount = lien.get("amount", 0)
                    total_pledged += amount
                    # Add to profile for frontend display
                    risk_liens.append(lien)
                
                # Risk Logic: High Leverage
                # If pledged amount > 80% of Equity (and Equity is positive)
                if financials:
                    latest_equity = financials[0].get("equity", 0) or 0
                    if latest_equity > 0 and total_pledged > (latest_equity * 0.8):
                        score += 30
                        red_flags.append(f"High Leverage: {total_pledged} pledged vs equity")

            # 4. COMPLIANCE CHECKS (Tax, Credit, Sanctions)
            from app.services.risk.compliance_interfaces import TaxService, CreditService, SanctionService
            
            providers = [TaxService(), CreditService(), SanctionService()]
            
            for provider in providers:
                try:
                    res = await provider.check_compliance(org_nr)
                    if res["status"] == "FAIL":
                        # Critical Stop Factor
                        return RiskProfile(100, "CRITICAL", [f"CRITICAL: {res['source']} - {res['details']}"], ["BLOCK_PAYMENTS"])
                    
                    if res["status"] == "WARNING":
                        score += res["score_modifier"]
                        red_flags.append(f"{res['source']}: {res['details']}")
                        
                except Exception:
                    logger.warning(f"Compliance check failed for {provider.__class__.__name__}")

            # 5. INTERNAL DATA (Unit4 / Early Warning)
            from app.services.internal.unit4_service import unit4_service
            
            # Check Bank Account Change (30 days)
            if await unit4_service.check_bank_change(org_nr):
                score += 30
                red_flags.append("OBS: Bank account changed recently")
            
            # Check Invoice Anomalies
            anomaly_score = await unit4_service.check_invoice_anomaly(org_nr)
            if anomaly_score > 0.8:
                score += 20
                red_flags.append("Anomaly: Unusual invoicing pattern")

            # 6. STABILITY (Age)
            # Fetch founding date from Enhetsregisteret if possible, or use API data
            # Simplified mock for age check (assuming BrregService could return founding date)
            # if org_age_months < 6: score += 10 ...
            
            # Cap Score
            score = min(score, 100)

            # Determine Level
            if score >= 100:
                level = "CRITICAL"
                actions.append("BLOCK_PAYMENTS")
                # Trigger Auto-Block
                await unit4_service.block_supplier(org_nr, "Risk Score 100 (Critical)")
            elif score >= 80:
                level = "HIGH"
                actions.append("CONTACT_CFO")
            elif score >= 40:
                level = "MEDIUM"
                actions.append("VERIFY_DELIVERY")
            else:
                level = "LOW"

            return RiskProfile(score, level, red_flags, actions, liens=risk_liens)

        except Exception as e:
            logger.exception(f"RiskEngine: Error calculating score for {org_nr}")
            return RiskProfile(0, "ERROR", [f"Calculation failed: {str(e)}"], [])

risk_engine = RiskEngine()
