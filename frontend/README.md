# SmartLight Frontend

React + TypeScript dashboard for the SmartLight Django backend (JWT auth + homes/rooms/lamps).

## Getting started

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Environment

- `VITE_API_BASE_URL` (default `http://localhost:8000`)

Create `.env.local`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Architecture

- `src/api`: axios client, JWT refresh, typed endpoints from `schemas/SmartLight.yaml`.
- `src/auth`: auth context + guards, persists tokens (refresh in localStorage; access mirrored for reloads).
- `src/features/auth`: login/register pages.
- `src/features/dashboard`: homes → rooms → lamps UI, add modals, grouping by names per schema.
- `src/components/ui`: small UI primitives (buttons, inputs, modals, pills, skeletons).

Data fetching: TanStack Query caches homes/rooms/lamps, refetches after mutations, and retries once on errors. Axios interceptor refreshes access token on 401 using `/Account/token/refresh/` then retries the request.

## Notes on JWT storage

- Refresh token: stored in `localStorage` for session persistence.
- Access token: kept in memory and mirrored to `localStorage` to allow reloads; cleared on logout or failed refresh. Adjust to stricter storage if needed.

## Development scripts

- `npm run dev` – start Vite dev server
- `npm run build` – type-check + production build
- `npm run preview` – preview production build
- `npm run lint` – ESLint
