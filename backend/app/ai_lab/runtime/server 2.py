from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import io
import contextlib
import traceback

app = FastAPI()

class CodeRequest(BaseModel):
    properties: dict

@app.post("/run")
async def execute_code(request: CodeRequest):
    code = request.properties.get("code", "")
    execution_type = request.properties.get("executionType", "synchronous")
    
    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = None
    status = "Success"
    
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # Safe-ish execution namespace
            local_scope = {}
            exec(code, {}, local_scope)
            # Try to get 'result' variable if defined, else None
            result = local_scope.get("result")
            
    except Exception:
        status = "Failure"
        traceback.print_exc(file=stderr_capture)
        
    return {
        "properties": {
            "status": status,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "result": str(result) if result is not None else None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
