"""
Fluent builders for mock data structures.

Provides builder classes for creating realistic test data that matches
Hyperliquid API response structures. Uses fluent interface for readability.

Example:
    >>> position = PositionBuilder()    \\
    ...     .with_coin("BTC")           \\
    ...     .with_size(0.5)             \\
    ...     .long()                     \\
    ...     .with_pnl(100.0)            \\
    ...     .build()
    >>> position["position"]["coin"]
    'BTC'
"""

from typing import Any


class PositionBuilder:
    """
    Fluent builder for position data structures.

    Matches the nested structure returned by Hyperliquid API:
    {
        "position": {
            "coin": str,
            "size": str,  # Note: API returns string
            "entry_price": str,
            "position_value": str,
            "unrealized_pnl": str,
            "return_on_equity": float,
            "leverage_value": int,
            "leverage": {"value": int, "type": str},
            "liquidation_price": str
        }
    }

    Reference:
        CLAUDE.md - Testing Best Practices > Mock Data Structure Must Match API
    """

    def __init__(self):
        self._coin = "BTC"
        self._size = 0.00432
        self._entry_price = 104088.0
        self._position_value = 449.66
        self._unrealized_pnl = 5.25
        self._return_on_equity = 0.0117
        self._leverage_value = 3
        self._leverage_type = "cross"
        self._liquidation_price = None

    def with_coin(self, coin: str) -> "PositionBuilder":
        """Set the coin symbol."""
        self._coin = coin
        return self

    def with_size(self, size: float) -> "PositionBuilder":
        """Set position size (positive for long, negative for short)."""
        self._size = size
        return self

    def long(self) -> "PositionBuilder":
        """Make this a long position (size > 0)."""
        if self._size < 0:
            self._size = abs(self._size)
        return self

    def short(self) -> "PositionBuilder":
        """Make this a short position (size < 0)."""
        if self._size > 0:
            self._size = -self._size
        return self

    def with_entry_price(self, price: float) -> "PositionBuilder":
        """Set entry price."""
        self._entry_price = price
        return self

    def with_position_value(self, value: float) -> "PositionBuilder":
        """Set position value in USD."""
        self._position_value = value
        return self

    def with_pnl(self, pnl: float) -> "PositionBuilder":
        """Set unrealized PnL."""
        self._unrealized_pnl = pnl
        return self

    def with_leverage(self, leverage: int, leverage_type: str = "cross") -> "PositionBuilder":
        """Set leverage value and type."""
        self._leverage_value = leverage
        self._leverage_type = leverage_type
        return self

    def with_liquidation_price(self, price: float) -> "PositionBuilder":
        """Set liquidation price."""
        self._liquidation_price = price
        return self

    def build(self) -> dict[str, Any]:
        """
        Build and return the position data structure.

        Returns:
            Dict matching account_service.get_account_info() output structure.
            Note: account_service converts API strings to floats/ints.
            Includes both flat leverage_value/leverage_type AND nested leverage object
            for compatibility with different parts of the codebase.
        """
        position = {
            "position": {
                "coin": self._coin,
                "size": float(self._size),  # Float (account_service converts)
                "entry_price": float(self._entry_price),  # Float
                "position_value": float(self._position_value),  # Float
                "unrealized_pnl": float(self._unrealized_pnl),  # Float
                "return_on_equity": self._return_on_equity,  # Float
                "leverage_value": self._leverage_value,  # Int (flat key for compatibility)
                "leverage_type": self._leverage_type,  # String (flat key)
                "leverage": {  # Nested object for get_all_leverage_settings()
                    "value": self._leverage_value,
                    "type": self._leverage_type,
                },
                "liquidation_price": float(self._liquidation_price)
                if self._liquidation_price is not None
                else None,
            }
        }

        return position


