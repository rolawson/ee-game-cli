#!/usr/bin/env python3
"""Test Claude AI competitive messaging"""

import os
from ai_spectator import AutoPlayEngine
from ai.claude_ai import ClaudeAI
from ai import EasyAI

def test_competitive_messaging():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude AI competitive messaging...")
    print("=" * 60)
    
    # Create a game with Claude vs a "human" player
    engine = AutoPlayEngine(["Claude", "Player"], ai_difficulty='claude', delay=0.1)
    
    # Set up Claude AI
    claude = ClaudeAI()
    claude.engine = engine
    engine.ai_strategies[0] = claude
    
    # Set up Easy AI for the "human" player
    easy = EasyAI()
    easy.engine = engine
    engine.ai_strategies[1] = easy
    
    # Make both AI (simulating human play)
    for player in engine.gs.players:
        player.is_human = False
    
    # Give different health situations to test different analysis types
    # Scenario 1: Claude is winning
    engine.gs.players[0].health = 4  # Claude
    engine.gs.players[1].health = 2  # "Player"
    
    try:
        engine._setup_game()
        print("\n>>> Running Round 1 (Claude has advantage)...")
        engine._run_round()
        
        # Scenario 2: Player is winning
        engine.gs.players[0].health = 1  # Claude
        engine.gs.players[1].health = 5  # "Player"
        
        print("\n>>> Running Round 2 (Player has advantage)...")
        engine._run_round()
        
        print("\n" + "=" * 60)
        print("Test complete! Check Claude's competitive analysis above.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_competitive_messaging()