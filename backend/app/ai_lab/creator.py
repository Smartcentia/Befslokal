# --- Pydantic V2 Monkeypatch for Semantic Kernel ---
try:
    import pydantic.networks
    if not hasattr(pydantic.networks, "Url"):
        from pydantic import AnyUrl
        pydantic.networks.Url = AnyUrl
except ImportError:
    pass
# ----------------------------------------------------

import os
import re
from semantic_kernel.functions import KernelFunctionFromPrompt
import semantic_kernel as sk


from dotenv import load_dotenv

# Load Env
load_dotenv(".env")


class ToolCreator:
    def __init__(self):
        self.kernel = sk.Kernel()
        
        # Configure AI Service
        api_key = os.getenv("OPENAI_API_KEY")
        model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
             print("❌ No OpenAI API configuration found for Creator Agent.")
             return

        print(f"🤖 Creator Agent: Using Standard OpenAI ({model_id})")
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
        service = OpenAIChatCompletion(
            service_id="creator_brain",
            ai_model_id=model_id,
            api_key=api_key
        )
        self.kernel.add_service(service)
        
        # Load System Prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "creator_prompt.txt")
        with open(prompt_path, "r") as f:
            plugin_instruction = f.read()
            
        # Create the Semantic Function
        # We treat the prompt as a template where {{user_request}} is injected
        self.creator_func = KernelFunctionFromPrompt(
            function_name="create_tool_code",
            plugin_name="CreatorAgent",
            prompt=plugin_instruction,
            prompt_execution_settings=sk.connectors.ai.open_ai.OpenAIPromptExecutionSettings(
                service_id="creator_brain",
                max_tokens=2000,
                temperature=0.2
            )
        )
        self.kernel.add_function(plugin_name="CreatorAgent", function=self.creator_func)

        # Fixer Prompt
        fixer_prompt = """
You are an expert Python developer fixing a broken tool.
User Request: {{$user_request}}
Broken Code:
{{$code}}

Error Message:
{{$error}}

INSTRUCTION:
Fix the implementation to resolve the error. 
Ensure specific imports are included if missing.
Maintain the same JSON output format as the Creator.
Class structure and @kernel_function decorators must remain.

OUTPUT FORMAT (JSON ONLY):
{
    "code": "The complete protected Python code as a single string",
    "requires_real_semantic_kernel": (bool),
    "dependencies": ["list", "of", "dependencies"]
}
"""
        self.fixer_func = KernelFunctionFromPrompt(
            function_name="fix_tool_code",
            plugin_name="CreatorAgent",
            prompt=fixer_prompt,
            prompt_execution_settings=sk.connectors.ai.open_ai.OpenAIPromptExecutionSettings(
                service_id="creator_brain",
                max_tokens=2000,
                temperature=0.2
            )
        )
        self.kernel.add_function(plugin_name="CreatorAgent", function=self.fixer_func)

    async def create_tool_code(self, user_request: str) -> dict:
        """
        Generates Python code and execution strategy based on the user request.
        Returns a dictionary with 'code', 'requires_real_semantic_kernel', and 'dependencies'.
        """
        print(f"🤖 Creator Agent received request: '{user_request}'")
        
        result = await self.kernel.invoke(
            self.creator_func,
            user_request=user_request
        )
        
        raw_output = str(result)
        return self._parse_output(raw_output)

    async def fix_tool_code(self, user_request: str, code: str, error: str) -> dict:
        """
        Attempts to fix the broken code based on the error message.
        """
        print(f"🔧 Fixer Agent repairing code for error: {error[:50]}...")
        
        result = await self.kernel.invoke(
            self.fixer_func,
            user_request=user_request,
            code=code,
            error=str(error)
        )
        
        return self._parse_output(str(result))

    def _parse_output(self, text: str) -> dict:
        """
        Parses the JSON output from the LLM. 
        Handles cases where LLM might wrap JSON in markdown blocks.
        """
        import json
        
        cleaned_text = text.strip()
        
        # Remove markdown fences if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.replace("```json", "").replace("```", "")
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace("```", "")
            
        cleaned_text = cleaned_text.strip()
        
        try:
            data = json.loads(cleaned_text)
            return {
                "code": data.get("code", ""),
                "requires_real_semantic_kernel": data.get("requires_real_semantic_kernel", False),
                "dependencies": data.get("dependencies", [])
            }
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON from Creator. Fallback to raw text extraction.")
            # Fallback for legacy/error cases (just extract python code if possible)
            # This is risky but necessary for robustness
            code_match = re.search(r"class .*:", text)
            if code_match:
                return {
                    "code": text, # Assume raw text is code
                    "requires_real_semantic_kernel": False, # Default to Fast Strategy
                    "dependencies": []
                }
            return {
                "code": "", 
                "error": "Failed to parse JSON"
            }

# Test logic
if __name__ == "__main__":
    import asyncio
    async def test():
        creator = ToolCreator()
        code = await creator.create_tool_code("Create a tool that generates a random password with a specific length.")
        print("\n--- GENERATED CODE ---\n")
        print(code)
        print("\n----------------------\n")
    
    asyncio.run(test())
