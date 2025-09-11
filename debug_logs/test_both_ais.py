#!/usr/bin/env python3
"""Quick test to see if both AIs are logging properly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.claude_savant import ClaudeSavantAI
from ai.claude_champion import ClaudeChampionAI

# Test if both AIs can be created
try:
    savant = ClaudeSavantAI()
    print("✓ Savant AI created successfully")
except Exception as e:
    print(f"✗ Savant AI failed: {e}")

try:
    champion = ClaudeChampionAI()
    print("✓ Champion AI created successfully")
except Exception as e:
    print(f"✗ Champion AI failed: {e}")

# Check if they have the right methods
if hasattr(savant, 'choose_card_to_play'):
    print("✓ Savant has choose_card_to_play method")
else:
    print("✗ Savant missing choose_card_to_play method")

if hasattr(champion, 'choose_card_to_play'):
    print("✓ Champion has choose_card_to_play method")
else:
    print("✗ Champion missing choose_card_to_play method")

# Check player_name attribute
print(f"\nSavant player_name: {getattr(savant, 'player_name', 'Not set')}")
print(f"Champion player_name: {getattr(champion, 'player_name', 'Not set')}")