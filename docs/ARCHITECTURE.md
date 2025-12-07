# Hyperbot Architecture

**Last Updated**: 2025-12-07

Hyperbot follows a layered architecture that separates interface logic from core business rules and external integrations. This structure keeps trading workflows consistent across FastAPI, Telegram, and future interfaces while isolating Hyperliquid concerns.

```
┌──────────────────────────────────────────┐
│            Interface Layer               │
│ (FastAPI, Telegram Bot, CLI, Swagger UI) │
└────────────────────┬─────────────────────┘
           │
┌────────────────────┴─────────────────────┐
│            Use Case Layer                │
│ (src/use_cases/* — shared business logic)│
│  • Trading (orders, cancellation, fills) │
│  • Portfolio (positions, risk, rebalance)│
│  • Scale Orders                          │
│  • Common utilities & validators         │
└────────────────────┬─────────────────────┘
           │ orchestrates
┌────────────────────┴─────────────────────┐
│            Services Layer                │
│ (Hyperliquid adapters & calculators)     │
│  • AccountService                        │
│  • PositionService                       │
│  • OrderService                          │
│  • RebalanceService                      │
│  • ScaleOrderService                     │
│  • MarketDataService                     │
│  • RiskCalculator & LeverageService      │
└────────────────────┬─────────────────────┘
           │ integrates with
┌────────────────────┴─────────────────────┐
│     External Integrations Layer          │
│  • Hyperliquid HTTP/WebSocket APIs       │
│  • Persistent state (data/*.json)        │
│  • Secrets & configuration (env files)   │
└──────────────────────────────────────────┘
```

Background workers: `OrderMonitorService` (WebSocket + polling recovery) runs beside
the interface layer, writing to `data/notification_state.json` and emitting
notifications through the same use cases.

## Layer Responsibilities

- **Interface Layer**: Handles transport concerns (HTTP, Telegram callbacks, CLI). Interfaces construct requests, delegate to use cases, and adapt responses for presentation.
- **Use Case Layer**: Centralized business logic in `src/use_cases/`. Use cases coordinate services, enforce validation, and return transport-agnostic results so API and bot remain in sync.
- **Services Layer**: Concrete integrations with Hyperliquid plus calculations that require direct market/account access. Services expose async APIs used by use cases and background workers.
- **External Integrations Layer**: Hyperliquid APIs, persisted JSON state, and environment configuration. Services and workers shield higher layers from transport/security details.

## Cross-Cutting Concerns

- **Configuration & Logging**: Centralized in `src/config`, imported by all layers for consistent logging and environment management.
- **Telegram Component Library**: Builders in `src/bot/components/` supply reusable UI fragments consumed by handlers, keeping messaging consistent with UX specs.
- **Testing**: Unit tests target use cases and services; integration scripts in `scripts/` validate Hyperliquid interactions on testnet to ensure end-to-end reliability.
