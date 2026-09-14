# IronMan

Personal-use investment operating system. Phase 1 establishes the safe application foundation only.

## Local setup

1. Create a Python 3.13 virtual environment.
2. Install the backend development dependencies from `backend/pyproject.toml`.
3. Copy `.env.example` to `.env` and set `DATABASE_URL` if PostgreSQL is not on the default local URL.
4. Start PostgreSQL with `docker compose up -d postgres`, or use an existing PostgreSQL instance.
5. Run migrations with `alembic -c alembic.ini upgrade head` from `backend/`.
6. Start the API with `uvicorn ironman.api.main:app --app-dir backend --reload` from the repository root.
7. Start the frontend with `npm install` and `npm run dev` from `frontend/`.
8. Run tests with `pytest -c pytest.ini` from `backend/`.

PostgreSQL is the only required external service for this phase. Docker Compose is optional and is provided for local database convenience.

## Phase 1 scope

The foundation includes configuration, PostgreSQL connectivity, Alembic, a health endpoint, a single-user authentication boundary, structured logging, financial precision primitives, audit-event foundations, frontend shell, and tests. It does not include the ledger, broker integration, AI, trading, or portfolio calculations.
