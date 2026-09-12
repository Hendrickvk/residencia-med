# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A study platform for medical residency exams (ENAMED/Revalida) with a question bank, performance dashboard, spaced repetition (SM-2), timed mock exams, and study materials (MediaFire-linked). Database is Postgres on Neon (region `sa-east-1`), connection string in `.streamlit/secrets.toml` (gitignored) for the Streamlit app, or the `DATABASE_URL` env var for everything else (`db.py` falls back to `os.environ` when `st.secrets` isn't available — see `db.py` top of file).

**Hybrid architecture, by deliberate design, not a half-finished migration:**
- Student-facing features (Painel, Praticar, Simulado, Revisão Espaçada, Materiais, busca) live in a FastAPI + React SPA (`api/`, `frontend/`).
- The 4 admin-only screens (Banco de Questões, Nova Questão, Importar Planilha, Sincronizar MediaFire) live permanently in the original Streamlit app (`app.py`, `ui.py`, `auth.py`) — decided explicitly, not migrating them (see `MIGRACAO.md` §4/§5).
- `db.py` and `repeticao_espacada.py` are the **single source of truth** for all business logic (SM-2 algorithm, filters, streak/ofensiva calculation, dashboard aggregation) and are shared unchanged by both the FastAPI app and the Streamlit app. Never duplicate business logic into the API layer or the frontend — add it to `db.py`/`repeticao_espacada.py` instead.

