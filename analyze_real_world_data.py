#!/usr/bin/env python3
"""Analyze real-world game data and generate reports"""

from game_logger import GameLogger
import os

def main():
    logger = GameLogger()
    
    # Check if we have game logs
    if not os.path.exists('game_logs') or not os.listdir('game_logs'):
        print("No game logs found!")
        print("\nTo generate real-world data:")
        print("1. Play some games using: python elephants_prototype.py")
        print("2. Make sure to complete the games (don't quit early)")
        print("3. Run this script again after playing several games")
        print("\nFor best results, play at least 10-20 games with different elements.")
        return
    
    # Generate the comprehensive report
    logger.generate_real_world_report()
    
    # Save report to file
    print("\n" + "=" * 80)
    print("Saving report to 'real_world_analysis.txt'...")
    
    import sys
    from io import StringIO
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = output_buffer = StringIO()
    
    # Generate report again for file
    logger.generate_real_world_report()
    
    # Restore stdout and save
    sys.stdout = old_stdout
    report_content = output_buffer.getvalue()
    
    with open('real_world_analysis.txt', 'w') as f:
        f.write(report_content)
    
    print("Report saved successfully!")
    
    # Additional analysis
    print("\n" + "=" * 80)
    print("ADDITIONAL INSIGHTS")
    print("-" * 80)
    
    # Count games per element
    element_games = {}
    spell_usage = {}
    
    for filename in os.listdir('game_logs'):
        if filename.endswith('.json'):
            import json
            with open(os.path.join('game_logs', filename), 'r') as f:
                game_data = json.load(f)
                
                # Count elements
                for player_key in ['player1', 'player2']:
                    elements = game_data['players'][player_key].get('elements', [])
                    for elem in elements:
                        element_games[elem] = element_games.get(elem, 0) + 1
                
                # Count spell usage
                for event in game_data.get('events', []):
                    if event['type'] == 'spell_played':
                        spell_name = event['spell']
                        spell_usage[spell_name] = spell_usage.get(spell_name, 0) + 1
    
    print("\nElement representation in games:")
    for elem, count in sorted(element_games.items(), key=lambda x: x[1], reverse=True):
        print(f"  {elem}: {count} games")
    
    print("\nMost frequently played spells:")
    for spell, count in sorted(spell_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {spell}: {count} times")


if __name__ == "__main__":
    main()