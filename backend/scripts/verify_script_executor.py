#!/usr/bin/env python3
"""Verify the run_analysis_script MCP tool works correctly."""
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from app.services.mcp.handler import mcp_handler

async def verify_script_executor():
    print("--- Verifying Script Executor Tool ---")
    
    # Test 1: audit_contracts (no params needed)
    print("\n1. Testing audit_contracts...")
    try:
        result = await mcp_handler.execute_tool("run_analysis_script", {
            "script_key": "audit_contracts"
        })
        if "COMPREHENSIVE CONTRACT DATA AUDIT" in result:
            print("   [PASS] audit_contracts executed successfully")
            print(f"   Output snippet: {result[:200]}...")
        else:
            print(f"   [FAIL] Unexpected output:\n{result[:500]}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 2: cost_analyzer_search with parameter
    print("\n2. Testing cost_analyzer_search with query='Alta'...")
    try:
        result = await mcp_handler.execute_tool("run_analysis_script", {
            "script_key": "cost_analyzer_search",
            "params": {"query": "Alta"}
        })
        if "Found" in result or "matches" in result:
            print("   [PASS] cost_analyzer_search executed successfully")
            print(f"   Output snippet: {result[:200]}...")
        else:
            print(f"   [FAIL] Unexpected output:\n{result[:500]}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 3: cost_analyzer_anomalies
    print("\n3. Testing cost_analyzer_anomalies...")
    try:
        result = await mcp_handler.execute_tool("run_analysis_script", {
            "script_key": "cost_analyzer_anomalies"
        })
        if "COST ANOMALIES" in result or "High Rent" in result:
            print("   [PASS] cost_analyzer_anomalies executed successfully")
            print(f"   Output snippet: {result[:200]}...")
        else:
            print(f"   [FAIL] Unexpected output:\n{result[:500]}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    print("\n✅ Script Executor verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_script_executor())
