#!/usr/bin/env python3
"""
Unified Analytics System for Elemental Elephants
Combines game generation, analysis, and recommendations
"""

import json
import os
import sys
import argparse
from datetime import datetime
from collections import defaultdict
import random
from typing import Dict, List, Tuple, Any
from contextlib import redirect_stdout
import io

# Import game components
from elephants_prototype import GameEngine, GameState, DashboardDisplay
from ai import EasyAI, MediumAI, HardAI
from game_logger import game_logger


class SilentGameEngine(GameEngine):
    """Game engine that doesn't pause for AI games"""
    
    def __init__(self, player_names, ai_difficulty='hard'):
        """Initialize without any prompts"""
        # Initialize game state directly without prompting
        self.gs = GameState(player_names)
        self.ai_strategies = {}
        self.display = DashboardDisplay()
        self.ai_difficulty = ai_difficulty
        self.condition_checker = None  # Will be set properly below
        self.action_handler = None  # Will be set properly below
        self.ai_decision_logs = []
        
        # Import these here to avoid circular imports
        from elephants_prototype import ConditionChecker, ActionHandler
        self.condition_checker = ConditionChecker()
        self.action_handler = ActionHandler(self)
        
        # Set both players as AI
        for i, player in enumerate(self.gs.players):
            player.is_human = False
        
        # Keep backward compatibility - ai_player is used as default
        self.ai_player = None
    
    def _pause(self, message=""):
        """Override to do nothing for AI games"""
        pass
    
    def _prompt_for_choice(self, player, options, prompt_message, view_key='name'):
        """Override to prevent input() calls for AI players"""
        if player.is_human:
            # This shouldn't happen in AI-only games
            return None
        return super()._prompt_for_choice(player, options, prompt_message, view_key)


