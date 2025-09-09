#!/usr/bin/env python3
"""Test Claude AI vs Expert AI in spectator mode"""

import os
import sys
from ai_spectator import AutoPlayEngine


def test_claude_vs_expert():
    """Test Claude AI against Expert AI"""
    
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    print("Starting Elemental Elephants: Claude AI vs Expert AI")
    print("=" * 60)
    
    # Create game with Claude vs Expert
    player_names = ["Claude", "Expert"]
    
    try:
        # Create spectator engine with Claude AI
        engine = AutoPlayEngine(player_names, ai_difficulty='claude', delay=2.0)
        
        # Override to make Expert the second player
        from ai import ExpertAI
        expert = ExpertAI()
        expert.engine = engine
        engine.ai_strategies[1] = expert
        
        # Set both as AI players
        for player in engine.gs.players:
            player.is_human = False
        
        # Run the game
        engine.run_game()
        
    except Exception as e:
        print(f"\nError during game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_claude_vs_expert()