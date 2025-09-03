#!/usr/bin/env python3
"""
AI Tournament - Run full games between all AI types and calculate win rates
Uses the complete game engine (not simplified) but runs without display for speed
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elephants_prototype import GameEngine, GameState, RoundOverException
from ai import EasyAI, MediumAI, HardAI, ExpertAI


class SilentGameEngine(GameEngine):
    """Game engine that runs silently for maximum speed"""
    
    def __init__(self, player_names, ai_difficulties):
        """Initialize with specific AI difficulties for each player"""
        # Call parent constructor with first AI's difficulty
        super().__init__(player_names, ai_difficulties[0])
        
        # Override display with a mock
        self.display = type('MockDisplay', (), {
            'draw': lambda *args, **kwargs: None,
            '_get_spell_type_icons': lambda self, card: ''
        })()
        
        # Set up AI strategies for both players
        self.ai_strategies = {}
        for i, difficulty in enumerate(ai_difficulties):
            if difficulty == 'easy':
                ai = EasyAI()
            elif difficulty == 'medium':
                ai = MediumAI()
            elif difficulty == 'hard':
                ai = HardAI()
            elif difficulty == 'expert':
                ai = ExpertAI()
            else:
                ai = MediumAI()  # Default
            
            ai.engine = self
            self.ai_strategies[i] = ai
        
        # Mark both players as AI
        for player in self.gs.players:
            player.is_human = False
    
    def _pause(self, message=""):
        """Override to skip all pauses"""
        pass
    
    def display_draw(self, gs, pov_player_index=0, prompt=""):
        """Override to skip display"""
        pass
    
    def _prompt_for_choice(self, player, options, prompt_message, view_key='name'):
        """This should never be called for AI players"""
        # Get AI for this player
        player_idx = self.gs.players.index(player)
        ai = self.ai_strategies.get(player_idx)
        
        if ai:
            # For drafting
            if isinstance(list(options.values())[0], list):
                # This is a draft choice
                choice = 1  # Default to first option
                if hasattr(ai, 'choose_draft_set'):
                    chosen_set = ai.choose_draft_set(player, self.gs, list(options.values()))
                    # Find which key corresponds to this set
                    for key, value in options.items():
                        if value == chosen_set:
                            return key
                return choice
            else:
                # Regular choice - return first valid option
                return list(options.keys())[0] if options else None
        
        return list(options.keys())[0] if options else None


class AITournament:
    """Run tournaments between all AI types"""
    
    def __init__(self, games_per_matchup=50):
        self.games_per_matchup = games_per_matchup
        self.results = defaultdict(lambda: defaultdict(int))
        self.game_lengths = defaultdict(list)
        self.element_usage = defaultdict(lambda: defaultdict(int))
        self.start_time = None
        
    def run_tournament(self):
        """Run all matchups between AI types"""
        ai_types = ['easy', 'medium', 'hard', 'expert']
        
        print(f"{'='*80}")
        print(f"AI TOURNAMENT - {self.games_per_matchup} games per matchup")
        print(f"{'='*80}\n")
        
        self.start_time = time.time()
        total_matchups = len(ai_types) * len(ai_types)
        matchup_count = 0
        
        # Test each AI against each other (including mirror matches)
        for ai1 in ai_types:
            for ai2 in ai_types:
                matchup_count += 1
                print(f"\n[{matchup_count}/{total_matchups}] {ai1.upper()} vs {ai2.upper()}")
                print("-" * 40)
                
                wins = {ai1: 0, ai2: 0, 'draws': 0}
                
                for game_num in range(self.games_per_matchup):
                    # Alternate who goes first
                    if game_num % 2 == 0:
                        player_names = [f"{ai1.upper()}_AI_1", f"{ai2.upper()}_AI_2"]
                        ai_order = [ai1, ai2]
                    else:
                        player_names = [f"{ai2.upper()}_AI_1", f"{ai1.upper()}_AI_2"]
                        ai_order = [ai2, ai1]
                    
                    # Run game
                    try:
                        winner_ai = self._run_single_game(player_names, ai_order)
                        if winner_ai:
                            wins[winner_ai] += 1
                        else:
                            wins['draws'] += 1
                    except Exception as e:
                        print(f"\n  Error in game {game_num + 1}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        continue
                    
                    # Progress update
                    if (game_num + 1) % 10 == 0:
                        elapsed = time.time() - self.start_time
                        print(f"  Progress: {game_num + 1}/{self.games_per_matchup} games "
                              f"({wins[ai1]}-{wins[ai2]}) [{elapsed:.1f}s]")
                
                # Store results
                win_rate = wins[ai1] / self.games_per_matchup if self.games_per_matchup > 0 else 0
                self.results[ai1][ai2] = win_rate
                
                print(f"  Final: {ai1} won {wins[ai1]}/{self.games_per_matchup} games ({win_rate:.1%})")
        
        # Generate report
        self._generate_report()
    
    def _run_single_game(self, player_names, ai_difficulties):
        """Run a single game and return winner AI type"""
        engine = SilentGameEngine(player_names, ai_difficulties)
        
        try:
            # Run setup
            engine._setup_game()
            
            # Run game rounds
            while len([p for p in engine.gs.players if p.trunks > 0]) > 1 and not engine.gs.game_over:
                try:
                    engine._run_round()
                    if not engine.gs.game_over:
                        engine.gs.round_num += 1
                except RoundOverException:
                    if not engine.gs.game_over:
                        engine.gs.round_num += 1
            
            # Track game length
            self.game_lengths[f"{ai_difficulties[0]}_vs_{ai_difficulties[1]}"].append(engine.gs.round_num - 1)
            
            # Determine winner
            winner = next((p for p in engine.gs.players if p.trunks > 0), None)
            if winner:
                winner_idx = engine.gs.players.index(winner)
                winner_ai = ai_difficulties[winner_idx]
                
                # Track element usage
                for i, player in enumerate(engine.gs.players):
                    ai_type = ai_difficulties[i]
                    elements = set()
                    for card in player.hand + player.discard_pile:
                        elements.add(card.element)
                    for element in elements:
                        self.element_usage[ai_type][element] += 1
                
                return winner_ai
            
            return None  # Draw
            
        except Exception as e:
            # Re-raise the error so we can see what's happening
            raise
    
    def _generate_report(self):
        """Generate comprehensive tournament report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"ai_tournament_report_{timestamp}.txt"
        
        ai_types = ['easy', 'medium', 'hard', 'expert']
        
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("AI TOURNAMENT REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Games per matchup: {self.games_per_matchup}\n")
            f.write(f"Total time: {time.time() - self.start_time:.1f} seconds\n")
            f.write("="*80 + "\n\n")
            
            # Win rate matrix
            f.write("-"*60 + "\n")
            f.write("WIN RATE MATRIX\n")
            f.write("-"*60 + "\n")
            f.write("         ")
            for ai in ai_types:
                f.write(f"{ai:>12}")
            f.write("\n")
            
            for ai1 in ai_types:
                f.write(f"{ai1:>8} ")
                for ai2 in ai_types:
                    win_rate = self.results[ai1].get(ai2, 0)
                    f.write(f"{win_rate:>11.1%} ")
                f.write("\n")
            
            # Overall win rates (excluding mirror matches)
            f.write("\n" + "-"*60 + "\n")
            f.write("OVERALL WIN RATES (excluding mirror matches)\n")
            f.write("-"*60 + "\n")
            
            overall_stats = []
            for ai in ai_types:
                total_wins = 0
                total_games = 0
                
                for opponent in ai_types:
                    if ai != opponent:
                        total_wins += self.results[ai][opponent] * self.games_per_matchup
                        total_games += self.games_per_matchup
                
                if total_games > 0:
                    overall_win_rate = total_wins / total_games
                    overall_stats.append((ai, overall_win_rate, int(total_wins), total_games))
            
            # Sort by win rate
            overall_stats.sort(key=lambda x: x[1], reverse=True)
            
            for rank, (ai, win_rate, wins, games) in enumerate(overall_stats, 1):
                f.write(f"{rank}. {ai.upper():>8}: {win_rate:>6.1%} ({wins}/{games} games)\n")
            
            # Average game lengths
            f.write("\n" + "-"*60 + "\n")
            f.write("AVERAGE GAME LENGTH\n")
            f.write("-"*60 + "\n")
            
            for matchup, lengths in sorted(self.game_lengths.items()):
                if lengths:
                    avg_length = sum(lengths) / len(lengths)
                    f.write(f"{matchup:>25}: {avg_length:>5.1f} rounds\n")
            
            # Element preferences
            f.write("\n" + "-"*60 + "\n")
            f.write("TOP 5 ELEMENT PREFERENCES BY AI\n")
            f.write("-"*60 + "\n")
            
            for ai in ai_types:
                f.write(f"\n{ai.upper()}:\n")
                element_counts = self.element_usage[ai]
                total = sum(element_counts.values())
                
                if total > 0:
                    sorted_elements = sorted(element_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]
                    for element, count in sorted_elements:
                        percentage = count / total * 100
                        f.write(f"  {element:>12}: {percentage:>5.1f}%\n")
            
            # Summary
            f.write("\n" + "="*80 + "\n")
            f.write("SUMMARY\n")
            f.write("="*80 + "\n")
            
            if overall_stats:
                best = overall_stats[0]
                worst = overall_stats[-1]
                f.write(f"Best AI:  {best[0].upper()} ({best[1]:.1%} win rate)\n")
                f.write(f"Worst AI: {worst[0].upper()} ({worst[1]:.1%} win rate)\n")
                
                # Performance gap
                gap = best[1] - worst[1]
                f.write(f"Performance gap: {gap:.1%}\n")
            
            f.write("\n" + "="*80 + "\n")
        
        print(f"\n{'='*80}")
        print("TOURNAMENT COMPLETE!")
        print(f"{'='*80}")
        print(f"\nReport saved to: {report_file}")
        
        # Also save raw data as JSON
        json_file = f"ai_tournament_data_{timestamp}.json"
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'games_per_matchup': self.games_per_matchup,
            'total_time_seconds': time.time() - self.start_time,
            'win_rates': dict(self.results),
            'game_lengths': dict(self.game_lengths),
            'element_usage': dict(self.element_usage),
            'rankings': [(ai, rate) for ai, rate, _, _ in overall_stats]
        }
        
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"Raw data saved to: {json_file}")
        
        # Print quick summary
        print(f"\nQUICK SUMMARY:")
        for rank, (ai, win_rate, _, _) in enumerate(overall_stats, 1):
            print(f"  {rank}. {ai.upper()}: {win_rate:.1%}")


def main():
    """Run the tournament"""
    games = 20  # Default
    
    if len(sys.argv) > 1:
        try:
            games = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [games_per_matchup]")
            print(f"Example: {sys.argv[0]} 50")
            sys.exit(1)
    
    print(f"Running AI Tournament with {games} games per matchup...")
    print("This will run the FULL game engine (all rules included)")
    print("Estimated time: ~{:.1f} minutes\n".format(games * 16 * 0.5 / 60))
    
    tournament = AITournament(games_per_matchup=games)
    tournament.run_tournament()


if __name__ == "__main__":
    main()