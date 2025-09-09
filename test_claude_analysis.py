#!/usr/bin/env python3
"""Test script to verify Claude's end-of-round analysis"""

import os
import sys

# Quick test to see if Claude analysis is working
def test_analysis():
    # First check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return
    
    # Import and test the round analysis prompt building
    from ai.claude_ai import ClaudeAI
    
    claude = ClaudeAI()
    
    # Test context for round analysis
    test_context = {
        'round': 1,
        'round_plays': [
            {'clash': 1, 'card': 'Familiar'},
            {'clash': 2, 'card': 'Sap'},
            {'clash': 3, 'card': 'Flow'},
            {'clash': 4, 'card': 'Imitate'}
        ],
        'player_health': [('Claude', 5, 5), ('Human', 3, 5)],
        'player_trunks': [('Claude', 3), ('Human', 3)]
    }
    
    # Build the prompt
    prompt = claude._build_round_analysis_prompt(test_context)
    print("Round Analysis Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    
    # Test the LLM decision making
    print("\nTesting Claude's analysis generation...")
    try:
        import asyncio
        
        async def get_analysis():
            result = await claude._get_llm_decision(test_context, "round_analysis")
            return result
        
        result = asyncio.run(get_analysis())
        if result:
            print(f"Analysis received: {result.get('analysis', 'No analysis')}")
        else:
            print("No result returned")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analysis()