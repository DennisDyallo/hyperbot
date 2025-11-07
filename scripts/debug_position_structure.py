#!/usr/bin/env python3
"""Debug position structure to see actual field names."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services import hyperliquid_service, position_service

# Initialize
hyperliquid_service.initialize()

# Get positions
positions = position_service.list_positions()

if positions:
    print("\n=== First Position Structure ===")
    print(json.dumps(positions[0], indent=2))
else:
    print("No positions found")
