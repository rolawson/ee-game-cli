#!/usr/bin/env python3
"""Test Claude AI with verbose output to check messaging"""

import os
import sys

def test_claude_verbose():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude AI messaging with verbose output...")
    print("=" * 60)
    
    # Import here to ensure proper path
    from ai_spectator import AutoPlayEngine
    from ai import EasyAI
    
    # Create engine
    engine = AutoPlayEngine(["Claude", "TestBot"], ai_difficulty='claude', delay=0.1)
    
    # Import Claude Savant AI
    from ai.claude_savant import ClaudeSavantAI
    
    # Set up AI strategies properly
    claude = ClaudeSavantAI()
    claude.engine = engine
    engine.ai_strategies[0] = claude  # Claude is player 0
    
    # Override second player to Easy AI
    easy = EasyAI()
    easy.engine = engine
    engine.ai_strategies[1] = easy
    
    # Make both AI
    for player in engine.gs.players:
        player.is_human = False
    
    # Set low health to end round quickly
    engine.gs.players[0].health = 1
    engine.gs.players[1].health = 1
    
    # Enable AI decision logs
    engine.ai_decision_logs = []
    
    try:
        engine._setup_game()
        
        print("\n>>> Running one round...")
        engine._run_round()
        
        print("\n" + "=" * 60)
        print("AI Decision Logs:")
        for log in engine.ai_decision_logs:
            print(log)
            
        print("\n" + "=" * 60)
        print("Action Log (Claude messages):")
        if hasattr(engine.gs, 'action_log'):
            for log in engine.gs.action_log:
                if "Claude" in log:
                    print(log)
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_claude_verbose()