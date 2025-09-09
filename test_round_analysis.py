#!/usr/bin/env python3
"""Test Claude AI round analysis specifically"""

import os
import asyncio
from ai.claude_ai import ClaudeAI

async def test_round_analysis():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
        
    print("Testing Claude AI round analysis directly...")
    print("=" * 60)
    
    # Create Claude AI instance
    claude = ClaudeAI()
    
    # Mock context for round analysis
    context = {
        'round': 1,
        'round_plays': [
            {'clash': 1, 'card': 'Quickshot', 'reasoning': 'Opening aggression'},
            {'clash': 2, 'card': 'Shield', 'reasoning': 'Defensive posture'},
            {'clash': 3, 'card': 'Agonize', 'reasoning': 'Setup for next turn'},
            {'clash': 4, 'card': 'Turbulence', 'reasoning': 'Board control'}
        ],
        'player_health': [
            ('Claude', 3, 5),
            ('TestBot', 1, 5)
        ],
        'player_trunks': [
            ('Claude', 3),
            ('TestBot', 2)
        ]
    }
    
    try:
        # Call the LLM decision method directly
        result = await claude._get_llm_decision(context, "round_analysis")
        
        print("\nLLM Response:")
        print(result)
        
        if result and isinstance(result, dict):
            analysis = result.get("analysis", "")
            if analysis:
                print(f"\nAnalysis Message: {analysis}")
            else:
                print("\nNo analysis message in response")
        else:
            print("\nNo valid response from LLM")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_round_analysis())