class UnifiedAnalytics:
    def __init__(self):
        self.game_logs = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_lines = []
        
    def run_games(self, num_games: int, ai1_type: str = 'hard', ai2_type: str = 'hard', silent: bool = True) -> None:
        """Run specified number of games and collect analytics"""
        print(f"\n{'='*60}")
        print(f"Running {num_games} games: {ai1_type} vs {ai2_type}")
        print(f"{'='*60}")
        
        for i in range(num_games):
            if not silent and i % 10 == 0:
                print(f"Progress: {i}/{num_games} games completed...")
            
            # Clear any existing game data
            game_logger.reset()
            
            # Run a game
            # Make sure player names are unique even if same AI type
            if ai1_type == ai2_type:
                player_names = [f"{ai1_type.upper()}_AI_1", f"{ai2_type.upper()}_AI_2"]
            else:
                player_names = [f"{ai1_type.upper()}_AI", f"{ai2_type.upper()}_AI"]
            engine = SilentGameEngine(player_names, ai_difficulty=ai1_type)
            
            # Set both players as AI
            engine.gs.players[0].is_human = False
            engine.gs.players[1].is_human = False
            
            # Set AI strategies for both players
            # Player 1
            if ai1_type == 'easy':
                engine.ai_strategies[0] = EasyAI()
            elif ai1_type == 'medium':
                engine.ai_strategies[0] = MediumAI()
            else:
                engine.ai_strategies[0] = HardAI()
            
            if hasattr(engine.ai_strategies[0], 'engine'):
                engine.ai_strategies[0].engine = engine
                
            # Player 2
            if ai2_type == 'easy':
                engine.ai_strategies[1] = EasyAI()
            elif ai2_type == 'medium':
                engine.ai_strategies[1] = MediumAI()
            else:
                engine.ai_strategies[1] = HardAI()
            
            if hasattr(engine.ai_strategies[1], 'engine'):
                engine.ai_strategies[1].engine = engine
            
            # Run the game (suppress output if silent)
            try:
                if silent:
                    # Redirect stdout to suppress game output
                    f = io.StringIO()
                    with redirect_stdout(f):
                        engine.run_game()
                else:
                    engine.run_game()
            except Exception as e:
                if not silent:
                    print(f"Error in game {i+1}: {e}")
                continue
            
            # Collect the game log
            if game_logger.current_game:
                self.game_logs.append(game_logger.current_game)
        
        print(f"\nCompleted {len(self.game_logs)} games successfully!")
    
    def run_tournament(self, games_per_matchup: int = 20) -> None:
        """Run a full tournament between all AI types"""
        ai_types = ['easy', 'medium', 'hard']
        
        print(f"\n{'='*60}")
        print(f"TOURNAMENT MODE: {games_per_matchup} games per matchup")
        print(f"{'='*60}")
        
        for ai1 in ai_types:
            for ai2 in ai_types:
                print(f"\n{ai1.upper()} vs {ai2.upper()}:")
                self.run_games(games_per_matchup, ai1, ai2)
    
    def analyze_games(self) -> Dict[str, Any]:
        """Comprehensive analysis of all game logs"""
        if not self.game_logs:
            print("No game logs to analyze!")
            return {}
        
        # Save game logs for detailed analysis
        with open('game_logs.json', 'w') as f:
            json.dump(self.game_logs, f)
        
        analysis = {
            'total_games': len(self.game_logs),
            'element_stats': self._analyze_elements(),
            'spell_stats': self._analyze_spells(),
            'game_stats': self._analyze_game_metrics(),
            'action_stats': self._analyze_actions(),
            'conjury_stats': self._analyze_conjuries(),
            'theme_stats': self._analyze_themes(),
            'playstyle_stats': self._analyze_playstyles(),
            'trunk_survival': self._analyze_trunk_survival(),
            'trunk_destroyers': self._analyze_trunk_destroyers(),
            'response_effectiveness': self._analyze_response_spells(),
            'balance_issues': self._detect_balance_issues()
        }
        
        return analysis
    
    def _analyze_elements(self) -> Dict[str, Any]:
        """Analyze element performance and win rates"""
        element_wins = defaultdict(int)
        element_games = defaultdict(int)
        element_damage = defaultdict(list)
        element_healing = defaultdict(list)
        element_selections = defaultdict(int)  # Track how often each element is selected
        
        for game in self.game_logs:
            winner = game.get('winner')
            
            # Track all elements that participated in this game
            for player, elements in game['player_elements'].items():
                for element in elements:
                    element_games[element] += 1
                    element_selections[element] += 1  # Count each selection
                    # Only count wins if this player won
                    if player == winner:
                        element_wins[element] += 1
            
            # Track damage/healing by element
            for event in game.get('events', []):
                if event['type'] == 'damage_dealt':
                    element = event.get('element', 'Unknown')
                    damage = event.get('amount', 0)
                    if element and damage > 0:
                        element_damage[element].append(damage)
                elif event['type'] == 'healing_done':
                    element = event.get('element', 'Unknown')
                    heal = event.get('amount', 0)
                    if element and heal > 0:
                        element_healing[element].append(heal)
        
        # Calculate win rates
        element_win_rates = {}
        for element in element_games:
            if element_games[element] > 0:
                # Win rate is wins / total games played with that element
                element_win_rates[element] = element_wins[element] / element_games[element]
        
        # Calculate category win rates
        category_win_rates = self._calculate_category_win_rates(element_win_rates)
        
        return {
            'win_rates': element_win_rates,
            'category_win_rates': category_win_rates,
            'total_games': element_games,
            'wins': element_wins,
            'selections': dict(element_selections),
            'avg_damage': {e: sum(dmg)/len(dmg) if dmg else 0 for e, dmg in element_damage.items()},
            'avg_healing': {e: sum(heal)/len(heal) if heal else 0 for e, heal in element_healing.items()}
        }
    
    def _calculate_category_win_rates(self, element_win_rates: Dict[str, float]) -> Dict[str, float]:
        """Calculate average win rates by element category"""
        import json
        import os
        
        # Load element categories
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            categories_path = os.path.join(current_dir, 'element_categories.json')
            with open(categories_path, 'r') as f:
                categories_data = json.load(f)
        except:
            return {}
        
        category_win_rates = {}
        
        for category_name, category_info in categories_data.get('categories', {}).items():
            elements = category_info.get('elements', [])
            
            # Get win rates for elements in this category
            category_rates = []
            for element in elements:
                if element in element_win_rates:
                    category_rates.append(element_win_rates[element])
            
            # Calculate average win rate for the category
            if category_rates:
                category_win_rates[category_name] = sum(category_rates) / len(category_rates)
            else:
                category_win_rates[category_name] = 0.0
        
        return category_win_rates
    
    def _analyze_spells(self) -> Dict[str, Any]:
        """Analyze individual spell performance"""
        spell_stats = defaultdict(lambda: {
            'times_played': 0,
            'total_damage': 0,
            'total_damage_weighted': 0,
            'total_healing': 0,
            'total_healing_weighted': 0,
            'total_weaken': 0,
            'total_bolster': 0,
            'times_advanced': 0,
            'times_cancelled': 0,
            'element': None
        })
        
        for game in self.game_logs:
            for event in game.get('events', []):
                if event['type'] == 'spell_played':
                    spell_name = event.get('spell', event.get('spell_name', 'Unknown'))
                    spell_stats[spell_name]['times_played'] += 1
                    spell_stats[spell_name]['element'] = event.get('element', 'Unknown')
                
                elif event['type'] == 'damage_dealt':
                    spell_name = event.get('spell', event.get('spell_name', 'Unknown'))
                    if spell_name:
                        spell_stats[spell_name]['total_damage'] += event.get('amount', 0)
                        spell_stats[spell_name]['total_damage_weighted'] += event.get('amount', 0)
                
                elif event['type'] == 'weaken_dealt':
                    spell_name = event.get('spell', event.get('spell_name', 'Unknown'))
                    if spell_name:
                        spell_stats[spell_name]['total_weaken'] += event.get('amount', 0)
                        # Weighted: weaken counts as 2x damage
                        spell_stats[spell_name]['total_damage_weighted'] += event.get('amount', 0) * 2
                
                elif event['type'] == 'healing_done':
                    spell_name = event.get('spell', event.get('spell_name', 'Unknown'))
                    if spell_name:
                        spell_stats[spell_name]['total_healing'] += event.get('amount', 0)
                        spell_stats[spell_name]['total_healing_weighted'] += event.get('amount', 0)
                
                elif event['type'] == 'bolster_done':
                    spell_name = event.get('spell', event.get('spell_name', 'Unknown'))
                    if spell_name:
                        spell_stats[spell_name]['total_bolster'] += event.get('amount', 0)
                        # Weighted: bolster counts as 2x healing
                        spell_stats[spell_name]['total_healing_weighted'] += event.get('amount', 0) * 2
                
                elif event['type'] == 'spell_advanced':
                    # Need to track which spell advanced
                    for played_event in game.get('events', []):
                        if played_event['type'] == 'spell_played' and played_event.get('clash') == event.get('clash'):
                            if played_event.get('player') == event.get('player'):
                                spell_stats[played_event['spell_name']]['times_advanced'] += 1
                                break
                
                elif event['type'] == 'spell_cancelled':
                    # Track cancellations
                    pass  # TODO: Need to track which spell was cancelled
        
        # Calculate averages
        spell_analysis = {}
        for spell, stats in spell_stats.items():
            if stats['times_played'] > 0:
                spell_analysis[spell] = {
                    'element': stats['element'],
                    'times_played': stats['times_played'],
                    'avg_damage': stats['total_damage'] / stats['times_played'],
                    'avg_damage_weighted': stats['total_damage_weighted'] / stats['times_played'],
                    'max_damage': stats['total_damage'],  # TODO: Track actual max
                    'avg_healing': stats['total_healing'] / stats['times_played'],
                    'avg_healing_weighted': stats['total_healing_weighted'] / stats['times_played'],
                    'avg_weaken': stats['total_weaken'] / stats['times_played'],
                    'avg_bolster': stats['total_bolster'] / stats['times_played'],
                    'advance_rate': stats['times_advanced'] / stats['times_played']
                }
        
        return spell_analysis
    
    def _analyze_game_metrics(self) -> Dict[str, Any]:
        """Analyze overall game metrics"""
        total_rounds = []
        game_lengths = []
        
        for game in self.game_logs:
            total_rounds.append(game.get('total_rounds', 0))
            # Calculate game length in terms of clashes
            game_lengths.append(game.get('total_rounds', 0) * 4)  # 4 clashes per round
        
        return {
            'avg_rounds': sum(total_rounds) / len(total_rounds) if total_rounds else 0,
            'min_rounds': min(total_rounds) if total_rounds else 0,
            'max_rounds': max(total_rounds) if total_rounds else 0,
            'avg_clashes': sum(game_lengths) / len(game_lengths) if game_lengths else 0
        }
    
    def _analyze_actions(self) -> Dict[str, Any]:
        """Analyze action usage (advance, recall, cancel, move, discard, reveal)"""
        action_counts = defaultdict(int)
        
        for game in self.game_logs:
            for event in game.get('events', []):
                event_type = event['type']
                if event_type == 'spell_advanced':
                    action_counts['advance'] += 1
                elif event_type == 'spell_recalled':
                    action_counts['recall'] += 1
                elif event_type == 'spell_cancelled':
                    action_counts['cancel'] += 1
                elif event_type == 'spell_moved':
                    action_counts['move'] += 1
                elif event_type == 'spell_discarded':
                    action_counts['discard'] += 1
                elif event_type == 'spell_revealed':
                    action_counts['reveal'] += 1
                # Count damage/healing as actions too
                elif event_type == 'damage_dealt':
                    action_counts['damage'] += 1
                elif event_type == 'healing_done':
                    action_counts['heal'] += 1
        
        total_actions = sum(action_counts.values())
        action_rates = {}
        if total_actions > 0:
            for action, count in action_counts.items():
                action_rates[action] = count / total_actions
        
        return {
            'counts': dict(action_counts),
            'rates': action_rates,
            'total': total_actions
        }
    
    def _analyze_conjuries(self) -> Dict[str, Any]:
        """Analyze conjury performance"""
        conjury_played = 0
        conjury_cancelled = 0
        conjuries_by_spell = defaultdict(lambda: {'played': 0, 'cancelled': 0})
        
        # First pass: identify all conjury spells
        conjury_spell_names = set()
        for game in self.game_logs:
            for event in game.get('events', []):
                if event['type'] == 'spell_played' and event.get('is_conjury', False):
                    spell_name = event.get('spell', event.get('spell_name'))
                    conjury_spell_names.add(spell_name)
        
        # Second pass: count plays and cancellations
        for game in self.game_logs:
            for event in game.get('events', []):
                if event['type'] == 'spell_played':
                    spell_name = event.get('spell', event.get('spell_name'))
                    if spell_name in conjury_spell_names:
                        conjury_played += 1
                        conjuries_by_spell[spell_name]['played'] += 1
                
                elif event['type'] == 'spell_cancelled':
                    # The cancelled spell is in the 'spell' field
                    cancelled_spell = event.get('spell')
                    if cancelled_spell in conjury_spell_names:
                        conjury_cancelled += 1
                        conjuries_by_spell[cancelled_spell]['cancelled'] += 1
        
        # Calculate cancellation rates per spell
        spell_cancel_rates = {}
        for spell, stats in conjuries_by_spell.items():
            if stats['played'] > 0:
                spell_cancel_rates[spell] = stats['cancelled'] / stats['played']
        
        return {
            'total_played': conjury_played,
            'total_cancelled': conjury_cancelled,
            'cancellation_rate': conjury_cancelled / conjury_played if conjury_played > 0 else 0,
            'by_spell': dict(conjuries_by_spell),
            'spell_cancel_rates': spell_cancel_rates
        }
    
    def _analyze_themes(self) -> Dict[str, Any]:
        """Analyze elephant theme effectiveness"""
        # Map elephants to themes based on HOWTOPLAY.md
        elephant_themes = {
            'Elé Phlambé': 'offense',
            'Spout Snout': 'defense',
            'Dumblo': 'mobility',
            'Columnfoot': 'control',
            'Trunxie': 'growth',
            'General Guardjendra': 'protection',
            'Tick-tock Tusker': 'speed',
            'Elephantus Infinitum': 'manipulation',
            'Gold Dust': 'retaliation',
            'Luna Doze': 'recuperation',
            'Twinkle Tyke': 'momentum',
            'Dawnotheridusk': 'choice',
            'The Matriarch': 'preservation',
            'Godesha': 'siphon',
            'Toxic Tai': 'affliction',
            'Onyx Oliphant': 'mimicry',
            'Beelzebabar': 'sacrifice',
            'Electrophantine': 'disruption',
            'Rolling Rolo': 'disruption'
        }
        
        theme_performance = defaultdict(lambda: {'games': 0, 'wins': 0})
        
        # TODO: Track elephant usage and success rates
        
        return theme_performance
    
    def _analyze_playstyles(self) -> Dict[str, Any]:
        """Analyze aggressive vs analytical playstyles"""
        playstyle_indicators = {
            'aggressive': 0,
            'defensive': 0,
            'balanced': 0
        }
        
        for game in self.game_logs:
            # Count attack vs remedy spell usage
            attack_count = 0
            remedy_count = 0
            
            for event in game.get('events', []):
                if event['type'] == 'spell_played':
                    # TODO: Need spell type information in events
                    pass
            
            # Classify based on ratios
            # TODO: Implement classification logic
        
        return playstyle_indicators
    
    def _analyze_trunk_survival(self) -> Dict[str, Any]:
        """Analyze how long trunks survive"""
        trunk_lifetimes = []
        trunk_losses_by_player = defaultdict(list)
        
        for game in self.game_logs:
            for event in game.get('events', []):
                if event['type'] == 'trunk_lost':
                    player = event['player']
                    lifetime = event.get('trunk_lifetime_rounds', 0)
                    if lifetime > 0:
                        trunk_lifetimes.append(lifetime)
                        trunk_losses_by_player[player].append(lifetime)
        
        # Calculate statistics
        avg_lifetime = sum(trunk_lifetimes) / len(trunk_lifetimes) if trunk_lifetimes else 0
        min_lifetime = min(trunk_lifetimes) if trunk_lifetimes else 0
        max_lifetime = max(trunk_lifetimes) if trunk_lifetimes else 0
        
        # Calculate per-player averages
        player_avg_lifetimes = {}
        for player, lifetimes in trunk_losses_by_player.items():
            if lifetimes:
                player_avg_lifetimes[player] = sum(lifetimes) / len(lifetimes)
        
        return {
            'avg_trunk_lifetime_rounds': avg_lifetime,
            'min_trunk_lifetime': min_lifetime,
            'max_trunk_lifetime': max_lifetime,
            'total_trunk_losses': len(trunk_lifetimes),
            'player_averages': player_avg_lifetimes
        }
    
    def _analyze_trunk_destroyers(self) -> Dict[str, Any]:
        """Analyze which spells are most likely to destroy trunks"""
        trunk_destroyers = defaultdict(int)
        damage_before_trunk_loss = defaultdict(list)
        
        for game in self.game_logs:
            recent_damage_events = []  # Track recent damage events
            
            for event in game.get('events', []):
                # Track damage events
                if event['type'] == 'damage_dealt':
                    recent_damage_events.append({
                        'spell': event.get('spell', event.get('spell_name', 'Unknown')),
                        'target': event.get('target_player'),  # Use target_player field
                        'amount': event.get('amount', 0),
                        'timestamp': event.get('timestamp')
                    })
                    # Keep only last 10 damage events
                    recent_damage_events = recent_damage_events[-10:]
                
                # When a trunk is lost, attribute it to recent damage
                elif event['type'] == 'trunk_lost':
                    lost_player = event.get('player')
                    
                    # Find damage that killed this player
                    for damage_event in reversed(recent_damage_events):
                        if damage_event['target'] == lost_player:
                            spell_name = damage_event['spell']
                            trunk_destroyers[spell_name] += 1
                            damage_before_trunk_loss[spell_name].append(damage_event['amount'])
                            break  # Only credit the killing blow
        
        # Calculate statistics
        trunk_destroyer_stats = {}
        for spell, count in trunk_destroyers.items():
            avg_damage = sum(damage_before_trunk_loss[spell]) / len(damage_before_trunk_loss[spell]) if damage_before_trunk_loss[spell] else 0
            trunk_destroyer_stats[spell] = {
                'trunk_kills': count,
                'avg_damage_for_kill': avg_damage
            }
        
        return trunk_destroyer_stats
    
    def _analyze_response_spells(self) -> Dict[str, Any]:
        """Analyze how often response spell conditions are met using logged condition evaluations"""
        response_spell_stats = defaultdict(lambda: {'played': 0, 'condition_met': 0})
        
        # Identify response spells from spell data
        import json
        import os
        response_spells = set()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            spells_path = os.path.join(current_dir, 'spells.json')
            with open(spells_path, 'r') as f:
                spell_data = json.load(f)
                for spell in spell_data:
                    if 'response' in spell.get('spell_types', []):
                        response_spells.add(spell.get('card_name'))
        except:
            pass
        
        # Track response spell effectiveness using the logged condition evaluations
        for game in self.game_logs:
            response_spell_evaluations = defaultdict(lambda: {'evaluated': 0, 'met': 0})
            
            for event in game.get('events', []):
                if event['type'] == 'response_condition_evaluated':
                    # Count every evaluation - each clash is a separate opportunity
                    spell_name = event.get('spell')
                    condition_met = event.get('condition_met', False)
                    
                    if spell_name in response_spells:
                        response_spell_evaluations[spell_name]['evaluated'] += 1
                        if condition_met:
                            response_spell_evaluations[spell_name]['met'] += 1
            
            # Add the evaluations to our stats
            for spell_name, eval_stats in response_spell_evaluations.items():
                response_spell_stats[spell_name]['played'] += eval_stats['evaluated']
                response_spell_stats[spell_name]['condition_met'] += eval_stats['met']
        
        # Calculate effectiveness rates
        response_effectiveness = {}
        for spell, stats in response_spell_stats.items():
            if stats['played'] > 0:
                effectiveness = stats['condition_met'] / stats['played']
                response_effectiveness[spell] = {
                    'times_played': stats['played'],
                    'times_triggered': stats['condition_met'],
                    'effectiveness_rate': effectiveness
                }
        
        return response_effectiveness
    
    def _detect_balance_issues(self) -> List[str]:
        """Detect potential balance issues"""
        issues = []
        
        # Analyze element win rates
        element_stats = self._analyze_elements()
        for element, win_rate in element_stats['win_rates'].items():
            if win_rate < 0.35:
                issues.append(f"{element} appears underpowered (win rate: {win_rate:.1%})")
            elif win_rate > 0.65:
                issues.append(f"{element} appears overpowered (win rate: {win_rate:.1%})")
        
        # Analyze spell usage
        spell_stats = self._analyze_spells()
        total_plays = sum(s['times_played'] for s in spell_stats.values())
        avg_plays = total_plays / len(spell_stats) if spell_stats else 0
        
        for spell, stats in spell_stats.items():
            if stats['times_played'] < avg_plays * 0.2:
                issues.append(f"{spell} is rarely used ({stats['times_played']} times)")
            
            # Check damage/healing outliers
            if stats['avg_damage'] > 3:
                issues.append(f"{spell} deals very high damage ({stats['avg_damage']:.1f} avg)")
        
        return issues
    
    def generate_report(self, analysis: Dict[str, Any]) -> None:
        """Generate comprehensive report"""
        self.report_lines = []
        
        # Header
        self._add_line("=" * 80)
        self._add_line("ELEMENTAL ELEPHANTS ANALYTICS REPORT")
        self._add_line(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"Total Games Analyzed: {analysis['total_games']}")
        self._add_line("=" * 80)
        
        # Game Metrics
        self._add_section("GAME METRICS")
        game_stats = analysis['game_stats']
        self._add_line(f"Average Game Length: {game_stats['avg_rounds']:.1f} rounds ({game_stats['avg_clashes']:.1f} clashes)")
        self._add_line(f"Shortest Game: {game_stats['min_rounds']} rounds")
        self._add_line(f"Longest Game: {game_stats['max_rounds']} rounds")
        
        # Element Performance
        self._add_section("ELEMENT PERFORMANCE")
        element_stats = analysis['element_stats']
        
        # Sort by win rate
        sorted_elements = sorted(element_stats['win_rates'].items(), key=lambda x: x[1], reverse=True)
        
        self._add_line("Win Rates by Element:")
        for element, win_rate in sorted_elements:
            games = element_stats['total_games'].get(element, 0)
            wins = element_stats['wins'].get(element, 0)
            avg_dmg = element_stats['avg_damage'].get(element, 0)
            self._add_line(f"  {element:12} - {win_rate:6.1%} ({wins:3}/{games:3} games) | Avg Damage: {avg_dmg:.1f}")
        
        # Add category win rates
        if 'category_win_rates' in element_stats:
            self._add_line("\nWin Rates by Category:")
            sorted_categories = sorted(element_stats['category_win_rates'].items(), key=lambda x: x[1], reverse=True)
            for category, win_rate in sorted_categories:
                self._add_line(f"  {category.capitalize():12} - {win_rate:6.1%}")
        
        # Add element selection frequency
        self._add_line("\nElement Selection Frequency:")
        total_selections = sum(element_stats['selections'].values())
        sorted_selections = sorted(element_stats['selections'].items(), key=lambda x: x[1], reverse=True)
        for element, count in sorted_selections[:15]:  # Top 15 most selected
            pct = (count / total_selections * 100) if total_selections > 0 else 0
            self._add_line(f"  {element:12} - {count:3} times ({pct:4.1f}%)")
        
        # Spell Performance
        self._add_section("TOP SPELLS BY CATEGORY")
        spell_stats = analysis['spell_stats']
        
        # Top damage dealers
        damage_spells = [(s, stats) for s, stats in spell_stats.items() if stats['avg_damage'] > 0]
        damage_spells.sort(key=lambda x: x[1]['avg_damage'], reverse=True)
        
        self._add_line("\nHighest Average Damage (Unweighted):")
        for spell, stats in damage_spells[:10]:
            self._add_line(f"  {spell:20} ({stats['element']:10}) - {stats['avg_damage']:5.2f} damage")
        
        self._add_line("\nHighest Average Damage (Weighted - Weaken 2x):")
        weighted_damage = sorted(damage_spells, key=lambda x: x[1]['avg_damage_weighted'], reverse=True)
        for spell, stats in weighted_damage[:10]:
            self._add_line(f"  {spell:20} ({stats['element']:10}) - {stats['avg_damage_weighted']:5.2f} weighted")
        
        # Top healers
        healing_spells = [(s, stats) for s, stats in spell_stats.items() if stats['avg_healing'] > 0]
        healing_spells.sort(key=lambda x: x[1]['avg_healing'], reverse=True)
        
        self._add_line("\nHighest Average Healing (Unweighted):")
        for spell, stats in healing_spells[:10]:
            self._add_line(f"  {spell:20} ({stats['element']:10}) - {stats['avg_healing']:5.2f} healing")
        
        # Action Usage
        self._add_section("ACTION USAGE")
        action_stats = analysis['action_stats']
        self._add_line("Action Frequencies:")
        for action, count in action_stats['counts'].items():
            rate = action_stats['rates'].get(action, 0)
            self._add_line(f"  {action:10} - {count:5} times ({rate:5.1%})")
        
        # Trunk Survival
        self._add_section("TRUNK SURVIVAL ANALYSIS")
        trunk_stats = analysis['trunk_survival']
        self._add_line(f"Average Trunk Lifetime: {trunk_stats['avg_trunk_lifetime_rounds']:.1f} rounds")
        self._add_line(f"Shortest Trunk Lifetime: {trunk_stats['min_trunk_lifetime']} rounds")
        self._add_line(f"Longest Trunk Lifetime: {trunk_stats['max_trunk_lifetime']} rounds")
        self._add_line(f"Total Trunk Losses: {trunk_stats['total_trunk_losses']}")
        
        # Trunk Destroyers
        self._add_section("TRUNK DESTROYER SPELLS")
        trunk_destroyers = analysis.get('trunk_destroyers', {})
        if trunk_destroyers:
            # Sort by trunk kills
            sorted_destroyers = sorted(trunk_destroyers.items(), 
                                     key=lambda x: x[1]['trunk_kills'], reverse=True)
            self._add_line("Spells Most Likely to End Rounds:")
            for spell, stats in sorted_destroyers[:10]:  # Top 10
                self._add_line(f"  {spell:20} - {stats['trunk_kills']:3} trunk kills "
                             f"(avg {stats['avg_damage_for_kill']:.1f} damage)")
        else:
            self._add_line("No trunk-destroying spells detected.")
        
        # Response Spell Effectiveness
        self._add_section("RESPONSE SPELL EFFECTIVENESS")
        response_stats = analysis.get('response_effectiveness', {})
        if response_stats:
            self._add_line("Response Spell Condition Success Rate (per clash evaluation):")
            sorted_responses = sorted(response_stats.items(), 
                                    key=lambda x: x[1]['effectiveness_rate'], reverse=True)
            for spell, stats in sorted_responses:
                self._add_line(f"  {spell:20} - {stats['effectiveness_rate']:5.1%} success rate "
                             f"({stats['times_triggered']}/{stats['times_played']} evaluations)")
        else:
            self._add_line("No response spells analyzed.")
        
        # Conjury Analysis
        self._add_section("CONJURY ANALYSIS")
        conjury_stats = analysis['conjury_stats']
        if conjury_stats['total_played'] > 0:
            self._add_line(f"Total Conjuries Played: {conjury_stats['total_played']}")
            self._add_line(f"Total Conjuries Cancelled: {conjury_stats['total_cancelled']}")
            self._add_line(f"Overall Cancellation Rate: {conjury_stats['cancellation_rate']:.1%}")
            
            if conjury_stats['by_spell']:
                self._add_line("\nConjuries by Spell:")
                for spell, stats in sorted(conjury_stats['by_spell'].items()):
                    cancel_rate = conjury_stats['spell_cancel_rates'].get(spell, 0)
                    self._add_line(f"  {spell:20} - {stats['played']:3} played, {stats['cancelled']:3} cancelled ({cancel_rate:.1%})")
        else:
            self._add_line("No conjuries were played in the analyzed games.")
        
        # Balance Issues
        self._add_section("BALANCE RECOMMENDATIONS")
        issues = analysis['balance_issues']
        if issues:
            for issue in issues:
                self._add_line(f"⚠️  {issue}")
        else:
            self._add_line("No significant balance issues detected.")
        
        # Footer
        self._add_line("\n" + "=" * 80)
        self._add_line("END OF REPORT")
    
    def _add_line(self, text: str = "") -> None:
        """Add a line to the report"""
        self.report_lines.append(text)
    
    def _add_section(self, title: str) -> None:
        """Add a section header"""
        self._add_line()
        self._add_line("-" * 60)
        self._add_line(title)
        self._add_line("-" * 60)
    
    def save_report(self) -> str:
        """Save report to file"""
        filename = f"analytics_report_{self.timestamp}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(self.report_lines))
        return filename
    
    def save_win_rates(self, analysis: Dict[str, Any]) -> None:
        """Save element win rates to a file for AI to use"""
        element_stats = analysis.get('element_stats', {})
        
        win_rate_data = {
            'last_updated': datetime.now().isoformat(),
            'total_games': analysis.get('total_games', 0),
            'win_rates': dict(element_stats.get('win_rates', {})),
            'category_win_rates': dict(element_stats.get('category_win_rates', {})),
            'selection_rates': {},
            'games_per_element': dict(element_stats.get('total_games', {}))
        }
        
        # Calculate selection rates
        total_selections = sum(element_stats.get('selections', {}).values())
        if total_selections > 0:
            for element, count in element_stats.get('selections', {}).items():
                win_rate_data['selection_rates'][element] = count / total_selections
        
        # Save to file
        with open('element_win_rates.json', 'w') as f:
            json.dump(win_rate_data, f, indent=2)
        
        print(f"\nWin rate data saved to element_win_rates.json")
    
    def display_report(self) -> None:
        """Display report to console"""
        for line in self.report_lines:
            print(line)


