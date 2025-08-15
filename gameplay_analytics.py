#!/usr/bin/env python3
"""Analyze gameplay statistics from AI battles"""

import json
import os
from collections import defaultdict
import statistics
import glob

class GameplayAnalyzer:
    """Analyze actual gameplay data from AI battles"""
    
    def __init__(self):
        self.battle_results = []
        self.load_battle_results()
    
    def load_battle_results(self):
        """Load all battle result files from test_results directory"""
        result_files = glob.glob('test_results/ai_*.json')
        
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.battle_results.append(data)
                    print(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    def analyze_ai_performance(self):
        """Analyze win rates by AI type"""
        print("\nAI PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        ai_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0})
        
        for result in self.battle_results:
            # Check different result formats
            if isinstance(result, dict):
                # Handle different data structures
                if 'games' in result:  # Tournament format
                    for game in result.get('games', []):
                        self._process_game_result(game, ai_stats)
                elif 'ai1_wins' in result:  # Simple format
                    # This format doesn't track individual games
                    pass
                else:
                    # Try to process as individual game
                    self._process_game_result(result, ai_stats)
        
        # Display results
        print(f"\n{'AI Type':<10} {'Games':<10} {'Wins':<10} {'Win Rate':<10}")
        print("-" * 40)
        
        for ai_type in ['easy', 'medium', 'hard']:
            stats = ai_stats[ai_type]
            if stats['games'] > 0:
                win_rate = (stats['wins'] / stats['games']) * 100
                print(f"{ai_type:<10} {stats['games']:<10} {stats['wins']:<10} {win_rate:<10.1f}%")
    
    def _process_game_result(self, game, ai_stats):
        """Process a single game result"""
        # Extract AI types and winner
        if 'ai1' in game and 'ai2' in game:
            ai1_type = game['ai1'].get('type', 'unknown')
            ai2_type = game['ai2'].get('type', 'unknown')
            
            ai_stats[ai1_type]['games'] += 1
            ai_stats[ai2_type]['games'] += 1
            
            if game.get('winner_idx') == 0:
                ai_stats[ai1_type]['wins'] += 1
                ai_stats[ai2_type]['losses'] += 1
            elif game.get('winner_idx') == 1:
                ai_stats[ai2_type]['wins'] += 1
                ai_stats[ai1_type]['losses'] += 1
    
    def analyze_game_metrics(self):
        """Analyze game length and other metrics"""
        print("\nGAME METRICS ANALYSIS")
        print("=" * 60)
        
        game_lengths = []
        game_durations = []
        
        for result in self.battle_results:
            if isinstance(result, dict):
                if 'games' in result:
                    for game in result.get('games', []):
                        if 'rounds' in game:
                            game_lengths.append(game['rounds'])
                        if 'duration' in game:
                            game_durations.append(game['duration'])
                elif 'rounds' in result:
                    game_lengths.append(result['rounds'])
                    if 'duration' in result:
                        game_durations.append(result['duration'])
        
        if game_lengths:
            print(f"\nGame Length Statistics:")
            print(f"  Average rounds: {statistics.mean(game_lengths):.1f}")
            print(f"  Min rounds: {min(game_lengths)}")
            print(f"  Max rounds: {max(game_lengths)}")
            print(f"  Median rounds: {statistics.median(game_lengths)}")
        
        if game_durations:
            print(f"\nGame Duration Statistics:")
            print(f"  Average duration: {statistics.mean(game_durations):.1f}s")
            print(f"  Min duration: {min(game_durations):.1f}s")
            print(f"  Max duration: {max(game_durations):.1f}s")


class LiveGameAnalyzer:
    """Analyze a live game for detailed statistics"""
    
    def __init__(self, game_engine):
        self.engine = game_engine
        self.stats = {
            'damage_dealt': defaultdict(int),
            'healing_done': defaultdict(int),
            'cards_played': defaultdict(int),
            'elements_used': defaultdict(lambda: defaultdict(int)),
            'spell_types_used': defaultdict(lambda: defaultdict(int)),
            'conjuries_played': defaultdict(int),
            'responses_triggered': defaultdict(int),
            'self_damage_taken': defaultdict(int)
        }
    
    def track_spell_played(self, player_name, card):
        """Track when a spell is played"""
        self.stats['cards_played'][player_name] += 1
        self.stats['elements_used'][player_name][card.element] += 1
        
        for spell_type in card.types:
            self.stats['spell_types_used'][player_name][spell_type] += 1
        
        if card.is_conjury:
            self.stats['conjuries_played'][player_name] += 1
    
    def track_damage(self, dealer_name, target_name, amount):
        """Track damage dealt"""
        if dealer_name == target_name:
            self.stats['self_damage_taken'][dealer_name] += amount
        else:
            self.stats['damage_dealt'][dealer_name] += amount
    
    def track_healing(self, healer_name, amount):
        """Track healing done"""
        self.stats['healing_done'][healer_name] += amount
    
    def track_response_triggered(self, player_name):
        """Track when a response spell triggers"""
        self.stats['responses_triggered'][player_name] += 1
    
    def generate_report(self):
        """Generate a summary report"""
        print("\nGAME STATISTICS REPORT")
        print("=" * 60)
        
        for player in self.engine.gs.players:
            print(f"\n{player.name}:")
            print(f"  Status: {'ALIVE' if player.trunks > 0 else 'ELIMINATED'}")
            print(f"  Final Health: {player.health}")
            print(f"  Trunks Remaining: {player.trunks}")
            print(f"  Cards Played: {self.stats['cards_played'][player.name]}")
            print(f"  Damage Dealt: {self.stats['damage_dealt'][player.name]}")
            print(f"  Healing Done: {self.stats['healing_done'][player.name]}")
            print(f"  Self Damage: {self.stats['self_damage_taken'][player.name]}")
            
            # Element usage
            elements = self.stats['elements_used'][player.name]
            if elements:
                print(f"  Elements Used: {dict(elements)}")
            
            # Spell type usage
            types = self.stats['spell_types_used'][player.name]
            if types:
                print(f"  Spell Types: {dict(types)}")


def main():
    print("ELEMENTAL ELEPHANTS - GAMEPLAY ANALYTICS")
    print("=" * 60)
    
    analyzer = GameplayAnalyzer()
    
    if not analyzer.battle_results:
        print("\nNo battle results found in test_results/")
        print("Run some AI battles first to generate data!")
        return
    
    analyzer.analyze_ai_performance()
    analyzer.analyze_game_metrics()


if __name__ == "__main__":
    main()