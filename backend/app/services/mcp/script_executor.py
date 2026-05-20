import asyncio
import subprocess
import os
import json

# Whitelist of safe analysis scripts (READ-ONLY operations only)
SAFE_ANALYSIS_SCRIPTS = {
    # === AUDIT SCRIPTS ===
    "audit_contracts": {
        "path": "backend/scripts/audit_contracts.py",
        "description": "Comprehensive contract data audit",
        "args": []
    },
    "audit_data_quality": {
        "path": "backend/scripts/audit_data_quality.py",
        "description": "Complete data quality audit across all tables",
        "args": []
    },
    "audit_missing_financial_data": {
        "path": "backend/scripts/audit_missing_financial_data.py",
        "description": "Find contracts and properties missing financial data",
        "args": []
    },
    
    # === COST ANALYSIS ===
    "cost_analyzer_search": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Search for properties by name",
        "args": ["search", "{query}"]
    },
    "cost_analyzer_details": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Detailed cost breakdown for a property",
        "args": ["details", "{property_name}"]
    },
    "cost_analyzer_compare": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Compare multiple properties",
        "args": ["compare", "{prop1}", "{prop2}"]
    },
    "cost_analyzer_region": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Regional cost statistics",
        "args": ["region", "{region_name}"]
    },
    "cost_analyzer_anomalies": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Find cost anomalies",
        "args": ["anomalies"]
    },
    "cost_analyzer_top": {
        "path": "backend/scripts/cost_analyzer.py",
        "description": "Top N properties by rent/costs/total",
        "args": ["top", "{n}", "{by}"]
    },
    
    # === ANALYSIS SCRIPTS ===
    "analyze_contracts": {
        "path": "backend/scripts/analyze_contracts.py",
        "description": "Analyze contract data patterns",
        "args": []
    },
    "analyze_contract_types": {
        "path": "backend/scripts/analyze_contract_types.py",
        "description": "Analyze distribution of contract types",
        "args": []
    },
    "analyze_price_per_sqm": {
        "path": "backend/scripts/analyze_price_per_sqm.py",
        "description": "Analyze price per square meter",
        "args": []
    },
    "analyze_usage_types": {
        "path": "backend/scripts/analyze_usage_types.py",
        "description": "Analyze property usage types",
        "args": []
    },
    "analyze_regional_integrity": {
        "path": "backend/scripts/analyze_regional_integrity.py",
        "description": "Check regional data integrity",
        "args": []
    },
    "analyze_rent_discrepancy": {
        "path": "backend/scripts/analyze_rent_discrepancy.py",
        "description": "Find discrepancies in rent data",
        "args": []
    },
    "analyze_negative_amounts": {
        "path": "backend/scripts/analyze_negative_amounts.py",
        "description": "Find and analyze negative amounts",
        "args": []
    },
    "ml_financial_forecasting": {
        "path": "backend/scripts/ml_financial_analysis.py",
        "description": "ML-based financial forecasting and anomaly detection",
        "args": ["{target}", "--type", "forecast"]
    },
    "ml_financial_anomalies": {
        "path": "backend/scripts/ml_financial_analysis.py",
        "description": "ML-based spending anomaly detection",
        "args": ["{target}", "--type", "anomalies"]
    },
    "ml_financial_patterns": {
        "path": "backend/scripts/ml_financial_analysis.py",
        "description": "ML-based pattern recognition and common cost structures",
        "args": ["--type", "patterns"]
    },
    
    # === CHECK SCRIPTS ===
    "check_data_quality": {
        "path": "backend/scripts/check_data_quality.py",
        "description": "Quick data quality check",
        "args": []
    },
    "check_contract_count": {
        "path": "backend/scripts/check_contract_count.py",
        "description": "Count contracts in database",
        "args": []
    },
    "check_properties_without_costs": {
        "path": "backend/scripts/check_properties_without_costs.py",
        "description": "Find properties with no cost data",
        "args": []
    },
    "check_property_details": {
        "path": "backend/scripts/check_property_details.py",
        "description": "Show details for specific property",
        "args": []
    },
    "check_all_duplicates": {
        "path": "backend/scripts/check_all_duplicates.py",
        "description": "Find duplicate entries across tables",
        "args": []
    },
    "check_hms_schema": {
        "path": "backend/scripts/check_hms_schema.py",
        "description": "Verify HMS database schema",
        "args": []
    },
    "check_internal_control_cases": {
        "path": "backend/scripts/check_internal_control_cases.py",
        "description": "Check internal control cases",
        "args": []
    },
    
    # === VERIFY SCRIPTS ===
    "verify_data": {
        "path": "backend/scripts/verify_data.py",
        "description": "Verify overall data integrity",
        "args": []
    },
    "verify_data_integrity": {
        "path": "backend/scripts/verify_data_integrity.py",
        "description": "Deep data integrity verification",
        "args": []
    },
    "verify_enrichment": {
        "path": "backend/scripts/verify_enrichment.py",
        "description": "Verify Bufdir enrichment data",
        "args": []
    },
    "verify_historical_data": {
        "path": "backend/scripts/verify_historical_data.py",
        "description": "Verify historical financial data",
        "args": []
    },
    "verify_property_financials": {
        "path": "backend/scripts/verify_property_financials.py",
        "description": "Verify property financial data",
        "args": []
    },
    "verify_vector_search": {
        "path": "backend/scripts/verify_vector_search.py",
        "description": "Test vector search functionality",
        "args": []
    },
    "verify_checklists": {
        "path": "backend/scripts/verify_checklists.py",
        "description": "Verify HMS checklists",
        "args": []
    },
    
    # === DIAGNOSE SCRIPTS ===
    "diagnose_contract": {
        "path": "backend/scripts/diagnose_contract.py",
        "description": "Diagnose specific contract issues",
        "args": []
    },
    
    # === INSPECT SCRIPTS ===
    "inspect_contracts": {
        "path": "backend/scripts/inspect_contracts.py",
        "description": "Inspect contract data",
        "args": []
    },
    "inspect_financial_data": {
        "path": "backend/scripts/inspect_financial_data.py",
        "description": "Inspect financial data quality",
        "args": []
    },
    "inspect_outliers": {
        "path": "backend/scripts/inspect_outliers.py",
        "description": "Find statistical outliers",
        "args": []
    },
    "inspect_schema": {
        "path": "backend/scripts/inspect_schema.py",
        "description": "Inspect database schema",
        "args": []
    },
    
    # === COMPARE SCRIPTS ===
    "compare_csv_portfolio": {
        "path": "backend/scripts/compare_csv_portfolio.py",
        "description": "Compare CSV with database portfolio",
        "args": []
    },
    
    # === COUNT SCRIPTS ===
    "count_contracts": {
        "path": "backend/scripts/count_contracts.py",
        "description": "Count contracts by category",
        "args": []
    },
    "count_unknown_parties": {
        "path": "backend/scripts/count_unknown_parties.py",
        "description": "Count unknown party entries",
        "args": []
    },
    
    # === SHOW/DISPLAY SCRIPTS ===
    "show_all_properties_contracts": {
        "path": "backend/scripts/show_all_properties_contracts.py",
        "description": "Show all properties with contracts",
        "args": []
    },
    "show_database_schema": {
        "path": "backend/scripts/show_database_schema.py",
        "description": "Display complete database schema",
        "args": []
    },
    
    # === EXPORT/REPORT SCRIPTS ===
    "export_overview_md": {
        "path": "backend/scripts/export_overview_md.py",
        "description": "Export portfolio overview as Markdown",
        "args": []
    },
    "export_properties_contracts": {
        "path": "backend/scripts/export_properties_contracts.py",
        "description": "Export properties and contracts data",
        "args": []
    },
    "export_financial_table": {
        "path": "backend/scripts/export_financial_table.py",
        "description": "Export financial data table",
        "args": []
    },
    
    # === COST MONITORING ===
    "cost_monitor": {
        "path": "backend/scripts/cost_monitor.py",
        "description": "Monitor cost trends and alerts",
        "args": []
    },
    
    # === PATTERN ANALYSIS ===
    "pattern_analyzer": {
        "path": "backend/scripts/pattern_analyzer.py",
        "description": "Advanced pattern analysis across data",
        "args": []
    },
    
    # === LIST SCRIPTS ===
    "list_properties": {
        "path": "backend/scripts/list_properties.py",
        "description": "List all properties",
        "args": []
    }
}

