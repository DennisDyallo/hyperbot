# Preliminary Plan: Strategy-Based Alert System & Webhook Architecture

**Date**: 2025-01-13
**Status**: Draft - Awaiting Approval
**Author**: Claude (Architectural Design)

---

## Executive Summary

This document presents an architectural design for:
1. **Strategy-based alert system** - Abstracts detection logic, event generation, and notification delivery
2. **Webhook integration** - Receives trading signals from TradingView and custom sources
3. **Unified signal routing** - Strategies and webhooks produce signals routed to handlers

### Key Design Principles

1. **Strategy Pattern** - Encapsulated, pluggable detection algorithms
2. **Event-Driven Architecture** - Loose coupling via signals and events
3. **Composable Conditions** - Build complex logic from simple primitives
4. **Observer Pattern** - Multiple handlers react to same signal
5. **Use Case Integration** - Leverages existing Phase 4 patterns
6. **Security-First Webhooks** - HMAC authentication, idempotency, replay protection

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Strategy System                           │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Strategy   │      │   Strategy   │                    │
│  │   Registry   │─────▶│   Executor   │                    │
│  │  (Plugin)    │      │  (Runner)    │                    │
│  └──────────────┘      └───────┬──────┘                    │
│                                 │                           │
│                                 ▼                           │
│  ┌──────────────────────────────────────────────┐          │
│  │         Concrete Strategies                  │          │
│  ├──────────────┬──────────────┬────────────────┤          │
│  │ Price Alert  │ Trend Change │ Engulfing      │          │
│  │ PnL Pivot    │ Risk Monitor │ Rebalance      │          │
│  └──────────────┴──────────────┴────────────────┘          │
│                                 │                           │
│                                 ▼                           │
│                          ┌──────────┐                       │
│                          │  Signals │                       │
│                          └────┬─────┘                       │
│                               │                             │
└───────────────────────────────┼─────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Signal Router       │
                    │   (Observer Pattern)  │
                    └─────┬─────────┬───────┘
                          │         │
              ┌───────────┘         └───────────┐
              ▼                                  ▼
    ┌──────────────────┐              ┌──────────────────┐
    │  Notification    │              │   Execution      │
    │  Handler         │              │   Handler        │
    │  (Telegram)      │              │  (Trade Orders)  │
    └──────────────────┘              └──────────────────┘
```

---

## Core Abstractions

### 1. **BaseStrategy** - The Foundation

**Purpose**: Define the interface for all trading strategies.

**Key Responsibilities**:
- Evaluate market conditions
- Generate signals when conditions met
- Maintain internal state (if needed)
- Validate configuration

**Interface**:

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, TypeVar

class StrategyType(Enum):
    """Strategy classification."""
    ALERT = "alert"           # Generate notifications only
    EXECUTION = "execution"   # Execute trades automatically
    ANALYSIS = "analysis"     # Calculate metrics/aggregates
    RISK = "risk"             # Risk monitoring and account health alerts

TSignal = TypeVar("TSignal", bound="Signal")

class BaseStrategy(ABC, Generic[TSignal]):
    """
    Base class for all trading strategies.

    Strategies are:
    - Self-contained (no global state dependencies)
    - Composable (can be combined)
    - Configurable (behavior driven by config)
    - Stateful or stateless (strategy decides)
    - Testable (pure logic, mockable dependencies)
    """

    def __init__(self, name: str, strategy_type: StrategyType):
        self.name = name
        self.strategy_type = strategy_type
        self.enabled = True
        self.state: dict = {}  # Optional internal state

    @abstractmethod
    async def evaluate(self, context: "StrategyContext") -> TSignal | None:
        """
        Core strategy logic: evaluate conditions and generate signal.

        Args:
            context: Current market state, positions, account data

        Returns:
            Signal if conditions met, None otherwise
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """
        Validate strategy configuration before instantiation.

        Returns:
            True if config is valid, False otherwise
        """
        pass

    def reset_state(self):
        """Reset internal state (useful for backtesting)."""
        self.state.clear()
```

**Design Rationale**:
- **Generic over TSignal**: Type-safe signal generation
- **Strategy Type**: Categorize strategies by intent (alert vs execution)
- **Enabled flag**: Runtime enable/disable without removing from registry
- **State dict**: Optional state for strategies that need memory
- **Async evaluate**: Non-blocking, can call async services
- **Validate config**: Fail fast on misconfiguration

---

### 2. **StrategyContext** - The Data Provider

**Purpose**: Provide all data a strategy might need to evaluate conditions.

**Key Responsibilities**:
- Centralize data access
- Abstract away service layer details
- Enable easy mocking for testing

**Interface**:

```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class StrategyContext:
    """
    Context object passed to strategies containing all necessary data.

    Built from current system state by StrategyExecutor before evaluation.
    """

    # Market data
    current_prices: Dict[str, float]  # {coin: price}
    price_history: "PriceHistoryService"  # For candle/trend queries

    # Account data
    account_value: float
    available_balance: float
    margin_used: float
    cross_margin_ratio: float

    # Position data
    positions: List[Dict]  # List of position dicts from position_service

    # Risk data
    portfolio_risk: "PortfolioRisk"  # From risk_calculator

    # Time context
    timestamp: datetime

    # Service references (for advanced strategies)
    market_data_service: "MarketDataService"
    position_service: "PositionService"
    risk_calculator: "RiskCalculator"
```

**Design Rationale**:
- **Pre-fetched data**: Avoid redundant API calls per strategy
- **Service references**: Allow strategies to fetch additional data if needed
- **Immutable snapshot**: Context represents a point in time
- **Testable**: Easy to create mock contexts for unit tests

---

### 3. **Signal** - The Output

**Purpose**: Represent actionable insights generated by strategies.

**Key Responsibilities**:
- Carry detection information
- Include routing metadata (priority, type)
- Provide execution parameters (if applicable)

**Interface**:

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any

class SignalType(Enum):
    """Signal classification for routing."""
    ALERT = "alert"              # Notification only
    BUY = "buy"                  # Execute buy order
    SELL = "sell"                # Execute sell order
    CLOSE_POSITION = "close"     # Close existing position
    REBALANCE = "rebalance"      # Trigger rebalancing
    ADJUST_LEVERAGE = "leverage" # Change position leverage

class SignalPriority(Enum):
    """Signal urgency levels."""
    CRITICAL = 100  # Liquidation risk, immediate action required
    HIGH = 75       # Position pivots, large swings
    MEDIUM = 50     # Trend changes, moderate moves
    LOW = 25        # Informational, analytics
    INFO = 0        # Background data, logging only

class Signal(BaseModel):
    """
    Trading signal generated by a strategy.

    Signals are routed to appropriate handlers based on type and priority.
    """

    # Core identification
    type: SignalType
    priority: SignalPriority = SignalPriority.MEDIUM
    coin: str

    # Human-readable description
    reason: str
    details: str | None = None

    # Metadata for handlers
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Strategy attribution
    strategy_name: str
    generated_at: datetime = Field(default_factory=datetime.now)

    # Optional execution parameters
    size: float | None = None
    price: float | None = None
    leverage: int | None = None

    # Deduplication support
    def calculate_hash(self) -> str:
        """Generate unique hash for deduplication."""
        key = f"{self.type.value}_{self.coin}_{self.reason}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
```

**Design Rationale**:
- **Pydantic model**: Type validation, serialization for logging/persistence
- **Priority enum**: Explicit urgency levels for routing decisions
- **Strategy attribution**: Track which strategy generated signal
- **Execution params**: Optional fields for automated execution
- **Deduplication hash**: Prevent duplicate alerts

---

### 4. **Condition System** - Composable Logic

**Purpose**: Build complex conditions from simple, reusable primitives.

**Key Responsibilities**:
- Encapsulate boolean logic
- Support composition (AND, OR, NOT)
- Enable readable, declarative condition definitions

**Interface**:

```python
from abc import ABC, abstractmethod
from typing import Callable

