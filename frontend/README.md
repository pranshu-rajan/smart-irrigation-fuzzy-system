# Smart Multizone Irrigation Frontend

Next.js 16 / React 19 frontend for the Smart Multizone Fuzzy Irrigation Platform.

## Local development

```bash
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000/api` when opened on localhost and to the deployed Render API otherwise. You can override this with `NEXT_PUBLIC_API_BASE`.

## Vercel deployment

Create/import the repository in Vercel and set the project **Root Directory** to `frontend`. Vercel will use the included `vercel.json`.

Recommended production environment variable:

```text
NEXT_PUBLIC_API_BASE=https://smart-irrigation-fuzzy-system.onrender.com/api
```

See `frontend/.env.production.example`.
