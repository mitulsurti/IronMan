from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ironman.auth import Actor, get_current_actor
from ironman.config import get_settings
from ironman.db.session import database_is_healthy
from ironman.db.session import get_db
from ironman.ledger.models import Account, Instrument, InstrumentIdentifier, LedgerEvent, LedgerLeg, PortfolioStateVersion, TaxLotAllocation
from ironman.ledger.schemas import AccountCreate, AccountRead, EventCreate, EventRead, InstrumentCreate, InstrumentRead, InstrumentIdentifierCreate, StateVersionRead
from ironman.ledger.service import DuplicateLedgerEvent, append_event, create_state_version
from ironman.ledger.domain import validate_event
from ironman.logging import configure_logging
from ironman.intelligence.models import InsightDecision, StructuredInsight
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, DecisionCreate, DecisionRead, InsightRead, InsightRequestResponse
from ironman.data_fabric.models import DataObservation, DataSource
from ironman.data_fabric.schemas import DataSourceCreate, ObservationCreate
from ironman.data_fabric.service import ObservationValidationError, persist_observation, persist_source

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name)
deployment_orchestrator = CapitalDeploymentOrchestrator()


@app.get("/health")
def health() -> JSONResponse:
    try:
        database_is_healthy()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "unavailable"})
    return JSONResponse(content={"status": "ok", "database": "ok"})


@app.get("/api/v1/me")
def current_user(actor: Actor = Depends(get_current_actor)) -> dict[str, str]:
    return {"actor_id": actor.actor_id, "actor_type": actor.actor_type}


@app.post("/api/v1/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> Account:
    account = Account(**payload.model_dump(), created_at=datetime.now(timezone.utc))
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get("/api/v1/accounts", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> list[Account]:
    return list(db.scalars(select(Account).order_by(Account.created_at, Account.id)))


@app.post("/api/v1/instruments", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> Instrument:
    instrument = Instrument(**payload.model_dump(), created_at=datetime.now(timezone.utc))
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@app.get("/api/v1/instruments", response_model=list[InstrumentRead])
def list_instruments(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> list[Instrument]:
    return list(db.scalars(select(Instrument).order_by(Instrument.created_at, Instrument.id)))


@app.post("/api/v1/instruments/{instrument_id}/identifiers", status_code=status.HTTP_201_CREATED)
def add_identifier(instrument_id, payload: InstrumentIdentifierCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> dict:
    if db.get(Instrument, instrument_id) is None:
        raise HTTPException(status_code=404, detail="instrument not found")
    identifier = InstrumentIdentifier(instrument_id=instrument_id, **payload.model_dump())
    db.add(identifier)
    db.commit()
    db.refresh(identifier)
    return {"id": str(identifier.id), "instrument_id": str(instrument_id), "provider": identifier.provider, "identifier": identifier.identifier}


@app.post("/api/v1/portfolio-state-versions", response_model=StateVersionRead, status_code=status.HTTP_201_CREATED)
def create_portfolio_state_version(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    events = list(db.scalars(select(LedgerEvent).order_by(LedgerEvent.effective_at, LedgerEvent.sequence, LedgerEvent.id)).unique())
    version = create_state_version(db, events, calculation_version="phase2-ledger-v1")
    db.commit()
    db.refresh(version)
    return version


@app.get("/api/v1/portfolio-state-versions", response_model=list[StateVersionRead])
def list_portfolio_state_versions(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    return list(db.scalars(select(PortfolioStateVersion).order_by(PortfolioStateVersion.created_at)))


@app.post("/api/v1/ledger/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> LedgerEvent:
    try:
        validate_event(payload.event_type, [leg.model_dump() for leg in payload.legs], payload.effective_at, correlation_id=payload.correlation_id, correction_of_id=payload.correction_of_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    event = LedgerEvent(
        **payload.model_dump(exclude={"legs", "lot_allocations"}),
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        created_at=datetime.now(timezone.utc),
    )
    legs = [LedgerLeg(**leg.model_dump()) for leg in payload.legs]
    try:
        append_event(db, event, legs, allocations=payload.lot_allocations)
        db.commit()
    except DuplicateLedgerEvent as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate source event") from exc
    db.refresh(event)
    return event


@app.get("/api/v1/ledger/events", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)) -> list[LedgerEvent]:
    return list(db.scalars(select(LedgerEvent).order_by(LedgerEvent.effective_at, LedgerEvent.sequence, LedgerEvent.id)))


@app.post("/api/v1/data-sources", status_code=status.HTTP_201_CREATED)
def create_data_source(payload: DataSourceCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    source = persist_source(db, DataSource(**payload.model_dump(), created_at=datetime.now(timezone.utc)))
    db.commit()
    return {"id": source.id}


@app.post("/api/v1/data-observations", status_code=status.HTTP_201_CREATED)
def create_data_observation(payload: ObservationCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    try:
        observation = persist_observation(db, DataObservation(**payload.model_dump(), observation_type=payload.observation_type.value, quality=payload.quality.value, freshness=payload.freshness.value, created_at=datetime.now(timezone.utc)))
        db.commit()
    except ObservationValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": observation.id}


@app.post("/api/v1/intelligence/capital-deployment", response_model=InsightRequestResponse, status_code=status.HTTP_201_CREATED)
def capital_deployment(payload: CapitalDeploymentRequest, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    state_version = db.get(PortfolioStateVersion, payload.portfolio_state_version_id)
    if state_version is None:
        raise HTTPException(status_code=404, detail="portfolio state version not found")
    insight = deployment_orchestrator.run(db, state_version, payload, actor.actor_id)
    db.commit()
    return {"insight_id": insight.id}


@app.get("/api/v1/intelligence/insights/{insight_id}", response_model=InsightRead)
def get_insight(insight_id, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    insight = db.get(StructuredInsight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="insight not found")
    return insight


@app.post("/api/v1/intelligence/insights/{insight_id}/decisions", response_model=DecisionRead, status_code=status.HTTP_201_CREATED)
def record_insight_decision(insight_id, payload: DecisionCreate, db: Session = Depends(get_db), actor: Actor = Depends(get_current_actor)):
    if db.get(StructuredInsight, insight_id) is None:
        raise HTTPException(status_code=404, detail="insight not found")
    decision = InsightDecision(insight_id=insight_id, actor_id=actor.actor_id, created_at=datetime.now(timezone.utc), **payload.model_dump())
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