class Condition(ABC):
    """
    Base class for strategy conditions.

    Conditions are composable using logical operators:
    - `cond1 & cond2` - AND
    - `cond1 | cond2` - OR
    - `~cond1` - NOT
    """

    @abstractmethod
    async def evaluate(self, context: StrategyContext) -> bool:
        """Evaluate condition against current context."""
        pass

    def __and__(self, other: "Condition") -> "AndCondition":
        """Combine with AND logic."""
        return AndCondition(self, other)

    def __or__(self, other: "Condition") -> "OrCondition":
        """Combine with OR logic."""
        return OrCondition(self, other)

    def __invert__(self) -> "NotCondition":
        """Invert condition with NOT logic."""
        return NotCondition(self)

# Composite conditions
class AndCondition(Condition):
    """AND combination of conditions."""
    def __init__(self, left: Condition, right: Condition):
        self.left = left
        self.right = right

    async def evaluate(self, context: StrategyContext) -> bool:
        return await self.left.evaluate(context) and await self.right.evaluate(context)

class OrCondition(Condition):
    """OR combination of conditions."""
    def __init__(self, left: Condition, right: Condition):
        self.left = left
        self.right = right

    async def evaluate(self, context: StrategyContext) -> bool:
        return await self.left.evaluate(context) or await self.right.evaluate(context)

class NotCondition(Condition):
    """NOT inversion of condition."""
    def __init__(self, condition: Condition):
        self.condition = condition

    async def evaluate(self, context: StrategyContext) -> bool:
        return not await self.condition.evaluate(context)
```

**Example Built-in Conditions**:

```python
class PriceAboveCondition(Condition):
    """Check if current price is above threshold."""
    def __init__(self, coin: str, threshold: float):
        self.coin = coin
        self.threshold = threshold

    async def evaluate(self, context: StrategyContext) -> bool:
        return context.current_prices.get(self.coin, 0) > self.threshold

class PositionExistsCondition(Condition):
    """Check if position exists for coin."""
    def __init__(self, coin: str):
        self.coin = coin

    async def evaluate(self, context: StrategyContext) -> bool:
        return any(p["position"]["coin"] == self.coin for p in context.positions)

class RiskLevelCondition(Condition):
    """Check if position risk level matches."""
    def __init__(self, coin: str, risk_level: RiskLevel):
        self.coin = coin
        self.risk_level = risk_level

    async def evaluate(self, context: StrategyContext) -> bool:
        position_risks = context.portfolio_risk.position_risks
        for risk in position_risks:
            if risk.coin == self.coin:
                return risk.risk_level == self.risk_level
        return False

# Usage example:
alert_condition = (
    PriceAboveCondition("BTC", 100000) &
    PositionExistsCondition("BTC") &
    RiskLevelCondition("BTC", RiskLevel.HIGH)
)
```

**Design Rationale**:
- **Operator overloading**: Natural Python syntax for composition
- **Reusable primitives**: Build library of common conditions
- **Testable in isolation**: Each condition can be unit tested
- **Declarative**: Condition composition reads like natural logic

---

### 5. **StrategyRegistry** - Plugin Discovery

**Purpose**: Register and instantiate strategies dynamically.

**Key Responsibilities**:
- Maintain registry of available strategies
- Support decorator-based registration
- Validate configuration before instantiation
- Enable/disable strategies at runtime

**Interface**:

```python
from typing import Dict, Type, List

