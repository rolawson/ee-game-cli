#!/usr/bin/env python3
"""AI vs AI testing framework for Elemental Elephants"""

import sys
import time
from elephants_prototype import GameEngine
import json
from datetime import datetime

class AITestRunner:
    def __init__(self, num_games=10, ai1_difficulty='hard', ai2_difficulty='hard'):
        self.num_games = num_games
        self.ai1_difficulty = ai1_difficulty
        self.ai2_difficulty = ai2_difficulty
        self.results = {
            'total_games': 0,
            'ai1_wins': 0,
            'ai2_wins': 0,
            'draws': 0,
            'avg_game_length': 0,
            'total_rounds': 0,
            'games': []
        }
    
    def run_single_game(self, game_num):
        """Run a single AI vs AI game"""
        print(f"\n{'='*60}")
        print(f"Game {game_num + 1} of {self.num_games}")
        print(f"AI 1 ({self.ai1_difficulty}) vs AI 2 ({self.ai2_difficulty})")
        print('='*60)
        
        # Create game with two AI players
        player_names = [f"AI_{self.ai1_difficulty}", f"AI_{self.ai2_difficulty}"]
        engine = GameEngine(player_names, ai_difficulty=self.ai1_difficulty)
        
        # Override both players to be AI
        engine.gs.players[0].is_human = False
        engine.gs.players[1].is_human = False
        
        # Set AI strategies for both players
        if self.ai1_difficulty == 'easy':
            from ai.easy import EasyAI
            ai1 = EasyAI()
        elif self.ai1_difficulty == 'hard':
            from ai.hard import HardAI
            ai1 = HardAI()
        else:
            from ai.medium import MediumAI
            ai1 = MediumAI()
        
        if self.ai2_difficulty == 'easy':
            from ai.easy import EasyAI
            ai2 = EasyAI()
        elif self.ai2_difficulty == 'hard':
            from ai.hard import HardAI
            ai2 = HardAI()
        else:
            from ai.medium import MediumAI
            ai2 = MediumAI()
        
        ai1.engine = engine
        ai2.engine = engine
        engine.ai_strategies[0] = ai1
        engine.ai_strategies[1] = ai2
        
        # Run game with auto-play
        game_start = time.time()
        rounds_played = 0
        max_rounds = 10  # Safety limit
        
        try:
            # Auto-draft phase
            for draft_round in range(2):
                for player_idx in range(2):
                    player = engine.gs.players[player_idx]
                    ai = engine.ai_strategies[player_idx]
                    
                    # Simple draft logic - pick first available set
                    if engine.gs.main_deck:
                        chosen_set = engine.gs.main_deck.pop(0)
                        for card in chosen_set:
                            player.discard_pile.append(card)
                        print(f"{player.name} drafted {chosen_set[0].elephant} set")
            
            # Shuffle discard into hand
            for player in engine.gs.players:
                player.hand = player.discard_pile[:]
                player.discard_pile = []
            
            # Main game loop
            while not engine.gs.game_over and rounds_played < max_rounds:
                rounds_played += 1
                print(f"\nRound {rounds_played}")
                
                # Run clashes
                for clash in range(1, 5):
                    if engine.gs.game_over:
                        break
                    
                    engine.gs.clash_num = clash
                    print(f"  Clash {clash}...", end='', flush=True)
                    
                    # Each AI plays a card
                    for player_idx in range(2):
                        player = engine.gs.players[player_idx]
                        ai = engine.ai_strategies[player_idx]
                        
                        if player.hand:
                            card_idx = ai.choose_card_to_play(player, engine.gs)
                            if card_idx is not None:
                                card = player.hand.pop(card_idx)
                                from elephants_prototype import PlayedCard
                                played = PlayedCard(card, player)
                                played.status = 'revealed'
                                player.board[clash - 1].append(played)
                    
                    print(" done")
                
                # Check for game end
                alive_players = [p for p in engine.gs.players if p.trunks > 0]
                if len(alive_players) <= 1:
                    engine.gs.game_over = True
                
                engine.gs.round_num += 1
        
        except Exception as e:
            print(f"Error during game: {e}")
            import traceback
            traceback.print_exc()
        
        game_duration = time.time() - game_start
        
        # Determine winner
        alive_players = [p for p in engine.gs.players if p.trunks > 0]
        winner = None
        if len(alive_players) == 1:
            winner = alive_players[0].name
        elif len(alive_players) == 0:
            winner = "Draw"
        else:
            # Game hit round limit - winner is player with most trunks/health
            alive_players.sort(key=lambda p: (p.trunks, p.health), reverse=True)
            if alive_players[0].trunks == alive_players[1].trunks and \
               alive_players[0].health == alive_players[1].health:
                winner = "Draw"
            else:
                winner = alive_players[0].name
        
        # Record results
        game_result = {
            'game_num': game_num + 1,
            'winner': winner,
            'rounds': rounds_played,
            'duration': game_duration,
            'final_state': {
                'ai1': {
                    'trunks': engine.gs.players[0].trunks,
                    'health': engine.gs.players[0].health
                },
                'ai2': {
                    'trunks': engine.gs.players[1].trunks,
                    'health': engine.gs.players[1].health
                }
            }
        }
        
        print(f"\nGame {game_num + 1} Result: {winner} wins!")
        print(f"Duration: {game_duration:.1f}s, Rounds: {rounds_played}")
        
        return game_result
    
    def run_all_games(self):
        """Run all test games and compile results"""
        print(f"\nStarting AI Tournament: {self.num_games} games")
        print(f"AI 1: {self.ai1_difficulty} vs AI 2: {self.ai2_difficulty}")
        
        for i in range(self.num_games):
            result = self.run_single_game(i)
            self.results['games'].append(result)
            self.results['total_games'] += 1
            self.results['total_rounds'] += result['rounds']
            
            if result['winner'] == f"AI_{self.ai1_difficulty}":
                self.results['ai1_wins'] += 1
            elif result['winner'] == f"AI_{self.ai2_difficulty}":
                self.results['ai2_wins'] += 1
            else:
                self.results['draws'] += 1
        
        self.results['avg_game_length'] = self.results['total_rounds'] / self.results['total_games']
        
        # Print summary
        self.print_summary()
        
        # Save detailed results
        self.save_results()
    
    def print_summary(self):
        """Print tournament summary"""
        print("\n" + "="*60)
        print("TOURNAMENT SUMMARY")
        print("="*60)
        print(f"Total Games: {self.results['total_games']}")
        print(f"AI 1 ({self.ai1_difficulty}) Wins: {self.results['ai1_wins']} " + 
              f"({self.results['ai1_wins']/self.results['total_games']*100:.1f}%)")
        print(f"AI 2 ({self.ai2_difficulty}) Wins: {self.results['ai2_wins']} " +
              f"({self.results['ai2_wins']/self.results['total_games']*100:.1f}%)")
        print(f"Draws: {self.results['draws']}")
        print(f"Average Game Length: {self.results['avg_game_length']:.1f} rounds")
    
    def save_results(self):
        """Save detailed results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/ai_test_results_{self.ai1_difficulty}_vs_{self.ai2_difficulty}_{timestamp}.json"
        
        # Ensure directory exists
        import os
        os.makedirs("test_results", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: {filename}")


def main():
    """Main entry point for AI testing"""
    if len(sys.argv) > 1:
        num_games = int(sys.argv[1])
    else:
        num_games = 10
    
    if len(sys.argv) > 3:
        ai1_diff = sys.argv[2]
        ai2_diff = sys.argv[3]
    else:
        ai1_diff = 'hard'
        ai2_diff = 'hard'
    
    print("Elemental Elephants AI Test Suite")
    print("=================================")
    print(f"Running {num_games} games: {ai1_diff} vs {ai2_diff}")
    
    runner = AITestRunner(num_games, ai1_diff, ai2_diff)
    runner.run_all_games()


if __name__ == "__main__":
    main()