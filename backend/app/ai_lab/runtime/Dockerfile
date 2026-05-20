# Standard Python Image
FROM python:3.10-slim

# Install Dependencies
# requests is needed for potential callbacks, uvicorn/fastapi for the server
RUN pip install semantic-kernel pandas matplotlib scikit-learn numpy fastapi uvicorn requests

# Copy Server
COPY server.py /app/server.py
WORKDIR /app

# Expose Port 80
EXPOSE 80

# Start Server
CMD ["python", "server.py"]
