import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self):
        self.gateway_url = settings.DOCKER_MCP_GATEWAY_URL
        self._client = httpx.AsyncClient(timeout=30.0)
        self._remote_servers = self._load_remote_servers()

    def _load_remote_servers(self) -> Dict[str, str]:
        """Load remote server mappings from JSON config."""
        try:
            if not settings.MCP_SERVERS_CONFIG:
                return {}
            return json.loads(settings.MCP_SERVERS_CONFIG)
        except Exception as e:
            logger.error(f"Failed to parse MCP_SERVERS_CONFIG: {e}")
            return {}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lists available tools. 
        Combines tools from Docker Gateway (if active) and configured Remote Servers.
        """
        all_tools = []
        
        # 1. Try Docker Gateway (Local)
        try:
            response = await self._client.get(f"{self.gateway_url}/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                # Mark them as 'local'
                for t in tools:
                    t["_source"] = "gateway"
                all_tools.extend(tools)
        except Exception:
            # Gateway might be down or not running (expected in prod)
            pass

        # 2. Try Remote Servers
        for name, url in self._remote_servers.items():
            try:
                response = await self._client.get(f"{url}/tools")
                if response.status_code == 200:
                    data = response.json()
                    tools = data.get("tools", [])
                    # Mark them with server name
                    for t in tools:
                        t["_source"] = name
                    all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"Failed to list tools from remote server '{name}' ({url}): {e}")

        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls a specific tool. Routes to Remote Server if defined, otherwise tries Gateway.
        """
        # Check if this server is a known remote server
        if server_name in self._remote_servers:
            url = self._remote_servers[server_name]
            return await self._call_direct(url, tool_name, arguments)
        
        # Fallback to Gateway
        return await self._call_gateway(server_name, tool_name, arguments)

    async def _call_direct(self, base_url: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        try:
            # Standard MCP HTTP Protocol: POST /tools/{name}/call or similar
            # Note: This path depends on the specific MCP server implementation. 
            # Often it's JSON-RPC or a specific REST endpoint.
            # Assuming a standard /call endpoint for now similar to gateway.
            payload = {
                "tool": tool_name,
                "arguments": arguments
            }
            response = await self._client.post(f"{base_url}/call", json=payload)
            if response.status_code == 200:
                return response.json()
            return {"error": f"Remote call failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def _call_gateway(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        try:
            payload = {
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments
            }
            response = await self._client.post(
                f"{self.gateway_url}/call",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Gateway call failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        await self._client.aclose()

mcp_service = MCPService()
