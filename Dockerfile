# Railway-Dockerfile for backend (striking-insight).
# Build context = repo root. All paths prefixed with backend/.
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install Python deps first (cached layer)
COPY backend/requirements.minimal.txt .
RUN pip install --no-cache-dir -r requirements.minimal.txt

# Copy help docs
COPY backend/docs ./docs

# Copy backend application code
COPY backend/ .

EXPOSE 8000

RUN chmod +x ./docker-entrypoint.sh

# NOTE: No Docker HEALTHCHECK - Railway assigns PORT dynamically (e.g. 8080, not always 8000).
# Railway uses its own HTTP healthcheck: healthcheckPath = "/api/v1/health" in railway.toml.

CMD ["./docker-entrypoint.sh"]