class AccountSummaryBuilder:
    """
    Fluent builder for account summary data.

    Used by AccountService.get_account_summary().
    """

    def __init__(self):
        self._wallet_address = "0xF67332761483018d2e604A094d7f00cA8230e881"
        self._total_account_value = 10942.58
        self._perps_account_value = 2850.25
        self._spot_account_value = 8092.33
        self._available_balance = 8500.00
        self._margin_used = 2442.58
        self._num_perp_positions = 3
        self._num_spot_balances = 5
        self._total_unrealized_pnl = 125.50
        self._cross_margin_ratio_pct = 22.35
        self._cross_maintenance_margin = 500.0
        self._cross_account_leverage = 2.5
        self._is_testnet = True

    def with_total_value(self, value: float) -> "AccountSummaryBuilder":
        """Set total account value."""
        self._total_account_value = value
        return self

    def with_available_balance(self, balance: float) -> "AccountSummaryBuilder":
        """Set available balance."""
        self._available_balance = balance
        return self

    def with_pnl(self, pnl: float) -> "AccountSummaryBuilder":
        """Set total unrealized PnL."""
        self._total_unrealized_pnl = pnl
        return self

    def with_positions(self, num_positions: int) -> "AccountSummaryBuilder":
        """Set number of perp positions."""
        self._num_perp_positions = num_positions
        return self

    def mainnet(self) -> "AccountSummaryBuilder":
        """Mark as mainnet account."""
        self._is_testnet = False
        return self

    def testnet(self) -> "AccountSummaryBuilder":
        """Mark as testnet account."""
        self._is_testnet = True
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the account summary."""
        return {
            "wallet_address": self._wallet_address,
            "total_account_value": self._total_account_value,
            "perps_account_value": self._perps_account_value,
            "spot_account_value": self._spot_account_value,
            "total_raw_usd": self._available_balance,
            "margin_used": self._margin_used,
            "num_perp_positions": self._num_perp_positions,
            "num_spot_balances": self._num_spot_balances,
            "total_unrealized_pnl": self._total_unrealized_pnl,
            "cross_margin_ratio_pct": self._cross_margin_ratio_pct,
            "cross_maintenance_margin": self._cross_maintenance_margin,
            "cross_account_leverage": self._cross_account_leverage,
            "is_testnet": self._is_testnet,
        }


class OrderResponseBuilder:
    """
    Fluent builder for order API response data.

    Matches Hyperliquid Exchange API responses.
    """

    def __init__(self):
        self._status = "ok"
        self._response_type = "order"
        self._filled_size = "0.00432"
        self._avg_price = "104088.0"
        self._order_id = None

    def success(self) -> "OrderResponseBuilder":
        """Mark response as successful."""
        self._status = "ok"
        return self

    def failed(self) -> "OrderResponseBuilder":
        """Mark response as failed."""
        self._status = "error"
        return self

    def with_filled_size(self, size: float) -> "OrderResponseBuilder":
        """Set filled size."""
        self._filled_size = str(size)
        return self

    def with_avg_price(self, price: float) -> "OrderResponseBuilder":
        """Set average execution price."""
        self._avg_price = str(price)
        return self

    def with_order_id(self, order_id: int) -> "OrderResponseBuilder":
        """Set order ID (for limit orders)."""
        self._order_id = order_id
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the order response."""
        response = {
            "status": self._status,
            "response": {
                "type": self._response_type,
                "data": {
                    "statuses": [
                        {"filled": {"totalSz": self._filled_size, "avgPx": self._avg_price}}
                    ]
                },
            },
        }

        if self._order_id is not None:
            response["response"]["data"]["statuses"][0]["resting"] = {"oid": self._order_id}

        return response


class MarketDataBuilder:
    """
    Fluent builder for market data responses.

    Provides asset metadata and price data.
    """

    def __init__(self):
        self._prices = {
            "BTC": 104088.0,
            "ETH": 3850.50,
            "SOL": 161.64,
            "ARB": 0.85,
            "AVAX": 35.20,
            "MATIC": 0.92,
        }
        self._metadata = {
            "BTC": {"name": "BTC", "szDecimals": 5, "maxLeverage": 50},
            "ETH": {"name": "ETH", "szDecimals": 4, "maxLeverage": 50},
            "SOL": {"name": "SOL", "szDecimals": 1, "maxLeverage": 20},
        }

    def with_price(self, coin: str, price: float) -> "MarketDataBuilder":
        """Add or update a coin price."""
        self._prices[coin] = price
        return self

    def with_metadata(
        self, coin: str, sz_decimals: int, max_leverage: int = 50
    ) -> "MarketDataBuilder":
        """Add or update asset metadata."""
        self._metadata[coin] = {
            "name": coin,
            "szDecimals": sz_decimals,
            "maxLeverage": max_leverage,
            "onlyIsolated": False,
        }
        return self

    def build_prices(self) -> dict[str, float]:
        """Build and return price dictionary."""
        return self._prices.copy()

    def build_metadata(self, coin: str | None = None) -> dict[str, Any]:
        """
        Build and return metadata.

        Args:
            coin: If provided, return metadata for single coin. Otherwise return all.

        Returns:
            Metadata dict or single coin metadata
        """
        if coin:
            return self._metadata.get(coin)
        return self._metadata.copy()


# Convenience functions for quick mock data creation
def make_position(coin: str = "BTC", size: float = 0.5, pnl: float = 0.0) -> dict[str, Any]:
    """Quick function to create a position with minimal parameters."""
    return PositionBuilder().with_coin(coin).with_size(size).with_pnl(pnl).build()


def make_long_position(coin: str = "BTC", size: float = 0.5) -> dict[str, Any]:
    """Quick function to create a long position."""
    return PositionBuilder().with_coin(coin).with_size(abs(size)).build()


def make_short_position(coin: str = "BTC", size: float = 0.5) -> dict[str, Any]:
    """Quick function to create a short position."""
    return PositionBuilder().with_coin(coin).with_size(-abs(size)).build()


def make_account_summary(total_value: float = 10000.0, pnl: float = 0.0) -> dict[str, Any]:
    """Quick function to create an account summary."""
    return AccountSummaryBuilder().with_total_value(total_value).with_pnl(pnl).build()
