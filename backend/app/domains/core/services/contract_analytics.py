"""Contract Analytics Service"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any
from datetime import datetime, timedelta
from ..models.contract import Contract
from ..models.property import Property
from ..models.party import Party
from ..models.unit import Unit


class ContractAnalyticsService:
    """Service for contract analytics and reporting"""
    
    @staticmethod
    async def get_cost_summary(db: AsyncSession) -> Dict[str, Any]:
        """Get overall cost summary"""
        result = await db.execute(
            select(Contract).where(Contract.status == 'active')
        )
        contracts = result.scalars().all()
        
        total_annual_rent = 0
        total_caretaker = 0
        total_cleaning = 0
        total_parking = 0
        total_other_costs = 0
        
        for contract in contracts:
            # Annual rent
            if contract.amount and isinstance(contract.amount, dict):
                total_annual_rent += contract.amount.get('amount_per_year', 0) or 0
            
            # Direct cost fields
            total_caretaker += contract.caretaker_cost or 0
            total_cleaning += contract.cleaning_cost or 0
            total_parking += contract.parking_cost or 0
            
            # External data costs
            if contract.external_data:
                total_other_costs += contract.external_data.get('common_costs', 0) or 0
                total_other_costs += contract.external_data.get('user_dependent_costs', 0) or 0
                total_other_costs += contract.external_data.get('internal_maintenance_cost', 0) or 0
                total_other_costs += contract.external_data.get('municipal_fees', 0) or 0
                total_other_costs += contract.external_data.get('energy_cost', 0) or 0
                total_other_costs += contract.external_data.get('heating_cost', 0) or 0
        
        total_cost = total_annual_rent + total_caretaker + total_cleaning + total_parking + total_other_costs
        
        return {
            "total_cost": total_cost,
            "annual_rent": total_annual_rent,
            "caretaker_cost": total_caretaker,
            "cleaning_cost": total_cleaning,
            "parking_cost": total_parking,
            "other_costs": total_other_costs,
            "active_contracts": len(contracts)
        }
    
    @staticmethod
    async def get_regional_breakdown(db: AsyncSession) -> List[Dict[str, Any]]:
        """Get cost breakdown by region"""
        # Get all active contracts with property info
        stmt = (
            select(Contract, Property)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Contract.status == 'active')
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        # Group by region
        regions = {}
        for contract, property in rows:
            region = property.region or "Ukjent"
            
            if region not in regions:
                regions[region] = {
                    "region": region,
                    "contract_count": 0,
                    "total_cost": 0,
                    "properties": set()
                }
            
            # Calculate total cost for this contract
            cost = 0
            if contract.amount and isinstance(contract.amount, dict):
                cost += contract.amount.get('amount_per_year', 0) or 0
            cost += contract.caretaker_cost or 0
            cost += contract.cleaning_cost or 0
            cost += contract.parking_cost or 0
            
            if contract.external_data:
                cost += contract.external_data.get('common_costs', 0) or 0
                cost += contract.external_data.get('internal_maintenance_cost', 0) or 0
            
            regions[region]["contract_count"] += 1
            regions[region]["total_cost"] += cost
            regions[region]["properties"].add(str(property.property_id))
        
        # Convert to list and add property count
        result_list = []
        for region_data in regions.values():
            region_data["property_count"] = len(region_data["properties"])
            del region_data["properties"]  # Remove set before returning
            result_list.append(region_data)
        
        # Sort by total cost descending
        result_list.sort(key=lambda x: x["total_cost"], reverse=True)
        
        return result_list
    
    @staticmethod
    async def get_landlord_comparison(db: AsyncSession) -> List[Dict[str, Any]]:
        """Compare costs by landlord"""
        # Get contracts with party info
        stmt = (
            select(Contract, Party)
            .join(Party, Contract.party_id == Party.party_id)
            .where(Contract.status == 'active')
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        # Group by landlord
        landlords = {}
        for contract, party in rows:
            party_id = str(party.party_id)
            
            if party_id not in landlords:
                landlords[party_id] = {
                    "landlord_name": party.name,
                    "landlord_type": "Statsbygg" if "statsbygg" in party.name.lower() else "Privat",
                    "contract_count": 0,
                    "total_cost": 0
                }
            
            # Calculate cost
            cost = 0
            if contract.amount and isinstance(contract.amount, dict):
                cost += contract.amount.get('amount_per_year', 0) or 0
            cost += contract.caretaker_cost or 0
            cost += contract.cleaning_cost or 0
            
            landlords[party_id]["contract_count"] += 1
            landlords[party_id]["total_cost"] += cost
        
        result_list = list(landlords.values())
        result_list.sort(key=lambda x: x["total_cost"], reverse=True)
        
        return result_list[:20]  # Top 20 landlords
    
    @staticmethod
    async def get_expiring_contracts(db: AsyncSession, days_ahead: int = 180) -> List[Dict[str, Any]]:
        """Get contracts expiring within specified days"""
        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)
        
        stmt = (
            select(Contract, Property, Party)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .outerjoin(Party, Contract.party_id == Party.party_id)
            .where(Contract.status == 'active')
            .where(Contract.end_date.isnot(None))
            .where(Contract.end_date <= cutoff_date)
            .order_by(Contract.end_date)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        expiring = []
        for contract, property, party in rows:
            days_until = (contract.end_date - datetime.now().date()).days
            
            # Get extension deadline if available
            extension_deadline = None
            if contract.external_data and contract.external_data.get('extension_terms'):
                extension_text = contract.external_data['extension_terms']
                # Parse "JA, må vasle utleier om forlengelse min 6 mnd før utløp"
                if 'mnd før' in extension_text:
                    try:
                        months = int(''.join(filter(str.isdigit, extension_text.split('mnd før')[0].split()[-1])))
                        extension_deadline = contract.end_date - timedelta(days=months * 30)
                    except:
                        pass
            
            expiring.append({
                "contract_id": str(contract.contract_id),
                "property_address": property.address,
                "property_name": property.name,
                "landlord": party.name if party else "Ukjent",
                "end_date": contract.end_date.isoformat(),
                "days_until_expiry": days_until,
                "extension_deadline": extension_deadline.isoformat() if extension_deadline else None,
                "annual_cost": contract.amount.get('amount_per_year', 0) if contract.amount else 0,
                "status": "Utgått" if days_until < 0 else "Utløpende"
            })
        
        return expiring
    
    @staticmethod
    async def get_cost_per_sqm_analysis(db: AsyncSession) -> List[Dict[str, Any]]:
        """Analyze cost per square meter by property type"""
        stmt = (
            select(Contract, Property)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Contract.status == 'active')
            .where(Property.total_area.isnot(None))
            .where(Property.total_area > 0)
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        properties_analysis = []
        for contract, property in rows:
            if not contract.amount:
                continue
                
            annual_rent = contract.amount.get('amount_per_year', 0) or 0
            if annual_rent == 0:
                continue
            
            cost_per_sqm = annual_rent / property.total_area
            
            properties_analysis.append({
                "property_name": property.name or property.address,
                "address": property.address,
                "total_area": property.total_area,
                "annual_rent": annual_rent,
                "cost_per_sqm": round(cost_per_sqm, 2),
                "region": property.region,
                "municipality": property.municipality
            })
        
        # Sort by cost per sqm
        properties_analysis.sort(key=lambda x: x["cost_per_sqm"], reverse=True)
        
        return properties_analysis
