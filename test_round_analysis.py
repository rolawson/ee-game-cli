#!/usr/bin/env python3
"""Test round analysis specifically"""

import sys
from elephants_prototype import GameEngine, Colors, PlayedCard, Card

def test_round_analysis():
    print("Testing round analysis for Claude Champion AI...")
    
    # Create engine with Claude Champion
    player_names = ["Human Player", "AI Opponent"]
    engine = GameEngine(player_names, ai_difficulty='claude_champion')
    
    # Create a fake game state for testing
    gs = engine.gs
    gs.round_num = 1
    
    # Add some fake action log entries
    gs.action_log = [
        "--- Round 1 Begins ---",
        "--- Clash 1: CAST ---",
        "AI Opponent plays Electrocute",
        "Human Player plays Shield",
        "AI Opponent dealt 3 damage to Human Player",
        "Human Player's health: 2/5"
    ]
    
    # Manually trigger the round analysis
    print("\n[95m=== Simulating End of Round ===[0m")
    engine._run_end_of_round()
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_round_analysis()