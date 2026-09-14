# PERSONAL AI INVESTMENT OPERATING SYSTEM

## Detailed Product & Technical Specification — Version 1.1

**Product type:** Personal AI-powered multi-asset investment intelligence and portfolio-management system
**Primary user:** Single retail investor
**Primary geography:** India
**Investment markets:** India + United States
**Execution model:** Human execution only
**AI execution authority:** None
**Broker integration:** Zerodha / Kite MCP, read-only
**Infrastructure preference:** Self-controlled infrastructure; Azure credits may be used where economically appropriate
**Architecture philosophy:** Deterministic financial computation + AI research/reasoning + explicit investment governance

---

# 1. EXECUTIVE SUMMARY

The Personal AI Investment Operating System is a private investment intelligence platform designed to help a retail investor make better capital-allocation decisions across a diversified multi-asset portfolio.

It is **not an autonomous trading bot**.

Its primary purpose is to answer:

> **Given my goals, investment policy, existing portfolio, available capital, market conditions, valuations, risks, taxes, liquidity and available opportunities, what is the best use of my next rupee/dollar of capital?**

The system covers:

* Indian equities
* US equities
* Government securities
* Treasury bills
* State development loans
* Corporate bonds/NCDs
* Debt funds
* FDs
* MLDs
* Structured fixed-income products
* Gold
* Cash / near-cash
* A separate tactical/positional equity/ETF sleeve

Oil is **not an investment asset in the system**. Oil is treated as a macroeconomic input affecting inflation, rates, currencies, sectors, margins and portfolio risk.

The system combines:

```text
Investor Profile
        ↓
Investment Policy / IPS
        ↓
Master Portfolio + Transaction Ledger
        ↓
Data Fabric
        ↓
Deterministic Analytical Engines
        ↓
AI Research & Reasoning Layer
        ↓
Opportunity / Portfolio / Tactical Engines
        ↓
Decision Engine
        ↓
Human Approval
        ↓
Manual Execution
        ↓
Outcome / Performance / Attribution
        ↓
Thesis & Process Learning
```

The system must always be capable of concluding:

> **NO ACTION**

---

# 2. PRODUCT VISION

Create a personal investment operating system that behaves like a disciplined investment research and portfolio-management function rather than a collection of stock-picking tools.

The system should continuously answer five questions:

### 2.1 What do I own?

Complete portfolio truth across all assets and accounts.

### 2.2 What is happening?

Markets, companies, rates, currencies, macroeconomics, credit and portfolio conditions.

### 2.3 What should I consider?

Identify attractive opportunities across the entire investable universe.

### 2.4 What should I do?

Determine the appropriate action considering the **existing portfolio**, not merely the standalone attractiveness of an asset.

### 2.5 What happened afterward?

Measure:

* decision quality
* portfolio performance
* risk
* attribution
* thesis validity
* recommendation accuracy
* opportunity cost

---

# 3. PRODUCT PRINCIPLES

## 3.1 Portfolio first, security second

The system must never evaluate an investment solely in isolation.

A security can be excellent but still be a poor addition because the portfolio already has excessive exposure to:

* the same sector
* geography
* factor
* issuer
* currency
* economic driver
* correlated securities

---

## 3.2 Risk can veto opportunity

A highly attractive opportunity must not automatically override:

* concentration limits
* liquidity requirements
* risk budgets
* investment-policy constraints
* tax considerations
* capital requirements

---

## 3.3 Deterministic computation, AI reasoning

Use traditional software for:

* arithmetic
* financial ratios
* valuation calculations
* portfolio weights
* risk calculations
* performance calculations
* tax calculations
* portfolio constraints
* backtesting
* reconciliation

Use AI for:

* research
* document understanding
* synthesis
* contradiction detection
* thesis development
* explanation
* qualitative reasoning
* research prioritization

AI should **not become the calculator of record**.

---

## 3.4 Evidence before conclusion

Every material investment claim should have traceable evidence.

The system must distinguish:

> **Evidence confidence**

from:

> **Model/reasoning confidence**

Strong evidence does not necessarily imply a strong investment conclusion, and vice versa.

---

## 3.5 Human capital allocation

The AI may:

* research
* analyze
* rank
* recommend
* warn
* explain

The human decides:

* whether to invest
* how much to invest
* whether to override
* whether to execute

---

## 3.6 No autonomous execution

The system must not:

* place orders
* modify orders
* cancel orders
* transfer money
* autonomously rebalance
* execute trades

Zerodha integration is read-only.

---

## 3.7 No unnecessary complexity

Explicitly avoid:

* HFT
* autonomous trading
* options scalping
* reinforcement-learning trader
* massive agent swarm
* continuous portfolio optimization
* social-media sentiment swarm
* AI price prediction as the core investment methodology
* microservices for their own sake

---

# 4. TARGET USER

Initial product scope is deliberately:

> **One sophisticated retail investor managing his own capital.**

The system is not initially designed as:

* an investment-adviser platform
* a wealth-management SaaS
* a broker
* a trading platform
* a public recommendation service

Any future multi-user/advisory commercialization requires a separate regulatory, legal, security and suitability architecture.

---

# 5. INVESTMENT UNIVERSE

## 5.1 Indian equities

* NSE-listed equities
* BSE-listed equities
* ETFs
* REITs/InvITs where supported
* IPO/new listings where data permits

## 5.2 US equities

* NYSE
* NASDAQ
* US-listed ETFs
* ADRs where applicable

## 5.3 Fixed income

* G-Secs
* T-bills
* SDLs
* Corporate bonds
* NCDs
* Debt funds
* FDs
* MLDs
* Structured products

## 5.4 Gold

Investable gold exposure:

* Gold ETFs
* Sovereign/appropriate government gold instruments where applicable
* Other approved gold holdings

## 5.5 Cash

* bank cash
* broker cash
* liquid/near-cash instruments

## 5.6 Tactical sleeve

Separate allocation for:

* positional equity trades
* ETFs
* tactical opportunities

Typical horizon:

> **2–12 weeks**

## 5.7 Oil

Oil is:

> **Macro variable only**

