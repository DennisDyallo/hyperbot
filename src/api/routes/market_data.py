"""
Market data API routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.services import market_data_service
from src.config import logger

router = APIRouter(prefix="/api/market", tags=["market_data"])


@router.get("/prices", summary="Get all market prices")
async def get_all_prices() -> Dict[str, float]:
    """
    Get current mid prices for all trading pairs.

    Returns a dictionary mapping coin symbols to their current prices.

    **Example Response:**
    ```json
    {
        "BTC": 109000.0,
        "ETH": 4200.5,
        "SOL": 125.3
    }
    ```
    """
    try:
        prices = market_data_service.get_all_prices()
        return prices

    except Exception as e:
        logger.error(f"Error fetching all prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{coin}", summary="Get price for specific coin")
async def get_price(coin: str) -> Dict[str, Any]:
    """
    Get current mid price for a specific coin.

    **Path Parameters:**
    - `coin`: Trading pair symbol (e.g., "BTC", "ETH")

    **Example Response:**
    ```json
    {
        "coin": "BTC",
        "price": 109000.0
    }
    ```

    **Error Responses:**
    - `400`: Coin not found
    - `500`: Internal server error
    """
    try:
        price = market_data_service.get_price(coin.upper())
        return {"coin": coin.upper(), "price": price}

    except ValueError as e:
        logger.warning(f"Invalid coin: {coin}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error fetching price for {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", summary="Get market metadata")
async def get_market_info() -> Dict[str, Any]:
    """
    Get exchange metadata including available pairs, tick sizes, and limits.

    Returns comprehensive market information including:
    - Available trading pairs (universe)
    - Tick sizes for each pair
    - Minimum order sizes
    - Leverage limits

    **Example Response:**
    ```json
    {
        "universe": [
            {
                "name": "BTC",
                "szDecimals": 4,
                "maxLeverage": 50,
                ...
            }
        ]
    }
    ```
    """
    try:
        meta = market_data_service.get_market_info()
        return meta

    except Exception as e:
        logger.error(f"Error fetching market info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orderbook/{coin}", summary="Get order book for coin")
async def get_order_book(coin: str) -> Dict[str, Any]:
    """
    Get Level 2 order book snapshot for a specific coin.

    **Path Parameters:**
    - `coin`: Trading pair symbol (e.g., "BTC", "ETH")

    Returns order book with bids and asks.

    **Example Response:**
    ```json
    {
        "coin": "BTC",
        "time": 1699000000,
        "levels": [
            [
                {"px": "109000.0", "sz": "0.5", "n": 1},
                {"px": "108995.0", "sz": "1.2", "n": 2}
            ],
            [
                {"px": "109005.0", "sz": "0.8", "n": 1},
                {"px": "109010.0", "sz": "0.3", "n": 1}
            ]
        ]
    }
    ```

    **Error Responses:**
    - `400`: Invalid coin
    - `500`: Internal server error
    """
    try:
        book = market_data_service.get_order_book(coin.upper())
        return {"coin": coin.upper(), **book}

    except ValueError as e:
        logger.warning(f"Invalid coin: {coin}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error fetching order book for {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/asset/{coin}", summary="Get asset metadata")
async def get_asset_metadata(coin: str) -> Dict[str, Any]:
    """
    Get metadata for a specific asset (tick size, min size, etc.).

    **Path Parameters:**
    - `coin`: Trading pair symbol (e.g., "BTC", "ETH")

    **Example Response:**
    ```json
    {
        "name": "BTC",
        "szDecimals": 4,
        "maxLeverage": 50,
        "onlyIsolated": false
    }
    ```

    **Error Responses:**
    - `404`: Asset not found
    - `500`: Internal server error
    """
    try:
        meta = market_data_service.get_asset_metadata(coin.upper())

        if meta is None:
            raise HTTPException(
                status_code=404, detail=f"Asset metadata not found for {coin}"
            )

        return meta

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error fetching asset metadata for {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
