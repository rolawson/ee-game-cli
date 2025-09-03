#!/usr/bin/env python3
"""
Simple AI Win Rate Test - Uses the proven SilentGameEngine from analytics.py
"""

import sys
from datetime import datetime
from collections import defaultdict

# Import the working SilentGameEngine from analytics
from analytics import SilentGameEngine


def test_ai_matchup(ai1_type, ai2_type, num_games=20):
    """Test a specific AI matchup"""
    wins = {ai1_type: 0, ai2_type: 0, 'draws': 0}
    
    print(f"\nTesting {ai1_type.upper()} vs {ai2_type.upper()} ({num_games} games)...")
    
    for game_num in range(num_games):
        # Alternate who goes first
        if game_num % 2 == 0:
            player_names = [f"{ai1_type.upper()}_1", f"{ai2_type.upper()}_2"]
            first_ai = ai1_type
            second_ai = ai2_type
        else:
            player_names = [f"{ai2_type.upper()}_1", f"{ai1_type.upper()}_2"]
            first_ai = ai2_type
            second_ai = ai1_type
        
        try:
            # Create silent game engine with 'hard' as default
            engine = SilentGameEngine(player_names, ai_difficulty='hard')
            
            # Import all AI types
            from ai import EasyAI, MediumAI, HardAI, ExpertAI
            
            # Set up first AI
            if first_ai == 'easy':
                engine.ai_strategies[0] = EasyAI()
            elif first_ai == 'medium':
                engine.ai_strategies[0] = MediumAI()
            elif first_ai == 'hard':
                engine.ai_strategies[0] = HardAI()
            elif first_ai == 'expert':
                engine.ai_strategies[0] = ExpertAI()
            
            # Set up second AI
            if second_ai == 'easy':
                engine.ai_strategies[1] = EasyAI()
            elif second_ai == 'medium':
                engine.ai_strategies[1] = MediumAI()
            elif second_ai == 'hard':
                engine.ai_strategies[1] = HardAI()
            elif second_ai == 'expert':
                engine.ai_strategies[1] = ExpertAI()
            
            # Set engine references
            if 0 in engine.ai_strategies:
                engine.ai_strategies[0].engine = engine
            if 1 in engine.ai_strategies:
                engine.ai_strategies[1].engine = engine
            
            # Run the game
            engine.run_game()
            
            # Determine winner
            winner = next((p for p in engine.gs.players if p.trunks > 0), None)
            if winner:
                if winner == engine.gs.players[0]:
                    wins[first_ai] += 1
                else:
                    wins[second_ai] += 1
            else:
                wins['draws'] += 1
                
            # Progress update
            if (game_num + 1) % 5 == 0:
                print(f"  Progress: {game_num + 1}/{num_games} - "
                      f"{ai1_type}: {wins[ai1_type]}, {ai2_type}: {wins[ai2_type]}")
                
        except Exception as e:
            print(f"  Error in game {game_num + 1}: {str(e)}")
            continue
    
    # Calculate win rates
    if num_games > 0:
        ai1_rate = wins[ai1_type] / num_games * 100
        ai2_rate = wins[ai2_type] / num_games * 100
        draw_rate = wins['draws'] / num_games * 100
        
        print(f"\nResults:")
        print(f"  {ai1_type.upper()}: {wins[ai1_type]}/{num_games} ({ai1_rate:.1f}%)")
        print(f"  {ai2_type.upper()}: {wins[ai2_type]}/{num_games} ({ai2_rate:.1f}%)")
        print(f"  Draws: {wins['draws']}/{num_games} ({draw_rate:.1f}%)")
    
    return wins


def run_all_matchups(games_per_matchup=10):
    """Run all AI matchups"""
    ai_types = ['easy', 'medium', 'hard', 'expert']
    all_results = defaultdict(lambda: defaultdict(int))
    
    print("="*60)
    print("AI WIN RATE TEST")
    print("="*60)
    
    # Test each combination
    for i, ai1 in enumerate(ai_types):
        for j, ai2 in enumerate(ai_types):
            if ai1 != ai2:  # Skip mirror matches - they don't provide useful data
                results = test_ai_matchup(ai1, ai2, games_per_matchup)
                
                # Store results
                all_results[ai1][ai2] = results[ai1]
                all_results[ai2][ai1] = results[ai2]
    
    # Calculate overall win rates
    print("\n" + "="*60)
    print("OVERALL WIN RATES")
    print("="*60)
    
    for ai in ai_types:
        total_wins = 0
        total_games = 0
        
        for opponent in ai_types:
            if ai != opponent:
                total_wins += all_results[ai][opponent]
                total_games += games_per_matchup
        
        if total_games > 0:
            win_rate = total_wins / total_games * 100
            print(f"{ai.upper():>8}: {win_rate:>5.1f}% ({total_wins}/{total_games} games)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_winrate_results_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("AI Win Rate Test Results\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Games per matchup: {games_per_matchup}\n\n")
        
        # Win matrix
        f.write("Win Matrix (row beats column):\n")
        f.write("         ")
        for ai in ai_types:
            f.write(f"{ai:>8}")
        f.write("\n")
        
        for ai1 in ai_types:
            f.write(f"{ai1:>8} ")
            for ai2 in ai_types:
                wins = all_results[ai1][ai2]
                f.write(f"{wins:>8}")
            f.write("\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    if len(sys.argv) > 2:
        # Test specific matchup
        ai1 = sys.argv[1]
        ai2 = sys.argv[2]
        games = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        test_ai_matchup(ai1, ai2, games)
    elif len(sys.argv) > 1:
        # Run all matchups with specified games
        games = int(sys.argv[1])
        run_all_matchups(games)
    else:
        # Default: quick test
        print("Usage:")
        print("  python ai_winrate_test.py [games_per_matchup]")
        print("  python ai_winrate_test.py ai1 ai2 [num_games]")
        print("\nRunning quick test with 5 games per matchup...")
        run_all_matchups(5)


if __name__ == "__main__":
    main()