class StrategyRegistry:
    """
    Central registry for trading strategies.

    Supports:
    - Decorator-based registration (@StrategyRegistry.register)
    - Dynamic instantiation from config
    - Strategy discovery and listing
    """

    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _instances: Dict[str, BaseStrategy] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register strategy class.

        Usage:
            @StrategyRegistry.register("price_alert")
            class PriceAlertStrategy(BaseStrategy):
                ...
        """
        def decorator(strategy_class: Type[BaseStrategy]):
            if name in cls._strategies:
                logger.warning(f"Strategy '{name}' already registered, overwriting")

            cls._strategies[name] = strategy_class
            logger.info(f"Registered strategy: {name}")
            return strategy_class
        return decorator

    @classmethod
    def get_strategy(cls, name: str, config: dict) -> BaseStrategy:
        """
        Instantiate strategy by name with configuration.

        Args:
            name: Registered strategy name
            config: Strategy-specific configuration

        Returns:
            Configured strategy instance

        Raises:
            ValueError: If strategy not registered or config invalid
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Strategy '{name}' not registered. "
                f"Available: {available}"
            )

        strategy_class = cls._strategies[name]
        instance = strategy_class(config)

        if not instance.validate_config(config):
            raise ValueError(
                f"Invalid configuration for strategy '{name}': {config}"
            )

        # Cache instance for reuse
        instance_key = f"{name}_{id(config)}"
        cls._instances[instance_key] = instance

        return instance

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all registered strategy names."""
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_info(cls, name: str) -> dict:
        """Get metadata about registered strategy."""
        if name not in cls._strategies:
            return {}

        strategy_class = cls._strategies[name]
        return {
            "name": name,
            "class": strategy_class.__name__,
            "doc": strategy_class.__doc__,
            "module": strategy_class.__module__
        }
```

**Design Rationale**:
- **Decorator pattern**: Clean, Pythonic registration
- **Lazy instantiation**: Only create strategies when needed
- **Config validation**: Fail fast on bad configuration
- **Instance caching**: Reuse strategies where appropriate

---

### 6. **SignalRouter** - Event Distribution

**Purpose**: Route signals to appropriate handlers using Observer pattern.

**Key Responsibilities**:
- Subscribe handlers to signal types
- Route signals to all interested handlers
- Handle errors gracefully (one handler failure doesn't affect others)
- Support priority-based routing

**Interface**:

```python
from typing import Callable, List, Dict, Awaitable
import asyncio

SignalHandler = Callable[[Signal], Awaitable[None]]

class SignalRouter:
    """
    Routes signals to registered handlers (Observer pattern).

    Handlers can be:
    - Telegram notification senders
    - Order execution functions
    - Analytics loggers
    - External webhooks

    Multiple handlers can subscribe to same signal type.
    """

    def __init__(self):
        self._handlers: Dict[SignalType, List[SignalHandler]] = {}
        self._priority_handlers: Dict[SignalPriority, List[SignalHandler]] = {}

    def subscribe(
        self,
        signal_type: SignalType,
        handler: SignalHandler,
        priority_filter: SignalPriority | None = None
    ):
        """
        Subscribe handler to signal type.

        Args:
            signal_type: Type of signals to handle
            handler: Async function that processes signal
            priority_filter: Only receive signals >= this priority (optional)
        """
        if signal_type not in self._handlers:
            self._handlers[signal_type] = []

        handler_entry = {
            "handler": handler,
            "priority_filter": priority_filter
        }
        self._handlers[signal_type].append(handler_entry)

        logger.info(
            f"Subscribed handler to {signal_type.value} signals "
            f"(priority filter: {priority_filter})"
        )

    async def route(self, signal: Signal):
        """
        Route signal to all registered handlers.

        Args:
            signal: Signal to distribute
        """
        handlers = self._handlers.get(signal.type, [])

        if not handlers:
            logger.warning(
                f"No handlers registered for signal type {signal.type.value}"
            )
            return

        # Filter handlers by priority
        applicable_handlers = [
            h["handler"] for h in handlers
            if h["priority_filter"] is None or
               signal.priority.value >= h["priority_filter"].value
        ]

        # Execute handlers concurrently
        tasks = [
            self._safe_execute(handler, signal)
            for handler in applicable_handlers
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, handler: SignalHandler, signal: Signal):
        """Execute handler with error catching."""
        try:
            await handler(signal)
        except Exception as e:
            logger.error(
                f"Signal handler failed for {signal.strategy_name}: {e}",
                exc_info=True
            )
```

**Design Rationale**:
- **Observer pattern**: Loose coupling between signal generation and handling
- **Priority filtering**: Handlers can opt to receive only urgent signals
- **Concurrent execution**: Handlers run in parallel (non-blocking)
- **Error isolation**: One handler failure doesn't affect others
- **Flexible subscription**: Multiple handlers per signal type

---

### 7. **StrategyExecutor** - The Orchestrator

**Purpose**: Execute strategies and route their signals.

**Key Responsibilities**:
- Build StrategyContext from current system state
- Execute all enabled strategies
- Route generated signals to handlers
- Track strategy performance and errors

**Interface**:

```python
class StrategyExecutor:
    """
    Orchestrates strategy execution and signal routing.

    Responsibilities:
    - Build context from current system state
    - Execute all enabled strategies
    - Route signals to handlers
    - Track strategy metrics
    """

    def __init__(
        self,
        registry: StrategyRegistry,
        router: SignalRouter,
        state_store: "StrategyStateStore"
    ):
        self.registry = registry
        self.router = router
        self.state_store = state_store
        self.active_strategies: List[BaseStrategy] = []
        self.execution_metrics: Dict[str, dict] = {}

    async def add_strategy(self, name: str, config: dict):
        """Add and enable strategy from config."""
        strategy = self.registry.get_strategy(name, config)

        # Restore previous state if exists
        saved_state = self.state_store.get_state(strategy.name)
        if saved_state:
            strategy.state = saved_state.state_data

        if strategy.enabled:
            self.active_strategies.append(strategy)
            logger.info(f"Added strategy: {strategy.name}")

    async def execute_all(self, context: StrategyContext):
        """
        Execute all active strategies concurrently.

        Args:
            context: Current market/account state
        """
        tasks = [
            self._execute_strategy(strategy, context)
            for strategy in self.active_strategies
            if strategy.enabled
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for strategy, result in zip(self.active_strategies, results):
            if isinstance(result, Exception):
                logger.error(f"Strategy '{strategy.name}' failed: {result}")
                self._record_failure(strategy.name)
            elif result:  # Signal generated
                await self.router.route(result)
                self._record_success(strategy.name, result)

    async def _execute_strategy(
        self,
        strategy: BaseStrategy,
        context: StrategyContext
    ) -> Signal | None:
        """Execute single strategy with timing."""
        start_time = datetime.now()

        try:
            signal = await strategy.evaluate(context)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(
                f"Strategy '{strategy.name}' executed in {execution_time:.3f}s"
            )

            return signal

        except Exception as e:
            logger.exception(f"Strategy '{strategy.name}' raised exception")
            raise

    def _record_success(self, strategy_name: str, signal: Signal):
        """Record successful signal generation."""
        if strategy_name not in self.execution_metrics:
            self.execution_metrics[strategy_name] = {
                "signals_generated": 0,
                "executions": 0,
                "failures": 0
            }

        self.execution_metrics[strategy_name]["signals_generated"] += 1
        self.execution_metrics[strategy_name]["executions"] += 1

    def _record_failure(self, strategy_name: str):
        """Record strategy execution failure."""
        if strategy_name not in self.execution_metrics:
            self.execution_metrics[strategy_name] = {
                "signals_generated": 0,
                "executions": 0,
                "failures": 0
            }

        self.execution_metrics[strategy_name]["failures"] += 1

    async def build_context(self) -> StrategyContext:
        """
        Build StrategyContext from current system state.

        Fetches data from all services and constructs context object.
        """
        from src.services.position_service import position_service
        from src.services.account_service import account_service
        from src.services.market_data_service import market_data_service
        from src.services.risk_calculator import risk_calculator
        from src.services.price_history_service import price_history_service

        # Fetch current data
        positions = position_service.list_positions()
        account_summary = account_service.get_account_summary()

        # Get prices for all active coins
        coins = [p["position"]["coin"] for p in positions]
        current_prices = {}
        for coin in coins:
            try:
                current_prices[coin] = market_data_service.get_price(coin)
            except Exception as e:
                logger.warning(f"Failed to fetch price for {coin}: {e}")

        # Calculate portfolio risk
        portfolio_risk = risk_calculator.assess_portfolio_risk(
            positions=positions,
            account_value=account_summary["total_account_value"]
        )

        return StrategyContext(
            current_prices=current_prices,
            price_history=price_history_service,
            account_value=account_summary["total_account_value"],
            available_balance=account_summary["available_balance"],
            margin_used=account_summary["margin_used"],
            cross_margin_ratio=account_summary["cross_margin_ratio_pct"],
            positions=positions,
            portfolio_risk=portfolio_risk,
            timestamp=datetime.now(),
            market_data_service=market_data_service,
            position_service=position_service,
            risk_calculator=risk_calculator
        )
```

**Design Rationale**:
- **Async execution**: Strategies run concurrently for performance
- **Context building**: Centralized data fetching, reused across strategies
- **Error isolation**: One strategy failure doesn't stop others
- **Metrics tracking**: Monitor strategy performance over time
- **State persistence**: Strategies can maintain state across restarts

---

## Example Strategy Implementations

### 1. **PnL Pivot Strategy**

**Purpose**: Alert when position crosses break-even point.

```python
@StrategyRegistry.register("pnl_pivot")
class PnLPivotStrategy(BaseStrategy):
    """
    Alert when position PnL changes sign (profit ↔ loss).

    Config:
        cooldown_seconds: int - Minimum time between alerts (default: 900)
    """

    def __init__(self, config: dict):
        super().__init__(
            name="PnLPivot",
            strategy_type=StrategyType.ALERT
        )
        self.cooldown_seconds = config.get("cooldown_seconds", 900)
        self.state = {
            "previous_pnl": {},      # {coin: pnl_value}
            "last_alert_time": {}    # {coin: timestamp}
        }

    async def evaluate(self, context: StrategyContext) -> Signal | None:
        for position in context.positions:
            coin = position["position"]["coin"]
            current_pnl = position["position"]["unrealized_pnl"]

            # Get previous PnL
            previous_pnl = self.state["previous_pnl"].get(coin, None)

            # Update state
            self.state["previous_pnl"][coin] = current_pnl

            # Check for sign change
            if previous_pnl is None:
                continue

            pivot_detected = (
                (previous_pnl < 0 and current_pnl > 0) or
                (previous_pnl > 0 and current_pnl < 0)
            )

            if not pivot_detected:
                continue

            # Check cooldown
            last_alert = self.state["last_alert_time"].get(coin, 0)
            now = datetime.now().timestamp()
            if now - last_alert < self.cooldown_seconds:
                continue

            # Generate signal
            self.state["last_alert_time"][coin] = now

            direction = "PROFIT → LOSS" if current_pnl < 0 else "LOSS → PROFIT"

            return Signal(
                type=SignalType.ALERT,
                priority=SignalPriority.HIGH,
                coin=coin,
                reason=f"PnL Pivot - {coin}",
                details=f"Position crossed break-even! {direction}",
                strategy_name=self.name,
                metadata={
                    "previous_pnl": previous_pnl,
                    "current_pnl": current_pnl,
                    "direction": direction
                }
            )

        return None

    def validate_config(self, config: dict) -> bool:
        cooldown = config.get("cooldown_seconds", 900)
        return isinstance(cooldown, int) and cooldown > 0
```

---

### 2. **Trend Change Strategy (Multi-Timeframe)**

**Purpose**: Alert when trend changes on any tracked timeframe.

```python
@StrategyRegistry.register("trend_change")
class TrendChangeStrategy(BaseStrategy):
    """
    Alert when price trend changes on any timeframe.

    Tracks: 1h, 4h, 1d, 1w

    Config:
        timeframes: list[str] - Timeframes to monitor (default: all)
        cooldown_per_tf: int - Cooldown per timeframe (default: 3600)
    """

    def __init__(self, config: dict):
        super().__init__(
            name="TrendChange",
            strategy_type=StrategyType.ALERT
        )
        self.timeframes = config.get("timeframes", ["1h", "4h", "1d", "1w"])
        self.cooldown = config.get("cooldown_per_tf", 3600)
        self.state = {
            "previous_trends": {},  # {coin: {tf: trend}}
            "last_alert": {}        # {coin: {tf: timestamp}}
        }

    async def evaluate(self, context: StrategyContext) -> Signal | None:
        for position in context.positions:
            coin = position["position"]["coin"]

            # Initialize state for coin
            if coin not in self.state["previous_trends"]:
                self.state["previous_trends"][coin] = {}
                self.state["last_alert"][coin] = {}

            # Check each timeframe
            for tf in self.timeframes:
                current_trend = context.price_history.get_trend(coin, tf)
                previous_trend = self.state["previous_trends"][coin].get(tf, None)

                # Update state
                self.state["previous_trends"][coin][tf] = current_trend

                # Check for change
                if previous_trend is None or previous_trend == current_trend:
                    continue

                # Check cooldown
                last_alert = self.state["last_alert"][coin].get(tf, 0)
                now = datetime.now().timestamp()
                if now - last_alert < self.cooldown:
                    continue

                # Generate signal
                self.state["last_alert"][coin][tf] = now

                trend_emoji = "📈" if current_trend == "UPTREND" else "📉"

                return Signal(
                    type=SignalType.ALERT,
                    priority=SignalPriority.MEDIUM,
                    coin=coin,
                    reason=f"Trend Change - {coin} ({tf})",
                    details=(
                        f"{trend_emoji} {tf} timeframe: "
                        f"{previous_trend} → {current_trend}"
                    ),
                    strategy_name=self.name,
                    metadata={
                        "timeframe": tf,
                        "previous_trend": previous_trend,
                        "current_trend": current_trend,
                        "current_price": context.current_prices.get(coin)
                    }
                )

        return None

    def validate_config(self, config: dict) -> bool:
        valid_tfs = ["1h", "4h", "1d", "1w"]
        timeframes = config.get("timeframes", valid_tfs)
        return all(tf in valid_tfs for tf in timeframes)
```

---

### 3. **Engulfing Candle Strategy**

**Purpose**: Alert on bullish/bearish engulfing candle patterns.

```python
@StrategyRegistry.register("engulfing_candle")
class EngulfingCandleStrategy(BaseStrategy):
    """
    Alert on engulfing candle patterns (reversal signals).

    Config:
        timeframes: list[str] - Timeframes to monitor (default: ["1h", "4h"])
        cooldown_seconds: int - Minimum time between alerts (default: 3600)
    """

    def __init__(self, config: dict):
        super().__init__(
            name="EngulfingCandle",
            strategy_type=StrategyType.ALERT
        )
        self.timeframes = config.get("timeframes", ["1h", "4h"])
        self.cooldown = config.get("cooldown_seconds", 3600)
        self.state = {
            "last_alert": {}  # {coin: {tf: timestamp}}
        }

    async def evaluate(self, context: StrategyContext) -> Signal | None:
        for position in context.positions:
            coin = position["position"]["coin"]

            # Initialize state
            if coin not in self.state["last_alert"]:
                self.state["last_alert"][coin] = {}

            # Check each timeframe
            for tf in self.timeframes:
                # Get engulfing pattern detection
                engulfing = context.price_history.detect_engulfing(coin, tf)

                if not engulfing:
                    continue

                # Check cooldown
                last_alert = self.state["last_alert"][coin].get(tf, 0)
                now = datetime.now().timestamp()
                if now - last_alert < self.cooldown:
                    continue

                # Generate signal
                self.state["last_alert"][coin][tf] = now

                pattern_type = engulfing["type"]  # "BULLISH" or "BEARISH"
                emoji = "🔥" if pattern_type == "BULLISH" else "❄️"

                # Check if pattern aligns with position
                is_long = position["position"]["size"] > 0
                alignment = (
                    "favorable" if (
                        (is_long and pattern_type == "BULLISH") or
                        (not is_long and pattern_type == "BEARISH")
                    ) else "unfavorable"
                )

                return Signal(
                    type=SignalType.ALERT,
                    priority=SignalPriority.MEDIUM,
                    coin=coin,
                    reason=f"{emoji} {pattern_type} Engulfing - {coin} ({tf})",
                    details=(
                        f"Strong reversal signal detected!\n"
                        f"Pattern is {alignment} for your "
                        f"{'LONG' if is_long else 'SHORT'} position"
                    ),
                    strategy_name=self.name,
                    metadata={
                        "timeframe": tf,
                        "pattern_type": pattern_type,
                        "alignment": alignment,
                        "candle_data": engulfing
                    }
                )

        return None

    def validate_config(self, config: dict) -> bool:
        valid_tfs = ["1h", "4h", "1d", "1w"]
        timeframes = config.get("timeframes", ["1h", "4h"])
        return all(tf in valid_tfs for tf in timeframes)
```

---

## Integration with Existing Architecture

### 1. **StrategyService** - The Singleton

```python
# src/services/strategy_service.py
class StrategyService:
    """
    Service for managing trading strategies.

    Follows existing service pattern (singleton).
    Integrates with existing notification and execution infrastructure.
    """

    def __init__(self):
        self.registry = StrategyRegistry()
        self.router = SignalRouter()
        self.state_store = StrategyStateStore()
        self.executor = StrategyExecutor(
            self.registry,
            self.router,
            self.state_store
        )

        # Set up signal handlers
        self._setup_handlers()

        # Load strategies from config
        asyncio.create_task(self._load_strategies())

    def _setup_handlers(self):
        """Connect signals to existing infrastructure."""
        from src.services.order_monitor_service import order_monitor_service

        # Route ALERT signals to Telegram
        async def telegram_alert_handler(signal: Signal):
            """Send alert to Telegram."""
            if order_monitor_service.bot:
                from src.config import settings

                message = self._format_alert_message(signal)

                await order_monitor_service.bot.send_message(
                    chat_id=settings.TELEGRAM_AUTHORIZED_USERS[0],
                    text=message,
                    parse_mode="Markdown"
                )

        self.router.subscribe(
            SignalType.ALERT,
            telegram_alert_handler,
            priority_filter=SignalPriority.MEDIUM  # Only send MEDIUM+ priority
        )

        # Route EXECUTION signals to order placement use case
        async def execution_handler(signal: Signal):
            """Execute trade from signal."""
            from src.use_cases.trading.place_order import place_order_use_case

            # Convert signal to order request
            # ... implementation ...

        self.router.subscribe(SignalType.BUY, execution_handler)
        self.router.subscribe(SignalType.SELL, execution_handler)

    async def _load_strategies(self):
        """Load strategies from settings."""
        from src.config import settings

        for strategy_config in settings.ACTIVE_STRATEGIES:
            try:
                await self.executor.add_strategy(
                    strategy_config["name"],
                    strategy_config["config"]
                )
                logger.info(f"Loaded strategy: {strategy_config['name']}")
            except Exception as e:
                logger.error(f"Failed to load strategy: {e}")

    async def execute_strategies(self):
        """Execute all active strategies."""
        context = await self.executor.build_context()
        await self.executor.execute_all(context)

    def _format_alert_message(self, signal: Signal) -> str:
        """Format signal as Telegram message."""
        priority_emoji = {
            SignalPriority.CRITICAL: "🚨",
            SignalPriority.HIGH: "⚠️",
            SignalPriority.MEDIUM: "📊",
            SignalPriority.LOW: "ℹ️",
            SignalPriority.INFO: "💡"
        }

        emoji = priority_emoji.get(signal.priority, "📌")

        message_lines = [
            f"{emoji} **{signal.reason}**",
            "",
            signal.details or "",
            "",
            f"_Strategy: {signal.strategy_name}_",
            f"_Time: {signal.generated_at.strftime('%H:%M:%S')}_"
        ]

        return "\n".join(filter(None, message_lines))

# Global singleton
strategy_service = StrategyService()
```

---

### 2. **Use Case Layer Integration**

```python
# src/use_cases/strategies/execute_strategies.py
from src.use_cases.base import BaseUseCase
from pydantic import BaseModel

class ExecuteStrategiesRequest(BaseModel):
    """Request to execute strategies."""
    strategy_names: list[str] | None = None  # None = execute all
    force_execution: bool = False

class ExecuteStrategiesResponse(BaseModel):
    """Response from strategy execution."""
    strategies_executed: int
    signals_generated: int
    execution_time_seconds: float
    errors: list[str] = []

class ExecuteStrategiesUseCase(BaseUseCase[ExecuteStrategiesRequest, ExecuteStrategiesResponse]):
    """
    Use case for executing trading strategies.

    Can be called from:
    - API endpoints (manual execution)
    - Telegram bot (/execute_strategies command)
    - Scheduled jobs (periodic execution)
    """

    async def execute(self, request: ExecuteStrategiesRequest) -> ExecuteStrategiesResponse:
        from src.services.strategy_service import strategy_service
        import time

        start_time = time.time()

        # Build context
        context = await strategy_service.executor.build_context()

        # Execute strategies
        await strategy_service.executor.execute_all(context)

        execution_time = time.time() - start_time

        # Gather metrics
        strategies_executed = len(strategy_service.executor.active_strategies)
        signals_generated = sum(
            metrics["signals_generated"]
            for metrics in strategy_service.executor.execution_metrics.values()
        )

        return ExecuteStrategiesResponse(
            strategies_executed=strategies_executed,
            signals_generated=signals_generated,
            execution_time_seconds=execution_time,
            errors=[]
        )

# Instantiate use case
execute_strategies_use_case = ExecuteStrategiesUseCase()
```

---

### 3. **Scheduled Execution (JobQueue Integration)**

```python
# src/bot/main.py (additions to post_init)
async def post_init(application: Application):
    # ... existing code ...

    # Start StrategyService
    from src.services.strategy_service import strategy_service
    strategy_service.bot = application.bot  # Inject bot for notifications

    # Schedule strategy execution every 5 minutes
    from src.use_cases.strategies.execute_strategies import execute_strategies_use_case

    async def execute_strategies_job(context: ContextTypes.DEFAULT_TYPE):
        """Periodic strategy execution."""
        try:
            request = ExecuteStrategiesRequest()
            result = await execute_strategies_use_case.execute(request)

            logger.info(
                f"Strategies executed: {result.strategies_executed}, "
                f"Signals: {result.signals_generated}"
            )
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")

    application.job_queue.run_repeating(
        callback=execute_strategies_job,
        interval=300,  # 5 minutes
        first=10,  # Start 10 seconds after bot starts
        name="strategy_execution"
    )

    logger.info("✅ Strategy system initialized")
```

---

## File Structure

```
src/
├── strategies/
│   ├── __init__.py
│   ├── base.py                     # BaseStrategy, StrategyType, StrategyContext
│   ├── registry.py                 # StrategyRegistry
│   ├── signals.py                  # Signal, SignalType, SignalPriority, SignalRouter
│   ├── conditions.py               # Condition, AndCondition, OrCondition, NotCondition
│   ├── executor.py                 # StrategyExecutor
│   ├── state.py                    # StrategyState, StrategyStateStore
│   └── built_in/
│       ├── __init__.py
│       ├── pnl_pivot.py            # PnLPivotStrategy
│       ├── trend_change.py         # TrendChangeStrategy
│       ├── engulfing_candle.py     # EngulfingCandleStrategy
│       ├── position_risk.py        # PositionRiskAlertStrategy
│       ├── price_alert.py          # PriceAlertStrategy
│       └── large_swing.py          # LargePnLSwingStrategy
├── services/
│   ├── strategy_service.py         # StrategyService (singleton)
│   └── price_history_service.py    # PriceHistoryService (NEW - multi-timeframe OHLC)
├── use_cases/
│   └── strategies/
│       ├── __init__.py
│       ├── execute_strategies.py   # ExecuteStrategiesUseCase
│       ├── list_strategies.py      # ListStrategiesUseCase
│       └── manage_strategy.py      # Enable/Disable strategy use cases
├── bot/
│   └── handlers/
│       └── strategies.py           # Telegram commands (/strategies, /toggle, etc.)
└── config/
    └── settings.py                 # Strategy configuration

tests/
└── strategies/
    ├── test_base.py
    ├── test_registry.py
    ├── test_signals.py
    ├── test_conditions.py
    ├── test_executor.py
    └── built_in/
        ├── test_pnl_pivot.py
        ├── test_trend_change.py
        └── test_engulfing_candle.py
```

---

## TradingView Webhook Integration

### Overview

The system integrates with TradingView alerts to receive trading signals and automatically execute orders. TradingView has specific constraints that require a tailored security architecture.

---

### TradingView Webhook Constraints

**🔴 CRITICAL LIMITATIONS:**

TradingView webhooks have the following technical constraints that MUST be addressed:

#### 1. **No Custom Headers Support**
- **Limitation**: TradingView does not allow custom HTTP headers in webhook requests
- **Impact**: Cannot use standard HMAC authentication via `X-Webhook-Signature` header
- **Solution**: Use secret token in JSON payload body instead

#### 2. **3-Second Timeout Requirement**
- **Limitation**: TradingView expects webhook endpoint to respond within 3 seconds
- **Impact**: Cannot perform long-running operations synchronously
- **Solution**:
  - Respond immediately with `202 Accepted`
  - Process webhook asynchronously using FastAPI BackgroundTasks
  - Target response time: <100ms

#### 3. **Static IP Addresses for Whitelisting**
- **Limitation**: TradingView webhooks originate from 4 static IP addresses
- **IPs**:
  - `52.89.214.238`
  - `34.212.75.30`
  - `54.218.53.128`
  - `52.32.178.7`
- **Solution**: IP whitelist middleware to reject requests from other sources

#### 4. **Port Restrictions**
- **Limitation**: Only ports 80 (HTTP) and 443 (HTTPS) are supported
- **Impact**: Cannot use non-standard ports
- **Solution**: Deploy on standard HTTPS port (443)

#### 5. **Content-Type Auto-Detection**
- **Limitation**: TradingView auto-detects content type (JSON vs plain text)
- **Impact**: Must structure alert message as valid JSON
- **Solution**: Use JSON payload format in alert message template

#### 6. **2FA Requirement**
- **Security**: TradingView requires 2FA enabled on account to use webhooks
- **Impact**: User must enable 2FA in TradingView account settings
- **Solution**: Document this requirement in user guide

---

### Security Architecture (TradingView-Specific)

**Adapted security model for TradingView constraints:**

#### 1. **Secret Token Authentication (Payload-Based)**

Since HMAC headers are not supported, use a secret token embedded in the JSON payload:

```python
# Webhook validation
async def validate_tradingview_webhook(payload: dict) -> bool:
    """
    Validate TradingView webhook using secret token.

    Args:
        payload: Webhook JSON payload

    Returns:
        True if valid, False otherwise
    """
    from src.config import settings

    # Extract secret from payload
    provided_secret = payload.get("secret")

    # Compare with configured secret (constant-time comparison)
    expected_secret = settings.TRADINGVIEW_WEBHOOK_SECRET

    if not provided_secret or not expected_secret:
        return False

    # Use secrets.compare_digest for timing-attack resistance
    import secrets
    return secrets.compare_digest(provided_secret, expected_secret)
```

**Configuration**:
```python
# .env
TRADINGVIEW_WEBHOOK_SECRET=your-random-secret-token-here
```

**Best practices**:
- Generate secret with `openssl rand -hex 32`
- Store in environment variable
- Use `secrets.compare_digest()` to prevent timing attacks
- Never log the secret

---

#### 2. **IP Whitelist Middleware**

Validate source IP address before processing webhook:

```python
# src/api/middleware/ip_whitelist.py
from fastapi import Request, HTTPException, status
from typing import List

TRADINGVIEW_IPS: List[str] = [
    "52.89.214.238",
    "34.212.75.30",
    "54.218.53.128",
    "52.32.178.7"
]

async def tradingview_ip_whitelist_middleware(request: Request, call_next):
    """
    Middleware to validate request originates from TradingView.

    Only allows requests from TradingView's static IP addresses.
    """
    client_ip = request.client.host

    # Check if IP is whitelisted
    if client_ip not in TRADINGVIEW_IPS:
        logger.warning(
            f"Rejected webhook from non-TradingView IP: {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid source IP"
        )

    response = await call_next(request)
    return response
```

**Integration with FastAPI**:
```python
# src/api/main.py
from src.api.middleware.ip_whitelist import tradingview_ip_whitelist_middleware

app.middleware("http")(tradingview_ip_whitelist_middleware)
```

---

#### 3. **Idempotency via Redis**

Prevent duplicate webhook processing using `alert_id`:

```python
# src/services/idempotency_service.py
import redis.asyncio as redis
from typing import Optional

class IdempotencyService:
    """
    Track processed webhooks to prevent duplicates.

    Uses Redis with 24-hour TTL.
    """

    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def is_processed(self, alert_id: str) -> bool:
        """
        Check if webhook with this alert_id was already processed.

        Args:
            alert_id: Unique identifier from TradingView

        Returns:
            True if already processed, False otherwise
        """
        key = f"webhook:tradingview:{alert_id}"
        exists = await self.redis.exists(key)
        return bool(exists)

    async def mark_processed(self, alert_id: str):
        """
        Mark webhook as processed.

        Args:
            alert_id: Unique identifier from TradingView
        """
        key = f"webhook:tradingview:{alert_id}"
        # Store for 24 hours
        await self.redis.setex(key, 86400, "1")

        logger.info(f"Marked webhook as processed: {alert_id}")

# Global singleton
idempotency_service = IdempotencyService()
```

---

#### 4. **Fast Response Pattern**

Meet the 3-second timeout requirement:

```python
# src/api/routes/webhooks.py
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/tradingview")
async def tradingview_webhook(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """
    Receive TradingView webhook and process asynchronously.

    CRITICAL: Must respond in <3 seconds.
    Target: <100ms response time.
    """
    from src.use_cases.webhooks.process_tradingview import process_tradingview_use_case
    from src.services.idempotency_service import idempotency_service

    # 1. Validate secret (fast - constant time)
    if not await validate_tradingview_webhook(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret"
        )

    # 2. Check idempotency (fast - Redis lookup)
    alert_id = payload.get("alert_id")
    if not alert_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing alert_id"
        )

    is_duplicate = await idempotency_service.is_processed(alert_id)
    if is_duplicate:
        logger.info(f"Duplicate webhook ignored: {alert_id}")
        return {"status": "ok", "message": "Already processed"}

    # 3. Mark as processed (fast - Redis write)
    await idempotency_service.mark_processed(alert_id)

    # 4. Queue async processing
    background_tasks.add_task(
        process_tradingview_use_case.execute,
        payload
    )

    # 5. Respond immediately (<100ms)
    return {
        "status": "accepted",
        "alert_id": alert_id,
        "message": "Webhook received and queued for processing"
    }
```

**Response Time Breakdown**:
- Secret validation: ~1-5ms (constant time comparison)
- Idempotency check: ~5-20ms (Redis lookup)
- Mark processed: ~5-20ms (Redis write)
- Queue task: ~1-5ms (in-memory)
- **Total: ~12-50ms** (well under 3-second limit)

---

#### 5. **Rate Limiting per IP**

Prevent abuse from compromised TradingView accounts:

```python
# src/api/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply to webhook endpoint
@router.post("/tradingview")
@limiter.limit("10/minute")  # Max 10 webhooks per minute per IP
async def tradingview_webhook(...):
    ...
```

---

### TradingView Webhook Payload Schema

**JSON payload structure sent by TradingView:**

```json
{
  "secret": "your-webhook-secret",
  "action": "buy",
  "ticker": "{{ticker}}",
  "usd_amount": 500,
  "leverage": 3,
  "timestamp": {{timenow}},
  "alert_id": "{{alert_name}}_{{timenow}}",
  "strategy": "{{strategy.order.comment}}",
  "close": {{close}},
  "volume": {{volume}}
}
```

**Field Descriptions**:

| Field | Type | Required | Description | TradingView Placeholder |
|-------|------|----------|-------------|------------------------|
| `secret` | string | ✅ Yes | Webhook authentication secret | Manual entry |
| `action` | string | ✅ Yes | Trade action to execute | Manual entry |
| `ticker` | string | ✅ Yes | Coin/asset symbol (e.g., "BTC") | `{{ticker}}` |
| `usd_amount` | number | ❌ No | USD value of order | Manual entry |
| `leverage` | integer | ❌ No | Position leverage (1-50) | Manual entry |
| `timestamp` | integer | ✅ Yes | Unix timestamp (milliseconds) | `{{timenow}}` |
| `alert_id` | string | ✅ Yes | Unique identifier for idempotency | `{{alert_name}}_{{timenow}}` |
| `strategy` | string | ❌ No | Strategy name/comment | `{{strategy.order.comment}}` |
| `close` | number | ❌ No | Current close price | `{{close}}` |
| `volume` | number | ❌ No | Current volume | `{{volume}}` |

**Action Types**:

- `"buy"` - Open long position or add to existing long
- `"sell"` - Open short position or add to existing short
- `"close"` - Close all positions for ticker
- `"close_all"` - Close ALL open positions (all tickers)

**Pydantic Model**:

```python
# src/models/webhook.py
from pydantic import BaseModel, Field, validator
from typing import Literal

class TradingViewWebhook(BaseModel):
    """TradingView webhook payload model."""

    secret: str = Field(..., description="Webhook authentication secret")
    action: Literal["buy", "sell", "close", "close_all"] = Field(
        ...,
        description="Trade action to execute"
    )
    ticker: str = Field(..., description="Coin/asset symbol")
    usd_amount: float | None = Field(
        None,
        description="USD value of order",
        gt=0
    )
    leverage: int | None = Field(
        None,
        description="Position leverage (1-50)",
        ge=1,
        le=50
    )
    timestamp: int = Field(..., description="Unix timestamp (ms)")
    alert_id: str = Field(..., description="Unique alert identifier")
    strategy: str | None = Field(None, description="Strategy name/comment")
    close: float | None = Field(None, description="Current close price")
    volume: float | None = Field(None, description="Current volume")

    @validator("ticker")
    def normalize_ticker(cls, v):
        """Normalize ticker to uppercase."""
        return v.upper()

    @validator("action")
    def validate_action(cls, v):
        """Validate action is supported."""
        valid_actions = {"buy", "sell", "close", "close_all"}
        if v not in valid_actions:
            raise ValueError(f"Invalid action: {v}")
        return v
```

---

### TradingView Alert Configuration

**Step-by-step guide for users to configure TradingView alerts:**

#### Step 1: Enable 2FA on TradingView Account

1. Go to TradingView Settings → Security
2. Enable Two-Factor Authentication (2FA)
3. Complete verification process

**⚠️ Webhooks will NOT work without 2FA enabled**

---

#### Step 2: Create Alert with Webhook

1. **Open TradingView chart** for desired asset (e.g., BTC/USD)

2. **Click Alert button** (alarm icon in toolbar)

3. **Configure alert condition**:
   - Select indicator/condition (e.g., "Crossing", "Greater Than", strategy signal)
   - Set parameters

4. **Configure notifications**:
   - Check **"Webhook URL"** checkbox
   - Enter webhook URL: `https://yourdomain.com/api/webhooks/tradingview`

5. **Set alert message** (JSON payload):

```json
{
  "secret": "your-webhook-secret-here",
  "action": "buy",
  "ticker": "{{ticker}}",
  "usd_amount": 500,
  "leverage": 3,
  "timestamp": {{timenow}},
  "alert_id": "{{alert_name}}_{{timenow}}"
}
```

**TradingView Placeholders**:
- `{{ticker}}` - Automatically replaced with coin symbol (e.g., "BTC")
- `{{timenow}}` - Current Unix timestamp in milliseconds
- `{{alert_name}}` - Alert name (for idempotency)
- `{{close}}` - Current close price
- `{{volume}}` - Current volume
- `{{strategy.order.comment}}` - Strategy comment (for Pine Script strategies)

6. **Set alert options**:
   - Alert name: Descriptive name (e.g., "BTC Long Entry")
   - Frequency: "Once Per Bar Close" (recommended for price-based alerts)
   - Expiration: "Open-ended" (never expires)

7. **Create Alert**

---

#### Step 3: Test Webhook

**Manual test using TradingView alert history:**

1. Trigger alert manually (modify condition to trigger immediately)
2. Check TradingView alert history:
   - Click alert icon → "Alert log"
   - Look for webhook delivery status
3. Check bot logs:
   - `logs/hyperbot.log` should show webhook received
4. Verify idempotency:
   - TradingView may retry failed webhooks
   - Bot should deduplicate using `alert_id`

---

#### Example Alert Configurations

**1. Simple Buy on Breakout**:
```json
{
  "secret": "your-secret",
  "action": "buy",
  "ticker": "{{ticker}}",
  "usd_amount": 1000,
  "leverage": 2,
  "timestamp": {{timenow}},
  "alert_id": "{{alert_name}}_{{timenow}}"
}
```

**2. Close Position on Stop Loss**:
```json
{
  "secret": "your-secret",
  "action": "close",
  "ticker": "{{ticker}}",
  "timestamp": {{timenow}},
  "alert_id": "{{alert_name}}_{{timenow}}",
  "close": {{close}}
}
```

**3. Strategy Signal (from Pine Script)**:
```json
{
  "secret": "your-secret",
  "action": "{{strategy.order.action}}",
  "ticker": "{{ticker}}",
  "usd_amount": {{strategy.position_size}},
  "leverage": 5,
  "timestamp": {{timenow}},
  "alert_id": "{{alert_name}}_{{timenow}}",
  "strategy": "{{strategy.order.comment}}"
}
```

---

### ProcessTradingViewUseCase

**Use case for processing TradingView webhooks:**

```python
# src/use_cases/webhooks/process_tradingview.py
from src.use_cases.base import BaseUseCase
from src.models.webhook import TradingViewWebhook
from pydantic import BaseModel

class ProcessTradingViewResponse(BaseModel):
    """Response from processing TradingView webhook."""
    success: bool
    action_taken: str
    order_id: int | None = None
    error: str | None = None

class ProcessTradingViewUseCase(BaseUseCase[TradingViewWebhook, ProcessTradingViewResponse]):
    """
    Process TradingView webhook and execute trading action.

    Converts webhook payload into Signal and routes to appropriate handler.
    """

    async def execute(self, request: TradingViewWebhook) -> ProcessTradingViewResponse:
        from src.services.strategy_service import strategy_service
        from src.strategies.signals import Signal, SignalType, SignalPriority
        from src.use_cases.trading.place_order import place_order_use_case
        from src.use_cases.trading.close_position import close_position_use_case

        try:
            # Map webhook action to signal type
            signal_type_map = {
                "buy": SignalType.BUY,
                "sell": SignalType.SELL,
                "close": SignalType.CLOSE_POSITION
            }

            # Handle close_all separately
            if request.action == "close_all":
                return await self._close_all_positions()

            # Create signal from webhook
            signal = Signal(
                type=signal_type_map[request.action],
                priority=SignalPriority.HIGH,  # TradingView signals are high priority
                coin=request.ticker,
                reason=f"TradingView Alert: {request.strategy or 'Manual'}",
                details=f"Action: {request.action.upper()}",
                strategy_name="TradingView",
                size=request.usd_amount,
                leverage=request.leverage,
                metadata={
                    "alert_id": request.alert_id,
                    "timestamp": request.timestamp,
                    "close_price": request.close,
                    "volume": request.volume
                }
            )

            # Route signal (will be handled by existing order placement handlers)
            await strategy_service.router.route(signal)

            logger.info(
                f"Processed TradingView webhook: {request.action} {request.ticker} "
                f"(alert_id: {request.alert_id})"
            )

            return ProcessTradingViewResponse(
                success=True,
                action_taken=f"{request.action} {request.ticker}",
                order_id=None  # Will be set by order handler
            )

        except Exception as e:
            logger.exception(f"Failed to process TradingView webhook: {e}")
            return ProcessTradingViewResponse(
                success=False,
                action_taken="none",
                error=str(e)
            )

    async def _close_all_positions(self) -> ProcessTradingViewResponse:
        """Close all open positions."""
        from src.services.position_service import position_service

        positions = position_service.list_positions()

        for position in positions:
            coin = position["position"]["coin"]
            # Close position logic...

        return ProcessTradingViewResponse(
            success=True,
            action_taken=f"Closed {len(positions)} positions"
        )

# Instantiate use case
process_tradingview_use_case = ProcessTradingViewUseCase()
```

---

### Updated File Structure

```
src/
├── api/
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── ip_whitelist.py          # ✨ NEW - IP validation for TradingView
│   │   └── rate_limit.py            # ✨ NEW - Rate limiting per IP
│   └── routes/
│       └── webhooks.py               # ✨ NEW - POST /api/webhooks/tradingview
├── use_cases/
│   └── webhooks/
│       ├── __init__.py
│       ├── process_tradingview.py   # ✨ NEW - ProcessTradingViewUseCase
│       └── validate_webhook.py      # ✨ NEW - ValidateWebhookUseCase
├── services/
│   └── idempotency_service.py       # ✨ NEW - Redis-based duplicate detection
└── models/
    └── webhook.py                    # ✨ NEW - TradingViewWebhook, WebhookAction models
```

---

## Configuration System

```python
# src/config/settings.py (additions)
class Settings(BaseSettings):
    # ... existing settings ...

    # Strategy System
    STRATEGIES_ENABLED: bool = True
    STRATEGY_EXECUTION_INTERVAL: int = 300  # seconds (5 minutes)

    # TradingView Webhook Configuration
    TRADINGVIEW_WEBHOOK_SECRET: str = Field(
        ...,
        description="Secret token for TradingView webhook authentication"
    )
    TRADINGVIEW_WEBHOOK_ENABLED: bool = True

    # Redis Configuration (for idempotency)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Active Strategies Configuration
    ACTIVE_STRATEGIES: list[dict] = [
        {
            "name": "pnl_pivot",
            "config": {
                "cooldown_seconds": 900  # 15 minutes
            }
        },
        {
            "name": "trend_change",
            "config": {
                "timeframes": ["1h", "4h", "1d", "1w"],
                "cooldown_per_tf": 3600  # 1 hour per timeframe
            }
        },
        {
            "name": "engulfing_candle",
            "config": {
                "timeframes": ["1h", "4h"],
                "cooldown_seconds": 3600
            }
        },
        {
            "name": "position_risk_alert",
            "config": {
                "risk_threshold": 20.0,  # Alert if < 20% from liquidation
                "check_interval": 300
            }
        }
    ]
```

---

## Benefits of This Architecture

### 1. **Separation of Concerns**
- **Detection logic** (Strategy) separate from **notification** (SignalRouter)
- **Configuration** separate from **implementation**
- **State management** separate from **execution**

### 2. **Composability**
- Conditions can be combined with `&`, `|`, `~` operators
- Strategies can be added/removed without changing core system
- Signals can be routed to multiple handlers

### 3. **Testability**
- Strategies can be tested in isolation with mock contexts
- Conditions can be unit tested independently
- SignalRouter can be tested with fake handlers

### 4. **Extensibility**
- New strategies: Just inherit BaseStrategy and register
- New signal types: Add to SignalType enum, subscribe handlers
- New conditions: Inherit Condition, implement evaluate()

### 5. **Maintainability**
- Clear abstractions with single responsibilities
- Decorator-based registration (no manual registry updates)
- Centralized configuration (settings.py)

### 6. **Performance**
- Strategies execute concurrently (asyncio.gather)
- Context built once, reused across all strategies
- Signal handlers run in parallel

### 7. **Observability**
- Metrics tracked per strategy (signals, failures, execution time)
- Comprehensive logging at key points
- State persistence for debugging

---

## Implementation Roadmap

### Phase 6A: Core Infrastructure (2-3 days)

**Tasks**:
1. Create base abstractions:
   - `BaseStrategy` (base.py)
   - `StrategyContext` (base.py)
   - `Signal`, `SignalType`, `SignalPriority` (signals.py)
   - `Condition` system (conditions.py)

2. Create orchestration components:
   - `StrategyRegistry` (registry.py)
   - `SignalRouter` (signals.py)
   - `StrategyExecutor` (executor.py)

3. Create `StrategyService` singleton (services/strategy_service.py)

4. Add state persistence (state.py)

**Deliverable**: Strategy system skeleton with no concrete strategies yet.

---

### Phase 6B: Built-in Strategies (2-3 days)

**Tasks**:
1. Implement core alert strategies:
   - `PnLPivotStrategy`
   - `LargePnLSwingStrategy`
   - `PositionRiskAlertStrategy`

2. Implement trend strategies:
   - `TrendChangeStrategy` (multi-timeframe)
   - `EngulfingCandleStrategy`

3. Implement price alert strategies:
   - `PriceAlertStrategy`
   - `PriceThresholdStrategy`

4. Create `PriceHistoryService` for candle data:
   - Multi-timeframe OHLC storage
   - Trend detection algorithms
   - Engulfing pattern detection

**Deliverable**: 6-8 working strategies with unit tests.

---

### Phase 6C: Integration (2 days)

**Tasks**:
1. Integrate with existing bot:
   - Inject bot instance into StrategyService
   - Connect SignalRouter to Telegram notifications
   - Add scheduled execution via JobQueue

2. Create use cases:
   - `ExecuteStrategiesUseCase`
   - `ListStrategiesUseCase`
   - `ManageStrategyUseCase` (enable/disable)

3. Add Telegram commands:
   - `/strategies` - List active strategies
   - `/strategy_toggle <name>` - Enable/disable
   - `/strategy_status` - Show metrics

4. Add configuration to settings.py

**Deliverable**: Fully integrated strategy system accessible via Telegram.

---

### Phase 6D: Testing & Refinement (1-2 days)

**Tasks**:
1. Comprehensive testing:
   - Unit tests for all strategies
   - Integration tests for executor
   - Signal routing tests

2. Performance optimization:
   - Profile strategy execution time
   - Optimize context building
   - Add caching where appropriate

3. Documentation:
   - API docs for creating custom strategies
   - User guide for Telegram commands
   - Configuration examples

**Deliverable**: Production-ready strategy system with documentation.

---

## Total Timeline: 7-10 days

---

## Future Enhancements

### Phase 7+: Advanced Features

1. **Custom Strategy Upload**
   - Allow users to upload Python files defining strategies
   - Sandbox execution for safety
   - Hot-reload strategies without restart

2. **Backtesting Framework**
   - Test strategies against historical data
   - Compare strategy performance
   - Optimize strategy parameters

3. **Strategy Marketplace**
   - Community-contributed strategies
   - Rating/review system
   - One-click installation

4. **Advanced Technical Indicators**
   - RSI, MACD, Bollinger Bands
   - Custom indicator composition
   - Machine learning-based signals

5. **Strategy Composition**
   - Combine multiple strategies into pipelines
   - Majority voting on signals
   - Confidence scoring

6. **Dashboard UI**
   - Visual strategy builder (drag-and-drop)
   - Real-time strategy execution monitoring
   - Performance charts and analytics

---

## Conclusion

This architecture provides a **clean, extensible, testable foundation** for trading alerts and automation. By abstracting strategies, signals, and handlers, we create a system that:

- ✅ Integrates seamlessly with existing codebase
- ✅ Supports unlimited strategy types
- ✅ Scales from simple alerts to complex execution
- ✅ Maintains separation of concerns
- ✅ Enables community contributions
- ✅ Provides clear paths for enhancement

The design follows industry best practices (Strategy Pattern, Observer Pattern, Event-Driven Architecture) while adapting to the specific needs of a crypto trading bot.

---

## User Interface & Experience

### Telegram Bot Account Health Display

**Design Specification**: See [preliminary-ux-plan.md](preliminary-ux-plan.md) for complete UX design.

**Overview**: The `/account` command displays comprehensive account health and risk indicators with a mobile-first, glanceable design.

**Key Features**:
- **Health Score (0-100)**: Primary at-a-glance metric with visual progress bar
- **Risk Alert Banner**: Conditional critical warnings when margin ratio ≥ 50% or critical positions exist
- **Cross Margin Ratio Display**: Primary risk metric with progress bar (liquidation at 100%)
- **Position Risk Distribution**: Count positions by risk level (SAFE/LOW/MODERATE/HIGH/CRITICAL)
- **Actionable Recommendations**: Specific guidance like "Add $500 margin or close BTC" not just "high risk"

**Visual Hierarchy** (top to bottom):
1. Critical alerts (if any) - 🚨 Immediate action required
2. Health overview - Big numbers, health score, total value
3. Margin breakdown - Cross margin ratio, leverage, usage
4. Position summary - Risk distribution, critical positions listed

**Interactive Elements**:
- 🔄 Refresh button - Re-fetch latest data
- 📊 View Details button - Individual position breakdowns
- ⚙️ Manage Positions button - Link to positions menu
- Auto-refresh every 30s

**Mobile-First Design Principles**:
- Short lines (< 35 chars) for vertical scrolling
- Text-based progress bars using filled/empty squares (■□)
- Color-coded risk emojis (✅💚💛🟠🔴)
- HTML formatting with monospace numbers for alignment
- Critical info visible without scrolling

**Implementation**: Leverages existing `RiskAnalysisUseCase`, `RiskCalculator`, and `AccountService` infrastructure.

---

**Next Steps**: Review this plan, provide feedback, and proceed to implementation.
