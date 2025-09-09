#!/usr/bin/env python3
"""Quick test of Claude AI with forced round end"""

import os
from ai_spectator import AutoPlayEngine

# Set up a quick test game
def test_claude_game():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Starting quick Claude test...")
    print("Watch for Claude's analysis after 'End of Round 1'")
    print("=" * 60)
    
    # Create a game with Claude vs Easy AI for quick testing
    engine = AutoPlayEngine(["Claude", "TestBot"], ai_difficulty='claude', delay=0.5)
    
    # Override the second player to be Easy AI for faster games
    from ai import EasyAI
    easy = EasyAI()
    easy.engine = engine
    engine.ai_strategies[1] = easy
    
    # Set both as AI
    for player in engine.gs.players:
        player.is_human = False
    
    # Modify first player's health to end round quickly
    engine.gs.players[1].health = 1  # TestBot will lose trunk quickly
    
    try:
        # Run just one round
        engine._setup_game()
        engine._run_round()
        print("\n" + "=" * 60)
        print("Test complete! Check above for Claude's analysis.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_claude_game()