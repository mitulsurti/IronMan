from datetime import datetime, timezone
from decimal import Decimal
import json

from sqlalchemy.orm import Session

from ironman.capabilities.deployment import EvidenceCapability, FundamentalCapability, PortfolioRiskCapability, SynthesisCapability, ValuationCapability
from ironman.intelligence.analytics import IntelligenceGateError, evaluate_opportunity, gate_is_actionable, load_portfolio_context, valuation_facts
from ironman.intelligence.models import InsightAction, Opportunity, StructuredInsight
from ironman.data_fabric.models import DataObservation, FreshnessState, ObservationQuality, ObservationType
from ironman.data_fabric.service import observation_gate
from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.research.agent import FakeResearchModel, ResearchEvidenceAgent
from ironman.research.fundamental_thesis import FakeFundamentalThesisModel, FundamentalThesisAgent
from ironman.research.schemas import ResearchRequest
from ironman.research.valuation import FakeValuationModel, ValuationAgent
from ironman.research.portfolio_risk import FakePortfolioRiskModel, PortfolioRiskOpportunityCostAgent
from ironman.research.macro_fx import FakeMacroFXModel, MacroFXAgent
from ironman.research.fixed_income import FakeFixedIncomeComparatorModel, FixedIncomeComparatorAgent
from ironman.research.synthesis import FakeSynthesisModel, SynthesisAgent
from ironman.research.synthesis import FakeSynthesisModel, SynthesisAgent