Used for:

* inflation analysis
* commodity-cycle analysis
* sector analysis
* geopolitical risk
* India's current-account sensitivity
* currency analysis
* interest-rate implications

It is not treated as an investable portfolio position.

---

# 6. CORE INVESTMENT HORIZONS

## Core portfolio

Approximately:

> **6 months to 5+ years**

Primary focus:

* compounding
* valuation
* fundamentals
* portfolio construction
* income
* capital preservation
* strategic asset allocation

## Tactical portfolio

Approximately:

> **2–12 weeks**

Primary focus:

* momentum
* trend
* catalysts
* technical structure
* relative strength
* volatility
* risk/reward
* tactical regime

The two systems must remain logically separate.

---

# 7. INVESTOR PROFILE ENGINE

The system must maintain a structured investor profile.

Inputs:

### Objectives

* wealth creation
* capital preservation
* income
* liquidity
* specific financial goals

### Risk tolerance

How much volatility/drawdown the investor is psychologically willing to tolerate.

### Risk capacity

How much financial risk the investor can actually absorb.

### Liquidity

* emergency requirements
* known future expenditures
* minimum cash requirement
* illiquid-asset tolerance

### Time horizons

* short
* medium
* long

### Liabilities

The system should support meaningful liabilities and future obligations without attempting to become a full financial-planning platform.

### Constraints

* asset-class restrictions
* concentration restrictions
* tax considerations
* liquidity restrictions
* tactical risk budget
* execution restrictions

---

# 8. GOAL / PORTFOLIO BUCKET MODEL

The system should support goal-oriented capital allocation.

Example:

```text
TOTAL CAPITAL

├── Long-Term Wealth
├── Medium-Term Goals
├── Liquidity Reserve
└── Tactical Capital
```

Each goal/bucket may have:

* target amount
* current amount
* horizon
* required liquidity
* risk tolerance
* target allocation
* funding status

Full financial planning is not required in V1, but the underlying data model must support it.

---

# 9. INVESTMENT POLICY / IPS ENGINE

The Investment Policy Statement is the **highest-level investment constraint layer**.

It defines:

* target asset allocation
* minimum allocation
* maximum allocation
* position limits
* sector limits
* issuer limits
* geography limits
* currency exposure limits
* liquidity requirements
* tactical risk budget
* rebalancing rules
* risk limits
* tax constraints
* investment exclusions
* execution rules

Example:

```text
Indian Equity:
Target 45%
Min 35%
Max 55%

US Equity:
Target 20%
Min 10%
Max 30%

Fixed Income:
Target 20%
Min 15%
Max 30%

Gold:
Target 10%
Min 5%
Max 15%

Cash:
Target 5%
Min 3%
Max 10%

Tactical:
Maximum 10%
```

The actual values are user-configurable.

---

# 10. DECISION RIGHTS

Decision authority must be encoded explicitly.

| Decision                | AI | System | Human |
| ----------------------- | -: | -----: | ----: |
| Retrieve data           |  ✓ |      ✓ |       |
| Research                |  ✓ |        |       |
| Calculate metrics       |    |      ✓ |       |
| Identify opportunities  |  ✓ |      ✓ |       |
| Assess risk             |    |      ✓ |       |
| Recommend               |  ✓ |      ✓ |       |
| Change IPS              |  ✗ |      ✗ |     ✓ |
| Change risk limits      |  ✗ |      ✗ |     ✓ |
| Approve investment      |  ✗ |      ✗ |     ✓ |
| Override recommendation |  ✗ |        |     ✓ |
| Execute trade           |  ✗ |      ✗ |     ✓ |
| Transfer money          |  ✗ |      ✗ |     ✓ |

AI recommendations cannot override deterministic policy constraints.

---

# 11. MASTER PORTFOLIO LEDGER

The Master Portfolio Ledger is the system's canonical representation of what the investor owns.

It must include:

* Indian equities
* US equities
* bonds
* debt funds
* FDs
* MLDs
* gold
* cash
* tactical positions
* other supported assets

Each holding contains:

* instrument ID
* instrument name
* asset class
* account
* quantity/principal
* average cost
* current value
* currency
* acquisition date
* tax lot
* portfolio role
* liquidity classification
* risk classification
* thesis ID
* goal/bucket
* source
* last verified timestamp

---

# 12. IMMUTABLE TRANSACTION LEDGER

The Portfolio Ledger answers:

> What do I own?

The Transaction Ledger answers:

> How did I get there?

Every transaction must be recorded as an immutable event.

Transaction types include:

* buy
* sell
* dividend
* coupon
* interest
* deposit
* withdrawal
* fee
* tax
* FX conversion
* corporate action
* bonus
* split
* rights
* merger
* redemption
* maturity
* call
* put
* other instrument lifecycle events

The transaction ledger is the source for:

* cost basis
* realized P&L
* tax lots
* XIRR
* performance
* attribution
* reconciliation

Corrections should create compensating entries rather than silently rewriting history.

---

# 13. CASH LEDGER

Cash must be tracked independently.

Track:

* bank cash
* broker cash
* currency
* restricted cash
* committed cash
* expected cash inflows
* expected cash outflows
* upcoming coupons
* dividends
* maturities

The system should calculate:

> **Available deployable capital**

rather than assuming all cash is investable.

---

# 14. RECONCILIATION ENGINE

The system must continuously compare external account state against the internal ledger.

Example:

```text
Zerodha:
RELIANCE = 100

Internal Ledger:
RELIANCE = 110

→ RECONCILIATION EXCEPTION
```

Never silently overwrite either side.

Each exception contains:

* source
* internal value
* external value
* variance
* detection timestamp
* probable cause
* resolution status
* resolution history

Reconciliation must cover:

* securities
* cash
* dividends
* corporate actions
* transactions
* quantities
* cost basis where available

---

# 15. ZERODHA INTEGRATION

Zerodha/Kite MCP is treated as:

> **Read-only portfolio and market-data integration.**

Use it for relevant:

* holdings
* positions
* portfolio information
* P&L
* margins
* market data

The application must **not expose order-placement capabilities to AI**.

