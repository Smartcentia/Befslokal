"""
Financial Analysis Service - Refactored from CLI scripts for web use

Utvidet med kostnadsmønstre:
- Geografiske, leverandør, tidsmønstre, kategori-bundles, skaleringsmønstre
- Bygningsalder, energimerking, brukstype, kostnad per kvm per kategori
- Budsjett vs faktisk, risiko-kostnad, leverandørportefølje-overlap
- Manglende data, kommune, senter, transaksjonstetthet, kategori-diversifikasjon
"""

from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
import statistics
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.utils.region_mapping import get_operational_region
from app.domains.core.models.unit import Unit


class FinancialAnalysisService:
    """Service for analyzing property financial data"""
    
    @staticmethod
    async def search_properties(db: AsyncSession, query: str) -> List[Dict[str, Any]]:
        """Search for properties by name and return financial summary"""
        query_lower = query.lower()
        
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Get all active contracts
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        # Build property -> contract mapping
        property_contracts = {}
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        # Find matches and build response
        matches = []
        
        for prop in properties:
            if query_lower not in prop.name.lower():
                continue
            
            prop_id = prop.property_id
            
            # Calculate rent
            total_rent = 0
            num_contracts = 0
            if prop_id in property_contracts:
                num_contracts = len(property_contracts[prop_id])
                for contract in property_contracts[prop_id]:
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        rent = float(rent) if rent else 0
                    except (ValueError, TypeError):
                        rent = 0
                    total_rent += rent
            
            # Calculate costs
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            total_costs = 0
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                    total_costs += amount
                except (ValueError, TypeError):
                    pass
            
            # Determine status
            has_rent = total_rent > 0
            has_costs = len(expenses) > 0
            
            if has_rent and has_costs:
                status = "complete"
            elif has_rent and not has_costs:
                status = "missing_costs"
            elif not has_rent and has_costs:
                status = "missing_rent"
            else:
                status = "missing_all"
            
            matches.append({
                'property_id': str(prop_id),
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'address': prop.address or '',
                'rent': total_rent,
                'costs': total_costs,
                'total': total_rent + total_costs,
                'num_contracts': num_contracts,
                'num_expenses': len(expenses),
                'status': status
            })
        
        return matches
    
    @staticmethod
    async def get_property_analysis(
        db: AsyncSession, 
        property_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed financial analysis for a property"""
        # Get property
        stmt = select(Property).where(Property.property_id == property_id)
        result = await db.execute(stmt)
        prop = result.scalar_one_or_none()
        
        if not prop:
            return None
        
        # Get contracts
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .join(Unit)
            .where(Unit.property_id == property_id)
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        # Calculate rent
        total_rent = 0
        contracts_list = []
        for contract in contracts:
            amount_data = contract.amount if isinstance(contract.amount, dict) else {}
            rent = amount_data.get('amount_per_year', 0)
            try:
                rent = float(rent) if rent else 0
            except (ValueError, TypeError):
                rent = 0
            total_rent += rent
            
            contracts_list.append({
                'contract_id': str(contract.contract_id),
                'rent': rent,
                'start_date': contract.start_date.isoformat() if contract.start_date else None,
                'end_date': contract.end_date.isoformat() if contract.end_date else None
            })
        
        # Get cost data
        ext = prop.external_data or {}
        expenses = ext.get('financials', {}).get('manual_expenses', [])
        
        total_costs = 0
        cost_by_category = defaultdict(float)
        cost_by_provider = defaultdict(float)
        
        for exp in expenses:
            try:
                amount = float(exp.get('amount', 0) or 0)
                total_costs += amount
                category = exp.get('type', 'Ukjent')
                provider = exp.get('provider', 'Ukjent')
                cost_by_category[category] += amount
                cost_by_provider[provider] += amount
            except (ValueError, TypeError):
                pass
        
        # Sort categories and providers
        sorted_categories = sorted(
            cost_by_category.items(), 
            key=lambda x: -x[1]
        )
        sorted_providers = sorted(
            cost_by_provider.items(), 
            key=lambda x: -x[1]
        )
        
        return {
            'property_id': str(prop.property_id),
            'name': prop.name,
            'region': prop.region or 'Unknown',
            'address': prop.address or '',
            'rent': total_rent,
            'costs': total_costs,
            'total': total_rent + total_costs,
            'num_contracts': len(contracts_list),
            'num_expenses': len(expenses),
            'contracts': contracts_list,
            'cost_by_category': [
                {'category': cat, 'amount': amt, 'percentage': (amt / total_costs * 100) if total_costs > 0 else 0}
                for cat, amt in sorted_categories
            ],
            'cost_by_provider': [
                {'provider': prov, 'amount': amt}
                for prov, amt in sorted_providers[:10]  # Top 10 only
            ]
        }
    
    @staticmethod
    async def get_common_patterns(db: AsyncSession, year: Optional[int] = None) -> Dict[str, Any]:
        """Get common cost patterns across all properties from GL transactions"""
        # Still need properties list for _get_extended_patterns
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        total_properties = len(properties)

        try:
            from app.models.financial_models import GLTransaction
            from sqlalchemy import distinct as sa_distinct

            # --- common_categories: distinct property count + avg amount per account ---
            cat_stmt = (
                select(
                    GLTransaction.konto_navn,
                    func.count(sa_distinct(GLTransaction.property_id)).label('prop_count'),
                    func.avg(GLTransaction.belop).label('avg_amount'),
                )
                .where(
                    GLTransaction.belop > 0,
                    GLTransaction.konto_navn.isnot(None),
                    GLTransaction.konto_navn != '',
                )
                .group_by(GLTransaction.konto_navn)
                .order_by(func.count(sa_distinct(GLTransaction.property_id)).desc())
                .limit(20)
            )
            if year:
                cat_stmt = cat_stmt.where(GLTransaction.ar == year)
            cat_rows = (await db.execute(cat_stmt)).fetchall()

            common_categories = [
                {
                    'category': r.konto_navn,
                    'property_count': r.prop_count,
                    'percentage': (r.prop_count / total_properties * 100) if total_properties else 0,
                    'avg_amount': float(r.avg_amount or 0),
                }
                for r in cat_rows
            ]

            # --- common_providers: total transaction count per supplier ---
            prov_stmt = (
                select(
                    GLTransaction.leverandor_navn,
                    func.count().label('cnt'),
                )
                .where(
                    GLTransaction.belop > 0,
                    GLTransaction.leverandor_navn.isnot(None),
                    GLTransaction.leverandor_navn != '',
                )
                .group_by(GLTransaction.leverandor_navn)
                .order_by(func.count().desc())
                .limit(15)
            )
            if year:
                prov_stmt = prov_stmt.where(GLTransaction.ar == year)
            prov_rows = (await db.execute(prov_stmt)).fetchall()

            common_providers = [
                {'provider': r.leverandor_navn, 'transaction_count': r.cnt}
                for r in prov_rows
            ]

        except Exception:
            common_categories = []
            common_providers = []

        # Extended patterns - unchanged (uses property JSONB data)
        extended = await FinancialAnalysisService._get_extended_patterns(db, properties)

        return {
            'total_properties': total_properties,
            'common_categories': common_categories,
            'common_providers': common_providers,
            **extended
        }

    @staticmethod
    def _parse_year_from_date(date_val: Any) -> Optional[int]:
        """Hent år fra utgiftens date-felt."""
        if date_val is None:
            return None
        s = str(date_val).strip()
        if not s:
            return None
        if len(s) >= 4 and s[:4].isdigit():
            try:
                return int(s[:4])
            except ValueError:
                pass
        if "-Q" in s:
            part = s.split("-Q")[0].strip()
            if part.isdigit():
                try:
                    return int(part)
                except ValueError:
                    pass
        if "." in s:
            parts = s.split(".")
            if len(parts) >= 3 and parts[-1].isdigit():
                try:
                    return int(parts[-1])
                except ValueError:
                    pass
        return None

    @staticmethod
    def _parse_month_from_date(date_val: Any) -> Optional[int]:
        """Hent måned (1-12) fra utgiftens date-felt."""
        if date_val is None:
            return None
        s = str(date_val).strip()
        if not s:
            return None
        # "2024-01-15" -> 1
        if len(s) >= 7 and s[4] == '-' and s[5:7].isdigit():
            try:
                return int(s[5:7])
            except ValueError:
                pass
        # "01.01.2024" -> 1
        if "." in s:
            parts = s.split(".")
            if len(parts) >= 2 and parts[0].isdigit():
                try:
                    return int(parts[0])
                except ValueError:
                    pass
        return None

    @staticmethod
    async def _get_extended_patterns(db: AsyncSession, properties: List) -> Dict[str, Any]:
        """Samle alle utvidede kostnadsmønstre."""
        # Build property -> contracts mapping for rent
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        property_contracts: Dict = defaultdict(list)
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                rent = amount_data.get('amount_per_year', 0) or amount_data.get('total_per_year', 0)
                try:
                    rent = float(rent) if rent else 0
                except (TypeError, ValueError):
                    rent = 0
                property_contracts[prop_id].append(rent)

        # Load units for usage_type
        stmt_units = select(Unit)
        result_units = await db.execute(stmt_units)
        units = result_units.scalars().all()
        property_usage_types: Dict = defaultdict(set)
        for u in units:
            ext = u.external_data or {}
            ut = ext.get('usage_type') or u.purpose or u.zone_type
            if ut:
                property_usage_types[u.property_id].add(str(ut))

        # Load risk assessments (latest per property)
        risk_by_property: Dict = {}
        try:
            from app.domains.hms.models.risk import RiskAssessment
            stmt_risk = (
                select(RiskAssessment)
                .order_by(RiskAssessment.assessment_date.desc())
            )
            result_risk = await db.execute(stmt_risk)
            for ra in result_risk.scalars().all():
                if ra.property_id not in risk_by_property:
                    risk_by_property[ra.property_id] = ra.overall_risk_score or 0
        except ImportError:
            pass

        # Build property data for analysis
        current_year = datetime.now().year
        prop_data_list = []
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            total_costs = sum(float(e.get('amount', 0) or 0) for e in expenses)
            total_rent = sum(property_contracts.get(prop.property_id, [0]))
            cost_by_category = defaultdict(float)
            cost_by_provider = defaultdict(float)
            providers = set()
            categories = set()
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                    cat = exp.get('type', 'Ukjent')
                    prov = exp.get('provider', 'Ukjent')
                    cost_by_category[cat] += amount
                    cost_by_provider[prov] += amount
                    if prov and prov != 'Ukjent':
                        providers.add(prov)
                    categories.add(cat)
                except (TypeError, ValueError):
                    pass

            construction_year = getattr(prop, 'construction_year', None)
            ext_data = prop.external_data or {}
            if not construction_year and ext_data:
                construction_year = ext_data.get('byggeår') or ext_data.get('year_built') or ext_data.get('building_year')

            prop_data_list.append({
                'property': prop,
                'property_id': str(prop.property_id),
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'municipality': getattr(prop, 'municipality', None) or 'Unknown',
                'postal_code': getattr(prop, 'postal_code', None) or '',
                'center_id': getattr(prop, 'center_id', None),
                'total_area': prop.total_area or 0,
                'total_costs': total_costs,
                'total_rent': total_rent,
                'expenses': expenses,
                'num_expenses': len(expenses),
                'cost_by_category': dict(cost_by_category),
                'cost_by_provider': dict(cost_by_provider),
                'providers': providers,
                'categories': categories,
                'construction_year': construction_year,
                'energy_label': getattr(prop, 'energy_label', None) or '',
                'usage': getattr(prop, 'usage', None) or 'Ukjent',
                'usage_types': list(property_usage_types.get(prop.property_id, set())),
                'risk_score': risk_by_property.get(prop.property_id),
            })

        # 1-8: Original patterns
        regional_patterns = FinancialAnalysisService._regional_patterns(prop_data_list)
        supplier_concentration = FinancialAnalysisService._supplier_concentration(prop_data_list)
        supplier_price_variation = FinancialAnalysisService._supplier_price_variation(prop_data_list)
        time_patterns = FinancialAnalysisService._time_patterns(prop_data_list)
        category_bundles = FinancialAnalysisService._category_bundles(prop_data_list)
        scaling_patterns = FinancialAnalysisService._scaling_patterns(prop_data_list)
        provider_category_patterns = FinancialAnalysisService._provider_category_patterns(prop_data_list)
        cluster_patterns = FinancialAnalysisService._cluster_patterns(prop_data_list)

        # 9-20: Nye mønstre
        building_age_patterns = FinancialAnalysisService._building_age_patterns(prop_data_list, current_year)
        energy_label_patterns = FinancialAnalysisService._energy_label_patterns(prop_data_list)
        usage_type_patterns = FinancialAnalysisService._usage_type_patterns(prop_data_list)
        cost_per_sqm_by_category = FinancialAnalysisService._cost_per_sqm_by_category(prop_data_list)
        budget_variance_patterns = await FinancialAnalysisService._budget_variance_patterns(db, prop_data_list, current_year)
        risk_cost_patterns = FinancialAnalysisService._risk_cost_patterns(prop_data_list)
        supplier_overlap_patterns = FinancialAnalysisService._supplier_overlap_patterns(prop_data_list)
        missing_data_patterns = FinancialAnalysisService._missing_data_patterns(prop_data_list)
        municipality_patterns = FinancialAnalysisService._municipality_patterns(prop_data_list)
        center_patterns = FinancialAnalysisService._center_patterns(prop_data_list)
        transaction_density_patterns = FinancialAnalysisService._transaction_density_patterns(prop_data_list)
        category_diversification_patterns = FinancialAnalysisService._category_diversification_patterns(prop_data_list)

        return {
            'regional_patterns': regional_patterns,
            'supplier_concentration': supplier_concentration,
            'supplier_price_variation': supplier_price_variation,
            'time_patterns': time_patterns,
            'category_bundles': category_bundles,
            'scaling_patterns': scaling_patterns,
            'provider_category_patterns': provider_category_patterns,
            'cluster_patterns': cluster_patterns,
            'building_age_patterns': building_age_patterns,
            'energy_label_patterns': energy_label_patterns,
            'usage_type_patterns': usage_type_patterns,
            'cost_per_sqm_by_category': cost_per_sqm_by_category,
            'budget_variance_patterns': budget_variance_patterns,
            'risk_cost_patterns': risk_cost_patterns,
            'supplier_overlap_patterns': supplier_overlap_patterns,
            'missing_data_patterns': missing_data_patterns,
            'municipality_patterns': municipality_patterns,
            'center_patterns': center_patterns,
            'transaction_density_patterns': transaction_density_patterns,
            'category_diversification_patterns': category_diversification_patterns,
        }

    @staticmethod
    def _regional_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Geografiske mønstre: kostnader per region, regional sammenligning."""
        by_region: Dict[str, Dict] = defaultdict(lambda: {
            'properties': [], 'total_costs': 0.0, 'total_rent': 0.0,
            'costs_with_area': [], 'total_area': 0.0
        })
        for p in prop_data_list:
            r = get_operational_region(p['region'] or "Sør")
            by_region[r]['properties'].append(p['name'])
            by_region[r]['total_costs'] += p['total_costs']
            by_region[r]['total_rent'] += p['total_rent']
            if p['total_area'] > 0 and p['total_costs'] > 0:
                by_region[r]['costs_with_area'].append(p['total_costs'] / p['total_area'])
                by_region[r]['total_area'] += p['total_area']

        regions = []
        for region, data in by_region.items():
            n = len(data['properties'])
            avg_costs = data['total_costs'] / n if n > 0 else 0
            avg_rent = data['total_rent'] / n if n > 0 else 0
            ratio = data['total_costs'] / data['total_rent'] if data['total_rent'] > 0 else 0
            cost_per_sqm = statistics.mean(data['costs_with_area']) if data['costs_with_area'] else None
            regions.append({
                'region': region,
                'property_count': n,
                'total_costs': data['total_costs'],
                'avg_costs': avg_costs,
                'avg_rent': avg_rent,
                'cost_to_rent_ratio': ratio,
                'cost_per_sqm': cost_per_sqm,
            })
        regions.sort(key=lambda x: -x['total_costs'])

        # Eiendommer over/under regionalt snitt
        above_below = []
        for p in prop_data_list:
            r = get_operational_region(p['region'] or "Sør")
            if r not in by_region or not by_region[r]['properties']:
                continue
            reg = by_region[r]
            n = len(reg['properties'])
            avg = reg['total_costs'] / n if n > 0 else 0
            if avg > 0:
                pct = ((p['total_costs'] - avg) / avg) * 100
                above_below.append({
                    'property': p['name'],
                    'region': r,
                    'costs': p['total_costs'],
                    'regional_avg': avg,
                    'deviation_pct': round(pct, 1),
                })
        above_below.sort(key=lambda x: -abs(x['deviation_pct']))

        return {
            'by_region': regions[:15],
            'above_below_regional_avg': above_below[:20],
        }

    @staticmethod
    def _supplier_concentration(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Leverandørkoncentration: få vs mange leverandører, leverandørandel."""
        few_suppliers = []  # 1-2 leverandører
        many_suppliers = []  # 10+
        high_concentration = []  # Største leverandør >50% av kostnad

        for p in prop_data_list:
            if p['total_costs'] <= 0:
                continue
            n_prov = len(p['providers']) or len(p['cost_by_provider'])
            max_prov_amount = max(p['cost_by_provider'].values()) if p['cost_by_provider'] else 0
            share = (max_prov_amount / p['total_costs']) * 100 if p['total_costs'] > 0 else 0

            if n_prov <= 2 and p['total_costs'] > 100000:
                few_suppliers.append({
                    'property': p['name'],
                    'supplier_count': n_prov,
                    'total_costs': p['total_costs'],
                })
            if n_prov >= 10:
                many_suppliers.append({
                    'property': p['name'],
                    'supplier_count': n_prov,
                    'total_costs': p['total_costs'],
                })
            if share > 50:
                top_prov = max(p['cost_by_provider'].items(), key=lambda x: x[1])[0]
                high_concentration.append({
                    'property': p['name'],
                    'top_provider': top_prov,
                    'share_pct': round(share, 1),
                    'amount': max_prov_amount,
                })

        return {
            'few_suppliers': few_suppliers[:15],
            'many_suppliers': many_suppliers[:15],
            'high_concentration': high_concentration[:15],
        }

    @staticmethod
    def _supplier_price_variation(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Leverandørprisvariasjon: samme leverandør, ulike priser på tvers av eiendommer."""
        provider_amounts: Dict[str, List[float]] = defaultdict(list)
        for p in prop_data_list:
            for prov, amount in p['cost_by_provider'].items():
                if prov and prov != 'Ukjent' and amount > 0:
                    provider_amounts[prov].append(amount)

        variation = []
        for prov, amounts in provider_amounts.items():
            if len(amounts) < 3:
                continue
            mean_amt = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            cv = (stdev / mean_amt * 100) if mean_amt > 0 else 0
            variation.append({
                'provider': prov,
                'property_count': len(amounts),
                'mean_amount': round(mean_amt, 0),
                'stdev': round(stdev, 0),
                'coefficient_of_variation_pct': round(cv, 1),
                'min': min(amounts),
                'max': max(amounts),
            })
        variation.sort(key=lambda x: -x['coefficient_of_variation_pct'])

        return {
            'by_provider': variation[:20],
        }

    @staticmethod
    def _time_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Tidsmønstre: sesong, måned, år-over-år (når date er fylt)."""
        by_year: Dict[int, float] = defaultdict(float)
        by_month: Dict[int, float] = defaultdict(float)
        expenses_with_date = 0
        total_expenses = 0

        for p in prop_data_list:
            for exp in p['expenses']:
                amount = float(exp.get('amount', 0) or 0)
                total_expenses += 1
                year = FinancialAnalysisService._parse_year_from_date(exp.get('date'))
                month = FinancialAnalysisService._parse_month_from_date(exp.get('date'))
                if year is not None:
                    expenses_with_date += 1
                    by_year[year] += amount
                if month is not None:
                    by_month[month] += amount

        date_coverage = (expenses_with_date / total_expenses * 100) if total_expenses > 0 else 0

        by_year_list = [{'year': y, 'total': by_year[y]} for y in sorted(by_year.keys())]
        by_month_list = [{'month': m, 'total': by_month[m]} for m in sorted(by_month.keys())]

        # Sesong: vinter (11-2) vs sommer (6-8)
        winter = sum(by_month.get(m, 0) for m in [11, 12, 1, 2])
        summer = sum(by_month.get(m, 0) for m in [6, 7, 8])
        seasonal = {'winter_total': winter, 'summer_total': summer} if by_month else {}

        return {
            'date_coverage_pct': round(date_coverage, 1),
            'by_year': by_year_list,
            'by_month': by_month_list,
            'seasonal': seasonal,
        }

    @staticmethod
    def _category_bundles(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Kategori-kombinasjoner: typiske bundles (f.eks. Fellesutgifter + Strøm)."""
        from itertools import combinations
        bundle_counts: Dict[Tuple[str, ...], int] = defaultdict(int)
        for p in prop_data_list:
            cats = sorted([c for c in p['categories'] if c and c != 'Ukjent'])
            if len(cats) < 2:
                continue
            for size in range(2, min(4, len(cats) + 1)):
                for combo in combinations(cats, size):
                    bundle_counts[combo] += 1

        bundles = [
            {'categories': list(b), 'property_count': c}
            for b, c in sorted(bundle_counts.items(), key=lambda x: -x[1])[:20]
        ]
        return {'common_bundles': bundles}

    @staticmethod
    def _scaling_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Skaleringsmønstre: kostnad per kvm per kategori, avvik fra porteføljen."""
        with_area = [p for p in prop_data_list if p['total_area'] > 0 and p['total_costs'] > 0]
        if not with_area:
            return {'cost_per_sqm': [], 'outliers': [], 'message': 'Ingen eiendommer med total_area og kostnader'}

        cost_per_sqm_list = []
        for p in with_area:
            cps = p['total_costs'] / p['total_area']
            cost_per_sqm_list.append({
                'property': p['name'],
                'cost_per_sqm': round(cps, 2),
                'total_costs': p['total_costs'],
                'total_area': p['total_area'],
            })
        cost_per_sqm_list.sort(key=lambda x: -x['cost_per_sqm'])

        values = [x['cost_per_sqm'] for x in cost_per_sqm_list]
        if len(values) >= 3:
            mean_cps = statistics.mean(values)
            stdev = statistics.stdev(values)
            outliers = [
                {**x, 'deviation': round((x['cost_per_sqm'] - mean_cps) / stdev, 2) if stdev > 0 else 0}
                for x in cost_per_sqm_list
                if stdev > 0 and abs(x['cost_per_sqm'] - mean_cps) > 2 * stdev
            ]
        else:
            outliers = []

        return {
            'cost_per_sqm': cost_per_sqm_list[:20],
            'outliers': outliers[:15],
        }

    @staticmethod
    def _provider_category_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Provider-kategori-mønstre: matrise provider x type, leverandørspesialisering."""
        provider_categories: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for p in prop_data_list:
            for exp in p['expenses']:
                prov = exp.get('provider', 'Ukjent')
                cat = exp.get('type', 'Ukjent')
                try:
                    amount = float(exp.get('amount', 0) or 0)
                except (TypeError, ValueError):
                    amount = 0
                if prov and prov != 'Ukjent':
                    provider_categories[prov][cat] += amount

        matrix = []
        for prov, cats in provider_categories.items():
            total = sum(cats.values())
            if total <= 0:
                continue
            dominant = max(cats.items(), key=lambda x: x[1])
            specialization = (dominant[1] / total) * 100
            matrix.append({
                'provider': prov,
                'total_amount': total,
                'categories': dict(cats),
                'dominant_category': dominant[0],
                'specialization_pct': round(specialization, 1),
            })
        matrix.sort(key=lambda x: -x['total_amount'])

        return {
            'provider_category_matrix': matrix[:25],
        }

    @staticmethod
    def _cluster_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Cluster-analyse: k-means på kostnadsvektorer (andel per kategori)."""
        try:
            from sklearn.cluster import KMeans
            import numpy as np
        except ImportError:
            return {'clusters': [], 'message': 'scikit-learn ikke tilgjengelig'}

        # Bygg vektorer: andel per kategori (property, operations, investment, other)
        from app.services.analytics.cost_analysis_service import categorize_expense, CostCategory

        vectors = []
        names = []
        for p in prop_data_list:
            if p['total_costs'] <= 0:
                continue
            vec = [0.0, 0.0, 0.0, 0.0]
            for cat, amount in p['cost_by_category'].items():
                c = categorize_expense(cat)
                idx = ['property', 'operations', 'investment', 'other'].index(c.value)
                vec[idx] += amount
            total = sum(vec)
            if total > 0:
                vec = [v / total for v in vec]
                vectors.append(vec)
                names.append(p['name'])

        if len(vectors) < 5:
            return {'clusters': [], 'message': 'For få eiendommer med kostnader for clustering'}

        X = np.array(vectors)
        n_clusters = min(5, len(vectors) - 1)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        cluster_names = ['property_dominant', 'operations_dominant', 'investment_dominant', 'balanced', 'other_dominant']
        clusters = []
        for i in range(n_clusters):
            mask = labels == i
            props_in_cluster = [names[j] for j in range(len(names)) if mask[j]]
            center = kmeans.cluster_centers_[i]
            dominant_idx = np.argmax(center)
            label = cluster_names[dominant_idx] if dominant_idx < len(cluster_names) else f'cluster_{i}'
            clusters.append({
                'cluster_id': i,
                'label': label,
                'property_count': len(props_in_cluster),
                'properties': props_in_cluster[:15],
                'center': [round(c, 3) for c in center.tolist()],
            })
        return {'clusters': clusters}

    @staticmethod
    def _building_age_patterns(prop_data_list: List[Dict], current_year: int) -> Dict[str, Any]:
        """Bygningsalder vs kostnad: eldre bygg har ofte høyere vedlikeholdskostnader."""
        age_buckets = {'<10': [], '10-30': [], '30-50': [], '>50': [], 'unknown': []}
        for p in prop_data_list:
            if p['total_costs'] <= 0:
                continue
            cy = p.get('construction_year')
            if cy is not None:
                try:
                    cy = int(cy) if cy else None
                except (TypeError, ValueError):
                    cy = None
            if cy and cy > 0:
                age = current_year - int(cy)
                if age < 10:
                    bucket = '<10'
                elif age <= 30:
                    bucket = '10-30'
                elif age <= 50:
                    bucket = '30-50'
                else:
                    bucket = '>50'
            else:
                bucket = 'unknown'
            age_buckets[bucket].append({'name': p['name'], 'costs': p['total_costs'], 'age': current_year - int(cy) if cy else None})

        by_bucket = []
        for bucket, items in age_buckets.items():
            if items:
                costs_list = [x['costs'] for x in items]
                by_bucket.append({
                    'age_bucket': bucket,
                    'property_count': len(items),
                    'avg_costs': round(statistics.mean(costs_list), 0),
                    'total_costs': sum(costs_list),
                })
        return {'by_age_bucket': sorted(by_bucket, key=lambda x: -x['property_count'])}

    @staticmethod
    def _energy_label_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Energimerking vs kostnad: dårlig merking ofte høyere strøm/oppvarming."""
        by_label: Dict[str, List[float]] = defaultdict(list)
        for p in prop_data_list:
            if p['total_costs'] <= 0:
                continue
            label = (p.get('energy_label') or 'Ukjent').strip().upper() or 'Ukjent'
            by_label[label].append(p['total_costs'])

        result = [{'label': k, 'property_count': len(v), 'avg_costs': round(statistics.mean(v), 0)}
                  for k, v in by_label.items() if v]
        return {'by_energy_label': sorted(result, key=lambda x: -x['property_count'])}

    @staticmethod
    def _usage_type_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Brukstype vs kostnad (Property.usage og units.usage_type)."""
        by_usage: Dict[str, List[float]] = defaultdict(list)
        for p in prop_data_list:
            if p['total_costs'] <= 0:
                continue
            usage = p.get('usage') or 'Ukjent'
            by_usage[usage].append(p['total_costs'])
            for ut in p.get('usage_types', []):
                by_usage[f"Unit:{ut}"].append(p['total_costs'])

        result = [{'usage': k, 'property_count': len(v), 'avg_costs': round(statistics.mean(v), 0)}
                  for k, v in by_usage.items() if v]
        return {'by_usage': sorted(result, key=lambda x: -x['property_count'])[:15]}

    @staticmethod
    def _cost_per_sqm_by_category(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Kostnad per kvm per kategori (property, operations, investment)."""
        from app.services.analytics.cost_analysis_service import categorize_expense, CostCategory

        with_area = [p for p in prop_data_list if p['total_area'] > 0 and p['total_costs'] > 0]
        if not with_area:
            return {'by_category': [], 'message': 'Ingen eiendommer med total_area'}

        by_cat: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for p in with_area:
            for cat_type, amount in p['cost_by_category'].items():
                c = categorize_expense(cat_type)
                cps = amount / p['total_area']
                by_cat[c.value].append((p['name'], cps))

        result = []
        for cat, items in by_cat.items():
            if items:
                values = [x[1] for x in items]
                result.append({
                    'category': cat,
                    'property_count': len(items),
                    'avg_per_sqm': round(statistics.mean(values), 2),
                    'max_property': max(items, key=lambda x: x[1])[0] if items else None,
                })
        return {'by_category': sorted(result, key=lambda x: -x['property_count'])}

    @staticmethod
    async def _budget_variance_patterns(db: AsyncSession, prop_data_list: List[Dict], year: int) -> Dict[str, Any]:
        """Budsjett vs faktisk: eiendommer med størst varians."""
        try:
            from app.models.financial_models import Budget, GLTransaction

            # Budget total per property for year
            stmt_b = select(Budget.property_id, func.sum(Budget.amount).label('total')).where(
                Budget.year == year
            ).group_by(Budget.property_id)
            res_b = await db.execute(stmt_b)
            budget_by_prop = {str(r.property_id): r.total for r in res_b.fetchall()}

            # GL actual per property
            stmt_a = select(GLTransaction.property_id, func.sum(GLTransaction.belop).label('total')).where(
                GLTransaction.ar == year
            ).group_by(GLTransaction.property_id)
            res_a = await db.execute(stmt_a)
            actual_by_prop = {str(r.property_id): r.total for r in res_a.fetchall()}

            variances = []
            for p in prop_data_list:
                pid = p['property_id']
                budget = budget_by_prop.get(pid, 0) or 0
                actual = actual_by_prop.get(pid, 0) or 0
                if budget > 0 or actual > 0:
                    var = budget - actual
                    var_pct = (var / budget * 100) if budget > 0 else 0
                    variances.append({
                        'property': p['name'],
                        'budget': budget,
                        'actual': actual,
                        'variance': var,
                        'variance_pct': round(var_pct, 1),
                    })
            variances.sort(key=lambda x: -abs(x['variance']))
            return {'year': year, 'variances': variances[:20], 'property_count': len(variances)}
        except Exception:
            return {'variances': [], 'message': 'Budget/GLTransaction ikke tilgjengelig'}

    @staticmethod
    def _risk_cost_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Risiko-kostnad-kobling: prioriteringsindeks (risiko × årskostnad)."""
        with_risk = [p for p in prop_data_list if p.get('risk_score') is not None and p['total_costs'] > 0]
        if not with_risk:
            return {'priority_list': [], 'message': 'Ingen eiendommer med risikoscore og kostnader'}

        annual_cost = lambda p: p['total_costs'] + p['total_rent']
        for p in with_risk:
            p['priority_index'] = (p['risk_score'] or 0) * annual_cost(p)

        sorted_list = sorted(with_risk, key=lambda x: -x['priority_index'])
        return {
            'priority_list': [
                {'property': p['name'], 'risk_score': p['risk_score'], 'annual_cost': annual_cost(p), 'priority_index': round(p['priority_index'], 0)}
                for p in sorted_list[:20]
            ]
        }

    @staticmethod
    def _supplier_overlap_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Leverandørportefølje-overlap: eiendommer som deler samme leverandører (Jaccard)."""
        prop_providers = {p['name']: p['providers'] for p in prop_data_list if p['providers']}
        if len(prop_providers) < 2:
            return {'overlap_pairs': [], 'message': 'For få eiendommer med leverandører'}

        pairs = []
        names = list(prop_providers.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                set_a = prop_providers[a]
                set_b = prop_providers[b]
                if not set_a or not set_b:
                    continue
                intersection = len(set_a & set_b)
                union = len(set_a | set_b)
                jaccard = intersection / union if union > 0 else 0
                if jaccard > 0.3:  # Min 30% overlap
                    pairs.append({'property_a': a, 'property_b': b, 'jaccard': round(jaccard, 2), 'shared_count': intersection})
        pairs.sort(key=lambda x: -x['jaccard'])
        return {'overlap_pairs': pairs[:15]}

    @staticmethod
    def _missing_data_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Manglende data-mønstre: eiendommer uten kostnader, husleie, date, total_area."""
        no_costs = [p['name'] for p in prop_data_list if p['total_rent'] > 100000 and p['total_costs'] == 0]
        no_rent = [p['name'] for p in prop_data_list if p['total_costs'] > 100000 and p['total_rent'] == 0]
        no_date = 0
        total_exp = 0
        for p in prop_data_list:
            for e in p['expenses']:
                total_exp += 1
                if not FinancialAnalysisService._parse_year_from_date(e.get('date')):
                    no_date += 1
        no_area = [p['name'] for p in prop_data_list if (p['total_area'] or 0) <= 0 and p['total_costs'] > 0]
        return {
            'high_rent_no_costs': no_costs[:15],
            'high_costs_no_rent': no_rent[:15],
            'expenses_without_date': no_date,
            'total_expenses': total_exp,
            'costs_without_area': no_area[:15],
        }

    @staticmethod
    def _municipality_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Kostnader per kommune/postnummer."""
        by_municipality: Dict[str, Dict] = defaultdict(lambda: {'costs': 0.0, 'count': 0, 'properties': []})
        for p in prop_data_list:
            m = p.get('municipality') or 'Ukjent'
            by_municipality[m]['costs'] += p['total_costs']
            by_municipality[m]['count'] += 1
            if p['total_costs'] > 0:
                by_municipality[m]['properties'].append(p['name'])

        result = [{'municipality': k, 'property_count': v['count'], 'total_costs': v['costs'], 'avg_costs': v['costs'] / v['count'] if v['count'] else 0}
                  for k, v in by_municipality.items()]
        return {'by_municipality': sorted(result, key=lambda x: -x['total_costs'])[:15]}

    @staticmethod
    def _center_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Kostnader per senter/center."""
        by_center: Dict[str, Dict] = defaultdict(lambda: {'costs': 0.0, 'count': 0})
        for p in prop_data_list:
            c = p.get('center_id') or 'Ingen senter'
            by_center[c]['costs'] += p['total_costs']
            by_center[c]['count'] += 1

        result = [{'center_id': k, 'property_count': v['count'], 'total_costs': v['costs']}
                  for k, v in by_center.items() if v['count'] > 0]
        return {'by_center': sorted(result, key=lambda x: -x['total_costs'])}

    @staticmethod
    def _transaction_density_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Transaksjonstetthet: antall poster per eiendom, få store vs mange små."""
        with_costs = [p for p in prop_data_list if p['total_costs'] > 0]
        if not with_costs:
            return {'low_density': [], 'high_density': [], 'avg_per_expense': []}

        avg_per_exp = [(p['name'], p['total_costs'] / p['num_expenses']) for p in with_costs if p['num_expenses'] > 0]
        avg_per_exp.sort(key=lambda x: -x[1])
        low_density = [p['name'] for p in with_costs if p['num_expenses'] <= 2 and p['total_costs'] > 100000]
        high_density = [p['name'] for p in with_costs if p['num_expenses'] >= 20]
        return {
            'low_density_few_transactions': low_density[:15],
            'high_density_many_transactions': high_density[:15],
            'highest_avg_per_expense': [{'property': n, 'avg': round(a, 0)} for n, a in avg_per_exp[:10]],
        }

    @staticmethod
    def _category_diversification_patterns(prop_data_list: List[Dict]) -> Dict[str, Any]:
        """Kategori-diversifikasjon: antall kategorier per eiendom."""
        single_cat = [p for p in prop_data_list if len(p['categories']) == 1 and p['total_costs'] > 100000]
        many_cat = [p for p in prop_data_list if len(p['categories']) >= 8]
        return {
            'single_category_high_costs': [{'property': p['name'], 'category': list(p['categories'])[0] if p['categories'] else ''} for p in single_cat[:15]],
            'many_categories': [{'property': p['name'], 'category_count': len(p['categories'])} for p in many_cat[:15]],
        }

    @staticmethod
    async def get_global_supplier_stats(db: AsyncSession, year: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate supplier statistics across all properties from GL transactions"""
        try:
            from app.models.financial_models import GLTransaction

            # 1. Build property_id → display name map
            prop_rows = (await db.execute(
                select(Property.property_id, Property.name, Property.address)
            )).fetchall()
            prop_map = {r[0]: r[1] or r[2] or str(r[0]) for r in prop_rows}

            # 2. Aggregate per (leverandor_navn, konto_navn, property_id)
            stmt = (
                select(
                    GLTransaction.leverandor_navn,
                    GLTransaction.konto_navn,
                    GLTransaction.property_id,
                    func.sum(GLTransaction.belop).label('total'),
                )
                .where(
                    GLTransaction.leverandor_navn.isnot(None),
                    GLTransaction.leverandor_navn != '',
                    GLTransaction.belop != 0,
                )
                .group_by(
                    GLTransaction.leverandor_navn,
                    GLTransaction.konto_navn,
                    GLTransaction.property_id,
                )
            )
            if year:
                year_stmt = stmt.where(GLTransaction.ar == year)
                rows = (await db.execute(year_stmt)).fetchall()
                # Fallback: if no data for requested year, return all years
                if not rows:
                    rows = (await db.execute(stmt)).fetchall()
            else:
                rows = (await db.execute(stmt)).fetchall()

            # 3. Build supplier_stats dict
            supplier_stats: Dict[str, Any] = defaultdict(lambda: {
                'total_amount': 0.0,
                'property_count': 0,
                'properties_seen': set(),
                'category': 'Ukjent',
                'category_amounts': {},   # track amount per category → pick primary by max
                'properties': [],
            })
            total_portfolio_cost = 0.0

            for row in rows:
                supplier = row.leverandor_navn
                account = row.konto_navn or 'Ukjent'
                prop_id = row.property_id
                amount = float(row.total)

                total_portfolio_cost += amount

                stats = supplier_stats[supplier]
                stats['total_amount'] += amount

                # Accumulate per-category amounts so we can pick the dominant one later
                if account != 'Ukjent':
                    stats['category_amounts'][account] = stats['category_amounts'].get(account, 0.0) + amount

                if prop_id not in stats['properties_seen']:
                    stats['property_count'] += 1
                    stats['properties_seen'].add(prop_id)

                stats['properties'].append({
                    'property_id': str(prop_id) if prop_id else '',
                    'name': prop_map.get(prop_id, str(prop_id) if prop_id else 'Ukjent'),
                    'amount': amount,
                    'category': account,
                    'date': None,
                })

            # 4. Sort and return (same interface as before)
            sorted_suppliers = sorted(
                [
                    {
                        'name': k,
                        # Primary category = the account with the highest aggregated amount
                        'category': max(v['category_amounts'], key=v['category_amounts'].get) if v['category_amounts'] else 'Ukjent',
                        'total_amount': v['total_amount'],
                        'property_count': v['property_count'],
                        'details': sorted(v['properties'], key=lambda x: -x['amount']),
                    }
                    for k, v in supplier_stats.items()
                ],
                key=lambda x: -x['total_amount'],
            )

            return {
                'total_portfolio_cost': total_portfolio_cost,
                'supplier_count': len(sorted_suppliers),
                'suppliers': sorted_suppliers,
            }
        except Exception as e:
            return {'total_portfolio_cost': 0.0, 'supplier_count': 0, 'suppliers': [], 'error': str(e)}
