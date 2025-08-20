#!/usr/bin/env python3
"""Game logger for tracking real-world spell performance"""

import json
import os
from datetime import datetime
from collections import defaultdict

class GameLogger:
    """Logs game events for analytics"""
    
    def __init__(self, log_dir="game_logs"):
        self.log_dir = log_dir
        self.current_game = None
        self.damage_events = []
        self.healing_events = []
        self.weaken_events = []
        self.bolster_events = []
        self.spell_plays = []
        self.game_metadata = {}
        self.trunk_start_times = {}  # Track when each trunk starts
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def reset(self):
        """Reset the logger for a new game"""
        self.current_game = None
        self.damage_events = []
        self.healing_events = []
        self.weaken_events = []
        self.bolster_events = []
        self.spell_plays = []
        self.game_metadata = {}
        self.trunk_start_times = {}
    
    def start_game(self, player1_name, player2_name, player1_elements, player2_elements, ai_difficulty=None):
        """Start logging a new game"""
        self.current_game = {
            'timestamp': datetime.now().isoformat(),
            'players': {
                'player1': {
                    'name': player1_name,
                    'elements': player1_elements,
                    'is_ai': ai_difficulty is not None
                },
                'player2': {
                    'name': player2_name,
                    'elements': player2_elements,
                    'is_ai': True
                }
            },
            'ai_difficulty': ai_difficulty,
            'events': [],
            'player_elements': {
                player1_name: player1_elements,
                player2_name: player2_elements
            }
        }
        self.damage_events = []
        self.healing_events = []
        self.weaken_events = []
        self.bolster_events = []
        self.spell_plays = []
        
        # Initialize trunk tracking - each player starts with 3 trunks at round 1
        self.trunk_start_times = {
            f"{player1_name}_trunk_1": 1,
            f"{player2_name}_trunk_1": 1
        }
    
    def log_spell_played(self, player_name, spell_name, element, clash_num, round_num, spell_types=None, is_conjury=False):
        """Log when a spell is played"""
        event = {
            'type': 'spell_played',
            'player': player_name,
            'spell': spell_name,
            'spell_name': spell_name,  # Duplicate for consistency
            'element': element,
            'spell_types': spell_types or [],
            'is_conjury': is_conjury,
            'clash': clash_num,
            'round': round_num,
            'timestamp': datetime.now().isoformat()
        }
        self.spell_plays.append(event)
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_damage_dealt(self, source_player, target_player, damage_amount, spell_name, element, 
                        clash_num, round_num, is_self_damage=False):
        """Log damage dealt by a spell"""
        event = {
            'type': 'damage_dealt',
            'source_player': source_player,
            'target_player': target_player,
            'amount': damage_amount,
            'spell': spell_name,
            'element': element,
            'clash': clash_num,
            'round': round_num,
            'is_self_damage': is_self_damage,
            'timestamp': datetime.now().isoformat()
        }
        self.damage_events.append(event)
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_healing_done(self, source_player, target_player, heal_amount, spell_name, element,
                        clash_num, round_num):
        """Log healing done by a spell"""
        event = {
            'type': 'healing_done',
            'source_player': source_player,
            'target_player': target_player,
            'amount': heal_amount,
            'spell': spell_name,
            'element': element,
            'clash': clash_num,
            'round': round_num,
            'timestamp': datetime.now().isoformat()
        }
        self.healing_events.append(event)
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_weaken_dealt(self, source_player, target_player, weaken_amount, spell_name, element,
                        clash_num, round_num):
        """Log weaken dealt by a spell"""
        event = {
            'type': 'weaken_dealt',
            'source_player': source_player,
            'target_player': target_player,
            'amount': weaken_amount,
            'spell': spell_name,
            'element': element,
            'clash': clash_num,
            'round': round_num,
            'timestamp': datetime.now().isoformat()
        }
        self.weaken_events.append(event)
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_bolster_done(self, source_player, target_player, bolster_amount, spell_name, element,
                        clash_num, round_num):
        """Log bolster done by a spell"""
        event = {
            'type': 'bolster_done',
            'source_player': source_player,
            'target_player': target_player,
            'amount': bolster_amount,
            'spell': spell_name,
            'element': element,
            'clash': clash_num,
            'round': round_num,
            'timestamp': datetime.now().isoformat()
        }
        self.bolster_events.append(event)
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_trunk_lost(self, player_name, round_num, remaining_trunks):
        """Log when a player loses a trunk"""
        event = {
            'type': 'trunk_lost',
            'player': player_name,
            'round': round_num,
            'remaining_trunks': remaining_trunks,
            'timestamp': datetime.now().isoformat()
        }
        
        # Track trunk lifetime
        trunk_key = f"{player_name}_trunk_{3 - remaining_trunks}"  # trunk 1, 2, or 3
        if trunk_key in self.trunk_start_times:
            start_round = self.trunk_start_times[trunk_key]
            event['trunk_lifetime_rounds'] = round_num - start_round
        
        # Start tracking next trunk
        if remaining_trunks > 0:
            next_trunk_key = f"{player_name}_trunk_{3 - remaining_trunks + 1}"
            self.trunk_start_times[next_trunk_key] = round_num
        
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_advanced(self, player_name, spell_name, from_clash, to_clash):
        """Log when a spell is advanced"""
        event = {
            'type': 'spell_advanced',
            'player': player_name,
            'spell': spell_name,
            'from_clash': from_clash,
            'to_clash': to_clash,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_cancelled(self, player_name, spell_name, cancelled_by):
        """Log when a spell is cancelled"""
        event = {
            'type': 'spell_cancelled',
            'player': player_name,
            'spell': spell_name,
            'cancelled_by': cancelled_by,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_recalled(self, player_name, spell_name, from_location):
        """Log when a spell is recalled"""
        event = {
            'type': 'spell_recalled',
            'player': player_name,
            'spell': spell_name,
            'from_location': from_location,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_moved(self, player_name, spell_name, from_clash, to_clash):
        """Log when a spell is moved"""
        event = {
            'type': 'spell_moved',
            'player': player_name,
            'spell': spell_name,
            'from_clash': from_clash,
            'to_clash': to_clash,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_discarded(self, player_name, spell_name, discarded_by):
        """Log when a spell is discarded"""
        event = {
            'type': 'spell_discarded',
            'player': player_name,
            'spell': spell_name,
            'discarded_by': discarded_by,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_spell_revealed(self, player_name, spell_name, revealed_by):
        """Log when a spell is revealed from hand"""
        event = {
            'type': 'spell_revealed',
            'player': player_name,
            'spell': spell_name,
            'revealed_by': revealed_by,
            'timestamp': datetime.now().isoformat()
        }
        if self.current_game:
            self.current_game['events'].append(event)
    
    def log_game_end(self, winner_name, winner_health, loser_health, total_rounds):
        """Log the end of a game"""
        if self.current_game:
            self.current_game['winner'] = winner_name  # Add winner at top level for easier access
            self.current_game['total_rounds'] = total_rounds  # Add at top level too
            self.current_game['result'] = {
                'winner': winner_name,
                'winner_health': winner_health,
                'loser_health': loser_health,
                'total_rounds': total_rounds,
                'end_timestamp': datetime.now().isoformat()
            }
            
            # Save to file
            filename = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.log_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.current_game, f, indent=2)
            
            return filepath
    
    def analyze_damage_by_spell(self, weighted=False):
        """Analyze damage statistics by spell from logged games
        
        Args:
            weighted: If True, count weaken as 2x damage and bolster as 2x healing
        """
        spell_damage_stats = defaultdict(lambda: {
            'total_damage': 0,
            'total_damage_weighted': 0,
            'times_played': 0,
            'damage_per_cast': [],  # Track damage values per cast
            'element': None
        })
        
        # Load all game logs
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.log_dir, filename), 'r') as f:
                    game_data = json.load(f)
                    
                    # First pass: count spell plays to get times_played
                    spell_plays = {}
                    for event in game_data.get('events', []):
                        if event['type'] == 'spell_played':
                            spell_name = event['spell']
                            element = event['element']
                            clash = event['clash']
                            key = f"{spell_name}_{clash}_{event['player']}"
                            spell_plays[key] = {'spell': spell_name, 'element': element, 'damage': 0, 'weaken': 0}
                    
                    # Second pass: accumulate damage and weaken for each spell play
                    for event in game_data.get('events', []):
                        if event['type'] == 'damage_dealt' and not event.get('is_self_damage', False):
                            spell_name = event['spell']
                            clash = event['clash']
                            key = f"{spell_name}_{clash}_{event['source_player']}"
                            if key in spell_plays:
                                spell_plays[key]['damage'] += event['amount']
                        
                        elif event['type'] == 'weaken_dealt':
                            spell_name = event['spell']
                            clash = event['clash']
                            key = f"{spell_name}_{clash}_{event['source_player']}"
                            if key in spell_plays:
                                spell_plays[key]['weaken'] += event['amount']
                    
                    # Now aggregate the data
                    for play_data in spell_plays.values():
                        spell_name = play_data['spell']
                        element = play_data['element']
                        damage_total = play_data['damage'] + play_data['weaken']  # Unweighted
                        
                        # For weighted, count weaken as 2x
                        if weighted:
                            damage_weighted = play_data['damage'] + (play_data['weaken'] * 2)
                        else:
                            damage_weighted = damage_total
                        
                        spell_damage_stats[spell_name]['element'] = element
                        spell_damage_stats[spell_name]['times_played'] += 1
                        spell_damage_stats[spell_name]['total_damage'] += damage_total
                        spell_damage_stats[spell_name]['total_damage_weighted'] += damage_weighted
                        spell_damage_stats[spell_name]['damage_per_cast'].append(damage_total)
        
        # Calculate averages and ranges
        results = []
        for spell_name, stats in spell_damage_stats.items():
            if stats['times_played'] > 0:
                result = {
                    'spell': spell_name,
                    'element': stats['element'],
                    'times_used': stats['times_played'],
                    'total_damage': stats['total_damage'],
                    'total_damage_weighted': stats['total_damage_weighted'],
                    'avg_damage': stats['total_damage'] / stats['times_played'],
                    'avg_damage_weighted': stats['total_damage_weighted'] / stats['times_played']
                }
                
                # Min/max from damage per cast
                if stats['damage_per_cast']:
                    result['min_damage'] = min(stats['damage_per_cast'])
                    result['max_damage'] = max(stats['damage_per_cast'])
                else:
                    result['min_damage'] = 0
                    result['max_damage'] = 0
                
                results.append(result)
        
        # Sort by average damage
        results.sort(key=lambda x: x['avg_damage'], reverse=True)
        return results
    
    def analyze_damage_by_element(self, weighted=False):
        """Analyze damage statistics by element from logged games
        
        Args:
            weighted: If True, count weaken as 2x damage and bolster as 2x healing
        """
        element_damage_stats = defaultdict(lambda: {
            'total_damage': 0,
            'total_damage_weighted': 0,
            'damage_spells_used': 0,
            'weaken_spells_used': 0,
            'spell_damage': defaultdict(list),
            'spell_weaken': defaultdict(list)
        })
        
        # Load all game logs
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.log_dir, filename), 'r') as f:
                    game_data = json.load(f)
                    
                    for event in game_data.get('events', []):
                        if event['type'] == 'damage_dealt' and not event.get('is_self_damage', False):
                            element = event['element']
                            damage = event['amount']
                            spell_name = event['spell']
                            
                            element_damage_stats[element]['total_damage'] += damage
                            element_damage_stats[element]['total_damage_weighted'] += damage
                            element_damage_stats[element]['damage_spells_used'] += 1
                            element_damage_stats[element]['spell_damage'][spell_name].append(damage)
                        
                        elif event['type'] == 'weaken_dealt':
                            element = event['element']
                            weaken = event['amount']
                            spell_name = event['spell']
                            
                            element_damage_stats[element]['weaken_spells_used'] += 1
                            element_damage_stats[element]['spell_weaken'][spell_name].append(weaken)
                            
                            if weighted:
                                element_damage_stats[element]['total_damage_weighted'] += weaken * 2
                            else:
                                element_damage_stats[element]['total_damage'] += weaken
        
        # Calculate element averages
        results = []
        for element, stats in element_damage_stats.items():
            total_uses = stats['damage_spells_used'] + stats['weaken_spells_used']
            if total_uses > 0:
                # Calculate averages
                avg_damage = stats['total_damage'] / total_uses
                avg_damage_weighted = stats['total_damage_weighted'] / total_uses
                
                # Find the spell variety
                unique_spells = len(stats['spell_damage']) + len(stats['spell_weaken'])
                
                result = {
                    'element': element,
                    'avg_damage_per_use': avg_damage,
                    'avg_damage_weighted': avg_damage_weighted,
                    'total_damage': stats['total_damage'],
                    'total_damage_weighted': stats['total_damage_weighted'],
                    'times_used': total_uses,
                    'damage_uses': stats['damage_spells_used'],
                    'weaken_uses': stats['weaken_spells_used'],
                    'unique_damage_spells': unique_spells,
                    'spells': dict(stats['spell_damage']),
                    'weaken_spells': dict(stats['spell_weaken'])
                }
                
                results.append(result)
        
        # Sort by average damage
        results.sort(key=lambda x: x['avg_damage_per_use'], reverse=True)
        return results
    
    def generate_real_world_report(self):
        """Generate a comprehensive real-world performance report"""
        print("ELEMENTAL ELEPHANTS - REAL-WORLD DAMAGE ANALYSIS")
        print("=" * 80)
        
        # Check if we have data
        log_files = [f for f in os.listdir(self.log_dir) if f.endswith('.json')]
        if not log_files:
            print("No game logs found. Play some games to generate data!")
            return
        
        print(f"\nAnalyzing {len(log_files)} logged games...")
        
        # Spell damage analysis - UNWEIGHTED
        spell_stats = self.analyze_damage_by_spell(weighted=False)
        
        print("\n" + "=" * 80)
        print("DAMAGE BY SPELL - UNWEIGHTED (Weaken = 1x damage)")
        print("-" * 80)
        print(f"{'Spell':<20} {'Element':<12} {'Avg Damage':<12} {'Min':<6} {'Max':<6} {'Times Used':<12}")
        print("-" * 80)
        
        for stat in spell_stats[:15]:  # Top 15 spells
            print(f"{stat['spell']:<20} {stat['element']:<12} {stat['avg_damage']:>10.1f} "
                  f"{stat['min_damage']:>6} {stat['max_damage']:>6} {stat['times_used']:>12}")
        
        # Spell damage analysis - WEIGHTED
        spell_stats_weighted = self.analyze_damage_by_spell(weighted=True)
        
        print("\n" + "=" * 80)
        print("DAMAGE BY SPELL - WEIGHTED (Weaken = 2x damage)")
        print("-" * 80)
        print(f"{'Spell':<20} {'Element':<12} {'Avg Damage':<12} {'Weaken Uses':<12} {'Total Uses':<12}")
        print("-" * 80)
        
        # Sort by weighted average
        spell_stats_weighted.sort(key=lambda x: x['avg_damage_weighted'], reverse=True)
        
        for stat in spell_stats_weighted[:15]:  # Top 15 spells
            weaken_uses = stat.get('weaken_uses', 0)
            print(f"{stat['spell']:<20} {stat['element']:<12} {stat['avg_damage_weighted']:>10.1f} "
                  f"{weaken_uses:>12} {stat['times_used']:>12}")
        
        # Element damage analysis - UNWEIGHTED
        element_stats = self.analyze_damage_by_element(weighted=False)
        
        print("\n" + "=" * 80)
        print("DAMAGE BY ELEMENT - UNWEIGHTED")
        print("-" * 80)
        print(f"{'Element':<15} {'Avg Damage':<12} {'Total Damage':<12} {'Uses':<8} {'Weaken':<8} {'Spells'}")
        print("-" * 80)
        
        for stat in element_stats[:15]:
            print(f"{stat['element']:<15} {stat['avg_damage_per_use']:>10.1f} "
                  f"{stat['total_damage']:>12} {stat['times_used']:>8} {stat['weaken_uses']:>8} {stat['unique_damage_spells']:>8}")
        
        # Element damage analysis - WEIGHTED
        element_stats_weighted = self.analyze_damage_by_element(weighted=True)
        element_stats_weighted.sort(key=lambda x: x['avg_damage_weighted'], reverse=True)
        
        print("\n" + "=" * 80)
        print("DAMAGE BY ELEMENT - WEIGHTED (Weaken = 2x)")
        print("-" * 80)
        print(f"{'Element':<15} {'Avg Weighted':<12} {'Total Weighted':<14} {'Uses':<8} {'Weaken':<8}")
        print("-" * 80)
        
        for stat in element_stats_weighted[:15]:
            print(f"{stat['element']:<15} {stat['avg_damage_weighted']:>10.1f} "
                  f"{stat['total_damage_weighted']:>14} {stat['times_used']:>8} {stat['weaken_uses']:>8}")
        
        # Compare to theoretical values
        print("\n" + "=" * 80)
        print("THEORETICAL VS REAL-WORLD COMPARISON")
        print("-" * 80)
        
        # Load theoretical values (simplified comparison)
        theoretical_values = {
            'Blood': 3.2, 'Time': 2.8, 'Wood': 2.2, 'Ichor': 2.0,
            'Fire': 1.8, 'Twilight': 1.8, 'Wind': 1.5, 'Earth': 1.5,
            'Sunbeam': 1.5, 'Thunder': 1.5, 'Aster': 1.2, 'Venom': 1.2,
            'Water': 1.0, 'Metal': 1.0, 'Space': 1.0, 'Moonshine': 1.0,
            'Shadow': 1.0, 'Nectar': 1.0, 'Lightning': 1.0
        }
        
        print(f"{'Element':<15} {'Theoretical':<12} {'Real-World':<12} {'Difference':<12}")
        print("-" * 80)
        
        for stat in element_stats:
            element = stat['element']
            real_avg = stat['avg_damage_per_use']
            theoretical = theoretical_values.get(element, 0)
            diff = real_avg - theoretical
            
            print(f"{element:<15} {theoretical:>11.1f} {real_avg:>11.1f} {diff:>+11.1f}")


# Create global logger instance
game_logger = GameLogger()

if __name__ == "__main__":
    # Generate report if run directly
    logger = GameLogger()
    logger.generate_real_world_report()