There should be no:

```text
place_order()
modify_order()
cancel_order()
```

capability available to the investment AI.

The user manually executes approved decisions in Zerodha.

Zerodha is an input/source system, not the master database.

---

# 16. DATA FABRIC

The Data Fabric is responsible for acquiring, normalizing, validating and storing investment data.

Data categories:

### Market data

* prices
* OHLCV
* volumes
* corporate actions
* indices
* FX
* yields
* commodity prices

### Fundamental data

* income statements
* balance sheets
* cash flows
* segment data
* ratios
* guidance
* filings

### Fixed income

* coupon
* yield
* maturity
* duration
* credit rating
* issuer
* security structure
* call/put
* liquidity
* tax treatment

### Macro

* inflation
* interest rates
* GDP
* employment
* PMI
* oil
* gold
* currency
* liquidity
* central-bank policy

### Alternative/research data

* earnings transcripts
* investor presentations
* company announcements
* regulatory filings
* research reports where legally available

---

# 17. DATA CONTRACT

Every material dataset should have a defined contract.

Minimum metadata:

| Field                      | Requirement             |
| -------------------------- | ----------------------- |
| Provider                   | Required                |
| Instrument identifier      | Required                |
| Source timestamp           | Required                |
| Ingestion timestamp        | Required                |
| Currency                   | Required                |
| Frequency                  | Required                |
| Data type                  | Required                |
| Adjusted/unadjusted status | Required where relevant |
| Corporate-action treatment | Required where relevant |
| Historical availability    | Required                |
| Data quality               | Required                |
| Licensing status           | Required                |
| Fallback source            | Preferred               |

The system must distinguish:

> source time

from:

> ingestion time

and:

> data vintage

where applicable.

---

# 18. DATA QUALITY ENGINE

Detect:

* missing values
* stale data
* impossible values
* price spikes
* duplicate records
* conflicting sources
* broken corporate-action adjustments
* incorrect currencies
* unexpected units
* changed historical data

Data should be assigned states:

```text
VALID
STALE
SUSPICIOUS
CONFLICTING
MISSING
INVALID
```

The AI must not silently use stale or invalid data.

---

# 19. DATA SOURCE HIERARCHY

Prefer:

### Tier 1 — Primary

* exchanges
* regulators
* company filings
* company disclosures
* official government sources

### Tier 2 — Institutional/high-quality secondary

* established financial data providers
* reputable research sources

### Tier 3 — Discovery

* news
* commentary
* forums
* social media

Tier-3 information may generate research leads but should not automatically become verified investment evidence.

---

# 20. DATA LICENSING

For every external data source, record whether the system is permitted to:

* retrieve
* store
* transform
* display
* send to an AI model
* retain historically

No core architecture should depend on data whose licensing rights are unclear.

---

# 21. FUNDAMENTAL ANALYSIS ENGINE

For equities calculate:

### Growth

* revenue growth
* EBITDA growth
* EBIT growth
* EPS growth
* FCF growth

### Profitability

* gross margin
* EBITDA margin
* EBIT margin
* net margin
* ROE
* ROCE
* ROIC

### Balance sheet

* debt
* net debt
* leverage
* interest coverage
* liquidity

### Cash flow

* operating cash flow
* free cash flow
* cash conversion
* capex
* working capital

### Quality

* earnings quality
* capital allocation
* management
* governance
* competitive advantage
* cyclicality

### Forward indicators

* guidance
* order book
* capacity expansion
* pricing
* market share
* industry cycle

---

# 22. VALUATION ENGINE

Support multiple methodologies.

### Relative

* P/E
* EV/EBITDA
* P/B
* EV/Sales
* FCF yield

### Intrinsic

* DCF
* dividend discount where applicable
* owner earnings

### Sector-specific

Use appropriate methodologies for:

* banks
* insurers
* financial institutions
* commodity businesses
* REITs/InvITs
* asset-heavy businesses

Outputs:

* base valuation
* bull valuation
* bear valuation
* implied expectations
* margin of safety
* valuation confidence

The system must never present a valuation as an objectively correct price.

---

# 23. FIXED-INCOME ENGINE

For bonds and debt products:

Calculate/track:

* coupon
* yield
* YTM
* duration
* modified duration
* maturity
* credit quality
* issuer concentration
* liquidity
* reinvestment risk
* interest-rate sensitivity
* default risk
* tax-adjusted return
* expected net return

---

# 24. FIXED-INCOME COMPARABILITY ENGINE

Different fixed-income products cannot be compared solely on headline yield.

The system must normalize opportunities for:

* gross yield
* expected net return
* taxation
* credit risk
* duration
* liquidity
* structure
* maturity
* downside
* reinvestment risk

Output:

> **Risk-adjusted after-tax comparison**

Example:

```text
Product A
8.4% yield
Low credit risk
High liquidity

Product B
10.2% yield
Higher credit risk
Low liquidity
Complex structure

→ Product B does not automatically rank higher.
```

---

# 25. MLD ENGINE

MLDs require dedicated analysis.

Track:

* principal protection
* underlying
* participation rate
* barriers
* observation dates
* payoff formula
* cap/floor
* maturity
* issuer
* credit risk
* liquidity
* taxation
* worst-case outcome
* best-case outcome
* probability scenarios where modelable

The system must translate complex payoff structures into plain economic outcomes.

---

# 26. GOLD ENGINE

Gold is treated as a strategic portfolio asset.

Analyze:

* allocation
* price
* volatility
* correlation
* inflation relationship
* real-rate sensitivity
* currency effects
* portfolio hedge properties

The system should answer:

> Does additional gold improve this portfolio?

rather than:

> Will gold go up tomorrow?

---

# 27. MACRO ENGINE

Track macro variables including:

* RBI policy
* Fed policy
* inflation
* growth
* liquidity
* bond yields
* USD/INR
* oil
* gold
* credit conditions
* global growth
* recession indicators
* geopolitical developments

Oil specifically feeds:

```text
Oil
 ↓
Inflation / Current Account / Margins
 ↓
Rates / INR / Earnings
 ↓
Portfolio impact
```

