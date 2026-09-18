# Deployment Readiness

## GitHub

The repository is source-control ready. Local secrets, SQLite databases, generated PDFs, Next.js build output, `node_modules`, caches, and scratch files are excluded by `.gitignore`.

Before the first push:

```bash
git init
git add .
git status
git commit -m "feat: verified end-to-end fuzzy irrigation platform"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

Never commit `.env` or real API keys.

## Render backend

The root `render.yaml` defines the FastAPI service:

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Required production secret(s) are configured in Render, not in GitHub. `GROQ_API_KEY` is optional for core fuzzy simulation. Supabase variables are optional when local SQLite fallback is acceptable.

Set `CORS_ORIGINS` to the exact frontend origin, for example:

```text
https://irrigation-fuzzy-system.vercel.app
```

Multiple origins may be comma-separated.

Health check: `/health`
Swagger: `/docs`

## Vercel frontend

Set the Vercel project **Root Directory** to `frontend`. The included `frontend/vercel.json` is configured for Next.js.

Production environment variable:

```text
NEXT_PUBLIC_API_BASE=https://smart-irrigation-fuzzy-system.onrender.com/api
```

The frontend also has a safe runtime fallback to the deployed Render API when accessed outside localhost, while localhost defaults to `http://localhost:8000/api`.

## Release verification

Run backend syntax checks and focused tests before deployment:

```bash
python -m compileall -q .
pytest -q tests/test_endpoint_contract_audit.py tests/test_verification.py
```

Run the full suite in a CI runner with a sufficiently long timeout because the closed-loop and PSO integration tests are intentionally computationally heavier than unit tests.

Run the frontend build in the `frontend` directory:

```bash
npm ci
npm run build
```
