#!/usr/bin/env python3
"""Script to generate analytics data from AI vs AI battles"""

import sys
import os
import time
from datetime import datetime

# Run AI vs AI battles and generate analytics data
from ai_vs_ai import AIGameRunner
from analyze_real_world_data import main as analyze_data

def generate_games(num_games=50, ai1_type='hard', ai2_type='hard', verbose=False):
    """Generate multiple AI vs AI games for analytics"""
    print(f"\nGenerating {num_games} AI vs AI games ({ai1_type} vs {ai2_type})...")
    print("=" * 60)
    
    successful_games = 0
    failed_games = 0
    start_time = time.time()
    
    for i in range(num_games):
        if verbose:
            print(f"\nGame {i+1}/{num_games}:")
        else:
            print(f"Running game {i+1}/{num_games}...", end='\r')
        
        try:
            runner = AIGameRunner(ai1_type, ai2_type, verbose=verbose)
            result = runner.run_game()
            
            if result:
                successful_games += 1
                if verbose:
                    print(f"  Winner: {result['winner']} in {result['rounds']} rounds")
            else:
                failed_games += 1
                if verbose:
                    print("  Game failed to complete")
        except Exception as e:
            failed_games += 1
            if verbose:
                print(f"  Game error: {e}")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n\nGeneration Complete!")
    print("-" * 60)
    print(f"Successful games: {successful_games}")
    print(f"Failed games: {failed_games}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds")
    print(f"Average time per game: {elapsed_time/num_games:.1f} seconds")
    
    return successful_games, failed_games

def run_tournament_for_analytics(games_per_matchup=10):
    """Run a full tournament between all AI types for analytics"""
    ai_types = ['easy', 'medium', 'hard']
    total_games = 0
    
    print("\nRunning AI Tournament for Analytics Data")
    print("=" * 60)
    
    for ai1 in ai_types:
        for ai2 in ai_types:
            print(f"\n{ai1.upper()} vs {ai2.upper()}:")
            successful, failed = generate_games(games_per_matchup, ai1, ai2, verbose=False)
            total_games += successful
    
    print(f"\n\nTotal games generated: {total_games}")
    return total_games

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'tournament':
            # Run full tournament
            games = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            total_games = run_tournament_for_analytics(games)
            
            # Generate analytics report
            print("\n" + "=" * 60)
            print("Generating analytics report...")
            print("=" * 60 + "\n")
            analyze_data()
            
        elif sys.argv[1] == 'quick':
            # Quick test with fewer games
            generate_games(5, 'hard', 'hard', verbose=True)
            
            print("\n" + "=" * 60)
            print("Generating analytics report...")
            print("=" * 60 + "\n")
            analyze_data()
            
        else:
            # Custom number of games
            num_games = int(sys.argv[1])
            ai1 = sys.argv[2] if len(sys.argv) > 2 else 'hard'
            ai2 = sys.argv[3] if len(sys.argv) > 3 else 'hard'
            
            generate_games(num_games, ai1, ai2)
            
            print("\n" + "=" * 60)
            print("Generating analytics report...")
            print("=" * 60 + "\n")
            analyze_data()
    else:
        print("Usage:")
        print("  python generate_analytics_data.py quick              # Quick test (5 games)")
        print("  python generate_analytics_data.py tournament [games] # Full tournament")
        print("  python generate_analytics_data.py [num] [ai1] [ai2]  # Custom games")
        print("\nExamples:")
        print("  python generate_analytics_data.py 100                # 100 hard vs hard games")
        print("  python generate_analytics_data.py 50 medium easy     # 50 medium vs easy games")
        print("  python generate_analytics_data.py tournament 20      # Tournament with 20 games per matchup")

if __name__ == "__main__":
    main()