class CapitalDeploymentOrchestrator:
    def __init__(self, *, synthesis_gateway: ModelGateway | None = None) -> None:
        self.portfolio = PortfolioRiskCapability()
        self.fundamental = FundamentalCapability()
        self.valuation = ValuationCapability()
        self.evidence = EvidenceCapability()
        self.synthesis = SynthesisCapability()
        self.research_agent = ResearchEvidenceAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-research", "fixture-v1", "research", "research-prompt-v1", {})]),
            {"fake": FakeResearchModel()},
        ))
        self.fundamental_thesis_agent = FundamentalThesisAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-fundamental-thesis", "fixture-v1", "fundamental_thesis", "fundamental-thesis-prompt-v1", {})]),
            {"fake": FakeFundamentalThesisModel()},
        ))
        self.valuation_agent = ValuationAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-valuation", "fixture-v1", "valuation", "valuation-prompt-v1", {})]),
            {"fake": FakeValuationModel()},
        ))
        self.portfolio_risk_agent = PortfolioRiskOpportunityCostAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-portfolio-risk", "fixture-v1", "portfolio_risk", "portfolio-risk-prompt-v1", {})]),
            {"fake": FakePortfolioRiskModel()},
        ))
        self.macro_fx_agent = MacroFXAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-macro-fx", "fixture-v1", "macro_fx", "macro-fx-prompt-v1", {})]),
            {"fake": FakeMacroFXModel()},
        ))
        self.fixed_income_comparator_agent = FixedIncomeComparatorAgent(ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-fixed-income", "fixture-v1", "fixed_income_comparator", "fixed-income-prompt-v1", {})]),
            {"fake": FakeFixedIncomeComparatorModel()},
        ))
        self.synthesis_agent = SynthesisAgent(synthesis_gateway or ModelGateway(
            ModelRegistry([ModelSpec("fake", "fixture-synthesis", "fixture-v1", "synthesis", "synthesis-prompt-v1", {})]),
            {"fake": FakeSynthesisModel()},
        ))

    def run(self, session: Session, state_version, request, actor_id: str) -> StructuredInsight:
        context = load_portfolio_context(state_version)
        candidates = []
        observation_map = {}
        for item in request.opportunities:
            observation_ids = item.observation_ids
            values = item.model_dump(exclude={"observation_ids"})
            values["analytics"] = {**values.get("analytics", {}), "observation_ids": [str(value) for value in observation_ids]}
            candidate = Opportunity(**values, created_at=datetime.now(timezone.utc))
            candidates.append(candidate)
            observation_map[candidate.id] = list(session.query(DataObservation).filter(DataObservation.id.in_(observation_ids))) if observation_ids else []
        best = None
        best_result = None
        for candidate in candidates:
            result = evaluate_opportunity(context, candidate, request.amount, request.max_concentration)
            observations = observation_map[candidate.id]
            if candidate.instrument_id and not observations:
                result["gates"]["observations"] = "INSUFFICIENT"
            elif observations:
                result["gates"]["observations"] = observation_gate(observations, required_types={ObservationType.PRICE})
            if best_result is None or sum(value == "PASS" for value in result["gates"].values()) > sum(value == "PASS" for value in best_result["gates"].values()):
                best, best_result = candidate, result
        assert best is not None and best_result is not None
        capabilities = [self.portfolio]
        if best.kind not in ("CASH", "FIXED_INCOME"):
            capabilities.extend([self.fundamental, self.valuation])
        capabilities.append(self.evidence)
        research = [cap.run(best.__dict__, best_result["analytics"]) for cap in capabilities]
        structured_evidence = [item for item in best.evidence if item.get("evidence_id") and item.get("excerpt")]
        research_result = None
        fundamental_thesis_result = None
        valuation_result = None
        portfolio_risk_result = None
        macro_fx_result = None
        fixed_income_comparison_result = None
        synthesis_result = None
        synthesis_result = None
        deterministic_valuation = valuation_facts({**best.analytics.get("valuation_inputs", {}), "currency": best.currency, "assumptions": best.analytics.get("valuation_assumptions", {})})
        if structured_evidence:
            research_result = self.research_agent.run(ResearchRequest(
                question=f"Assess {best.name} for the capital deployment question.",
                instrument_id=best.instrument_id,
                observations=[best_result["analytics"]],
                evidence=structured_evidence,
            ))
            thesis = best.analytics.get("thesis")
            if thesis:
                fundamental_thesis_result = self.fundamental_thesis_agent.run(ResearchRequest(
                    question=f"Assess the fundamental evidence against the investment thesis for {best.name}.",
                    instrument_id=best.instrument_id,
                    thesis=thesis,
                    observations=[best_result["analytics"]],
                    evidence=structured_evidence,
                ))
            valuation_result = self.valuation_agent.run(ResearchRequest(
                question=f"Interpret the supplied valuation facts for {best.name}.",
                instrument_id=best.instrument_id,
                observations=[best_result["analytics"]],
                evidence=structured_evidence,
            ), deterministic_valuation)
            portfolio_risk_result = self.portfolio_risk_agent.run(ResearchRequest(
                question=f"Assess portfolio fit and opportunity cost for {best.name}.",
                instrument_id=best.instrument_id,
                portfolio_state_version_id=state_version.id,
                observations=[best_result["analytics"]],
                evidence=structured_evidence,
            ), {**best_result["analytics"], "gates": best_result["gates"]}, [{"name": item.name, "kind": item.kind, "analytics": item.analytics} for item in candidates])
            macro_observations = best.analytics.get("macro_fx_observations", [])
            if best.analytics.get("macro_fx_relevant") and macro_observations:
                macro_fx_result = self.macro_fx_agent.run(ResearchRequest(
                    question=f"Assess macroeconomic and currency context for {best.name}.",
                    instrument_id=best.instrument_id,
                    thesis=best.analytics.get("thesis"),
                    observations=[best_result["analytics"]],
                    evidence=structured_evidence,
                ), macro_observations)
            fixed_income_facts = best.analytics.get("fixed_income_facts")
            if best.analytics.get("fixed_income_relevant") and fixed_income_facts:
                fixed_income_comparison_result = self.fixed_income_comparator_agent.run(
                    ResearchRequest(
                        question=f"Compare the fixed-income alternative for {best.name} against the supplied capital use.",
                        instrument_id=best.instrument_id,
                        portfolio_state_version_id=state_version.id,
                        observations=[best_result["analytics"]],
                        evidence=structured_evidence,
                    ),
                    fixed_income_facts,
                    best.analytics.get("fixed_income_alternative"),
                )
            synthesis_result = self.synthesis_agent.run(
                ResearchRequest(
                    question=f"Synthesize the supplied assessment for {best.name}.",
                    instrument_id=best.instrument_id,
                    portfolio_state_version_id=state_version.id,
                    observations=[best_result["analytics"]],
                    evidence=structured_evidence,
                ),
                portfolio_state_version_id=state_version.id,
                portfolio_facts=best_result["analytics"],
                deterministic_valuation=deterministic_valuation,
                research=research_result,
                fundamental_thesis=fundamental_thesis_result,
                valuation=valuation_result,
                portfolio_risk=portfolio_risk_result,
                macro_fx=macro_fx_result,
                fixed_income_comparison=fixed_income_comparison_result,
                alternatives=[{"name": item.name, "kind": item.kind, "analytics": item.analytics} for item in candidates],
                gates=best_result["gates"],
            )
            synthesis_result = self.synthesis_agent.run(
                ResearchRequest(question=f"Synthesize the supplied assessment for {best.name}.", instrument_id=best.instrument_id, portfolio_state_version_id=state_version.id, observations=[best_result["analytics"]], evidence=structured_evidence),
                portfolio_state_version_id=state_version.id,
                portfolio_facts=best_result["analytics"],
                deterministic_valuation=deterministic_valuation,
                research=research_result,
                fundamental_thesis=fundamental_thesis_result,
                valuation=valuation_result,
                portfolio_risk=portfolio_risk_result,
                macro_fx=macro_fx_result,
                fixed_income_comparison=fixed_income_comparison_result,
                alternatives=[{"name": item.name, "kind": item.kind, "analytics": item.analytics} for item in candidates],
                gates=best_result["gates"],
            )
        actionable = gate_is_actionable(best_result["gates"])
        synthesis = self.synthesis.run(best.__dict__, best_result["analytics"], actionable)
        action = InsightAction.ADD if actionable and best.kind != "CASH" else InsightAction.WAIT if best.kind == "CASH" else InsightAction.NO_ACTION
        reason = None if actionable else "; ".join(f"{key}: {value}" for key, value in best_result["gates"].items() if value != "PASS")
        insight = StructuredInsight(
            portfolio_state_version_id=state_version.id,
            requested_amount=request.amount,
            action=action.value,
            horizon=request.horizon,
            conclusion=synthesis.summary,
            thesis=json.dumps(best.analytics.get("thesis"), sort_keys=True) if isinstance(best.analytics.get("thesis"), dict) else best.analytics.get("thesis"),
            instrument_id=best.instrument_id,
            portfolio_context={"cash": {f"{account}:{currency}": str(amount) for (account, currency), amount in context["cash"].items()}},
            analytics={**best_result["analytics"], "deterministic_valuation": deterministic_valuation, "research": research_result.model_dump(mode="json") if research_result else None, "fundamental_thesis": fundamental_thesis_result.model_dump(mode="json") if fundamental_thesis_result else None, "valuation": valuation_result.model_dump(mode="json") if valuation_result else None, "portfolio_risk": portfolio_risk_result.model_dump(mode="json") if portfolio_risk_result else None, "macro_fx": macro_fx_result.model_dump(mode="json") if macro_fx_result else None, "fixed_income_comparison": fixed_income_comparison_result.model_dump(mode="json") if fixed_income_comparison_result else None, "synthesis": synthesis_result.model_dump(mode="json") if synthesis_result else None},
            evidence=synthesis.evidence,
            alternatives=[{"name": item.name, "kind": item.kind} for item in candidates],
            gates=best_result["gates"],
            confidence={"evidence": "provided" if synthesis.evidence else "insufficient", "model": "deterministic-fixture"},
            contradictions=synthesis.contradictions,
            abstention_reason=reason,
            created_at=datetime.now(timezone.utc),
        )
        session.add(insight)
        return insight
