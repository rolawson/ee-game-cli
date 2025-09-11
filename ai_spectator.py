#!/usr/bin/env python3
"""Watch AI vs AI games play out automatically with visual display"""

import sys
import time
import threading
from queue import Queue, Empty

# Import game components
from elephants_prototype import GameEngine, GameState, PlayedCard
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
    print("Note: Claude AIs not available. Set ANTHROPIC_API_KEY to enable.")


class AutoPlayEngine(GameEngine):
    """Modified game engine that auto-advances but shows display"""
    
    def __init__(self, player_names, ai_difficulty='medium', delay=1.0, verbose=True):
        super().__init__(player_names, ai_difficulty)
        self.delay = delay  # Seconds between actions
        self.verbose = verbose
        self.auto_mode = True
        
    def _pause(self, message=""):
        """Override pause to just show and wait briefly"""
        if self.verbose:
            # Show the current game state
            prompt = f"{message} [Auto-advancing in {self.delay}s...]" if message else f"[Auto-advancing in {self.delay}s...]"
            self.display.draw(self.gs, prompt=prompt)
        
        # Wait for configured delay
        time.sleep(self.delay)
    
    def _prompt_for_choice(self, player, options, prompt_message, view_key='name'):
        """Override to make AI choices automatically"""
        if not player.is_human:
            # Let AI make the choice
            ai = self.ai_strategies.get(self.gs.players.index(player))
            if ai and hasattr(ai, 'make_choice'):
                # Show the prompt briefly
                if self.verbose:
                    self.display.draw(self.gs, self.gs.players.index(player), prompt=prompt_message)
                    time.sleep(self.delay * 0.5)  # Shorter delay for choices
                
                # AI makes choice
                choice = ai.make_choice(list(options.values()), player, self.gs, None)
                if choice in options.values():
                    # Find the key for this choice
                    for k, v in options.items():
                        if v == choice:
                            return k
                
                # Fallback to first option
                return list(options.keys())[0] if options else None
        
        # Should not reach here in AI vs AI
        return list(options.keys())[0] if options else None
    
    def _setup_game(self):
        """Override setup to handle drafting automatically"""
        self.gs.action_log.append("--- Game Setup ---")
        
        # Draft phase
        for draft_round in range(2):
            turn_order = [(self.gs.ringleader_index + i) % len(self.gs.players) 
                         for i in range(len(self.gs.players))]
            
            for player_index in turn_order:
                player = self.gs.players[player_index]
                
                if self.verbose:
                    self._pause(f"{player.name}'s turn to draft...")
                
                # Get available sets
                available_sets = [s for s in self.gs.main_deck if s]
                if not available_sets:
                    continue
                
                # Let AI choose
                ai = self.ai_strategies.get(player_index)
                if ai and hasattr(ai, 'choose_draft_set'):
                    chosen_set = ai.choose_draft_set(player, self.gs, available_sets)
                else:
                    # Fallback to first available
                    chosen_set = available_sets[0]
                self.gs.main_deck.remove(chosen_set)
                
                # Add to discard pile
                for card in chosen_set:
                    player.discard_pile.append(card)
                
                self.gs.action_log.append(f"{player.name} drafted the '{chosen_set[0].elephant}' ({chosen_set[0].element}) set.")
                
                if self.verbose:
                    self._pause()
        
        # Shuffle discard piles into hands
        for player in self.gs.players:
            player.hand = player.discard_pile[:]
            player.discard_pile = []
            self.gs.action_log.append(f"{player.name} shuffled their deck.")
        
        self._pause("Setup complete! Starting game...")


