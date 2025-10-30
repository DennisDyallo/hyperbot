"""
Response models for API endpoints.
Uses Pydantic for data validation and serialization.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MarginSummary(BaseModel):
    """Margin and account value summary."""

    account_value: float = Field(description="Total account value in USD")
    total_margin_used: float = Field(description="Total margin currently used")
    total_ntl_pos: float = Field(description="Total notional position value")
    total_raw_usd: float = Field(description="Total raw USD available")


class PositionDetails(BaseModel):
    """Detailed position information."""

    coin: str = Field(description="Trading pair (e.g., BTC, ETH)")
    size: float = Field(description="Position size (positive = long, negative = short)")
    entry_price: float = Field(description="Average entry price")
    position_value: float = Field(description="Current position value in USD")
    unrealized_pnl: float = Field(description="Unrealized profit/loss in USD")
    return_on_equity: float = Field(description="ROE as decimal (e.g., 0.05 = 5%)")
    leverage_type: str = Field(description="Leverage type: 'cross' or 'isolated'")
    leverage_value: int = Field(description="Leverage multiplier")
    liquidation_price: Optional[float] = Field(
        None, description="Estimated liquidation price"
    )


class Position(BaseModel):
    """Position response wrapper."""

    position: PositionDetails


class SpotBalance(BaseModel):
    """Spot balance for a specific asset."""

    coin: str = Field(description="Asset/coin symbol")
    total: float = Field(description="Total balance")
    hold: float = Field(description="Amount locked in open orders")


class AccountInfo(BaseModel):
    """Complete account information including positions, margin, and spot balances."""

    margin_summary: MarginSummary = Field(description="Account margin and value summary (perps)")
    positions: List[Position] = Field(
        default_factory=list, description="List of open perpetual positions"
    )
    withdrawable: float = Field(description="Amount available for withdrawal in USD (perps)")
    spot_balances: List[SpotBalance] = Field(
        default_factory=list, description="Spot/DEX balances"
    )
    spot_total_usd: float = Field(description="Total spot balance value in USD")


class AccountSummary(BaseModel):
    """Quick account summary for dashboard."""

    wallet_address: str = Field(description="Connected wallet address")
    total_account_value: float = Field(description="Total account value in USD (perps + spot)")
    perps_account_value: float = Field(description="Perpetuals account value in USD")
    spot_account_value: float = Field(description="Spot/DEX account value in USD")
    available_balance: float = Field(description="Available balance for trading (perps)")
    margin_used: float = Field(description="Total margin in use (perps)")
    num_perp_positions: int = Field(description="Number of open perpetual positions")
    num_spot_balances: int = Field(description="Number of spot balances")
    total_unrealized_pnl: float = Field(description="Total unrealized PnL (perps only)")
    is_testnet: bool = Field(description="Whether connected to testnet")
