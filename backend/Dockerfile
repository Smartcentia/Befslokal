# syntax=docker/dockerfile:1
# Pin to Bookworm; no apt-get – Railway build often fails on apt. Rely on PyPI binary wheels.
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy only requirements first (better layer cache: code changes don't re-run pip)
COPY requirements.minimal.txt .
RUN pip install --no-cache-dir -r requirements.minimal.txt

# Copy help docs (prepared by build script)
COPY docs ./docs

# Copy data (total_kost_per_region_*.json for Financials Total kost 2025)
COPY data ./data

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var at runtime - do not hardcode 8000)
EXPOSE 8000

# NOTE: No Docker HEALTHCHECK here - Railway uses its own HTTP healthcheck
# (healthcheckPath = "/api/v1/health" in railway.toml).
# A Docker HEALTHCHECK with hardcoded port 8000 would fail when Railway
# assigns a different PORT, causing container to be marked unhealthy.

# Run Alembic migrations before starting the app
# This ensures tables exist before serving requests
# PORT environment variable - use it if available, otherwise default to 8000
# Add entrypoint script and run in JSON form so signals reach the app
RUN chmod +x ./docker-entrypoint.sh
CMD ["./docker-entrypoint.sh"]
