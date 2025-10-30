"""
Account API routes.
Handles account information, balances, and positions.
"""
from fastapi import APIRouter, HTTPException
from src.services import account_service
from src.api.models import AccountInfo, AccountSummary
from src.config import logger

router = APIRouter(prefix="/api/account", tags=["Account"])


@router.get("/", response_model=AccountInfo)
async def get_account():
    """
    Get complete account information including positions and margin.

    Returns:
        AccountInfo with margin summary, positions, and withdrawable balance
    """
    try:
        account_data = account_service.get_account_info()
        return account_data
    except RuntimeError as e:
        logger.error(f"Account info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get account info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch account information")


@router.get("/summary", response_model=AccountSummary)
async def get_account_summary():
    """
    Get quick account summary for dashboard.

    Returns:
        AccountSummary with key metrics (balance, positions count, PnL, etc.)
    """
    try:
        summary_data = account_service.get_account_summary()
        return summary_data
    except RuntimeError as e:
        logger.error(f"Account summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch account summary")


@router.get("/balance")
async def get_balance():
    """
    Get detailed balance breakdown.

    Returns:
        Balance details including total value, available, in positions, and withdrawable
    """
    try:
        balance_data = account_service.get_balance_details()
        return balance_data
    except RuntimeError as e:
        logger.error(f"Balance details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get balance details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch balance details")
