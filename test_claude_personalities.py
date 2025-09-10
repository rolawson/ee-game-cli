#!/usr/bin/env python3
"""Test both Claude personalities - Savant and Champion"""

import os
from ai_spectator import AutoPlayEngine
from ai.claude_savant import ClaudeSavantAI
from ai.claude_champion import ClaudeChampionAI
from ai import EasyAI

def test_claude_personalities():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude Savant vs Claude Champion personalities...")
    print("=" * 80)
    print("Savant: Analytical, competitive but respectful")
    print("Champion: Snarky, taunting, knows all spells by name")
    print("=" * 80)
    
    # Test 1: Claude Savant
    print("\n>>> TEST 1: Claude Savant (analytical)")
    engine1 = AutoPlayEngine(["Claude Savant", "TestBot"], ai_difficulty='claude_savant', delay=0.1)
    
    # Set up Savant
    savant = ClaudeSavantAI()
    savant.engine = engine1
    engine1.ai_strategies[0] = savant
    
    # Easy AI for opponent
    easy1 = EasyAI()
    easy1.engine = engine1
    engine1.ai_strategies[1] = easy1
    
    # Make both AI
    for player in engine1.gs.players:
        player.is_human = False
    
    # Set up game state
    engine1.gs.players[0].health = 3  # Savant
    engine1.gs.players[1].health = 2  # TestBot
    
    try:
        engine1._setup_game()
        print("\nRunning one round with Claude Savant...")
        engine1._run_round()
    except Exception as e:
        print(f"Error in Savant test: {e}")
    
    print("\n" + "=" * 80)
    
    # Test 2: Claude Champion
    print("\n>>> TEST 2: Claude Champion (snarky)")
    engine2 = AutoPlayEngine(["Claude Champion", "Victim"], ai_difficulty='claude_champion', delay=0.1)
    
    # Set up Champion
    champion = ClaudeChampionAI()
    champion.engine = engine2
    engine2.ai_strategies[0] = champion
    
    # Easy AI for opponent
    easy2 = EasyAI()
    easy2.engine = engine2
    engine2.ai_strategies[1] = easy2
    
    # Make both AI
    for player in engine2.gs.players:
        player.is_human = False
    
    # Set up game state
    engine2.gs.players[0].health = 4  # Champion
    engine2.gs.players[1].health = 2  # Victim
    
    try:
        engine2._setup_game()
        print("\nRunning one round with Claude Champion...")
        engine2._run_round()
    except Exception as e:
        print(f"Error in Champion test: {e}")
    
    print("\n" + "=" * 80)
    print("Personality test complete! Check the analysis messages above.")

if __name__ == "__main__":
    test_claude_personalities()