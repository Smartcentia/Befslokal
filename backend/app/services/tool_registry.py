import os
import json
import inspect
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings

class ToolRegistry:
    def __init__(self):
        self.endpoint = None
        self.key = None
        self.index_name = "tools-index"
        self._in_memory_tools = {}
        
    def _get_embedding_client(self):
        """Returns configured OpenAI client for embeddings."""
        if settings.OPENAI_API_KEY:
            return OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        return None

    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding for the tool description."""
        client = self._get_embedding_client()
        if not client:
            return []
        
        try:
            response = client.embeddings.create(
                input=text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def initialize_index(self):
        """No-op for now as we use only in-memory registry."""
        print("ℹ️ ToolRegistry: External search disabled. Using in-memory registry.")

    def register_tool(self, func: callable, tool_name: str = None, description_override: str = None) -> Dict:
        """
        Registers a Python function as a tool in the library.
        Stores in memory for now.
        """
        final_tool_name = tool_name or func.__name__
        description = description_override or func.__doc__ or "No description provided."
        source_code = inspect.getsource(func)
        
        # Schema Generation
        sig = inspect.signature(func)
        params = {}
        for name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            
            params[name] = {"type": param_type}

        schema = {
            "type": "object",
            "properties": params,
            "required": [n for n, p in sig.parameters.items() if p.default == inspect.Parameter.empty]
        }

        # Embed (Optional, for future use)
        # embedding = self.generate_embedding(description) 

        document = {
            "id": f"{final_tool_name}_v1",
            "tool_name": final_tool_name,
            "description": description,
            "python_code": source_code,
            "arguments_schema": json.dumps(schema),
            "status": "active",
            # "vector_embedding": embedding
        }

        self._in_memory_tools[final_tool_name] = document
        print(f"Tool '{final_tool_name}' registered successfully (In-Memory).")
        return document

    def search_tools(self, query: str, top: int = 3) -> List[Dict]:
        """Simple keyword search for tools since Vector Search is removed."""
        if not self._in_memory_tools:
            return []

        results = []
        for name, doc in self._in_memory_tools.items():
             if query.lower() in doc["description"].lower() or query.lower() in name.lower():
                 results.append({
                    "name": doc["tool_name"],
                    "description": doc["description"],
                    "code": doc["python_code"],
                    "schema": json.loads(doc["arguments_schema"])
                 })
        
        return results[:top]

tool_registry = ToolRegistry()
