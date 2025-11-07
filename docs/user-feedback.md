1. Getting this when running against mainnet:
2025-11-07 00:27:46 | WARNING  | src.services.account_service:get_account_info:137 | Could not get price for spot token JEFF (0.99656 tokens), excluding from total: Coin 'JEFF' not found. Available coins: 0G, 2Z, @1, @10, @100, @101, @102, @103, @104, @105...
2025-11-07 00:27:46 | WARNING  | src.services.account_service:get_account_info:137 | Could not get price for spot token POINTS (1.79028 tokens), excluding from total: Coin 'POINTS' not found. Available coins: 0G, 2Z, @1, @10, @100, @101, @102, @103, @104, @105...
2025-11-07 00:27:47 | WARNING  | src.services.account_service:get_account_info:137 | Could not get price for spot token OMNIX (385563.261699 tokens), excluding from total: Coin 'OMNIX' not found. Available coins: 0G, 2Z, @1, @10, @100, @101, @102, @103, @104, @105...
2025-11-07 00:27:47 | WARNING  | src.services.account_service:get_account_info:137 | Could not get price for spot token UBTC (0.0022509462 tokens), excluding from total: Coin 'UBTC' not found. Available coins: 0G, 2Z, @1, @10, @100, @101, @102, @103, @104, @105...
2025-11-07 00:27:48 | WARNING  | src.services.account_service:get_account_info:137 | Could not get price for spot token LICKO (0.8544621 tokens), excluding from total: Coin 'LICKO' not found. Available coins: 0G, 2Z, @1, @10, @100, @101, @102, @103, @104, @105...


2. When trying to buy $10 of ETH I got this error: > File "/home/dyallo/Code/hyperbot/src/bot/handlers/wizard_market_order.py", line 271, in market_execute
    response = await place_order_use_case.execute(request)
                     │                    │       └ PlaceOrderRequest(coin='ETH', is_buy=True, usd_amount=None, coin_size=0.003, is_market=True, limit_price=None, slippage=0.05,...
                     │                    └ <function PlaceOrderUseCase.execute at 0x7ff8a699e5c0>
                     └ <src.use_cases.trading.place_order.PlaceOrderUseCase object at 0x7ff8a69c5160>

  File "/home/dyallo/Code/hyperbot/src/use_cases/trading/place_order.py", line 162, in execute
    raise RuntimeError(f"Failed to place order: {str(e)}")

RuntimeError: Failed to place order: OrderService.place_market_order() got an unexpected keyword argument 'reduce_only'

3. The positions menu item should include a keyboard button to the close positions wizard

