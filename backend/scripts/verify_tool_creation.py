
import asyncio
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai_lab.creator import ToolCreator

async def main():
    print("🚀 Starting Tool Verification...")
    
    try:
        creator = ToolCreator()
        prompt = "Create a python function called 'calculate_factorial' that takes an integer n and returns the factorial."
        
        print(f"📝 Requesting: '{prompt}'")
        result = await creator.create_tool_code(prompt)
        
        print("\n--- RESULT ---")
        if result.get("code"):
            print("✅ Code Generated Successfully:")
            print("---------------------------------------------------")
            print(result["code"])
            print("---------------------------------------------------")
            
            # Optional: Try to verify it's valid python
            try:
                compile(result["code"], "<string>", "exec")
                print("✅ Code Compilation Verified (Syntax is valid)")
            except Exception as e:
                print(f"❌ Code Compilation Failed: {e}")
                
        else:
            print("❌ No code generated.")
            print(f"Full Result: {result}")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(main())
