"""
Progress bar utilities for Telegram bot.

Provides text-based progress bars and risk level emoji mapping.
"""


def build_progress_bar(
    percentage: float, length: int = 10, filled_char: str = "■", empty_char: str = "□"
) -> str:
    """
    Build visual progress bar using filled/empty squares.

    Args:
        percentage: Value from 0-100
        length: Number of characters (default 10)
        filled_char: Character for filled portion (default ■)
        empty_char: Character for empty portion (default □)

    Returns:
        Progress bar string like "■■■■■□□□□□"

    Examples:
        >>> build_progress_bar(75.5)
        '■■■■■■■■□□'
        >>> build_progress_bar(100)
        '■■■■■■■■■■'
        >>> build_progress_bar(0)
        '□□□□□□□□□□'
    """
    filled_count = int((percentage / 100) * length)
    empty_count = length - filled_count
    return filled_char * filled_count + empty_char * empty_count


def get_risk_emoji(risk_level: str) -> str:
    """
    Get emoji for risk level.

    Args:
        risk_level: One of SAFE, LOW, MODERATE, HIGH, CRITICAL

    Returns:
        Emoji string matching risk level

    Examples:
        >>> get_risk_emoji("SAFE")
        '✅'
        >>> get_risk_emoji("CRITICAL")
        '🔴'
    """
    return {"SAFE": "✅", "LOW": "💚", "MODERATE": "💛", "HIGH": "🟠", "CRITICAL": "🔴"}.get(
        risk_level, "❓"
    )
