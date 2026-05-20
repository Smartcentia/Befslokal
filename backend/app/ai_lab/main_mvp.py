# --- Pydantic V2 Monkeypatch for Semantic Kernel ---
try:
    import pydantic.networks
    if not hasattr(pydantic.networks, "Url"):
        from pydantic import AnyUrl
        pydantic.networks.Url = AnyUrl
except ImportError:
    pass
# ----------------------------------------------------

import asyncio
import os
import sys
import uuid
import json
import traceback
from typing import List, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.ai_tool import AITool, ToolStatus, QAStatus
from app.ai_lab.memory import create_memory_store
from app.ai_lab.creator import ToolCreator
from app.ai_lab.sandbox import SandboxClient
from app.ai_lab.harness import HarnessBuilder
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

class AILab:
    def __init__(self):
        self.memory: Optional[SemanticTextMemory] = None
        self.creator = ToolCreator()
        self.sandbox = SandboxClient()
        self.collection = "tool_library"

    async def initialize(self):
        print("🧠 Initializing AI Lab...")
        self.memory = await create_memory_store()

    async def process_request(self, user_request: str) -> dict:
        logs = []
        def log(msg): 
            print(msg) 
            logs.append(msg)
            
        # 1. Search (Hybrid: Memory -> DB Validation)
        log("🔍 Searching Shared Tool Library...")

        try:
            if not self.memory:
                await self.initialize()
                
            results = await self.memory.search(
                collection=self.collection,
                query=user_request,
                limit=1,
                min_relevance_score=0.75
            )
            
            if results:
                tool_mem = results[0]
                tool_id = tool_mem.id
                log(f"✅ Found semantic match in Memory: {tool_id} (Score: {tool_mem.relevance:.2f})")
                
                # Fetch full code from DB
                async with SessionLocal() as db:
                     # Attempt to parse UUID
                     try:
                        t_uuid = uuid.UUID(tool_id)
                        stmt = select(AITool).where(AITool.id == t_uuid)
                        res = await db.execute(stmt)
                        db_tool = res.scalars().first()
                     except Exception as ex:
                        log(f"⚠️ Failed to load tool from DB: {ex}")
                        db_tool = None
                
                if db_tool:
                     log(f"✅ Loaded Tool from Library: {db_tool.name}")
                     return {
                        "status": "found",
                        "tool_id": str(db_tool.id),
                        "code": db_tool.code,
                        "description": db_tool.description,
                        "logs": logs,
                        "message": f"Found existing tool: {db_tool.name}"
                     }
        except Exception as e:
            log(f"⚠️ Memory Search Error: {e}")

        log("⚠️ No suitable tool found. Entering CREATION MODE.")
        
        # 2. Create Tool
        log("🎨 Generating Tool Code (with Self-Healing)...")
        
        max_retries = 3
        current_code = None
        current_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    creator_result = await self.creator.create_tool_code(user_request)
                else:
                    log(f"🩹 Self-Healing Attempt {attempt+1}/{max_retries}...")
                    creator_result = await self.creator.fix_tool_code(user_request, current_code, current_error)

                # Handle dictionary return
                if isinstance(creator_result, dict):
                    code = creator_result.get("code", "")
                    use_real_sk = creator_result.get("requires_real_semantic_kernel", False)
                    dependencies = creator_result.get("dependencies", [])
                else:
                    code = creator_result
                    use_real_sk = False
                    dependencies = []

                # Robustness: Fix double-escaped newlines and quotes if present
                if isinstance(code, str):
                    code = code.replace("\\n", "\n").replace('\\"', '"')
                
                current_code = code # Update for potential next fix
                log(f"📜 Generated Code (Snippet): {code[:100]}...")

                strategy_name = "REAL (Slow & Robust)" if use_real_sk else "LIGHTWEIGHT (Fast)"
                log(f"🧠 Chosen Strategy: {strategy_name}")
                
                # 3. Test/Verify (The Validator Loop)
                log("🧪 Testing Tool in Sandbox...")
                
                # USE SHARED HARNESS
                validation_code = HarnessBuilder.build_tool_harness(
                    tool_code=code, 
                    mode="validation",
                    use_real_sk=use_real_sk, 
                    dependencies=dependencies
                )
                
                result = self.sandbox.run_code(validation_code)
                
                if "error" in result:
                        log(f"❌ Sandbox Error: {result}")
                        current_error = str(result.get("error", "Unknown Sandbox Error"))
                        if isinstance(result.get("details"), str):
                            current_error += f": {result['details']}"
                        # Continue to next attempt instead of failing immediately
                        continue
                        
                # Inspect Execution Result
                props = result 
                stdout = props.get("stdout", "")
                stderr = props.get("stderr", "")
                
                # Check for success
                if props.get("status") == "Success" and "VALIDATION_SUCCESS" in stdout:
                        log(f"✅ Test Execution Successful.")
                        
                        # 4. Save to Shared Library (DB + Memory)
                        log("💾 Saving Tool to Shared Library...")
                        try:
                            async with SessionLocal() as db:
                                new_tool = AITool(
                                    name=f"AutoTool-{hash(user_request)}", # Temporary name
                                    description=user_request,
                                    code=code,
                                    dependencies=json.dumps(dependencies),
                                    requires_real_sk=use_real_sk,
                                    status=ToolStatus.EXPERIMENTAL,
                                    is_public=False
                                )
                                db.add(new_tool)
                                await db.commit()
                                await db.refresh(new_tool)
                                
                                tool_id_str = str(new_tool.id)
                                log(f"✅ Saved to DB: ID {tool_id_str}")
                                
                                # Save to Memory for Semantic Search
                                await self.memory.save_information(
                                    collection=self.collection,
                                    id=tool_id_str, # Use DB UUID as Memory ID
                                    text=f"{tool_id_str}: {user_request}",
                                    description=user_request
                                )
                                log("✅ Index Updated.")
                                
                        except Exception as e:
                            log(f"❌ Save Failed: {e}")
                        
                        return {
                            "status": "created",
                            "tool_id": tool_id_str if 'tool_id_str' in locals() else "temp",
                            "code": code,
                            "strategy": strategy_name,
                            "sandbox_stdout": stdout,
                            "logs": logs,
                            "message": "Created and saved new tool."
                        }
                        
                else:
                        error_msg = stderr if stderr else stdout
                        log(f"❌ Test Failed (Attempt {attempt+1}): {error_msg}")
                        current_error = error_msg
                        # Loop continues to next retry
                        
            except Exception as e:
                log(f"⚠️ Creation Loop Exception: {e}")
                current_error = str(e)

        # Retries exhausted
        return {
            "status": "failed", 
            "error": f"Failed after {max_retries} attempts. Last error: {current_error}", 
            "sandbox_stdout": stdout if 'stdout' in locals() else "",
            "logs": logs
        }

    async def list_tools(self, status: str = None) -> list:
        """Retrieves tools from the Shared Library."""
        async with SessionLocal() as db:
            query = select(AITool)
            if status:
                query = query.where(AITool.status == status)
            query = query.order_by(AITool.created_at.desc())
            
            result = await db.execute(query)
            tools = result.scalars().all()
            return tools

    async def publish_tool(self, tool_id: str) -> dict:
        """Promotes a tool to PENDING QA status."""
        async with SessionLocal() as db:
            try:
                t_uuid = uuid.UUID(tool_id)
                stmt = (
                    update(AITool)
                    .where(AITool.id == t_uuid)
                    .values(qa_status=QAStatus.PENDING, is_public=False)
                    .execution_options(synchronize_session=False)
                )
                result = await db.execute(stmt)
                
                if result.rowcount == 0:
                     return {"status": "error", "message": "Tool not found"}

                await db.commit()
                return {"status": "success", "message": f"Tool {tool_id} queued for QA!"}
            except Exception as e:
                traceback.print_exc()
                return {"status": "error", "message": str(e)}

    async def search_tools(self, query: str, limit: int = 5) -> list:
        """
        Performs a semantic search for tools in the library.
        """
        if not self.memory:
            await self.initialize()
            
        try:
             # 1. Semantic Search
             mem_results = await self.memory.search(
                collection=self.collection,
                query=query,
                limit=limit,
                min_relevance_score=0.6 
             )
             
             if not mem_results:
                 return []
                 
             tool_ids = [m.id for m in mem_results]
             
             # 2. Fetch Details from DB
             valid_uuids = []
             for tid in tool_ids:
                 try:
                     valid_uuids.append(uuid.UUID(tid))
                 except:
                     pass
                     
             if not valid_uuids:
                 return []

             async with SessionLocal() as db:
                 stmt = select(AITool).where(AITool.id.in_(valid_uuids))
                 result = await db.execute(stmt)
                 tools = result.scalars().all()
                 return tools

        except Exception as e:
            print(f"Search Error: {e}")
            return []

    async def toggle_pin_tool(self, tool_id: str, is_pinned: bool) -> dict:
        """Pins or unpins a tool."""
        async with SessionLocal() as db:
            try:
                t_uuid = uuid.UUID(tool_id)
                stmt = (
                    update(AITool)
                    .where(AITool.id == t_uuid)
                    .values(is_pinned=is_pinned)
                    .execution_options(synchronize_session=False)
                )
                await db.execute(stmt)
                await db.commit()
                return {"status": "success", "message": f"Tool {tool_id} pinned: {is_pinned}"}
            except Exception as e:
               traceback.print_exc()
               return {"status": "error", "message": str(e)}

    async def execute_tool(self, tool_id: str, input_text: str) -> dict:
        """Execution of a specific tool from the library."""
        # 1. Fetch Code
        async with SessionLocal() as db:
             try:
                 t_uuid = uuid.UUID(tool_id)
                 result = await db.execute(select(AITool).where(AITool.id == t_uuid))
                 tool = result.scalars().first()
                 if not tool:
                     return {"status": "error", "message": "Tool not found"}
                 
                 code = tool.code
                 # Safer dependency loading
                 try:
                    dependencies = json.loads(tool.dependencies) if tool.dependencies else []
                 except:
                    dependencies = []
                    
                 use_real_sk = tool.requires_real_sk
             except Exception as e:
                 return {"status": "error", "message": str(e)}

        # 2. Build Execution Harness (SHARED LOGIC)
        final_code = HarnessBuilder.build_tool_harness(
            tool_code=code,
            input_text=input_text,
            use_real_sk=use_real_sk,
            dependencies=dependencies,
            mode="execution"
        )

        # 3. Run in Sandbox
        res = self.sandbox.run_code(final_code)
        return res

# Singleton instance for API
lab_service = AILab()

if __name__ == "__main__":
    async def main():
        await lab_service.initialize()
        res = await lab_service.process_request("Create a tool that generates a random password.")
        print(res)
    asyncio.run(main())
