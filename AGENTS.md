<!-- gentle-ai:project-context -->
# IST Investiga — Asistente de Accidentes (Django)

Plataforma web para investigación de accidentes laborales del **Instituto de Seguridad del Trabajo (IST)** de Chile. Django 5.2 con templates + HTMX, Gunicorn, Nginx, MySQL/SQLite.

## Project structure

```
investigacion-django_v2/
└── arbol_causa_accidentes_ist/   ← Django project root (manage.py lives here)
    ├── accidentes/               ← Main app: models, views, IA, templates
    │   ├── views_api/            ← Sub-flow endpoints (árbol, hechos, relato…)
    │   ├── views_ia.py           ← AI-powered view logic
    │   └── setting/prompt/       ← Versioned AI prompts (prompt.json)
    ├── accounts/                 ← Custom User model, RUT auth, superuser command
    ├── adminpanel/               ← Panel for investigation management
    ├── core/                     ← Django settings, urls, email services
    ├── utils/                    ← Cross-cutting utilities
    └── protected_media/          ← Uploaded/generated files (gitignored)
```

## Quick start

```powershell
# Django project root
cd arbol_causa_accidentes_ist

# Create .env (required — gitignored)
copy .env.example .env   # or create manually

# Use SQLite for local dev
$env:AMBIENTE = "desarrollo"

# Install deps
pip install -r requirements.txt

# Migrate + run
python manage.py migrate
python manage.py runserver
```

## Required `.env` vars

| Var | Required? | Notes |
|-----|-----------|-------|
| `AMBIENTE=desarrollo` | Dev | Switches DB to SQLite |
| `IA_PROVIDER=ollama` | Dev | Ollama is default for local dev |
| `OPENAI_API_KEY` | If OpenAI | Not needed for Ollama |
| `OLLAMA_BASE_URL` | If Ollama | Default: `http://localhost:11434/v1` |
| `OLLAMA_DEFAULT_MODEL` | If Ollama | Default: `qwen2.5:7b` |
| `DB_ENGINE`, `DB_NAME`, etc. | Prod | MySQL connection |

Other env vars read by settings: `API_EMAIL_CLIENT`, `API_EMAIL_SECRET`, `DEFAULT_MODEL`, `FALLBACK_MODEL`, `IST_EMAIL_ACTOR`.

## Auth

- **Login via RUT** (Chilean ID) — `accounts/backends.RutOnlyBackend`. Username/email not supported.
- Custom `User` model (`accounts.User`) with fields: `rut`, `rol`, `team`, `empresa`, `holding`.
- Roles: `admin`, `admin_ist`, `admin_holding`, `admin_empresa`, `coordinador`, `investigador`, `investigador_ist`.
- `ForcePasswordChangeMiddleware` in middleware stack.
- `python manage.py ensure_superuser` creates superuser from `DJANGO_SUPERUSER_*` env vars.

## AI integration

- **Two providers**: OpenAI (remote) or Ollama (local). Switch via `IA_PROVIDER` in `.env`.
- **Default**: Ollama with `qwen2.5:7b`. Start via `docker compose -f docker-compose-dev.yml up ollama`.
- OpenAI GPT (gpt-4.1-mini) optional, config via `DEFAULT_MODEL`/`FALLBACK_MODEL` env vars.
- All prompts versioned in `accidentes/setting/prompt/prompt.json` (Spanish, GPT-4.1-mini).
- `accidentes/views_ia.py` for AI views; `accidentes/views_api/` for sub-flow endpoints.
- `IA_LOG_PROMPTS = True` in settings (logs all prompts to console).
- **Lazy clients**: OpenAI/Ollama clients initialize on first use, not at import time. Missing API keys won't crash the server.

## Testing

- Skeleton only: empty `TestCase` classes in `accidentes/tests.py` and `adminpanel/tests.py`.
- **`python manage.py test`** — no pytest.
- No CI, no linters, no formatters, no pre-commit, no type hints.

## Deployment (Docker)

```powershell
# Development (SQLite container not needed, but MySQL still runs)
docker compose -f docker-compose-dev.yml up --build

# Production
docker compose -f docker-compose.yml up -d
```

- `gunicorn-cfg.py`: port **5005**, gthread worker, 4 workers/threads, 120s timeout.
- `entrypoint.sh`: runs `makemigrations` → `migrate` → `collectstatic` → optional seed data.
- Seed data via env vars: `RUN_IMPORT_HOLDINGS=1`, `RUN_SEED_DATA=1`, `RUN_SMU_DATA=1`, etc.
- Nginx serves staticfiles, proxies to gunicorn, internal `/protected_media_internal/` for file downloads.

## Key quirks

- Django project root is **`arbol_causa_accidentes_ist/`** — one level below repo root.
- `settings.py` uses `python-decouple` for `.env` but also reads `os.getenv` directly for DB vars.
- Windows: prints with emoji (`✅`, `🔧`, etc.) crash because cp1252 can't encode them. Use plain text in `print()` calls.
- `AMBIENTE=desarrollo` uses SQLite; anything else (default) uses MySQL.
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'http')` — uses `http`, not `https`.
- `ALLOWED_HOSTS = ['*']`, `CSRF_TRUSTED_ORIGINS` has hardcoded IPs.
- `.gitignore` excludes `accidentes/setting/data/*` — demo data JSON is not versioned.
- `db.sqlite3` **is committed** (has demo data). `staticfiles/` is gitignored (generated via `collectstatic`).
- Container runs `makemigrations` on every start — not just `migrate`.
- Graphviz installed in Docker image for tree visualization (imported via `graphviz` pip package).
- Email sent via custom backend `core.email_backends.ist_via_token` → `apiemail.ist.cl`.
