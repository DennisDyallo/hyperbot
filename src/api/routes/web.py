"""
Web UI routes for Hyperbot dashboard.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import settings

router = APIRouter(tags=["Web UI"])

# Templates configuration
templates = Jinja2Templates(directory="src/api/templates")


@router.get("/", response_class=HTMLResponse, summary="Dashboard page")
async def dashboard(request: Request):
    """
    Render the main dashboard page.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "environment": settings.ENVIRONMENT,
        },
    )


@router.get("/positions", response_class=HTMLResponse, summary="Positions page")
async def positions_page(request: Request):
    """
    Render the positions management page.
    """
    return templates.TemplateResponse(
        "positions.html",
        {
            "request": request,
            "environment": settings.ENVIRONMENT,
        },
    )


@router.get("/rebalance", response_class=HTMLResponse, summary="Rebalance page")
async def rebalance_page(request: Request):
    """
    Render the portfolio rebalancing page.
    """
    return templates.TemplateResponse(
        "rebalance.html",
        {
            "request": request,
            "environment": settings.ENVIRONMENT,
        },
    )
