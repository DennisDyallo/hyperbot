"""
Account service for managing account information and balances.
"""

from typing import Any

from src.config import logger, settings
from src.services.hyperliquid_service import hyperliquid_service


# Import market_data_service for pricing spot tokens
def get_market_data_service():
    """Lazy import to avoid circular dependency."""
    from src.services.market_data_service import market_data_service

    return market_data_service


class AccountService:
    """Service for account-related operations."""

    def __init__(self):
        """Initialize account service."""
        self.hyperliquid = hyperliquid_service

    def get_account_info(self) -> dict[str, Any]:
        """
        Get complete account information including positions, margin, and spot balances.

        Returns:
            Dict with account info, positions, margin summary, and spot balances

        Raises:
            RuntimeError: If wallet address not configured
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            info_client = self.hyperliquid.get_info_client()

            # Get perps (perpetuals) data
            user_state = info_client.user_state(settings.HYPERLIQUID_WALLET_ADDRESS)

            # Get spot data
            spot_state = info_client.spot_user_state(settings.HYPERLIQUID_WALLET_ADDRESS)

            # Extract margin summary (perps)
            margin_data = user_state.get("marginSummary", {})
            user_state.get("crossMarginSummary", {})
            cross_maintenance_margin = float(user_state.get("crossMaintenanceMarginUsed", 0))

            account_value = float(margin_data.get("accountValue", 0))
            total_ntl_pos = float(margin_data.get("totalNtlPos", 0))

            # Calculate Hyperliquid GUI metrics
            # Cross Margin Ratio = Maintenance Margin / Account Value * 100
            # When this reaches 100%, liquidation occurs!
            cross_margin_ratio_pct = (
                (cross_maintenance_margin / account_value * 100) if account_value > 0 else 0
            )

            # Cross Account Leverage = Total Position Value / Account Value
            cross_account_leverage = (total_ntl_pos / account_value) if account_value > 0 else 0

            margin_summary = {
                "account_value": account_value,
                "total_margin_used": float(margin_data.get("totalMarginUsed", 0)),
                "total_ntl_pos": total_ntl_pos,
                "total_raw_usd": float(margin_data.get("totalRawUsd", 0)),
                # Cross margin metrics (matches Hyperliquid GUI)
                "cross_maintenance_margin": cross_maintenance_margin,
                "cross_margin_ratio_pct": cross_margin_ratio_pct,
                "cross_account_leverage": cross_account_leverage,
            }

            # Extract positions
            positions = []
            for asset_pos in user_state.get("assetPositions", []):
                pos = asset_pos.get("position", {})
                leverage = pos.get("leverage", {})

                position_details = {
                    "coin": pos.get("coin", ""),
                    "size": float(pos.get("szi", 0)),
                    "entry_price": float(pos.get("entryPx", 0)),
                    "position_value": float(pos.get("positionValue", 0)),
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),
                    "return_on_equity": float(pos.get("returnOnEquity", 0)),
                    "leverage_type": leverage.get("type", "cross"),
                    "leverage_value": int(leverage.get("value", 1)),
                    "liquidation_price": float(pos.get("liquidationPx", 0))
                    if pos.get("liquidationPx")
                    else None,
                }
                positions.append({"position": position_details})

            # Withdrawable amount (perps)
            withdrawable = float(user_state.get("withdrawable", 0))

            # Extract spot balances
            spot_balances = []
            for balance in spot_state.get("balances", []):
                spot_balances.append(
                    {
                        "coin": balance.get("coin", ""),
                        "total": float(balance.get("total", 0)),
                        "hold": float(balance.get("hold", 0)),  # Amount locked in orders
                    }
                )

            # Calculate total spot value (USD equivalent)
            # Need to price each token at market value
            total_spot_usd = 0
            market_data = get_market_data_service()

            for balance in spot_balances:
                coin = balance["coin"]
                amount = balance["total"]

                if amount == 0:
                    continue

                # USDC and other stablecoins are already in USD
                if coin in ["USDC", "USDT", "DAI", "USDEEE", "USDZZ", "USDH"]:
                    total_spot_usd += amount
                else:
                    # Get market price for other tokens
                    try:
                        price = market_data.get_price(coin)
                        token_value = amount * price
                        total_spot_usd += token_value
                        logger.debug(f"Spot token {coin}: {amount} × ${price} = ${token_value:.2f}")
                    except Exception as e:
                        # If price not available, skip (but warn)
                        logger.warning(
                            f"Could not get price for spot token {coin} ({amount} tokens), excluding from total: {e}"
                        )
                        continue

            result = {
                "margin_summary": margin_summary,
                "positions": positions,
                "withdrawable": withdrawable,
                "spot_balances": spot_balances,
                "spot_total_usd": total_spot_usd,
            }

            logger.debug(
                f"Account info fetched: {len(positions)} perp positions, "
                f"{len(spot_balances)} spot balances, "
                f"perp_value=${margin_summary['account_value']:.2f}, "
                f"spot_value=${total_spot_usd:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_account_summary(self) -> dict[str, Any]:
        """
        Get quick account summary for dashboard.

        Returns:
            Dict with summary stats

        Raises:
            RuntimeError: If wallet address not configured
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            account_info = self.get_account_info()
            margin = account_info["margin_summary"]
            positions = account_info["positions"]
            spot_balances = account_info.get("spot_balances", [])
            spot_total = account_info.get("spot_total_usd", 0)

            # Calculate total unrealized PnL (perps only)
            total_pnl = sum(p["position"]["unrealized_pnl"] for p in positions)

            # Combined account value (perps + spot)
            total_account_value = margin["account_value"] + spot_total

            summary = {
                "wallet_address": settings.HYPERLIQUID_WALLET_ADDRESS,
                "total_account_value": total_account_value,  # Combined perps + spot
                "perps_account_value": margin["account_value"],
                "spot_account_value": spot_total,
                "available_balance": margin["total_raw_usd"],  # Perps available
                "margin_used": margin["total_margin_used"],
                "num_perp_positions": len(positions),
                "num_spot_balances": len(spot_balances),
                "total_unrealized_pnl": total_pnl,  # Perps PnL only
                # Cross margin metrics (Hyperliquid GUI format)
                "cross_maintenance_margin": margin["cross_maintenance_margin"],
                "cross_margin_ratio_pct": margin["cross_margin_ratio_pct"],
                "cross_account_leverage": margin["cross_account_leverage"],
                "is_testnet": settings.HYPERLIQUID_TESTNET,
            }

            logger.debug(
                f"Account summary: {summary['num_perp_positions']} perp positions, "
                f"{summary['num_spot_balances']} spot balances, "
                f"total=${total_account_value:.2f}, PnL=${total_pnl:.2f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            raise

    def get_balance_details(self) -> dict[str, Any]:
        """
        Get detailed balance breakdown.

        Returns:
            Dict with balance details including available, used, and locked amounts

        Raises:
            RuntimeError: If wallet address not configured
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            account_info = self.get_account_info()
            margin = account_info["margin_summary"]

            balance = {
                "total_value": margin["account_value"],
                "available": margin["total_raw_usd"],
                "in_positions": margin["total_ntl_pos"],
                "margin_used": margin["total_margin_used"],
                "withdrawable": account_info["withdrawable"],
            }

            logger.debug(
                f"Balance details: total=${balance['total_value']:.2f}, "
                f"available=${balance['available']:.2f}"
            )

            return balance

        except Exception as e:
            logger.error(f"Failed to get balance details: {e}")
            raise


# Global service instance
account_service = AccountService()
