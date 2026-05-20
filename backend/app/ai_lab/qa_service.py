
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
import io
import json
import logging
import asyncio
from typing import Dict, List, Any
from uuid import UUID

import semantic_kernel as sk
from semantic_kernel.functions import KernelFunctionFromPrompt

    
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ai_tool import AITool, QAStatus
from app.ai_lab.sandbox import SandboxClient
from app.db.session import SessionLocal
from app.ai_lab.harness import HarnessBuilder

# Setup Logger
logger = logging.getLogger(__name__)

class QualityAssuranceAgent:
    def __init__(self):
        self.kernel = sk.Kernel()
        
        # Configure AI Service
        api_key = os.getenv("OPENAI_API_KEY")
        model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
             print("❌ No OpenAI API configuration found for QA Agent.")
             return

        print(f"🤖 QA Agent: Using Standard OpenAI ({model_id})")
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
        service = OpenAIChatCompletion(
            service_id="qa_brain",
            ai_model_id=model_id,
            api_key=api_key
        )
        self.kernel.add_service(service)

        # Load QA Prompt
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "qa_prompt.txt")
            if not os.path.exists(prompt_path):
                # Fallback path logic
                prompt_path = "app/ai_lab/prompts/qa_prompt.txt"
                
            with open(prompt_path, "r") as f:
                prompt_text = f.read()

            from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
            self.qa_func = KernelFunctionFromPrompt(
                function_name="generate_tests",
                plugin_name="QAAgent",
                prompt=prompt_text,
                prompt_execution_settings=OpenAIPromptExecutionSettings(
                    service_id="qa_brain",
                    max_tokens=2000,
                    temperature=0.4
                )
            )
            self.kernel.add_function(plugin_name="QAAgent", function=self.qa_func)
        except Exception as e:
            logger.error(f"Failed to load QA prompt: {e}")

    async def generate_test_cases(self, tool_code: str) -> List[Dict[str, Any]]:
        """
        Generates 3-5 test cases based on code analysis.
        """
        try:
            result = await self.kernel.invoke(
                self.qa_func,
                tool_code=tool_code
            )
            
            # Parse JSON
            raw_text = str(result)
            cleaned = raw_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "").replace("```", "")
            
            data = json.loads(cleaned)
            return data.get("tests", [])
        except Exception as e:
            logger.error(f"Formatting error in QA: {e}")
            return [
                {"name": "Fallback Test", "input_text": "Hello QA", "expected_behavior": "Should not crash"}
            ]

    async def validate_tool(self, tool_id: UUID) -> Dict[str, Any]:
        """
        Main orchestration method:
        1. Fetch Tool
        2. Generate Tests
        3. Execute in Sandbox (PARALLEL)
        4. Update DB
        """
        async with SessionLocal() as db:
            tool = await db.get(AITool, tool_id)
            if not tool:
                return {"status": "error", "message": "Tool not found"}

            tool.qa_status = QAStatus.PENDING
            await db.commit()
            
            # 1. Generate Tests
            logger.info(f"Generating QA tests for {tool.name}")
            tests = await self.generate_test_cases(tool.code)
            
            # 2. Setup Sandbox
            sandbox = SandboxClient()
            
            # Prepare Dependency Info
            dependencies = json.loads(tool.dependencies) if tool.dependencies else []
            use_real_sk = tool.requires_real_sk
            
            # 3. Execute Parallel
            async def run_single_test(test):
                input_text = test.get("input_text", "")
                
                # Create Harness code
                harness_code = HarnessBuilder.build_tool_harness(
                    tool_code=tool.code,
                    input_text=input_text,
                    dependencies=dependencies,
                    use_real_sk=use_real_sk,
                    mode="execution"
                )
                
                # Run (Sandbox run_code is sync/blocking I/O usually, but we want to parallelize at the network level if possible.
                # However, SandboxClient.run_code uses 'requests' (Sync).
                # Refactor: We need to wrap it in asyncio.to_thread if we want concurrency, 
                # OR update SandboxClient to be async (better).
                # For now, asyncio.to_thread is the safe "Fix" without rewriting SandboxClient entirely.
                
                result = await asyncio.to_thread(sandbox.run_code, harness_code)
                
                status = result.get("status", "Failure")
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                
                passed = (status == "Success")
                
                return {
                    "name": test.get("name"),
                    "input": input_text,
                    "passed": passed,
                    "output": stdout.strip(),
                    "error": stderr.strip()
                }

            # Gather results
            test_results = await asyncio.gather(*[run_single_test(t) for t in tests])
            
            # Analyze
            passed_count = sum(1 for r in test_results if r['passed'])
            failed_count = len(test_results) - passed_count
            overall_success = (failed_count == 0)
            
            report = {
                "total_tests": len(tests),
                "passed": passed_count,
                "failed": failed_count,
                "details": test_results
            }

            # 4. Update DB
            tool.qa_status = QAStatus.PASS if overall_success else QAStatus.FAIL
            tool.qa_report = json.dumps(report, indent=2)
            await db.commit()
            
            logger.info(f"QA Complete for {tool.name}: {tool.qa_status}")
            return report

qa_agent = QualityAssuranceAgent()
