# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A study platform for medical residency exams (ENAMED/Revalida) with a question bank, performance dashboard, spaced repetition (SM-2), timed mock exams, and study materials (MediaFire-linked). Database is Postgres on Neon (region `sa-east-1`), connection string in `.streamlit/secrets.toml` (gitignored) for the Streamlit app, or the `DATABASE_URL` env var for everything else (`db.py` falls back to `os.environ` when `st.secrets` isn't available — see `db.py` top of file).

**Hybrid architecture, by deliberate design, not a half-finished migration:**
- Student-facing features (Painel, Praticar, Simulado, Revisão Espaçada, Materiais, busca) live in a FastAPI + React SPA (`api/`, `frontend/`).
- The 4 admin-only screens (Banco de Questões, Nova Questão, Importar Planilha, Sincronizar MediaFire) live permanently in the original Streamlit app (`app.py`, `ui.py`, `auth.py`) — decided explicitly, not migrating them (see `MIGRACAO.md` §4/§5).
- `db.py` and `repeticao_espacada.py` are the **single source of truth** for all business logic (SM-2 algorithm, filters, streak/ofensiva calculation, dashboard aggregation) and are shared unchanged by both the FastAPI app and the Streamlit app. Never duplicate business logic into the API layer or the frontend — add it to `db.py`/`repeticao_espacada.py` instead.
- Content classification is a fixed two-level taxonomy, `db.TAXONOMIA` (the 5 grandes áreas of the exams > especialidades), seeded by `init_db()`. Questions, materials and subtopicos carry `area_id` (the grande área — what the Painel aggregates) plus `especialidade_id`. Importers (spreadsheet, MediaFire sync) resolve free-text names with `db.classificar_nome_area` / `resolver_area_especialidade` and report unknown names as errors — never insert an `areas` row from an imported name (that's how MediaFire folders like "Aprenda Nefro" used to show up as areas). MediaFire subtopicos keep the original folder name in `subtopicos.origem`, which is how a re-sync finds them after they were renamed.

Read `MIGRACAO.md` (migration plan, phase-by-phase decisions, the real function→endpoint contract) and `DEPLOY.md` (production runbook, checklist of what's actually deployed) before making structural changes to the API or touching the production server. `HISTORICO.md` is the condensed history of decisions still in force ("why was this built this way"), the pending work, and the Streamlit admin CSS gotchas — check it before re-deriving a past decision. Superseded history exists only in git (the old `contextoconversaclaude.txt`).

The app is branded **Conduta**, but internal identifiers (systemd user `residenciamed`, service names, session cookie, demo e-mail, paths) deliberately kept the old name — renaming them breaks the deploy and open sessions.

## Commands

### Backend (FastAPI)
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload            # dev server, http://localhost:8000
pytest                                     # runs everything in tests/ (pytest.ini: testpaths = tests)
pytest tests/test_sm2.py                   # single file
pytest tests/test_sm2.py::test_nome        # single test
```
If `uvicorn --reload` keeps serving old routes after edits (has happened on this Windows machine), stop both uvicorn processes and start it again. `streamlit run` never picks up `db.py`/`ui.py` changes on refresh — restart it.
**There is no separate test database** — tests run directly against the production Neon Postgres (same `DATABASE_URL`/secrets as prod). Fixtures in `tests/conftest.py` create uuid-suffixed data (`pytest_<uuid>@teste.local`, `__pytest_area_<uuid>`) and clean up via `ON DELETE CASCADE` in teardown. Any new fixture must follow this pattern — never write a fixture without teardown, and never reuse real user data. Production also holds two non-real accounts: `demo@residenciamed.com` (fake history from `scripts/seed_demo_user.py`, plus spaced-repetition history from `scripts/seed_demo_revisao.py`; both idempotent) and `qa.claude@residenciamed.local` for browser QA.

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
- The official-edition simulado (`POST /simulados/oficial`, "Prova oficial" tab), the edition list and the banca filter read `questoes_provas` (question id, banca, edicao like `"2025/1"`, numero_prova = number in the INEP booklet). A question can belong to more than one booklet: Revalida 2025/2 and ENAMED 2025 applied the same questions 1–50, stored once and linked to both. `questoes.edicao`/`questoes.numero_prova` still hold the primary booklet only, because the server's older code reads them; `init_db()` backfilled the table from them when it was created. Any new import of an official exam must insert its `questoes_provas` rows (and fill the columns), or the edition won't be listed or will come out of order.

### `frontend/` (Vite + React 19 + TS + Tailwind v3)
- Tailwind v3 was an explicit choice over v4. The visual system is "Triagem" — read `DESIGN_TRIAGEM.md` before touching UI. Tokens are mapped in `tailwind.config.js` / `src/styles/theme.css`; dark mode via a `.dark` class on `<html>`. The five triage colors (`t1`–`t5`) only ever encode a triage level (`src/lib/triagem.ts`), never decoration, and primary buttons are ink (`bg-ink`), not a brand color. `REDESIGN.md` ("laudo clínico") now only governs the Streamlit admin screens.
- Tailwind only generates classes it finds written out literally: per-level classes are precomputed in `CLASSES_NIVEL` (`src/lib/triagem.ts`) — never build class names like `` `bg-t${n}` `` at runtime.
- Layout is a top bar with tabs (no side rail). Session screens (Praticar session, Simulado in progress, Revisão) render `<BarraFoco>` (`src/lib/foco.tsx`), which portals the session's own bar into the top bar and hides the tabs, so the shell never needs to know which session is running.
- TanStack Query (React Query) for server state. **Known pitfall already hit twice**: a hook with `staleTime: Infinity` reused across two different screens under the *same* queryKey leaks stale data from one screen's phase into another's (happened with `useItensSimulado` between "em andamento" and "resultado"). Before setting a long/infinite `staleTime`, confirm the queryKey is exclusive to one screen/phase, or invalidate explicitly before navigating (see `EmAndamento.tsx`).
- React Router paths are stable keys, deliberately decoupled from the nav label shown in the menu (same lesson learned the hard way on the Streamlit side, where the label used to double as the routing key).
- `src/lib/respostasQueue.ts` — module-level retry queue with backoff for answer submissions; invalidates the `["me"]` query on success so the topbar streak/counters update (they don't otherwise, since the queue lives outside React).
- Admin-only routes (`ACERVO` in `src/lib/nav.ts`) render `PermaneceNoStreamlit.tsx` (a placeholder linking to `VITE_STREAMLIT_URL`) instead of a real page — this is intentional per the Fase 7 decision, not a stub to fill in. Links to them appear only in the account menu, and only for `is_admin`.
- `frontend/.env.production` has no secrets (just `VITE_API_URL`/`VITE_STREAMLIT_URL`) but is easy to accidentally gitignore: the root `.gitignore` pattern for the backend's `.env.production` must stay anchored to the repo root (`/.env.production`), or it will also match and silently exclude the frontend one.

### Postgres specifics
- `LIKE` is case-sensitive in Postgres (unlike SQLite, which earlier docs incorrectly assumed). Any free-text filter in `db.py` must use `ILIKE`.
- Postgres doesn't auto-index foreign keys — indexes on `respostas.usuario_id`, `respostas.questao_id`, `questoes.area_id`, `questoes.banca` are created explicitly in `init_db()`.
- `revisao.proxima_revisao` is a real `TIMESTAMP` (migrated from `TEXT`/date-only), so short "review again in 10 minutes" scheduling works for real — don't regress this back to date-only comparisons.
- Neon drops connections when its compute suspends for inactivity, and psycopg2 only notices on the next query. `db.get_conn()` therefore pings (`SELECT 1`) any pooled connection idle for more than 30 s and replaces it if dead — without that, the first request after a quiet period failed with "connection already closed". Keep that check if you touch the pool; `tests/test_conexao.py` covers it.
- `questoes.area_id` and `materiais.area_id` are `ON DELETE CASCADE` to `areas`: deleting an area silently deletes its questions and materials. Always verify an area is empty first.
- Bulk changes to production data (imports, reclassification, text fixes): write a script that runs everything in one transaction, prints a summary and rolls back unless given an explicit apply flag; save a JSON backup of the touched rows; apply only after the user confirms. Update rows in place (never delete and re-insert questions) — `respostas` and `revisao` reference question ids.

### Question bank content
- One image per question, stored in the DB (`questoes.imagem` BYTEA + `imagem_mime`). Two figures → stack them into a single PNG.
- **Importing an official INEP exam** (done for Revalida 2022-2 through 2026-1 and ENAMED 2025):
  - Links: INEP's main page loads them by script, but each year tab (`https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/revalida/provas-e-gabaritos/{ano}`) has the PDF links in plain HTML — `curl` it and grep for `download.inep.gov.br`. Names changed over time: up to 2025/1, `{ed}_PV_objetiva_regular.pdf` and `{ed}_GB_objetiva_definitivo.pdf` with an underscore (`2025_1_…`; 2022-2 is `2022-2_PV_objetiva.pdf`); from 2025/2 on, `{ed}_caderno_1_….pdf` and `{ed}_gabarito_definitivo_caderno1.pdf` (2025/2's key is `2025_2_gabarito_caderno_1.pdf`, definitive despite the name). Always use caderno 1 and the definitive answer key.
  - If a booklet shares questions with one already in the bank (Revalida 2025/2 questions 1–50 are ENAMED 2025's), add a `questoes_provas` row to the existing question instead of inserting a copy.
  - The booklet has two columns: filter pdfplumber chars by x-center relative to the page middle before `extract_text()`, or the columns interleave. Tables flatten into one line and subscripts detach — rewrite those statements in prose. The perception questionnaire after Q100 can stick to the last question.
  - Figures: `page.images` bboxes (ignore the small repeated header logos ~135×17/145×40), `page.crop(bbox).to_image(resolution=200)`, and look at the PNG before saving — wrong-question crops have happened.
  - ENAMED 2025's PDF font (Calibri) has no ToUnicode map, so pdfplumber returns `(cid:N)`; the CIDs are Calibri glyph ids — decode by inverting the cmap of `C:\Windows\Fonts\calibri*.ttf` with fontTools (ligatures included). Its questionnaire reuses "QUESTÃO 1..9": take only the first occurrence of each number.
  - Leave out annulled questions and ones that depend on third-party images. Classify area + especialidade by the question's content, not booklet order. Fill `banca`, `ano`, `edicao`, `numero_prova`.
  - Explanations are written from scratch. Before saving, check each one argues for the official answer letter (caught one written for the wrong letter), no table debris remains, and images exist. Dedupe by banca + ano + start of statement.
- **Importing SP university exams** (done for USP 2026 and UNICAMP 2023; UNIFESP doesn't publish its booklet and Santa Casa only shows it behind a candidate login):
  - USP (FUVEST, `fuvest.br/residencia-medica-provas-e-gabarito`): only the current edition is online. Booklets AD1/AD2/AD3 are the same 120 questions shuffled, with a correspondence answer key — import AD1 numbering. The layout mixes full-width and two-column blocks, so extract with PyMuPDF text blocks (`page.get_text("blocks")`), not a page-middle split. Leave out annulled questions, questions with two accepted letters and questions whose image the booklet removed ("IMAGEM REMOVIDA NOS TERMOS DO ESTATUTO DA CRIANÇA E DO ADOLESCENTE").
  - UNICAMP (COMVEST, `comvest.unicamp.br/residenciamedica{ano}/provas.html`): from 2024 on, the acesso direto exam is short-answer, with no alternatives, so it can't be imported; 2023 (versions W–Z, same questions) is multiple choice. Figures sit in a "caderno de imagens" at the end of the booklet, cited as "Figura N (anexo)", and each stem ends with the question in capitals — convert it to sentence case, keeping acronyms and proper names.
  - Crop figures as page regions, with captions and (A)–(D) labels, not as separate images stacked together (that loses the captions). When the alternatives are images, store the labeled figure and the alternatives as "Imagem A." … "Imagem D." (user decision).

### Deployment
Production runs on Oracle Cloud Free Tier (São Paulo region); `DEPLOY.md` is the runbook and checklist. The server still serves over plain IP: `COOKIE_SECURE=false` and the admin Streamlit on port 8080 restricted to the admin's IP are both *consequences of not having HTTPS*, not independent choices — change them together.

HTTPS via the free DuckDNS subdomain (`conduta.duckdns.org`, `admin.conduta.duckdns.org`) is already committed (`deploy/Caddyfile`, env files) but **not applied**: the SSH key authorized on the server is on another computer. Every commit since then (Triagem redesign, official-exam simulado, especialidades taxonomy) is waiting on that deploy — steps and the server host key fingerprint are in `HISTORICO.md`. The database is shared, so data changes are already live while the server runs old code. `DEPLOY.md` still describes the IP setup; update it only after the HTTPS deploy is tested, and don't close port 8080 before that. Use the `residencia-med` SSH alias and keep remote commands short — long composite SSH commands have tripped the safety classifier.

## Known constraints (not stylistic preferences — don't relax these)

- Never copy questions or explanations from paid competitor platforms (Estratégia MED, Medcof, etc.) — official free sources (INEP) or original content only.
- Clinical explanations authored for questions must not be labeled as AI-generated — explicit user decision, don't reintroduce an "AI-generated" marker without asking first.
- Never type a password into a login/signup field via browser automation, including for test accounts — the user always logs in manually in an already-open tab.
- Never open a firewall port or Security List rule to `0.0.0.0/0` for a service without HTTPS — restrict it to the admin's /32 or use an SSH tunnel. If the safety classifier blocks such a change, the block is right.
- `git commit` / `git push` only when the user asks.
