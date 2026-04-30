# RAPTR
RAPTR is an open-source, API-enabled collaboration platform for Red and Purple Team engagements. It bridges the gap between offensive and defensive teams by allowing you to plan campaigns, log attacks and detections side-by-side, evaluate the results, and generate high-quality reports.

## Documentation
Head over to the [docs](https://raptr.app) for detailed documentation.

## Quick Start
To start using RAPTR locally, you can use the following command:

```bash
docker run -d \
  --name raptr \
  -p 8000:8000 \
  -e DB_ENGINE=sqlite \
  -e SQLITE_DB_PATH=/data/raptr.db \
  -e TLS_ENABLED=false \
  -e ADMIN_EMAIL=admin@raptr.app \
  -e ADMIN_PASSWORD=your-secure-password \
  -v raptr_data:/data \
  ghcr.io/CompassSecurity/raptr:latest
```

## Sandobx
A sandbox playground is available at [https://sandbox.raptr.app/](https://sandbox.raptr.app/).

## Project Structure

- `backend/`: Python FastAPI application.
- `frontend/`: Vue 3 + Vite application.
- `docs/`: Documentation which is used to generate the static documentation website at [https://raptr.app](https://raptr.app).
- `example templates/`: Example templates for RAPTR
- `Dockerfile`: Configuration for building the RAPTR single-container deployment
- `docker-compose.yml`: Example compose file for local deployment