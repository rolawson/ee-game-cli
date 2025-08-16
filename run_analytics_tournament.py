#!/usr/bin/env python3
"""Run a large AI tournament to generate comprehensive analytics data"""

import time
from generate_analytics_data import run_tournament_for_analytics
from analyze_real_world_data import main as analyze_data

def main():
    """Run a comprehensive tournament for analytics"""
    print("=" * 80)
    print("ELEMENTAL ELEPHANTS - ANALYTICS DATA GENERATION")
    print("=" * 80)
    print("\nThis will run a large tournament to generate comprehensive analytics data.")
    print("Recommended: 50+ games per matchup for good statistical coverage")
    print()
    
    # Get number of games per matchup
    while True:
        try:
            games_per_matchup = input("Games per matchup (default: 50): ").strip()
            if not games_per_matchup:
                games_per_matchup = 50
            else:
                games_per_matchup = int(games_per_matchup)
            if games_per_matchup < 1:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    # Calculate total games
    ai_types = ['easy', 'medium', 'hard']
    total_matchups = len(ai_types) * len(ai_types)
    total_games = total_matchups * games_per_matchup
    
    print(f"\nThis will run {total_games} total games ({total_matchups} matchups x {games_per_matchup} games each)")
    print(f"Estimated time: {total_games * 0.1:.1f} seconds")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run the tournament
    start_time = time.time()
    print("\nStarting tournament...")
    
    try:
        total_games_run = run_tournament_for_analytics(games_per_matchup)
        
        elapsed_time = time.time() - start_time
        print(f"\nTournament completed in {elapsed_time:.1f} seconds")
        print(f"Games run: {total_games_run}")
        print(f"Average time per game: {elapsed_time/total_games_run:.2f} seconds")
        
        # Generate comprehensive report
        print("\n" + "=" * 80)
        print("GENERATING COMPREHENSIVE ANALYTICS REPORT")
        print("=" * 80 + "\n")
        
        analyze_data()
        
        print("\n" + "=" * 80)
        print("ANALYTICS GENERATION COMPLETE!")
        print("=" * 80)
        print("\nReports generated:")
        print("  - real_world_analysis.txt: Comprehensive damage and element analysis")
        print("  - game_logs/: Individual game logs for detailed analysis")
        print("\nUse this data to:")
        print("  - Balance spell damage values")
        print("  - Identify over/underperforming elements")
        print("  - Compare theoretical vs actual damage output")
        print("  - Track spell usage patterns")
        
    except KeyboardInterrupt:
        print("\n\nTournament interrupted by user.")
        print("Partial data has been saved.")
    except Exception as e:
        print(f"\nError during tournament: {e}")
        print("Partial data may have been saved.")

if __name__ == "__main__":
    main()