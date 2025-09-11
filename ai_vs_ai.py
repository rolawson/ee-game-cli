#!/usr/bin/env python3
"""Automated AI vs AI testing with proper game flow"""

import sys
import os
import time
import json
from datetime import datetime

# Suppress pygame import if not needed
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# Monkey patch input to automate AI responses
original_input = input
def mock_input(prompt=""):
    # Return empty string for all prompts (simulate Enter key)
    return ""

# Replace input before importing game
input = mock_input

from elephants_prototype import GameEngine, DEBUG_AI
from ai.easy import EasyAI
from ai.medium import MediumAI  
from ai.hard import HardAI
from ai.expert import ExpertAI

# Try to import Claude AIs if available
try:
    from ai.claude_savant import ClaudeSavantAI
    from ai.claude_champion import ClaudeChampionAI
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


class AIGameRunner:
    """Runs a single AI vs AI game with full automation"""
    
    def __init__(self, ai1_type='hard', ai2_type='hard', verbose=False):
        self.ai1_type = ai1_type
        self.ai2_type = ai2_type
        self.verbose = verbose
        self.game_log = []
        
    def create_ai(self, ai_type):
        """Create an AI instance of the specified type"""
        if ai_type == 'easy':
            return EasyAI()
        elif ai_type == 'medium':
            return MediumAI()
        elif ai_type == 'hard':
            return HardAI()
        elif ai_type == 'expert':
            return ExpertAI()
        elif ai_type in ['claude_savant', 'savant'] and CLAUDE_AVAILABLE:
            return ClaudeSavantAI()
        elif ai_type in ['claude_champion', 'champion'] and CLAUDE_AVAILABLE:
            return ClaudeChampionAI()
        else:
            if ai_type.startswith('claude') and not CLAUDE_AVAILABLE:
                print(f"Claude AI not available, falling back to Expert AI")
                return ExpertAI()
            return MediumAI()
    
    def run_game(self):
        """Run a complete AI vs AI game"""
        # Create game engine
        player_names = [f"AI_{self.ai1_type}_1", f"AI_{self.ai2_type}_2"]
        engine = GameEngine(player_names, ai_difficulty=self.ai1_type)
        
        # Make both players AI
        engine.gs.players[0].is_human = False
        engine.gs.players[1].is_human = False
        
        # Set up AI for both players
        ai1 = self.create_ai(self.ai1_type)
        ai2 = self.create_ai(self.ai2_type)
        
        ai1.engine = engine
        ai2.engine = engine
        
        engine.ai_strategies[0] = ai1
        engine.ai_strategies[1] = ai2
        
        # Override the pause method to prevent input blocking
        original_pause = engine._pause
        engine._pause = lambda msg="": None  # No-op pause
        
        # Capture game state
        game_start = time.time()
        rounds_played = 0
        
        try:
            # Run the game - the engine handles everything
            engine.run_game()
            
            rounds_played = engine.gs.round_num
            
        except Exception as e:
            if self.verbose:
                print(f"Game ended with exception: {e}")
                import traceback
                traceback.print_exc()
        
        game_duration = time.time() - game_start
        
        # Determine winner
        alive_players = [(i, p) for i, p in enumerate(engine.gs.players) if p.trunks > 0]
        
        winner_info = {
            'winner': None,
            'winner_idx': None,
            'method': 'elimination'
        }
        
        if len(alive_players) == 1:
            winner_info['winner'] = alive_players[0][1].name
            winner_info['winner_idx'] = alive_players[0][0]
        elif len(alive_players) == 0:
            winner_info['winner'] = 'Draw'
            winner_info['method'] = 'mutual_elimination'
        else:
            # Multiple players alive - tiebreak by trunks then health
            alive_players.sort(key=lambda x: (x[1].trunks, x[1].health), reverse=True)
            if alive_players[0][1].trunks == alive_players[1][1].trunks and \
               alive_players[0][1].health == alive_players[1][1].health:
                winner_info['winner'] = 'Draw'
                winner_info['method'] = 'tiebreak_draw'
            else:
                winner_info['winner'] = alive_players[0][1].name
                winner_info['winner_idx'] = alive_players[0][0]
                winner_info['method'] = 'tiebreak'
        
        # Compile results
        result = {
            'winner': winner_info['winner'],
            'winner_idx': winner_info['winner_idx'],
            'win_method': winner_info['method'],
            'rounds': rounds_played,
            'duration': game_duration,
            'ai1': {
                'type': self.ai1_type,
                'final_trunks': engine.gs.players[0].trunks,
                'final_health': engine.gs.players[0].health,
                'cards_played': len([s for clash in engine.gs.players[0].board for s in clash])
            },
            'ai2': {
                'type': self.ai2_type,
                'final_trunks': engine.gs.players[1].trunks,
                'final_health': engine.gs.players[1].health,
                'cards_played': len([s for clash in engine.gs.players[1].board for s in clash])
            }
        }
        
        return result


