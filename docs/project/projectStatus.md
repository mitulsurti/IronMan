# IronMan Project Status

## Identity
IronMan is a personal-use investment intelligence and decision-support system for one user. It is a modular monolith with deterministic financial authority, advisory AI, and human-only execution.

## Current phase
**Phase 3N — Real-data Capital Deployment validation slice complete.** Phase 2 remains closed. SQLite is the local development/test database; PostgreSQL validation remains deferred.

## Completed
- Phase 1–2: foundation and authoritative ledger.
- Phase 3A–3J: Capital Deployment, provider-independent data fabric, deterministic analytics, bounded research/thesis/valuation/portfolio-risk capabilities, Azure provider boundary, and Synthesis Agent.
- Phase 3K–3L: Yahoo Finance current-price and selected fundamental observation adapters.
- Phase 3M: optional Azure smoke-test path and offline real-data-shaped validation.
- Phase 3O — Live connectivity validation attempted. Phase 2 remains closed. SQLite is the local development/test database; PostgreSQL validation remains deferred.

## Validation
- Full backend suite: **101 passed, 1 skipped, 0 failed**.
- Compilation: passed.
- Azure live smoke test: skipped because live configuration was unavailable; no live Azure request was made.
- Automated tests use deterministic fixtures/mocks; no live Yahoo dependency.

## Deferred
- PostgreSQL migration/integration validation.
- Live Azure validation until credentials/configuration are available.
- Additional providers, broad ingestion, crawling, semantic search, UI, Zerodha, and advanced intelligence capabilities.

## Last checkpoint
2026-09-14: Phase 3O live connectivity attempts recorded: Yahoo price/fundamentals returned HTTP 429; Azure was skipped for missing configuration. Offline suite remains 101 passed, 1 skipped. No transaction was executed.

## Next recommended action
Resolve Yahoo rate limiting/provider access and configure Azure endpoint/key/deployment if live validation is required. Do not make live services a normal test dependency.

## Useful commands
```text
cd backend
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m compileall -q ironman migrations
```
# IronMan Project Status

## Identity
IronMan is a personal-use investment operating system for one user. It is a modular monolith with deterministic financial authority, human-only execution, and advisory AI planned for later phases.

## Current phase
**Phase 3S — Fixed-income comparator capability implemented; Phase 2 remains closed.** Normal tests remain offline and deterministic; PostgreSQL validation remains deferred.
## Completed

## Locked references
- Focused fundamental tests: **4 passed**; full backend suite remains **94 passed**.
- Phase 3J includes one controlled Synthesis Agent combining supplied research, thesis, valuation, portfolio-risk, alternatives, evidence, and deterministic gate outputs.
- Full backend suite after Evidence boundary: **83 passed**.
- Azure adapter uses environment-only endpoint/key/API-version configuration and remains behind `ModelGateway`; fake-model operation remains available.
- Research output validation preserves supplied-evidence claim traceability and records provider/deployment/model/prompt/latency/status/token telemetry when available.
The foundation preserves acquisition event identity, remaining quantity, cost basis, and explicit consumption allocations without selecting FIFO, average cost, or another universal policy. PostgreSQL persistence and reconstruction of these allocation rows still require integration validation.

2026-09-14: Phase 3S added separate FixedIncomeComparatorAgent over application-supplied fixed-income facts. Decimal cash-flow totals, settlement consistency, explicit currency/maturity/liquidity/credit/tax dimensions, insufficiency/conflict abstention, selective Capital Deployment invocation, and synthesis consumption were validated. Focused comparator tests: 6 passed. Full backend suite: 121 passed, 6 live tests deselected.
- The local `ironman` role/database and `.env` connection string still need to be created/configured by the user; no credentials are stored in the repository.
Phase 3S is complete. Fixed-income comparison is bounded and fixture-driven; no live fixed-income provider, yield prediction, ranking score, allocation, or broker-write capability was introduced.

## Last checkpoint
2026-09-14: Phase 3S checkpoint: G-Sec, T-bill, and corporate-bond/NCD fixtures validated through FixedIncomeComparatorAgent. Missing maturity/cash flows, invalid currency, stale data, and conflicting settlement terms abstain. Comparator output is selectively persisted and passed to existing synthesis; normal suite: 121 passed, 6 deselected.

## Next recommended action
Fixed-income comparison is complete for supplied deterministic terms. Future expansion must separately validate any additional fixed-income data inputs; no credentials are stored in the repository and no broker writes are permitted.

## Useful commands
```text
cd backend
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m pytest -m live
..\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```