Macro analysis should primarily identify:

* regime
* transmission mechanism
* affected assets
* portfolio vulnerabilities
* potential opportunities

It should not become a simplistic market-direction predictor.

---

# 28. QUANTITATIVE ENGINE

Support:

* returns
* volatility
* beta
* correlation
* covariance
* Sharpe
* Sortino
* drawdown
* downside deviation
* rolling metrics
* factor exposure
* momentum
* relative strength
* trend
* volume
* volatility regime

Calculations are deterministic.

---

# 29. PORTFOLIO RISK ENGINE

Calculate:

### Concentration

* single-stock
* sector
* issuer
* geography
* asset class
* currency

### Market risk

* volatility
* beta
* drawdown
* downside

### Credit risk

* issuer
* rating
* maturity concentration

### Liquidity

* liquidity bucket
* days-to-liquidate where meaningful
* lock-in
* maturity

### Currency

Especially:

> USD exposure relative to INR portfolio.

### Correlation

Identify hidden concentration through correlated holdings.

---

# 30. LOOK-THROUGH ANALYSIS

The system should identify indirect exposures.

Example:

```text
Holding A
Holding B
Holding C

All appear diversified.

But:

A → Banking
B → Financial ETF
C → Insurance

→ High financial-sector exposure
```

Look-through should operate across:

* ETFs
* funds
* conglomerates where practical
* debt products
* sector exposures
* geographic exposures

---

# 31. STRESS-TESTING ENGINE

Stress scenarios include:

* India equities -20%
* US equities -25%
* gold +15%
* USD/INR +10%
* bond yields +150 bps
* oil +40%
* recession
* inflation shock
* liquidity shock
* credit event
* INR depreciation

Outputs:

* portfolio impact
* asset-class impact
* largest contributors
* liquidity implications
* concentration revealed
* possible actions

Scenarios are:

> **Stress scenarios, not forecasts.**

---

# 32. RISK BUDGET

Separate:

### Strategic risk budget

Risk permitted within the core portfolio.

### Tactical risk budget

Risk specifically allocated to positional opportunities.

Tactical positions must not silently consume strategic risk capacity.

---

# 33. OPPORTUNITY ENGINE

The Opportunity Engine searches across asset classes.

For each opportunity evaluate:

* expected return
* downside
* probability
* valuation
* quality
* liquidity
* tax
* transaction cost
* correlation
* portfolio role
* concentration
* thesis strength
* opportunity cost

The output should not simply be:

> "Best stock."

It should be:

> **Best incremental use of capital given the existing portfolio.**

---

# 34. PORTFOLIO OPPORTUNITY COST ENGINE

This is a key decision layer.

For any new opportunity:

> What existing position or alternative investment is this capital competing against?

Example:

```text
Stock X:
Standalone attractiveness = 9/10

But portfolio already has:
Bank A
Bank B
Financial ETF
Insurance C

Incremental portfolio value = low

→ Recommendation may be NO ACTION
```

This prevents security-level analysis from overwhelming portfolio-level judgment.

---

# 35. CAPITAL DEPLOYMENT ENGINE

This engine answers:

> Where should new money go?

Inputs:

* available cash
* target allocation
* current drift
* opportunities
* risk
* valuation
* tax
* liquidity
* portfolio correlation
* goals
* tactical budget

Output:

```text
₹X → Asset A
₹Y → Asset B
₹Z → Cash
```

or:

> **Do not deploy yet.**

Capital deployment is distinct from security selection.

---

# 36. CORE INVESTMENT ENGINE

Core horizon:

> 6 months to 5+ years.

Inputs:

* fundamentals
* valuation
* quality
* macro
* portfolio fit
* risk
* liquidity
* tax
* opportunity cost

Possible outputs:

* BUY
* ADD
* ACCUMULATE
* HOLD
* REDUCE
* EXIT
* WATCH
* NO ACTION

Each recommendation must include rationale and evidence.

---

# 37. TACTICAL / POSITIONAL ENGINE

Horizon:

> 2–12 weeks.

Inputs:

* trend
* momentum
* relative strength
* technical structure
* volume
* catalyst
* sector regime
* market regime
* volatility
* risk/reward

Output:

* LONG / ENTER
* WAIT
* EXIT

If entering, provide:

* preferred entry zone
* invalidation
* target zone
* expected holding period
* position size
* risk per position
* rationale
* catalyst
* risk/reward

This engine must operate inside the tactical risk budget.

---

# 38. INVESTMENT THESIS LEDGER

Every meaningful investment idea can have a persistent thesis.

Track:

* thesis
* supporting evidence
* counter-evidence
* key assumptions
* catalysts
* risks
* invalidation conditions
* thesis health
* last review
* next review
* recommendation

Possible thesis state:

```text
STRONG
HEALTHY
WATCH
DETERIORATING
BROKEN
SUPERSEDED
```

---

# 39. SEPARATE INVESTMENT AND TACTICAL THESIS

These must be separate objects.

### Investment thesis

Example:

> Business has durable competitive advantages and can compound earnings over five years.

### Tactical thesis

Example:

> Price has entered a positive momentum regime following earnings.

A tactical thesis may break while the investment thesis remains intact.

An investment thesis may break while short-term price action remains positive.

The system must not conflate them.

---

# 40. RESEARCH STATE MACHINE

Research should progress through defined states:

```text
DISCOVERY
   ↓
RESEARCHING
   ↓
RESEARCH COMPLETE
   ↓
CANDIDATE
   ↓
DECISION
```

Incomplete research must not automatically become an actionable recommendation.

---

# 41. AI RESEARCH LAYER

AI handles:

### Document ingestion

* filings
* presentations
* transcripts
* announcements
* research material

### Extraction

Extract:

* facts
* changes
* management commentary
* guidance
* risks
* catalysts

### Synthesis

Combine multiple sources.

### Contradiction detection

Identify:

* management vs historical evidence
* source vs source
* reported metric vs calculated metric

### Thesis analysis

Ask:

> Has the evidence strengthened or weakened the thesis?

### Explanation

Turn quantitative results into understandable conclusions.

---