def main():
    parser = argparse.ArgumentParser(description='Elemental Elephants Analytics System')
    parser.add_argument('mode', nargs='?', default='100', 
                       help='Number of games or mode (quick/tournament)')
    parser.add_argument('--games', type=int, help='Games per matchup for tournament')
    parser.add_argument('--ai1', default='hard', choices=['easy', 'medium', 'hard'])
    parser.add_argument('--ai2', default='hard', choices=['easy', 'medium', 'hard'])
    parser.add_argument('--silent', action='store_true', help='Suppress progress messages')
    
    args = parser.parse_args()
    
    analytics = UnifiedAnalytics()
    
    # Determine mode
    if args.mode == 'quick':
        analytics.run_games(10, args.ai1, args.ai2, args.silent)
    elif args.mode == 'tournament':
        games_per_matchup = args.games or 20
        analytics.run_tournament(games_per_matchup)
    else:
        try:
            num_games = int(args.mode)
            analytics.run_games(num_games, args.ai1, args.ai2, args.silent)
        except ValueError:
            print(f"Invalid mode: {args.mode}")
            sys.exit(1)
    
    # Analyze and report
    print("\nAnalyzing games...")
    analysis = analytics.analyze_games()
    
    print("Generating report...")
    analytics.generate_report(analysis)
    
    # Display and save
    analytics.display_report()
    filename = analytics.save_report()
    
    # Save win rate data for AI
    analytics.save_win_rates(analysis)
    
    print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    main()