async def execute_analysis_script(script_key: str, params: dict = None, preview_only: bool = False):
    """
    Execute a whitelisted analysis script safely.
    
    Args:
        script_key: Key from SAFE_ANALYSIS_SCRIPTS
        params: Dictionary of parameters to substitute in args template
        preview_only: If True, return command preview without executing
    
    Returns:
        Script output as string OR preview dict if preview_only=True
    """
    if script_key not in SAFE_ANALYSIS_SCRIPTS:
        return f"Error: Script '{script_key}' not in whitelist. Available: {', '.join(SAFE_ANALYSIS_SCRIPTS.keys())}"
    
    script_config = SAFE_ANALYSIS_SCRIPTS[script_key]
    script_path = script_config["path"]
    args_template = script_config["args"]
    
    # Build full path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    full_path = os.path.join(project_root, script_path)
    
    if not os.path.exists(full_path):
        return f"Error: Script file not found at {full_path}"
    
    # Substitute parameters in args
    params = params or {}
    args = []
    for arg in args_template:
        if "{" in arg and "}" in arg:
            # Extract placeholder name
            placeholder = arg.strip("{}")
            if placeholder in params:
                args.append(str(params[placeholder]))
            else:
                return f"Error: Missing required parameter '{placeholder}'"
        else:
            args.append(arg)
    
    # Build command
    cmd = ["python3", full_path] + args
    
    # Preview mode: Just return what would be executed
    if preview_only:
        return {
            "script_key": script_key,
            "description": script_config["description"],
            "command": " ".join(cmd),
            "path": full_path,
            "params": params
        }
    
    # Execute script
    try:
        # Run with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_root
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
        
        output = stdout.decode('utf-8')
        errors = stderr.decode('utf-8')
        
        if process.returncode != 0:
            return f"Script failed with exit code {process.returncode}:\n{errors}\n{output}"
        
        return output if output else "Script executed successfully (no output)"
        
    except asyncio.TimeoutError:
        return "Error: Script execution timeout (60s limit)"

def list_available_scripts() -> dict:
    """
    List all available whitelisted scripts with their descriptions.
    
    Returns:
        Dictionary mapping script_key to description
    """
    return {
        key: config["description"] 
        for key, config in SAFE_ANALYSIS_SCRIPTS.items()
    }

def get_script_info(script_key: str) -> dict:
    """
    Get detailed information about a specific script.
    
    Args:
        script_key: Key from SAFE_ANALYSIS_SCRIPTS
        
    Returns:
        Dictionary with script details or None if not found
    """
    if script_key not in SAFE_ANALYSIS_SCRIPTS:
        return None
        
    config = SAFE_ANALYSIS_SCRIPTS[script_key]
    return {
        "key": script_key,
        "description": config["description"],
        "args": config["args"],
        "path": config["path"]
    }