# 42. AI SECURITY

All external content must be considered:

> **UNTRUSTED DATA**

This includes:

* web pages
* PDFs
* filings
* transcripts
* research reports
* news
* social media

External content must never be treated as instructions.

Retrieved content cannot:

* alter the IPS
* modify portfolio data
* change risk limits
* invoke tools
* execute transactions
* change system instructions

Prompt injection defenses must exist at the architecture/tool boundary, not merely in prompts.

---

# 43. AI MODEL ARCHITECTURE

Model-agnostic architecture.

Use routing based on task complexity.

### Lightweight models

For:

* extraction
* classification
* tagging
* summarization
* document preprocessing

### General reasoning models

For:

* research synthesis
* company analysis
* portfolio explanations
* thesis evaluation

### High-reasoning models

For:

* complex investment research
* conflicting evidence
* portfolio-level decisions
* difficult scenario analysis

Models should be replaceable without changing business logic.

---

# 44. MODEL REGISTRY

Maintain:

* provider
* model ID
* version
* context size
* capabilities
* known limitations
* cost
* latency
* evaluation results
* deployment status

---

# 45. PROMPT / POLICY VERSIONING

Store versions of:

* system prompts
* research prompts
* decision prompts
* extraction prompts
* portfolio-analysis prompts

Every AI-generated recommendation should be traceable to:

* model
* model version
* prompt version
* relevant data version
* policy version

---

# 46. AI EVALUATION FRAMEWORK

The AI system must be evaluated independently from investment performance.

Test:

### Factuality

Does it correctly extract facts?

### Citation correctness

Does evidence actually support the statement?

### Numerical fidelity

Does it interpret deterministic calculations correctly?

### Contradiction detection

Does it find conflicting information?

### Thesis reasoning

Does it distinguish thesis change from price noise?

### Recommendation consistency

Does materially identical evidence generate materially consistent reasoning?

### Abstention

Does the AI correctly say:

> Insufficient evidence.

### Policy compliance

Does it respect portfolio constraints?

---

# 47. DECISION ENGINE

The Decision Engine combines:

```text
Investor Policy
+
Portfolio State
+
Opportunity
+
Risk
+
Evidence
+
Valuation
+
Liquidity
+
Tax
+
Macro
+
Thesis
+
Opportunity Cost
```

It produces a decision.

The Decision Engine is the central decision-support component.

It should not be implemented as a collection of autonomous AI agents voting with each other.

---

# 48. HARD POLICY ENFORCEMENT

Deterministic policy checks happen **outside the LLM**.

Example:

```text
Maximum stock weight = 10%

AI recommendation = 15%

→ POLICY VIOLATION
→ Recommendation blocked/modified
```

The AI cannot override the policy.

---

# 49. RECOMMENDATION OBJECT

Every recommendation should have a structured representation.

Example:

```text
Recommendation
├── Asset
├── Action
├── Amount / Position Size
├── Horizon
├── Thesis
├── Evidence
├── Valuation
├── Expected Return
├── Downside
├── Risk
├── Portfolio Impact
├── Opportunity Cost
├── Tax Impact
├── Liquidity
├── Confidence
├── Evidence Confidence
├── Model Confidence
├── Invalidation Conditions
├── Expiry
├── Policy Check
└── Audit Metadata
```

---

# 50. RECOMMENDATION EXPIRY / DECAY

Recommendations cannot remain permanently actionable.

Every recommendation has:

* creation timestamp
* validity period
* expiry date/condition
* invalidation conditions
* superseding events

Example:

> BUY until next earnings unless thesis-break event occurs.

After expiry:

> **REQUIRES RE-EVALUATION**

The system must not continue presenting stale recommendations as current.

---

# 51. DECISION LIFECYCLE

Every decision should move through:

```text
IDEA
 ↓
RESEARCH
 ↓
CANDIDATE
 ↓
RECOMMENDATION
 ↓
USER REVIEW
 ↓
ACCEPT / MODIFY / REJECT
 ↓
EXECUTED / NOT EXECUTED
 ↓
OUTCOME
 ↓
PERFORMANCE
 ↓
ATTRIBUTION
 ↓
THESIS REVIEW
```

The system must record the difference between:

> AI recommendation

and:

> Actual user decision.

Example:

AI:

> Invest ₹1 lakh.

User:

> Invest ₹50,000.

The system records both.

---

# 52. TAX & COST ENGINE

Calculate:

* brokerage
* exchange charges
* transaction costs
* taxes
* capital gains
* dividend/coupon tax
* withholding where applicable
* FX conversion costs

Where sufficiently supported, calculate:

```text
Gross Return
    ↓
Transaction Costs
    ↓
Taxes
    ↓
Net Return
    ↓
Risk Adjustment
```

Investment ranking should use net economics where possible.

Tax rules must be versioned by date.

---

# 53. PERFORMANCE ENGINE

Measure:

### Absolute

* total return
* profit/loss
* CAGR
* XIRR

### Risk

* volatility
* maximum drawdown
* downside deviation
* Sharpe
* Sortino

### Cash-flow-aware

* XIRR
* money-weighted return

### Portfolio/sleeve level

* total portfolio
* Indian equity
* US equity
* fixed income
* gold
* tactical
* cash

---

# 54. BENCHMARKING ENGINE

Benchmark:

* Indian equity sleeve against suitable Indian equity benchmark
* US equity against appropriate US benchmark
* fixed income against appropriate debt benchmark
* gold against gold benchmark
* tactical sleeve against suitable tactical benchmark
* total portfolio against a strategic blended benchmark

The system should not judge performance purely by absolute return.

---

# 55. PERFORMANCE ATTRIBUTION

Determine where performance came from.

Possible attribution:

* asset allocation
* security selection
* sector allocation
* Indian equity
* US equity
* fixed income
* gold
* tactical
* FX
* costs
* taxes

The system should eventually answer:

> **Why did the portfolio outperform or underperform?**

---

# 56. CORPORATE ACTION / INSTRUMENT LIFECYCLE ENGINE

Handle:

### Equities

* dividends
* splits
* bonuses
* rights
* buybacks
* mergers
* demergers
* delistings

