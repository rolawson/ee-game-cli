#!/usr/bin/env python3
"""Test script for Claude AI integration"""

import os
import sys
from elephants_prototype import GameEngine


def test_claude_ai():
    """Test the Claude AI implementation"""
    
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    print("Starting Elemental Elephants with Claude AI...")
    print("-" * 50)
    
    # Create game with Claude AI as opponent
    player_names = ["Human", "Claude"]
    
    try:
        # Initialize game engine with Claude AI
        engine = GameEngine(player_names, ai_difficulty='claude')
        
        # Run the game
        engine.run_game()
        
    except Exception as e:
        print(f"Error during game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_claude_ai()