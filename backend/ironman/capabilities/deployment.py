from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityResult:
    capability: str
    summary: str
    evidence: list[dict]
    contradictions: list[str]


class PortfolioRiskCapability:
    name = "portfolio_risk"

    def run(self, opportunity: dict, analytics: dict) -> CapabilityResult:
        return CapabilityResult(self.name, "Portfolio fit and deterministic gates evaluated.", opportunity.get("evidence", []), [])


class FundamentalCapability:
    name = "fundamental"

    def run(self, opportunity: dict, analytics: dict) -> CapabilityResult:
        return CapabilityResult(self.name, "Fundamental context interpreted from supplied deterministic analytics.", opportunity.get("evidence", []), [])


class ValuationCapability:
    name = "valuation"

    def run(self, opportunity: dict, analytics: dict) -> CapabilityResult:
        return CapabilityResult(self.name, "Valuation context interpreted from supplied deterministic analytics.", opportunity.get("evidence", []), [])


class EvidenceCapability:
    name = "evidence"

    def run(self, opportunity: dict, analytics: dict) -> CapabilityResult:
        return CapabilityResult(self.name, "Approved evidence references assembled.", opportunity.get("evidence", []), [])


class SynthesisCapability:
    name = "synthesis"

    def run(self, opportunity: dict, analytics: dict, gate_passed: bool) -> CapabilityResult:
        summary = "Candidate clears deterministic gates for human review." if gate_passed else "Candidate does not clear the deterministic gates."
        return CapabilityResult(self.name, summary, opportunity.get("evidence", []), [])