Read `MIGRACAO.md` (migration plan, phase-by-phase decisions, the real function→endpoint contract) and `DEPLOY.md` (production runbook, checklist of what's actually deployed) before making structural changes to the API or touching the production server. `contextoconversaclaude.txt` is a curated running history of decisions/gotchas across sessions — check it for "why was this built this way" before re-deriving from scratch.

## Commands

### Backend (FastAPI)
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload            # dev server, http://localhost:8000
pytest                                     # runs everything in tests/ (pytest.ini: testpaths = tests)
pytest tests/test_sm2.py                   # single file
pytest tests/test_sm2.py::test_nome        # single test
```
**There is no separate test database** — tests run directly against the production Neon Postgres (same `DATABASE_URL`/secrets as prod). Fixtures in `tests/conftest.py` create uuid-suffixed data (`pytest_<uuid>@teste.local`, `__pytest_area_<uuid>`) and clean up via `ON DELETE CASCADE` in teardown. Any new fixture must follow this pattern — never write a fixture without teardown, and never reuse real user data.

### Streamlit (admin screens)
```bash
streamlit run app.py                      # http://localhost:8501, needs .streamlit/secrets.toml
```
Running this via a sandboxed/isolated shell (no outbound network) hangs forever inside `db.init_db()` with no visible error — if `streamlit run` seems to hang, check network isolation before assuming a code bug (`timeout 8 bash -c "cat < /dev/tcp/<host>/<port>"` against the DB host is a quick diagnostic).

### Frontend (Vite + React + TS)
```bash
cd frontend
npm install
npm run dev                                # http://localhost:5173, expects API at :8000 (.env.development)
npm run build                              # tsc -b && vite build → dist/
npm run lint                               # oxlint
```

## Architecture

### `api/` (FastAPI)
- `main.py` — app + lifespan hook (calls `db.init_db()`) + CORS via `CORS_ORIGENS` env var.
- `security.py` — auth is JWT in an **httpOnly cookie**, not bearer+refresh. `COOKIE_SECURE` is env-controlled and defaults to `false` (must be `true` once served over real HTTPS — see Deployment below).
- `deps.py` — `usuario_atual`, `exigir_admin`, `eh_admin` (checks `ADMIN_EMAILS` env var, comma-separated).
- `schemas.py` — Pydantic models. `CredenciaisIn.email` is plain `str` + a custom validator, not `EmailStr`, because `email-validator` rejects `.local`/reserved TLDs used by test fixtures.
- `serialize.py` — `questao_publica()` must wrap every question row returned by any endpoint: strips `imagem`/`imagem_mime` (Postgres BYTEA, not JSON-serializable) into a `tem_imagem` bool, and parses the `alternativas` column (stored as a TEXT/JSON string) into an object.
- `routers/` — one file per resource. **Central architectural decision**: `GET /praticar/sessao` returns the *entire* question batch for a session with gabarito+explicação already embedded (via `serialize`), not one question at a time. This is what makes instant client-side feedback possible without a round-trip per answer — don't "optimize" this into a paginated/lazy endpoint.
- `POST /respostas` is fire-and-forget from the frontend's perspective — the UI never waits on it to show correct/incorrect.

### `frontend/` (Vite + React 19 + TS + Tailwind v3)
- Tailwind v3 was an explicit choice over v4. Design tokens (colors, typography, spacing, radii) come from `REDESIGN.md` and are mapped in `tailwind.config.js` / `src/styles/theme.css`; dark mode via a `.dark` class on `<html>`.
- TanStack Query (React Query) for server state. **Known pitfall already hit twice**: a hook with `staleTime: Infinity` reused across two different screens under the *same* queryKey leaks stale data from one screen's phase into another's (happened with `useItensSimulado` between "em andamento" and "resultado"). Before setting a long/infinite `staleTime`, confirm the queryKey is exclusive to one screen/phase, or invalidate explicitly before navigating (see `EmAndamento.tsx`).
- React Router paths are stable keys, deliberately decoupled from the nav label shown in the menu (same lesson learned the hard way on the Streamlit side, where the label used to double as the routing key).
- `src/lib/respostasQueue.ts` — module-level retry queue with backoff for answer submissions; invalidates the `["me"]` query on success so the topbar streak/counters update (they don't otherwise, since the queue lives outside React).
- Admin-only routes render `PermaneceNoStreamlit.tsx` (a placeholder linking to `VITE_STREAMLIT_URL`) instead of a real page — this is intentional per the Fase 7 decision, not a stub to fill in.
- `frontend/.env.production` has no secrets (just `VITE_API_URL`/`VITE_STREAMLIT_URL`) but is easy to accidentally gitignore: the root `.gitignore` pattern for the backend's `.env.production` must stay anchored to the repo root (`/.env.production`), or it will also match and silently exclude the frontend one.

### Postgres specifics
- `LIKE` is case-sensitive in Postgres (unlike SQLite, which earlier docs incorrectly assumed). Any free-text filter in `db.py` must use `ILIKE`.
- Postgres doesn't auto-index foreign keys — indexes on `respostas.usuario_id`, `respostas.questao_id`, `questoes.area_id`, `questoes.banca` are created explicitly in `init_db()`.
- `revisao.proxima_revisao` is a real `TIMESTAMP` (migrated from `TEXT`/date-only), so short "review again in 10 minutes" scheduling works for real — don't regress this back to date-only comparisons.

### Deployment
Production runs on Oracle Cloud Free Tier (São Paulo region), IP-only for now (no domain yet, so no automatic HTTPS) — see `DEPLOY.md` for the full runbook and current checklist state. `COOKIE_SECURE=false` and the admin Streamlit port is IP-restricted at the network level are both *consequences of not having HTTPS yet*, not independent choices — don't "fix" one without the other when a domain is eventually added (`deploy/Caddyfile.com-dominio.example` has the HTTPS-ready config waiting).

## Known constraints (not stylistic preferences — don't relax these)

- Never copy questions or explanations from paid competitor platforms (Estratégia MED, Medcof, etc.) — official free sources (INEP) or original content only.
- Clinical explanations authored for questions must not be labeled as AI-generated — explicit user decision, don't reintroduce an "AI-generated" marker without asking first.
- Never type a password into a login/signup field via browser automation, including for test accounts — the user always logs in manually in an already-open tab.
