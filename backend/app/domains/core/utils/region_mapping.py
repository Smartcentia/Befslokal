"""Region and County Mapping Utilities

Standardformat: Nord, Midt-Norge, Vest, Sør, Øst, Bufdir (se docs/REGION_STANDARD.md).
Bufdir er eget direktorat, ikke en region.
"""
from typing import Dict, List

# Kanoniske regioner og direktorat
REGIONS_AND_DIRECTORATE = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir"]

# Mapping from county codes to operational regions (standardformat)
COUNTY_TO_REGION: Dict[str, str] = {
    # Nord
    "18": "Nord", "55": "Nord", "56": "Nord",
    "Nordland": "Nord", "Troms": "Nord", "Finnmark": "Nord",
    "Troms og Finnmark": "Nord",
    "01 - Nordland": "Nord", "02 - Troms og Finnmark": "Nord",
    "Region Nord": "Nord", "Nord": "Nord",
    
    # Midt-Norge
    "50": "Midt-Norge", "15": "Midt-Norge",
    "Trøndelag": "Midt-Norge", "Møre og Romsdal": "Midt-Norge",
    "03 - Trøndelag": "Midt-Norge", "04 - Møre og Romsdal": "Midt-Norge",
    "Region Midt": "Midt-Norge", "Region Midt-Norge": "Midt-Norge",
    "Midt-Norge": "Midt-Norge",
    
    # Vest
    "46": "Vest", "11": "Vest",
    "Vestland": "Vest", "Rogaland": "Vest",
    "05 - Vestland": "Vest", "06 - Rogaland": "Vest",
    "Region Vest": "Vest", "Vest": "Vest",
    "03 - Vest": "Vest",
    
    # Sør
    "42": "Sør", "38": "Sør", "40": "Sør", "07": "Sør", "08": "Sør",
    "Agder": "Sør", "Vestfold": "Sør", "Telemark": "Sør",
    "Vestfold og Telemark": "Sør",
    "07 - Agder": "Sør", "08 - Vestfold og Telemark": "Sør",
    "Region Sør": "Sør", "Sør": "Sør",
    "04 - Sør": "Sør",
    
    # Øst
    "03": "Øst", "30": "Øst", "31": "Øst", "32": "Øst", "33": "Øst", "34": "Øst",
    "Oslo": "Øst", "Akershus": "Øst", "Buskerud": "Øst", "Østfold": "Øst", "Innlandet": "Øst",
    "Viken": "Øst", "Oslo og Viken": "Øst",
    "09 - Viken": "Øst", "10 - Innlandet": "Øst", "11 - Oslo og Viken": "Øst",
    "Region Øst": "Øst", "Øst": "Øst",
    "05 - Øst": "Øst",
    
    # Bufdir – eget direktorat (ikke region)
    "12": "Bufdir",
    "06 - Bufdir": "Bufdir",
    "12 - Bufdir": "Bufdir",
    "Bufdir": "Bufdir",
    "Region Bufdir": "Bufdir",
}

# Friendly display names for counties (2024 Split)
COUNTY_DISPLAY_NAMES: Dict[str, str] = {
    "18": "Nordland", "55": "Troms", "56": "Finnmark",
    "50": "Trøndelag", "15": "Møre og Romsdal",
    "46": "Vestland", "11": "Rogaland",
    "42": "Agder", "38": "Vestfold", "40": "Telemark",
    "03": "Oslo", "31": "Østfold", "32": "Akershus", "33": "Buskerud", "34": "Innlandet",
    # Legacy / Combined
    "Nordland": "Nordland",
    "Troms og Finnmark": "Troms og Finnmark",
    "Trøndelag": "Trøndelag",
    "Møre og Romsdal": "Møre og Romsdal",
    "Vestland": "Vestland",
    "Rogaland": "Rogaland",
    "Agder": "Agder",
    "Vestfold og Telemark": "Vestfold og Telemark",
    "Oslo": "Oslo",
    "Viken": "Viken",
    "Innlandet": "Innlandet",
}


def get_operational_region(county: str) -> str:
    """Convert county code to operational region"""
    return COUNTY_TO_REGION.get(county, county)


def get_county_display_name(county: str) -> str:
    """Get friendly display name for county"""
    return COUNTY_DISPLAY_NAMES.get(county, county)


def group_by_operational_regions(county_data: List[Dict]) -> List[Dict]:
    """
    Group county-level data by operational regions
    
    Args:
        county_data: List of dicts with 'region' (county code), 'contract_count', 'total_cost', etc.
    
    Returns:
        List of dicts grouped by operational region
    """
    region_groups = {}
    
    for item in county_data:
        county = item.get('region', '')
        operational_region = get_operational_region(county)
        
        if operational_region not in region_groups:
            region_groups[operational_region] = {
                'region': operational_region,
                'contract_count': 0,
                'total_cost': 0,
                'property_count': 0,
            }
        
        region_groups[operational_region]['contract_count'] += item.get('contract_count', 0)
        region_groups[operational_region]['total_cost'] += item.get('total_cost', 0)
        region_groups[operational_region]['property_count'] += item.get('property_count', 0)
    
    # Convert to list and sort
    result = list(region_groups.values())
    result.sort(key=lambda x: x['total_cost'], reverse=True)
    
    return result