### Bonds

* coupons
* maturity
* calls
* puts
* defaults
* restructuring

### MLDs

* observation dates
* payoff events
* maturity
* early redemption where applicable

This is essential to keeping the Master Portfolio Ledger accurate.

---

# 57. ALERT ENGINE

Alerts should be meaningful rather than noisy.

### Portfolio

* allocation breach
* concentration breach
* liquidity issue

### Investment

* thesis deterioration
* earnings surprise
* guidance change
* valuation change
* major corporate action

### Credit

* rating downgrade
* issuer deterioration
* liquidity deterioration

### Macro

* regime change
* rate shock
* currency shock
* oil shock

### Tactical

* entry condition
* invalidation
* target
* regime change

---

# 58. EVIDENCE & PROVENANCE

Every material research claim should retain:

* source
* source URL/document
* publication date
* source timestamp
* retrieval timestamp
* relevant passage/section
* data version
* confidence
* whether primary or secondary evidence

The user should be able to ask:

> **Why does the system believe this?**

and trace the answer back to evidence.

---

# 59. EVIDENCE CONFIDENCE VS MODEL CONFIDENCE

These must remain separate.

### Evidence confidence

How trustworthy and complete is the underlying evidence?

### Model confidence

How strongly does the analytical/reasoning layer support the conclusion?

Example:

```text
Evidence confidence: 95%
Model confidence: 65%

Meaning:
Facts are reliable, but interpretation remains uncertain.
```

---

# 60. AUDIT TRAIL

Record material changes to:

* portfolio
* transactions
* IPS
* risk limits
* model versions
* prompts
* recommendations
* user decisions
* overrides
* data sources
* tax rules

The system should be able to reconstruct:

> **What did the system know and why did it produce this recommendation at that point in time?**

---

# 61. PORTFOLIO STATE SNAPSHOT

For every major decision, preserve the relevant portfolio state:

* holdings
* allocation
* cash
* risk
* prices
* valuation
* policy
* relevant macro state

This allows historical reconstruction.

---

# 62. DATABASE / LOGICAL DATA MODEL

Core entities:

```text
User
InvestorProfile
Goal
InvestmentPolicy
RiskBudget

Account
Asset
Security
Holding
TaxLot

Transaction
CashTransaction
CorporateAction
InstrumentLifecycleEvent

MarketData
FundamentalData
FixedIncomeData
MacroData

ResearchDocument
ResearchClaim
Evidence
ResearchState

InvestmentThesis
TacticalThesis

Opportunity
Recommendation
Decision
DecisionOutcome

RiskSnapshot
StressScenario

Benchmark
PerformanceSnapshot
Attribution

Alert

Model
ModelVersion
PromptVersion

AuditEvent
ReconciliationException
```

---

# 63. SERVICE BOUNDARIES

Initially use a:

> **Modular monolith**

rather than microservices.

Logical modules:

```text
portfolio
transactions
cash
accounts
market_data
fundamentals
valuation
fixed_income
gold
macro
quant
risk
allocation
capital_deployment
tax
research
thesis
recommendations
performance
benchmarking
attribution
alerts
corporate_actions
integrations
ai
audit
reconciliation
```

These should have clean internal interfaces so individual modules can later be separated if genuinely required.

---

# 64. DATA STORAGE

Recommended logical storage:

### Relational database

For:

* portfolio
* transactions
* securities
* recommendations
* policies
* audit

### Time-series storage

For:

* prices
* yields
* macro series
* indicators

### Object storage

For:

* PDFs
* filings
* presentations
* transcripts
* research documents

### Search/index

For document retrieval.

### Vector database

Optional.

Do **not** introduce a vector database simply because the system uses AI.

---

# 65. INFRASTRUCTURE

The system should be designed to run under user-controlled infrastructure.

Potential components:

* containerized application
* relational database
* object storage
* scheduled jobs
* API gateway
* secrets management
* model gateway
* monitoring
* backup

Azure can be used where its existing credits provide economic value.

The architecture should remain portable rather than being inseparably tied to a particular LLM provider.

---

# 66. AI COST CONTROL

AI calls should be routed according to value.

Example:

```text
Routine extraction
→ inexpensive model

Standard research
→ general model

Complex portfolio reasoning
→ stronger reasoning model
```

Cache deterministic and reusable outputs.

Do not repeatedly send unchanged documents to expensive models.

Track:

* token consumption
* model cost
* latency
* calls per workflow

This enables optimization against available infrastructure/credits.

---

# 67. SECURITY ARCHITECTURE

Required:

* encrypted secrets
* API credentials isolated from AI
* least-privilege tool permissions
* read-only broker integration
* database access controls
* encrypted data at rest
* encrypted transport
* audit logs
* session authentication
* backup protection

Most importantly:

> **Broker credentials capable of executing trades must never be available to the AI layer.**

---

# 68. TOOL PERMISSION MODEL

AI tools should be explicitly allowlisted.

Example:

```text
READ_PORTFOLIO          ✓
READ_MARKET_DATA        ✓
READ_DOCUMENTS          ✓
RUN_ANALYSIS            ✓
GENERATE_RECOMMENDATION ✓

CHANGE_IPS              ✗
CHANGE_RISK_LIMIT       ✗
TRANSFER_MONEY          ✗
PLACE_ORDER             ✗
MODIFY_ORDER            ✗
CANCEL_ORDER            ✗
```

This is an architectural permission boundary.

---

# 69. OBSERVABILITY

System monitoring must include:

### Data

* ingestion success
* freshness
* source failures
* conflicting data

### Application

* job failures
* API failures
* processing latency

### AI

* model latency
* token usage
* cost
* failed calls
* evaluation scores

### Portfolio

* reconciliation exceptions
* stale holdings
* stale valuations

### Infrastructure

* CPU
* memory
* database
* storage
* backup status

---

# 70. DATA FRESHNESS

Every important dataset should expose:

> **Last successfully updated**

Examples:

```text
NSE prices: 12 minutes ago
US prices: 14 hours ago
Portfolio: 18 minutes ago
Fundamentals: 12 days ago
Macro: 2 days ago
```