class AITournament:
    """Run multiple AI vs AI games and analyze results"""
    
    def __init__(self, num_games=10):
        self.num_games = num_games
        self.results = []
        
    def run_matchup(self, ai1_type, ai2_type, games_per_matchup=None):
        """Run games between two AI types"""
        if games_per_matchup is None:
            games_per_matchup = self.num_games
            
        print(f"\nRunning {games_per_matchup} games: {ai1_type} vs {ai2_type}")
        print("="*60)
        
        matchup_results = {
            'ai1_type': ai1_type,
            'ai2_type': ai2_type,
            'games': [],
            'ai1_wins': 0,
            'ai2_wins': 0,
            'draws': 0
        }
        
        for i in range(games_per_matchup):
            print(f"Game {i+1}/{games_per_matchup}...", end='', flush=True)
            
            runner = AIGameRunner(ai1_type, ai2_type)
            result = runner.run_game()
            
            matchup_results['games'].append(result)
            
            if result['winner_idx'] == 0:
                matchup_results['ai1_wins'] += 1
                print(f" {ai1_type} wins!")
            elif result['winner_idx'] == 1:
                matchup_results['ai2_wins'] += 1
                print(f" {ai2_type} wins!")
            else:
                matchup_results['draws'] += 1
                print(" Draw!")
        
        # Calculate statistics
        total = games_per_matchup
        matchup_results['ai1_win_rate'] = matchup_results['ai1_wins'] / total * 100
        matchup_results['ai2_win_rate'] = matchup_results['ai2_wins'] / total * 100
        matchup_results['draw_rate'] = matchup_results['draws'] / total * 100
        matchup_results['avg_rounds'] = sum(g['rounds'] for g in matchup_results['games']) / total
        matchup_results['avg_duration'] = sum(g['duration'] for g in matchup_results['games']) / total
        
        self.results.append(matchup_results)
        return matchup_results
    
    def run_all_matchups(self):
        """Run all possible AI matchups"""
        ai_types = ['easy', 'medium', 'hard']
        
        for ai1 in ai_types:
            for ai2 in ai_types:
                self.run_matchup(ai1, ai2)
    
    def print_summary(self):
        """Print tournament summary"""
        print("\n" + "="*80)
        print("AI TOURNAMENT SUMMARY")
        print("="*80)
        
        for matchup in self.results:
            print(f"\n{matchup['ai1_type'].upper()} vs {matchup['ai2_type'].upper()}")
            print("-"*40)
            print(f"{matchup['ai1_type']} wins: {matchup['ai1_wins']} ({matchup['ai1_win_rate']:.1f}%)")
            print(f"{matchup['ai2_type']} wins: {matchup['ai2_wins']} ({matchup['ai2_win_rate']:.1f}%)")
            print(f"Draws: {matchup['draws']} ({matchup['draw_rate']:.1f}%)")
            print(f"Avg game length: {matchup['avg_rounds']:.1f} rounds")
            print(f"Avg duration: {matchup['avg_duration']:.1f} seconds")
    
    def save_results(self, filename=None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results/ai_tournament_results_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs("test_results", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        return filename


def main():
    """Main entry point"""
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'tournament':
            # Run full tournament
            games = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            tournament = AITournament(games)
            tournament.run_all_matchups()
            tournament.print_summary()
            tournament.save_results()
        else:
            # Run specific matchup
            ai1 = sys.argv[1] if len(sys.argv) > 1 else 'hard'
            ai2 = sys.argv[2] if len(sys.argv) > 2 else 'hard'
            games = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            
            tournament = AITournament(games)
            tournament.run_matchup(ai1, ai2)
            tournament.print_summary()
            tournament.save_results()
    else:
        print("Usage:")
        print("  python ai_vs_ai.py tournament [games_per_matchup]")
        print("  python ai_vs_ai.py [ai1_type] [ai2_type] [num_games]")
        print("\nAI types: easy, medium, hard")
        print("\nExample:")
        print("  python ai_vs_ai.py hard medium 20")
        print("  python ai_vs_ai.py tournament 5")


if __name__ == "__main__":
    # Restore original input when done
    import atexit
    atexit.register(lambda: globals().update({'input': original_input}))
    
    main()