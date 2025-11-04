"""
API routes module.
"""
from src.api.routes.account import router as account_router
from src.api.routes.positions import router as positions_router
from src.api.routes.orders import router as orders_router
from src.api.routes.market_data import router as market_data_router
from src.api.routes.rebalance import router as rebalance_router
from src.api.routes.scale_orders import router as scale_orders_router
from src.api.routes.leverage import router as leverage_router
from src.api.routes.web import router as web_router

__all__ = ["account_router", "positions_router", "orders_router", "market_data_router", "rebalance_router", "scale_orders_router", "leverage_router", "web_router"]
