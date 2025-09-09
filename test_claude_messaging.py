#!/usr/bin/env python3
"""Test Claude AI messaging functionality"""

import os
import sys
from ai_spectator import AutoPlayEngine

def test_claude_messaging():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude AI messaging...")
    print("=" * 60)
    
    # Create a game with Claude vs Easy AI
    engine = AutoPlayEngine(["Claude", "TestBot"], ai_difficulty='claude', delay=0.1)
    
    # Override the second player to be Easy AI for faster games
    from ai import EasyAI
    easy = EasyAI()
    easy.engine = engine
    engine.ai_strategies[1] = easy
    
    # Set both as AI
    for player in engine.gs.players:
        player.is_human = False
    
    # Modify health to trigger trunk loss and round end quickly
    engine.gs.players[0].health = 2  # Claude has low health
    engine.gs.players[1].health = 2  # TestBot has low health
    
    try:
        # Setup and run one round
        engine._setup_game()
        
        print("\n>>> Starting Round 1...")
        engine._run_round()
        
        print("\n" + "=" * 60)
        print("Test complete!")
        
        # Check if any messages were logged
        if hasattr(engine.gs, 'action_log'):
            claude_messages = [log for log in engine.gs.action_log if "[Claude]" in log or "Claude's Round" in log]
            if claude_messages:
                print(f"\nFound {len(claude_messages)} Claude messages:")
                for msg in claude_messages:
                    print(f"  - {msg}")
            else:
                print("\nNo Claude messages found in action log.")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_claude_messaging()