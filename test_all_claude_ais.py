#!/usr/bin/env python3
"""Test all four Claude AI personalities"""

import os
import sys
from ai_spectator import AutoPlayEngine
from ai.claude_savant import ClaudeSavantAI
from ai.claude_champion import ClaudeChampionAI
from ai.claude_daredevil import ClaudeDaredevilAI
from ai.claude_chevalier import ClaudeChevalierAI
from ai import EasyAI


def test_ai_personality(ai_class, ai_name, opponent_name="TestBot"):
    """Test a single AI personality"""
    print(f"\n{'='*60}")
    print(f"Testing {ai_name}")
    print(f"{'='*60}")
    
    # Create engine
    engine = AutoPlayEngine([ai_name, opponent_name], ai_difficulty='medium', delay=0.1)
    
    # Set up the Claude AI
    ai = ai_class()
    ai.engine = engine
    engine.ai_strategies[0] = ai
    
    # Set up opponent (Easy AI for quick testing)
    opponent = EasyAI()
    opponent.engine = engine
    engine.ai_strategies[1] = opponent
    
    # Run a quick game (just 2 rounds for testing)
    try:
        for round_num in range(2):
            print(f"\n>>> Playing round {round_num + 1}...")
            engine._play_round()
            
            # Check if game ended
            if engine.gs.is_game_complete():
                print(f">>> Game ended! Winner: {engine.gs.get_winner().name if engine.gs.get_winner() else 'Draw'}")
                break
    except Exception as e:
        print(f">>> Error during game: {e}")
    
    print(f"\n>>> {ai_name} test complete!")


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    print("Testing all four Claude AI personalities")
    print("========================================")
    
    # Test each personality
    personalities = [
        (ClaudeSavantAI, "SAVANT_AI"),
        (ClaudeChampionAI, "CHAMPION_AI"),
        (ClaudeDaredevilAI, "DAREDEVIL_AI"),
        (ClaudeChevalierAI, "CHEVALIER_AI")
    ]
    
    for ai_class, ai_name in personalities:
        try:
            test_ai_personality(ai_class, ai_name)
        except Exception as e:
            print(f"\n>>> Error testing {ai_name}: {e}")
    
    print("\n" + "="*60)
    print("All personality tests complete!")
    print("="*60)
    
    # Show a quick match between two Claude AIs
    print("\n\nBonus: Quick match between Daredevil and Chevalier!")
    print("="*60)
    
    try:
        engine = AutoPlayEngine(["DAREDEVIL_AI", "CHEVALIER_AI"], ai_difficulty='medium', delay=0.2)
        
        # Set up Daredevil
        daredevil = ClaudeDaredevilAI()
        daredevil.engine = engine
        engine.ai_strategies[0] = daredevil
        
        # Set up Chevalier
        chevalier = ClaudeChevalierAI()
        chevalier.engine = engine
        engine.ai_strategies[1] = chevalier
        
        # Play one round
        print("\n>>> Playing one round of Daredevil vs Chevalier...")
        engine._play_round()
        
        print("\n>>> Match preview complete!")
        
    except Exception as e:
        print(f"\n>>> Error in bonus match: {e}")


if __name__ == "__main__":
    main()