class SpectatorMode:
    """Watch AI games with configurable speed and verbosity"""
    
    def __init__(self, ai1_type='expert', ai2_type='expert', delay=1.0, verbose=True):
        self.ai1_type = ai1_type
        self.ai2_type = ai2_type
        self.delay = delay
        self.verbose = verbose
        
    def run_game(self):
        """Run a single spectator game"""
        print(f"\n{'='*60}")
        print(f"AI SPECTATOR MODE: {self.ai1_type.upper()} vs {self.ai2_type.upper()}")
        print(f"Delay: {self.delay}s | Verbose: {self.verbose}")
        print('='*60)
        
        # Create player names
        player_names = [f"{self.ai1_type.upper()}_AI", f"{self.ai2_type.upper()}_AI"]
        
        # Create auto-play engine
        engine = AutoPlayEngine(player_names, ai_difficulty=self.ai1_type, 
                               delay=self.delay, verbose=self.verbose)
        
        # Make both players AI
        engine.gs.players[0].is_human = False
        engine.gs.players[1].is_human = False
        
        # Set up AI strategies
        ai1 = self._create_ai(self.ai1_type)
        ai2 = self._create_ai(self.ai2_type)
        
        ai1.engine = engine
        ai2.engine = engine
        
        engine.ai_strategies[0] = ai1
        engine.ai_strategies[1] = ai2
        
        # Run the game
        try:
            engine.run_game()
        except Exception as e:
            print(f"\nGame ended with exception: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
        
        # Show final results
        print(f"\n{'='*60}")
        print("GAME OVER - Final Results:")
        print('='*60)
        
        for i, player in enumerate(engine.gs.players):
            status = "WINNER" if player.trunks > 0 else "ELIMINATED"
            print(f"{player.name}: {status} | Trunks: {player.trunks} | Health: {player.health}")
        
        return engine.gs
    
    def _create_ai(self, ai_type):
        """Create AI instance"""
        if ai_type == 'easy':
            return EasyAI()
        elif ai_type == 'medium':
            return MediumAI()
        elif ai_type == 'hard':
            return HardAI()
        elif ai_type == 'expert':
            return ExpertAI()
        elif ai_type == 'claude_savant' or ai_type == 'savant':
            if CLAUDE_AVAILABLE:
                return ClaudeSavantAI()
            else:
                print(f"Claude Savant not available, falling back to Expert AI")
                return ExpertAI()
        elif ai_type == 'claude_champion' or ai_type == 'champion':
            if CLAUDE_AVAILABLE:
                return ClaudeChampionAI()
            else:
                print(f"Claude Champion not available, falling back to Expert AI")
                return ExpertAI()
        else:
            return MediumAI()
    
    def run_series(self, num_games):
        """Run multiple games and track results"""
        results = {
            f'{self.ai1_type}_wins': 0,
            f'{self.ai2_type}_wins': 0,
            'draws': 0
        }
        
        for game_num in range(num_games):
            print(f"\n\nGAME {game_num + 1} of {num_games}")
            gs = self.run_game()
            
            # Determine winner
            alive = [p for p in gs.players if p.trunks > 0]
            if len(alive) == 1:
                if alive[0].name.startswith(self.ai1_type.upper()):
                    results[f'{self.ai1_type}_wins'] += 1
                else:
                    results[f'{self.ai2_type}_wins'] += 1
            else:
                results['draws'] += 1
            
            # Show running tally
            print(f"\nRunning Score: {self.ai1_type}: {results[f'{self.ai1_type}_wins']} | "
                  f"{self.ai2_type}: {results[f'{self.ai2_type}_wins']} | "
                  f"Draws: {results['draws']}")
            
            if game_num < num_games - 1:
                print("\nNext game starting in 3 seconds...")
                time.sleep(3)
        
        # Final summary
        print(f"\n\n{'='*60}")
        print("SERIES COMPLETE")
        print('='*60)
        print(f"{self.ai1_type.upper()} Wins: {results[f'{self.ai1_type}_wins']}")
        print(f"{self.ai2_type.upper()} Wins: {results[f'{self.ai2_type}_wins']}")
        print(f"Draws: {results['draws']}")


def main():
    # Parse arguments
    ai1 = sys.argv[1] if len(sys.argv) > 1 else 'expert'
    ai2 = sys.argv[2] if len(sys.argv) > 2 else 'expert'
    
    if len(sys.argv) > 3:
        try:
            delay = float(sys.argv[3])
        except:
            delay = 1.0
    else:
        delay = 1.0
    
    if len(sys.argv) > 4:
        num_games = int(sys.argv[4])
    else:
        num_games = 1
    
    print("AI Spectator Mode")
    print("=================")
    print(f"Matchup: {ai1} vs {ai2}")
    print(f"Delay between actions: {delay}s")
    print(f"Number of games: {num_games}")
    print("\nControls:")
    print("- Adjust delay for faster/slower playback")
    print("- Set delay to 0 for maximum speed")
    print("- Ctrl+C to stop")
    
    # Create and run spectator
    spectator = SpectatorMode(ai1, ai2, delay=delay, verbose=True)
    
    if num_games == 1:
        spectator.run_game()
    else:
        spectator.run_series(num_games)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python ai_spectator.py [ai1] [ai2] [delay] [num_games]")
        print("\nExample:")
        print("  python ai_spectator.py hard easy 0.5      # Fast game")
        print("  python ai_spectator.py hard medium 2.0 5  # 5 slower games")
        print("  python ai_spectator.py hard hard 0        # Maximum speed")
        print("\nAI types: easy, medium, hard, expert, savant, champion")
        print("Delay: seconds between actions (default 1.0)")
        if not CLAUDE_AVAILABLE:
            print("\nNote: Claude AIs require ANTHROPIC_API_KEY environment variable")
    else:
        main()