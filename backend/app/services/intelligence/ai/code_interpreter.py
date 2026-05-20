import sys
import io
import contextlib
import traceback
import os

# Use non-interactive backend before importing pyplot (required for headless/Render)
os.environ.setdefault("MPLBACKEND", "Agg")
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64
from typing import Dict, Any, Optional

class CodeInterpreter:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        # In a real dynamic session, this would be an API client.
        # For local dev, we keep a persistent global state per session if needed.
        print("WARNING: CodeInterpreter initialized in LOCAL MODE. This uses 'exec' and is NOT secure for production.")
        self.globals = {
            "pd": pd,
            "plt": plt,
        }

    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Executes Python code in a local restricted environment.
        WARNING: This uses `exec`. It is NOT secure for production with untrusted input.

        """
        
        # Capture stdout
        buffer = io.StringIO()
        
        # Reset plot
        plt.clf()
        
        result_pkg = {
            "status": "success",
            "text_output": "",
            "image_output": None,
            "error": None
        }

        try:
            with contextlib.redirect_stdout(buffer):
                # Executing code with our globals
                exec(code, self.globals)
            
            result_pkg["text_output"] = buffer.getvalue()
            
            # Check if any plot was generated
            if plt.get_fignums():
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png')
                img_buf.seek(0)
                img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
                result_pkg["image_output"] = img_base64
                plt.close()

        except Exception as e:
            result_pkg["status"] = "error"
            result_pkg["error"] = str(e)
            result_pkg["traceback"] = traceback.format_exc()
        
        return result_pkg

    def _sanitize_code(self, code: str) -> str:
        """
        Basic sanitization. In production, the sandbox handles this.
        """
        # Strip markdown code blocks if present
        if code.startswith("```python"):
            code = code.replace("```python", "").replace("```", "")
        elif code.startswith("```"):
            code = code.replace("```", "")
        return code.strip()
