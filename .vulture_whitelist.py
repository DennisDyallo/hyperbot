"""
Vulture whitelist for false positives.

Add patterns here that Vulture incorrectly identifies as unused.
This typically includes:
- FastAPI route functions (used via decorators)
- Pydantic model fields (used for serialization)
- pytest fixtures (used by the test framework)
"""


# Dummy class for Vulture whitelist pattern
class _:
    pass


# FastAPI routes are used via @router.get(), @router.post(), etc.
# Pattern: Functions decorated with @router.* in src/api/routes/
_.get_account
_.get_balance
_.get_position_summary
_.bulk_close_positions
_.get_risk_summary
_.dashboard
_.positions_page
_.rebalance_page
_.health

# Pydantic model fields are used for serialization/deserialization
# Pattern: Class attributes in Pydantic models
_.total_raw_usd
_.return_on_equity
_.leverage_value
_.hold
_.spot_total_usd
_.wallet_address
_.perps_account_value
_.spot_account_value
_.available_balance
_.margin_used
_.num_perp_positions
_.num_spot_balances
_.total_unrealized_pnl
_.is_testnet
_.total_position_value
_.created_at
_.updated_at
_.completed_at
_.total_filled_size
_.average_fill_price
_.target_allocation
_.total_coins

# Pydantic Config classes
_.Config

# Settings class properties that might be used in templates or API responses
_.API_HOST
_.API_PORT
_.API_KEY

# Validator methods (used by Pydantic)
_.validate
_.validate_price_range
_.validate_price_direction

# Utility methods that may be used in future features
_.is_production
_.is_development
_.convert_coin_to_usd
_.format_dual_amount

# Bot handlers and menus that may be work-in-progress
_.menu_scale_callback
_.build_with_back
_.build_rebalance_menu
_.build_scale_order_menu
_.build_num_orders_menu
_.admin_only
