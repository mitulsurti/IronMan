from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, Session

from ironman.db.base import Base


class EvidenceStatus(StrEnum):
    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT = "INSUFFICIENT"


class SourceTier(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DISCOVERY = "DISCOVERY"


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    source_provider: Mapped[str] = mapped_column(String(200), nullable=False)
    source_id: Mapped[str] = mapped_column(String(300), nullable=False)
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_tier: Mapped[str] = mapped_column(String(30), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    licensing: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("research_documents.id"), nullable=False)
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    claim_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    passage_reference: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceBoundaryError(ValueError):
    pass


def validate_document(document: ResearchDocument) -> None:
    if not document.source_provider or not document.source_id:
        raise EvidenceBoundaryError("evidence requires source provider and source ID")
    if not document.provenance or not document.provenance.get("source"):
        raise EvidenceBoundaryError("evidence requires provenance source")
    if document.status not in {status.value for status in EvidenceStatus}:
        raise EvidenceBoundaryError("invalid evidence status")
    if document.ingested_at.tzinfo is None or document.ingested_at.utcoffset() != timezone.utc.utcoffset(document.ingested_at):
        raise EvidenceBoundaryError("ingested_at must be UTC")
    if document.instrument_id is not None and not isinstance(document.instrument_id, UUID):
        raise EvidenceBoundaryError("instrument_id must be a canonical UUID")


def validate_claim_references(claims, evidence_ids: set[str], statuses: dict[str, str]) -> None:
    for claim in claims:
        if claim.kind.value == "FACT" and not claim.evidence_ids:
            raise EvidenceBoundaryError("FACT claims require evidence references")
        if not set(claim.evidence_ids).issubset(evidence_ids):
            raise EvidenceBoundaryError("claim references nonexistent evidence")
        if any(statuses.get(evidence_id) != EvidenceStatus.VALID.value for evidence_id in claim.evidence_ids):
            raise EvidenceBoundaryError("claim references evidence that is not currently valid")


def persist_document(session, document: ResearchDocument) -> ResearchDocument:
    validate_document(document)
    session.add(document)
    session.flush()
    return document


def persist_evidence_claim(session, claim: EvidenceClaim) -> EvidenceClaim:
    if claim.claim_kind == "FACT" and not claim.document_id:
        raise EvidenceBoundaryError("FACT evidence claims require a document reference")
    if session.get(ResearchDocument, claim.document_id) is None:
        raise EvidenceBoundaryError("evidence claim references nonexistent document")
    session.add(claim)
    session.flush()
    return claim


def validate_evidence_items(session: Session | None, items) -> None:
    """Validate application-supplied evidence before it is given to a research model."""
    for item in items:
        if not item.source or not item.provenance or not item.provenance.get("source"):
            raise EvidenceBoundaryError("evidence item requires source and provenance")
        if item.status not in {status.value for status in EvidenceStatus}:
            raise EvidenceBoundaryError("invalid evidence item status")
        if item.document_id is not None and session is not None:
            document = session.get(ResearchDocument, item.document_id)
            if document is None:
                raise EvidenceBoundaryError("evidence item references nonexistent document")
            if document.status != item.status:
                raise EvidenceBoundaryError("evidence item status does not match document status")
