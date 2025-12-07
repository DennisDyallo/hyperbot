# Telegram UX Implementation Playbook

**Status**: Active Workstream
**Effective**: 2025-12-07
**Owner**: Documentation Lead (in partnership with UX + Engineering)

> This playbook translates the canonical design system (`docs/telegram-ux-system-guide.md`) into actionable engineering tasks. Historical planning notes are archived in `docs/archive/2025-12-07-ux/`.

---

## 1. How to Use This Playbook

- Treat each section as a living checklist; update status columns as work progresses.
- Capture open questions inline so UX and engineering can resolve them before implementation.
- Link PRs, specs, or test plans beside the tasks they satisfy.
- Review and update during weekly UX/engineering syncs.

## 2. Workstream Overview

| Workstream | Goal | Primary Owners | Status |
| --- | --- | --- | --- |
| Foundations & Atomic Components | Implement shared formatting, buttons, loading, and risk helpers with tests | Bot Platform team | In Progress |
| Molecular Components | Deliver reusable cards, previews, and list builders respecting system guide rules | Bot Platform team + UX | Planned |
| Flow Migrations | Retrofit high-impact wizards and menus to the new components | Bot Platform team | Planned |
| Quality & Rollout | Achieve coverage, manual validation, and staged deployment | QA + SRE | Planned |

## 3. Foundations & Atomic Components

| Task | Details | Status | Notes |
| --- | --- | --- | --- |
| Formatters module parity | Implement `format_currency`, `format_percentage`, `format_coin_size`, `format_pnl`, `format_timestamp` with edge-case tests | ☐ | Snapshot fixtures must mirror real API payloads |
| ButtonBuilder | Fluent builder with `.action`, `.cancel`, `.back`, `.navigation_back_cancel`, `.navigation_main`, `.next_actions`, `.build` presets | ☐ | Ensure callback IDs remain stable for existing handlers |
| Loading states | `LoadingMessage.show/hide` helpers and preset messages (order, leverage, pricing) | ☐ | Pair with async context manager once handlers refactor |
| Risk indicators | `RiskLevel` + `RiskDescriptor` metadata, `calculate_risk_level`, `format_risk_indicator`, `build_risk_summary`, `build_risk_tooltip` | ☐ | Centralize thresholds; add regression tests |
| Test coverage | ≥90% coverage across atomic modules | ☐ | Integrate into CI gate |

## 4. Molecular Components

| Component | Deliverables | Status | Notes |
| --- | --- | --- | --- |
| InfoCard | Chainable builder, capital impact factory, risk assessment factory | ☐ | Output must follow typography & spacing in system guide |
| PreviewBuilder | `set_order_details`, `set_capital_impact`, `set_risk_assessment`, `build_quick`, `build_full` | ☐ | Quick preview ≤10 lines; full preview adds scenarios |
| SortableList | Sorting (risk, size, PnL), grouping (urgency), markdown rendering | ☐ | Verify stable ordering for deterministic tests |
| Forms Toolkit | (Optional) Shared helpers for validated numeric/text input | ☐ | Define scope once atomic work completes |
| Molecular test harness | Snapshot and property tests for builders | ☐ | Use fixture data that mirrors production |

## 5. Flow Migration Roadmap

### 5.1 Priority 1 — Critical User Journeys

1. **Market Order Wizard** (`src/bot/handlers/wizard_market_order.py`)
   - Add leverage selection after amount entry with contextual recommendations.
   - Inject quick preview (default) + full preview toggle using new builders.
   - Replace generic "Confirm" with action-specific CTA ("Buy $1,000 BTC").
   - Surface buying power, liquidation estimate, risk indicator, and 30-second undo window.
   - Add loading states around preview computation and execution.

2. **Scale Order Wizard** (`src/bot/handlers/wizard_scale_order.py`)
   - Reduce steps from 12 → ~8 by combining range inputs and distribution choices.
   - Introduce leverage selection and capital validation before preview.
   - Provide risk ranges ("If all fill" vs "Top 2 fill") within the preview.
   - Render ladder visualization with SortableList or InfoCard layouts.
   - Replace confirmation CTA with action-specific copy ("Place 5 Orders").

### 5.2 Priority 2 — High Value Enhancements

3. **Close Position Flow** (`src/bot/handlers/wizard_close_position.py`)
   - Offer partial close presets (25%, 50%, 75%, 100%, Custom).
   - Provide market impact preview (estimated fill, resulting PnL, freed margin).
   - Add alternative CTA for setting a stop loss instead of closing.
   - Use SortableList to sort positions by risk before selection.

4. **Rebalance Wizard** (`src/bot/handlers/wizard_rebalance.py`)
   - Adopt new preview builder for before/after allocations.
   - Display capital and risk cards for target vs current state.
   - Integrate undo timer and success follow-up actions.

5. **Positions & Account Views** (`/positions`, `/account`, `/balance`)
   - Standardize list rendering via SortableList and InfoCard summaries.
   - Ensure risk indicators and capital metrics align with previews.
   - Provide drill-down links to relevant wizards (e.g., rebalance, hedge).

### 5.3 Priority 3 — Supporting Menus & Extras

6. **Orders Management & Menus** (`src/bot/handlers/orders.py`, `menus.py`)
   - Introduce navigation presets and consistent button styling.
   - Align copy with emoji legend and heading hierarchy.

7. **Notification & Alert Flows**
   - Audit existing messages against typography and spacing rules.
   - Ensure actionable buttons appear beneath content with blank line separation.

## 6. Quality, Testing, and Rollout

| Checkpoint | Requirement | Owner | Status |
| --- | --- | --- | --- |
| Unit tests | ≥90% coverage for new component modules | Engineering | ☐ |
| Integration tests | Full journey tests for market order, scale order, close position, rebalance | QA | ☐ |
| Manual validation | Mobile checks on iPhone SE + mid-range Android | UX | ☐ |
| Performance | Button response <500 ms for standard flows | Engineering | ☐ |
| Staged rollout | Staging → 10% → 50% → 100%, 48h soak at each stage | SRE | ☐ |
| Telemetry | Capture adoption metrics for new flows | Data/Telemetry | ☐ |

## 7. Change Log & Open Questions

Maintain a running table during execution.

| Date | Change | Owner | Notes |
| --- | --- | --- | --- |
| 2025-12-07 | Playbook initialized; legacy docs archived | Documentation Lead | — |

**Open Questions**

- What leverage defaults should we present when historical user preference is unavailable?
- Should undo windows vary by flow complexity?
- How do we expose advanced previews (e.g., scenario analysis) without overwhelming first-time users?

## 8. References

- Canonical design rules: `docs/telegram-ux-system-guide.md`
- Historical docs (snapshot as of 2025-12-07): `docs/archive/2025-12-07-ux/`
- Architecture & roadmap context: `docs/ARCHITECTURE.md`, `docs/PLAN.md`
