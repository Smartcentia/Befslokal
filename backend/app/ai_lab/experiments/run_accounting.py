import asyncio
import os
import sys
import json
import re
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from creator import ToolCreator
from sandbox import SandboxClient

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class AccountingLab:
    def __init__(self):
        self.creator = ToolCreator()
        self.sandbox = SandboxClient()

    async def run_experiment(self):
        print("🧪 Starting Accounting Experiment (Refactored Strategy)...")
        
        # 1. Prompt
        # Explicit instructions for Return Value and No Args
        prompt = (
            "Create a Python tool class that generates mock monthly accounting data for a year. "
            "1. Use 'pandas' for data manipulation. "
            "2. Use 'matplotlib' to generate a simple Bar Chart of Income vs Expenses. "
            "3. Optimize the chart for small file size (figsize=(6, 4), dpi=70). "
            "4. The tool MUST return a dictionary with two keys: "
            "   - 'summary': A text or dict summary of the data. "
            "   - 'chart_base64': The Base64 encoded string of the PNG chart. "
            "5. IMPORTANT: The method MUST NOT take any arguments. Use default values internally. "
            "6. Do NOT print the image to stdout, just return it."
        )
        
        print(f"\n🚀 Sending Request: '{prompt}'")
        code = await self.creator.create_tool_code(prompt)
        print(f"📜 Generated Code (Snippet):\n{code[:300]}...\n")
        
        # 2. Prepare Sandbox Harness with MOCKING
        # We define a dummy 'semantic_kernel' module so we don't need to install it.
        harness = f"""
import sys
from types import ModuleType

# --- MOCK START ---
# Create dummy semantic_kernel module
mock_sk = ModuleType("semantic_kernel")
mock_funcs = ModuleType("semantic_kernel.functions")
sys.modules["semantic_kernel"] = mock_sk
sys.modules["semantic_kernel.functions"] = mock_funcs

# Create dummy decorator
def kernel_function(name=None, description=None):
    def decorator(func):
        return func
    return decorator

mock_funcs.kernel_function = kernel_function
# --- MOCK END ---

# Install Real Dependencies
%pip install -q pandas matplotlib
import matplotlib
matplotlib.use('Agg')

# Inject Generated Code
{code}

# Execution Logic
try:
    import inspect
    import json
    
    # 1. Find Plugin Class
    classes = [obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(obj) and name != 'Annotated']
    classes = [c for c in classes if c.__module__ == __name__]
    
    target_plugin_cls = classes[-1] 
    
    plugin_instance = target_plugin_cls()
    
    # 2. Find Generative Method
    methods = [func for func in dir(plugin_instance) if callable(getattr(plugin_instance, func)) and not func.startswith("__")]
    target_method = methods[0]
    for m in methods:
        if "generate" in m or "accounting" in m:
            target_method = m
            break
            
    # 3. Execute
    result = getattr(plugin_instance, target_method)()
    
    # 4. Serialize Output CAREFULLY
    # Print Summary separately
    if isinstance(result, dict):
        summary = result.get("summary", "No Summary")
        b64 = result.get("chart_base64", "")
        
        print("__SUMMARY_START__")
        print(json.dumps(summary, default=str))
        print("__SUMMARY_END__")
        
        if b64:
            print("__IMAGE_START__")
            print(b64)
            print("__IMAGE_END__")
        else:
            print("NO_IMAGE")
    else:
        print(f"UNEXPECTED_RESULT: {{result}}")

except Exception as e:
    print(f"❌ ERROR: {{e}}")
    import traceback
    traceback.print_exc()
"""
        # 3. Run in Sandbox
        import uuid
        sid = str(uuid.uuid4())
        print(f"🆔 Session ID: {sid} (Clean Room)")
        
        result_pkg = self.sandbox.run_code(harness, session_id=sid)
        
        stdout = result_pkg.get("stdout", "")
        stderr = result_pkg.get("stderr", "")
        
        if stderr:
             print(f"\n--- STDERR (Snippet) ---\n{stderr[:500]}")

        # 4. Parse Result
        try:
            if "__SUMMARY_START__" in stdout:
                summary_str = stdout.split("__SUMMARY_START__")[1].split("__SUMMARY_END__")[0].strip()
                print(f"\n📊 Summary:\n{summary_str}")
                
            if "__IMAGE_START__" in stdout:
                b64_str = stdout.split("__IMAGE_START__")[1].split("__IMAGE_END__")[0].strip()
                print("\n✅ Image Data Found.")
                self._save_image(b64_str)
            else:
                print("❌ No __IMAGE_START__ token found.")
                
        except Exception as e:
            print(f"❌ Parsing Error: {e}")
            if len(stdout) < 2000:
                print(f"Stdout dump:\n{stdout}")

    def _save_image(self, b64_str):
        try:
            import base64
            import re
            
            # Clean: Remove header if present
            if "base64," in b64_str:
                b64_str = b64_str.split("base64,")[1]
            
            # Violent cleaning: Remove ALL non-base64 characters (newlines, spaces, etc)
            # Base64 chars are A-Z, a-z, 0-9, +, / and =
            pattern = re.compile(r'[^A-Za-z0-9+/=]')
            b64_str = pattern.sub('', b64_str)
            
            # Fix Padding
            pad = len(b64_str) % 4
            if pad:
                b64_str += "=" * (4 - pad)
                
            path = os.path.join(OUTPUT_DIR, "accounting_chart.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64_str))
            print(f"📸 Chart saved to: {path}")
        except Exception as e:
            print(f"❌ Image Save Error: {e}")

if __name__ == "__main__":
    asyncio.run(AccountingLab().run_experiment())
