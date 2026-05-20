import json

class HarnessBuilder:
    """
    Centralized logic for building Python execution harnesses for the AI Lab.
    Consolidates logic from main_mvp.py and qa_service.py.
    """

    @staticmethod
    def build_tool_harness(
        tool_code: str, 
        input_text: str = None, 
        use_real_sk: bool = False, 
        dependencies: list = [],
        mode: str = "execution"
    ) -> str:
        """
        Builds a complete executable Python script that:
        1. Installs dependencies (if any).
        2. Configures Virtual or Real Semantic Kernel.
        3. Defines the Tool Class.
        4. Instantiates and Runs the Tool.
        
        :param mode: 'execution' (runs with input) or 'validation' (instantiates only to check syntax).
        """
        
        # 1. Dependency Installation
        pip_installs = ""
        if dependencies:
            libs = " ".join(dependencies)
            pip_installs += f"%pip install -q {libs}\n"
            
        if use_real_sk:
             pip_installs += "%pip install semantic-kernel\n"
             sk_header = "" # Real import happens in code
        else:
             # Fast-track Strategy
             sk_header = """
import sys
from types import ModuleType

# --- FAST-TRACK START ---
mock_sk = ModuleType("semantic_kernel")
mock_funcs = ModuleType("semantic_kernel.functions")
sys.modules["semantic_kernel"] = mock_sk
sys.modules["semantic_kernel.functions"] = mock_funcs

def kernel_function(name=None, description=None):
    def decorator(func):
        return func
    return decorator

mock_funcs.kernel_function = kernel_function
# --- FAST-TRACK END ---
"""

        # 2. The Runner Logic (Introspection)
        # We use a robust introspection script to find the class and method
        input_injection = ""
        if input_text is not None:
            # Safe JSON serialization of the input string
            import json
            safe_input = json.dumps(input_text)
            input_injection = f"INPUT_VAL = {safe_input}"
        else:
            input_injection = "INPUT_VAL = None"

        runner_logic = f"""
{input_injection}

# Runner Logic
import inspect
import sys
import asyncio
import json

async def main():
    try:
        # 1. Find the Tool Class
        # We search for the LAST defined class in this module, excluding special ones
        classes = [obj for name, obj in inspect.getmembers(sys.modules[__name__]) 
                  if inspect.isclass(obj) and name != 'Annotated' and obj.__module__ == __name__]
        
        if not classes:
            print("No Plugin class found.")
            return

        PluginClass = classes[-1]
        plugin = PluginClass()
        
        # If Validation Mode, we stop here (successful instantiation)
        if "{mode}" == "validation":
            print(f"VALIDATION_SUCCESS: Instantiated {{PluginClass.__name__}}")
            return

        # 2. Find the Method
        # Look for methods that are not dunder methods
        methods = [func for func in dir(plugin) 
                  if callable(getattr(plugin, func)) and not func.startswith("__")]
        
        target_method = None
        
        # Heuristic: Prefer methods named 'run', 'execute', 'generate', 'calculate'
        priority_names = ['run', 'execute', 'invoke', 'generate', 'calculate']
        for pname in priority_names:
            for m in methods:
                 if pname in m.lower():
                     target_method = m
                     break
            if target_method: break
        
        # Fallback: First available method
        if not target_method and methods:
            target_method = methods[0]
            
        if target_method:
            func = getattr(plugin, target_method)
            
            # 3. Call with Arguments
            sig = inspect.signature(func)
            params = sig.parameters
            
            result = None
            if len(params) == 0:
                 if asyncio.iscoroutinefunction(func):
                    result = await func()
                 else:
                    result = func()
            elif len(params) >= 1:
                 # Pass INPUT_VAL
                 if INPUT_VAL:
                     if asyncio.iscoroutinefunction(func):
                        result = await func(INPUT_VAL)
                     else:
                        result = func(INPUT_VAL)
                 else:
                     # Attempt to call without args if input is None, or fail?
                     # Ideally we provide empty string if None
                     if asyncio.iscoroutinefunction(func):
                        result = await func("")
                     else:
                        result = func("")
            
            print(f"OUTPUT: {{result}}")
        else:
            print("No executable method found.")

    except Exception as e:
        print(f"EXECUTION ERROR: {{e}}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if 'asyncio' in sys.modules:
        asyncio.run(main())
    else:
        # Fallback if asyncio somehow not working? No, standard lib.
        pass
"""

        return f"{pip_installs}\n{sk_header}\n{tool_code}\n{runner_logic}"