The system must explicitly flag stale data.

---

# 71. DISASTER RECOVERY

Protect:

* portfolio database
* transaction ledger
* cash ledger
* Investment Policy
* theses
* research documents
* audit trail
* model/prompt configuration

Required:

* automated backups
* point-in-time recovery where supported
* backup verification
* restore testing

The Portfolio/Transaction Ledger must be recoverable independently of the AI layer.

---

# 72. TESTING STRATEGY

## Unit tests

Financial calculations.

## Integration tests

* Zerodha
* market-data sources
* databases
* document ingestion

## Data-quality tests

* missing values
* duplicate data
* outliers
* corporate actions

## Portfolio tests

* allocation
* constraints
* risk
* rebalancing

## AI evaluation tests

* factuality
* citation
* reasoning
* contradiction detection
* abstention

## Regression tests

Model/prompt changes.

## Security tests

* prompt injection
* unauthorized tool use
* credential isolation
* permission escalation

## Disaster recovery

Backup restoration.

---

# 73. BACKTESTING ENGINE

Where historical testing is appropriate:

Must account for:

* transaction costs
* slippage
* taxes where modelable
* liquidity
* corporate actions
* survivorship bias
* look-ahead bias
* delisted securities
* historical data revisions
* position sizing
* turnover
* realistic execution assumptions

The system must not use today's universe to falsely evaluate historical strategies.

---

# 74. DECISION QUALITY MEASUREMENT

Do not judge the system only by whether recommendations made money.

Measure:

### Research quality

* factual accuracy
* citation accuracy
* thesis quality

### Decision quality

* risk-adjusted outcome
* portfolio fit
* policy compliance
* opportunity cost

### Process quality

* avoided bad decisions
* correctly identified thesis breaks
* avoided concentration
* avoided stale recommendations

A recommendation can be correct even if the short-term price moves against it.

---

# 75. NO-ACTION AS A FIRST-CLASS OUTCOME

Possible decisions:

```text
BUY
ADD
ACCUMULATE
HOLD
REDUCE
EXIT
WATCH
WAIT
NO ACTION
```

NO ACTION should be used when:

* valuation is unattractive
* evidence is insufficient
* portfolio already has exposure
* risk is excessive
* opportunity cost is poor
* liquidity is inadequate
* policy prohibits it
* expected return does not compensate for risk

---

# 76. USER INTERFACE

## 76.1 Home Dashboard

Display:

* total portfolio
* allocation
* P&L
* risk
* cash
* upcoming events
* top opportunities
* alerts
* thesis changes
* tactical opportunities

---

## 76.2 Portfolio

Views:

* asset class
* geography
* sector
* currency
* account
* goal
* portfolio role
* risk
* liquidity

---

## 76.3 Investment Detail

For each security:

```text
Price
Valuation
Fundamentals
Quality
Thesis
Evidence
Risk
Portfolio exposure
Peers
Catalysts
Risks
Recommendation
Decision history
```

---

## 76.4 Opportunity Dashboard

Rank opportunities by:

* attractiveness
* portfolio fit
* expected return
* downside
* valuation
* confidence
* liquidity
* opportunity cost

---

## 76.5 Tactical Dashboard

Display:

* setup
* entry
* invalidation
* target
* risk/reward
* position size
* catalyst
* technical evidence

---

## 76.6 Risk Dashboard

Show:

* concentration
* drawdown
* volatility
* asset allocation
* factor exposure
* currency
* liquidity
* credit

---

## 76.7 Decision Journal

Show:

* recommendation
* user decision
* executed amount
* actual outcome
* thesis status
* retrospective assessment

---

# 77. PRODUCT WORKFLOWS

## Workflow A — New capital available

```text
New capital
 ↓
Check liquidity requirements
 ↓
Check target allocation
 ↓
Identify allocation gaps
 ↓
Search opportunities
 ↓
Risk check
 ↓
Tax/cost check
 ↓
Opportunity-cost comparison
 ↓
Capital Deployment Recommendation
 ↓
Human decision
 ↓
Manual execution
```

---

## Workflow B — Existing holding review

```text
Holding
 ↓
Updated fundamentals
 ↓
Valuation
 ↓
Macro
 ↓
Portfolio exposure
 ↓
Thesis
 ↓
Risk
 ↓
Decision
```

---

## Workflow C — Major market event

```text
Event
 ↓
Validate evidence
 ↓
Identify affected assets
 ↓
Assess portfolio impact
 ↓
Stress test
 ↓
Check thesis
 ↓
Determine whether action is warranted
 ↓
NO ACTION / REVIEW / REDUCE / ADD
```

---

# 78. V1 — MUST HAVE

### Portfolio

* Master Portfolio Ledger
* Transaction Ledger
* Cash Ledger
* manual non-Zerodha assets
* Zerodha read-only integration
* reconciliation

### Governance

* Investor Profile
* Investment Policy
* risk budgets
* decision rights

### Equities

* India
* US
* fundamentals
* valuation
* basic quantitative analysis

### Portfolio

* allocation
* concentration
* risk
* liquidity
* basic correlation

### AI

* research
* document analysis
* evidence
* citations
* synthesis
* recommendation explanation

### Governance/security

* audit trail
* model/prompt versioning
* AI tool permissions
* no execution

---

# 79. V2

Add:

* advanced fixed income
* MLD analysis
* gold analytics
* macro engine
* capital deployment engine
* opportunity-cost engine
* thesis ledger
* corporate-action lifecycle
* tax/cost engine
* advanced alerts
* look-through analysis

---

# 80. V3

Add:

* positional scanner
* technical analytics
* tactical engine
* advanced stress testing
* paper trading
* backtesting
* performance attribution
* benchmark engine
* decision-quality analytics

---

# 81. V4 — ONLY IF JUSTIFIED

Potential future additions:

* more asset classes
* sophisticated portfolio optimization
* advanced scenario engines
* additional data sources
* deeper factor analytics

These should only be implemented if they demonstrably improve decisions.

---

# 82. EXPLICITLY OUT OF SCOPE

