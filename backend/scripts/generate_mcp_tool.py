import asyncio
import httpx
import json
import sys
from typing import Dict, Any

# Configuration
GATEWAY_URL = "http://localhost:5555"

async def generate_tool_code(tool_name: str):
    print(f"--- Generating Code for MCP Tool: {tool_name} ---")
    
    async with httpx.AsyncClient() as client:
        # 1. Fetch all tools to find the specific one
        try:
            response = await client.get(f"{GATEWAY_URL}/tools")
            if response.status_code != 200:
                print(f"Error connecting to gateway: {response.status_code}")
                return

            data = response.json()
            tools = data.get("tools", [])
            
            target_tool = next((t for t in tools if t["name"] == tool_name), None)
            
            if not target_tool:
                print(f"Tool '{tool_name}' not found in gateway.")
                print("Available tools:")
                for t in tools:
                    print(f"- {t['name']}")
                return

            # 2. Extract Schema
            name = target_tool["name"]
            description = target_tool.get("description", "No description provided.")
            schema = target_tool.get("inputSchema", {})
            
            # 3. Generate Python Code
            print("\n✅ Found tool! Here is your Python code for 'backend/app/services/mcp/handler.py':\n")
            print("-" * 60)
            
            # Imports generator (simple heuristic)
            print("# Add imports if needed:")
            print("from typing import Any, Dict")
            print("\n")
            
            # Decorator
            print("@mcp_handler.register_tool(")
            print(f'    name="{name}",')
            print(f'    description="{description}",')
            print(f"    parameters={json.dumps(schema, indent=4)}")
            print(")")
            
            # Function Signature
            props = schema.get("properties", {})
            params = []
            for prop_name, prop_def in props.items():
                py_type = "str"
                if prop_def.get("type") == "integer": py_type = "int"
                elif prop_def.get("type") == "number": py_type = "float"
                elif prop_def.get("type") == "boolean": py_type = "bool"
                elif prop_def.get("type") == "array": py_type = "list"
                elif prop_def.get("type") == "object": py_type = "dict"
                
                # Check required
                if prop_name not in schema.get("required", []):
                    params.append(f"{prop_name}: {py_type} = None")
                else:
                    params.append(f"{prop_name}: {py_type}")
            
            param_str = ", ".join(params)
            
            print(f"async def {name}_tool({param_str}):")
            print('    """')
            print(f'    Implementation of {name}.')
            print(f'    Docs: {description}')
            print('    """')
            print('    # TODO: Implement the actual logic here.')
            print('    # If this was an external API, use httpx to call it.')
            print('    # Example:')
            print('    # async with httpx.AsyncClient() as client:')
            print('    #     resp = await client.get("https://api.example.com/...")')
            print('    #     return resp.json()')
            print('\n    return {"status": "not_implemented", "message": "This tool needs logic!"}')
            
            print("-" * 60)
            print("\nCopy the code above and paste it into 'backend/app/services/mcp/handler.py'")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_tool_code.py <tool_name>")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    asyncio.run(generate_tool_code(tool_name))
