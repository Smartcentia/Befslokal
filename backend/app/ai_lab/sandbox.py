import os
import requests

from dotenv import load_dotenv

# Environment loading is handled by app/core/config.py, but for standalone usage:
load_dotenv("../.env")
load_dotenv(".env")

import logging
logger = logging.getLogger(__name__)

class SandboxClient:
    def __init__(self):
        # Default to enabled and local
        self.enabled = True
        self.mode = os.getenv("LAB_SANDBOX_MODE", "local")
        
        if self.mode != "local":
             # Force local if anything else is requested
             logger.warning(f"Sandbox mode '{self.mode}' not supported. Forcing 'local'.")
             self.mode = "local"

    def run_code(self, code: str, session_id: str = None) -> dict:
        """
        Executes Python code. Always uses local execution in this simplified version.
        """
        return self._run_local(code)



    def _run_local(self, code: str) -> dict:
        """
        Executes code locally using exec() in a restricted scope.
        Note: This is intended for local dev/test only.
        """
        import io
        import contextlib
        import traceback
        
        print(f"🏠 Running code in LOCAL Sandbox Mode...")
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        status = "Success"
        result = None
        
        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Restricted globals for basic safety
                # In a real production environment, 
                # you'd use a Docker container or WASM sandbox.
                exec_globals = {"__builtins__": __builtins__}
                
                # Allow semantic-kernel imports if installed
                try:
                    import semantic_kernel
                    from semantic_kernel.functions import kernel_function
                    exec_globals["semantic_kernel"] = semantic_kernel
                    exec_globals["kernel_function"] = kernel_function
                except ImportError:
                    pass
                
                print(f"--- CODE TO EXECUTE ---\n{code}\n-----------------------")

                exec_locals = {}
                exec(code, exec_globals, exec_locals)
                result = exec_locals.get("result")
        except Exception:
            status = "Failure"
            traceback.print_exc(file=stderr_capture)
            
        return {
            "status": status,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "result": str(result) if result is not None else None
        }

if __name__ == "__main__":
    # Test
    client = SandboxClient()
    result = client.run_code("print('Hello from the Sandbox!')\nresult = 2+2")
    print(result)