The following are not part of the core system:

* autonomous trading
* order execution
* HFT
* options scalping
* reinforcement-learning trader
* AI-only price prediction
* uncontrolled agent swarm
* automatic portfolio rebalancing
* automatic money transfer
* social-media sentiment engine as a primary signal
* public investment-advisory platform
* unnecessary microservices
* unnecessary vector infrastructure

---

# 83. NON-FUNCTIONAL REQUIREMENTS

## Reliability

Critical portfolio data must be durable and recoverable.

## Accuracy

Financial calculations must be deterministic and testable.

## Traceability

Material recommendations must be reproducible from their underlying evidence and data state.

## Freshness

Stale data must be explicitly identified.

## Security

No execution credentials exposed to AI.

## Explainability

Every recommendation must have a comprehensible rationale.

## Performance

Routine portfolio views should respond quickly; expensive AI research can be asynchronous.

## Extensibility

New asset classes/data sources/models should be addable without rewriting the core portfolio engine.

## Portability

The system should not depend irreversibly on one AI provider.

---

# 84. ACCEPTANCE CRITERIA FOR CORE SYSTEM

The V1 system is not considered complete unless:

### Portfolio truth

The system can reconstruct the current portfolio from transactions and reconcile it against supported external accounts.

### Policy

The system can determine whether a proposed investment violates the IPS.

### Risk

The system can identify concentration and allocation breaches.

### Research

The system can produce evidence-backed research.

### Recommendation

The system can produce a structured recommendation.

### Human control

No AI pathway can execute an order.

### Auditability

A historical recommendation can be reconstructed.

### Data quality

Stale/conflicting data is surfaced.

### AI governance

Model and prompt versions are recorded.

### Recovery

The portfolio ledger can be restored independently of AI infrastructure.

---

# 85. CORE SYSTEM DATA FLOW

```text
                  ┌─────────────────────┐
                  │   INVESTOR PROFILE  │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │   INVESTMENT POLICY │
                  │       / IPS         │
                  └──────────┬──────────┘
                             ↓
      ┌───────────────────────────────────────────┐
      │             MASTER PORTFOLIO              │
      │ Holdings + Transactions + Cash + Goals    │
      └─────────────────────┬─────────────────────┘
                            ↓
      ┌───────────────────────────────────────────┐
      │                DATA FABRIC                 │
      │ Zerodha + Market + Filings + Macro + Docs │
      └─────────────────────┬─────────────────────┘
                            ↓
      ┌───────────────────────────────────────────┐
      │           DETERMINISTIC CORE              │
      │ Fundamentals • Valuation • Risk • Quant   │
      │ Fixed Income • Tax • Liquidity • Macro    │
      └─────────────────────┬─────────────────────┘
                            ↓
      ┌───────────────────────────────────────────┐
      │               AI LAYER                    │
      │ Research • Synthesis • Thesis • Evidence │
      │ Contradictions • Explanation              │
      └─────────────────────┬─────────────────────┘
                            ↓
      ┌───────────────────────────────────────────┐
      │           DECISION ENGINES                │
      │ Core • Tactical • Capital Deployment     │
      └─────────────────────┬─────────────────────┘
                            ↓
      ┌───────────────────────────────────────────┐
      │              DECISION ENGINE              │
      │ Policy + Risk + Portfolio + Opportunity  │
      └─────────────────────┬─────────────────────┘
                            ↓
                    ┌───────────────┐
                    │ HUMAN REVIEW  │
                    └───────┬───────┘
                            ↓
                    MANUAL EXECUTION
                            ↓
                  TRANSACTION LEDGER
                            ↓
             PERFORMANCE / ATTRIBUTION
                            ↓
                    THESIS REVIEW
```

---

# 86. THE MOST IMPORTANT ARCHITECTURAL BOUNDARY

The system has three fundamentally different types of intelligence:

### 1. Truth

```text
Portfolio
Transactions
Prices
Financial statements
Rates
Cash
```

These come from data systems.

### 2. Mathematics

```text
Valuation
Risk
Allocation
Returns
Tax
Performance
Stress testing
```

These come from deterministic software.

### 3. Judgment

```text
What matters?
Why did it happen?
Does the thesis still hold?
Which evidence matters?
What is the best opportunity?
```

These are where AI adds value.

The architecture should **not blur these three layers**.

---

# 87. FINAL ARCHITECTURE

The final product should therefore be understood as:

> **A personal investment operating system with an AI research and decision-support layer.**

Not:

> An AI trading bot.

The canonical architecture is:

```text
Investor
   ↓
Investor Profile
   ↓
Investment Policy / IPS
   ↓
Master Portfolio
   ↕
Transaction + Cash Ledger
   ↕
Zerodha / External Assets
   ↓
Data Fabric
   ↓
Deterministic Analytical Core
   ├── Fundamental
   ├── Valuation
   ├── Quant
   ├── Fixed Income
   ├── Gold
   ├── Macro
   ├── Risk
   ├── Liquidity
   ├── Tax / Cost
   └── Performance
   ↓
AI Research Layer
   ├── Extraction
   ├── Research
   ├── Synthesis
   ├── Contradiction Detection
   ├── Thesis Analysis
   └── Explanation
   ↓
Opportunity Engine
   ↓
Core Investment Engine
   +
Tactical Engine
   +
Capital Deployment Engine
   ↓
Decision Engine
   ↓
Policy / Risk Gate
   ↓
Human Review
   ↓
Manual Execution
   ↓
Transaction Ledger
   ↓
Performance / Attribution
   ↓
Decision & Thesis Learning
```

---

# 88. GUIDING ARCHITECTURAL DECISION

The platform should optimize for:

> **Better decisions, better portfolio construction, better risk management and better use of capital.**

It should not optimize for:

* number of trades
* number of AI agents
* amount of AI usage
* prediction accuracy for its own sake
* automation for its own sake

The system's most valuable capability is ultimately:

> **Knowing when to invest, where to invest, how much to invest, when not to invest, and when an existing thesis should be changed — within the constraints of the investor's total portfolio.**

The human remains the final capital allocator.
