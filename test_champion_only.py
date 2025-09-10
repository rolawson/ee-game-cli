#!/usr/bin/env python3
"""Test Claude Champion personality"""

import os
from ai_spectator import AutoPlayEngine
from ai.claude_champion import ClaudeChampionAI
from ai import EasyAI

def test_champion():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude Champion (snarky personality)...")
    print("=" * 80)
    
    # Create engine with claude_champion difficulty
    engine = AutoPlayEngine(["Claude Champion", "Poor Soul"], ai_difficulty='claude_champion', delay=0.5)
    
    # Manually set up Champion AI (to ensure it's used)
    champion = ClaudeChampionAI()
    champion.engine = engine
    engine.ai_strategies[0] = champion
    
    # Easy AI for opponent
    easy = EasyAI()
    easy.engine = engine
    engine.ai_strategies[1] = easy
    
    # Make both AI
    for player in engine.gs.players:
        player.is_human = False
    
    # Give Champion slight advantage to encourage taunting
    engine.gs.players[0].health = 4  # Champion
    engine.gs.players[1].health = 2  # Poor Soul
    
    try:
        engine._setup_game()
        print("\n>>> Running one round with Claude Champion...")
        engine._run_round()
        
        print("\n" + "=" * 80)
        print("Test complete! Look for Champion's snarky messages above.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_champion()