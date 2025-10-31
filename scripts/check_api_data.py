#!/usr/bin/env python3
"""
Script to check all available data from Hyperliquid API.
This helps us match the official GUI metrics.
"""
import json
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Initialize
info = Info(constants.TESTNET_API_URL, skip_ws=True)

# Get user state
user_address = "0xF67332761483018d2e604A094d7f00cA8230e881"
user_state = info.user_state(user_address)

print("=" * 80)
print("FULL USER_STATE RESPONSE")
print("=" * 80)
print(json.dumps(user_state, indent=2))

print("\n" + "=" * 80)
print("AVAILABLE TOP-LEVEL KEYS")
print("=" * 80)
for key in user_state.keys():
    print(f"  - {key}")

if "marginSummary" in user_state:
    print("\n" + "=" * 80)
    print("MARGIN SUMMARY")
    print("=" * 80)
    print(json.dumps(user_state["marginSummary"], indent=2))

if "crossMarginSummary" in user_state:
    print("\n" + "=" * 80)
    print("CROSS MARGIN SUMMARY")
    print("=" * 80)
    print(json.dumps(user_state["crossMarginSummary"], indent=2))

if "assetPositions" in user_state and len(user_state["assetPositions"]) > 0:
    print("\n" + "=" * 80)
    print(f"FIRST POSITION (Total: {len(user_state['assetPositions'])})")
    print("=" * 80)
    print(json.dumps(user_state["assetPositions"][0], indent=2))
