#!/usr/bin/env python3
"""Fully automated AI vs AI battles - no input required"""

import sys
import json
import os
from datetime import datetime
from collections import defaultdict

# Create a modified game engine that skips all pauses
class AutoGameEngine:
    def __init__(self):
        # Import here to avoid circular imports
        from elephants_prototype import GameState, DashboardDisplay, ConditionChecker, ActionHandler
        from ai.easy import EasyAI
        from ai.medium import MediumAI
        from ai.hard import HardAI
        from ai.expert import ExpertAI
        
        self.EasyAI = EasyAI
        self.MediumAI = MediumAI
        self.HardAI = HardAI
        self.ExpertAI = ExpertAI
        self.GameState = GameState
        self.DashboardDisplay = DashboardDisplay
        self.ConditionChecker = ConditionChecker
        self.ActionHandler = ActionHandler
    
    def create_game(self, ai1_type='hard', ai2_type='hard'):
        """Create a game with two AI players"""
        player_names = [f"AI_{ai1_type}_1", f"AI_{ai2_type}_2"]
        
        # Create game components
        gs = self.GameState(player_names)
        display = self.DashboardDisplay()
        condition_checker = self.ConditionChecker()
        
        # Make both players AI
        gs.players[0].is_human = False
        gs.players[1].is_human = False
        
        # Create AI instances
        ai1 = self._create_ai(ai1_type)
        ai2 = self._create_ai(ai2_type)
        
        # Create a mock engine object with minimal interface
        mock_engine = type('MockEngine', (), {
            'gs': gs,
            'display': display,
            'condition_checker': condition_checker,
            'ai_decision_logs': [],
            '_pause': lambda self, msg="": None,  # No-op pause
            '_handle_trunk_loss': self._mock_handle_trunk_loss
        })()
        
        # Set up action handler
        action_handler = self.ActionHandler(mock_engine)
        mock_engine.action_handler = action_handler
        
        # Link AIs to engine
        ai1.engine = mock_engine
        ai2.engine = mock_engine
        
        return gs, ai1, ai2, mock_engine
    
    def _create_ai(self, ai_type):
        """Create AI instance by type"""
        if ai_type == 'easy':
            return self.EasyAI()
        elif ai_type == 'hard':
            return self.HardAI()
        elif ai_type == 'expert':
            return self.ExpertAI()
        else:
            return self.MediumAI()
    
    def _mock_handle_trunk_loss(self, player):
        """Simple trunk loss handler"""
        if player.trunks > 0:
            player.lose_trunk()
            return 'continue'
        return 'game_over'
    
    def run_automated_game(self, ai1_type='hard', ai2_type='hard', max_rounds=10):
        """Run a fully automated game"""
        gs, ai1, ai2, engine = self.create_game(ai1_type, ai2_type)
        ais = [ai1, ai2]
        
        # Draft phase - each AI picks 2 sets
        for draft_round in range(2):
            for player_idx in range(2):
                if gs.main_deck:
                    # Simple draft - take first available
                    chosen_set = gs.main_deck.pop(0)
                    player = gs.players[player_idx]
                    for card in chosen_set:
                        player.discard_pile.append(card)
        
        # Move cards to hand
        for player in gs.players:
            player.hand = player.discard_pile[:]
            player.discard_pile = []
        
        # Game loop
        rounds_played = 0
        while not gs.game_over and rounds_played < max_rounds:
            rounds_played += 1
            gs.round_num = rounds_played
            
            # Run each clash
            for clash in range(1, 5):
                gs.clash_num = clash
                
                # Prepare phase - each AI plays a card
                for player_idx in range(2):
                    player = gs.players[player_idx]
                    ai = ais[player_idx]
                    
                    if player.hand:
                        card_idx = ai.choose_card_to_play(player, gs)
                        if card_idx is not None and card_idx < len(player.hand):
                            card = player.hand.pop(card_idx)
                            from elephants_prototype import PlayedCard
                            played_card = PlayedCard(card, player)
                            player.board[clash - 1].append(played_card)
                
                # Cast phase - reveal all cards
                for player in gs.players:
                    for spell in player.board[clash - 1]:
                        if spell.status == 'prepared':
                            spell.status = 'revealed'
                
                # Simple resolution - just mark spells as resolved
                # In a real game this would process effects
                for player in gs.players:
                    for spell in player.board[clash - 1]:
                        if spell.status == 'revealed':
                            spell.has_resolved = True
                
                # Simulate some damage for testing
                if clash % 2 == 0:  # Even clashes
                    # Simple combat simulation
                    for i, player in enumerate(gs.players):
                        other = gs.players[1 - i]
                        attack_spells = [s for s in player.board[clash - 1] 
                                       if s.status == 'revealed' and 'attack' in s.card.types]
                        if attack_spells and other.health > 0:
                            damage = min(len(attack_spells), other.health)
                            other.health -= damage
                            if other.health <= 0:
                                if other.trunks > 0:
                                    other.lose_trunk()
                                else:
                                    gs.game_over = True
                                    break
            
            # Check end conditions
            alive_players = [p for p in gs.players if p.trunks > 0]
            if len(alive_players) <= 1:
                gs.game_over = True
        
        # Determine winner
        alive_players = [p for p in gs.players if p.trunks > 0]
        if len(alive_players) == 1:
            winner_idx = gs.players.index(alive_players[0])
            winner = alive_players[0].name
        elif len(alive_players) == 0:
            winner_idx = None
            winner = "Draw"
        else:
            # Tiebreak by trunks then health
            best_player = max(alive_players, key=lambda p: (p.trunks, p.health))
            winner_idx = gs.players.index(best_player)
            winner = best_player.name
        
        return {
            'winner': winner,
            'winner_idx': winner_idx,
            'rounds': rounds_played,
            'final_state': [
                {
                    'name': p.name,
                    'trunks': p.trunks,
                    'health': p.health,
                    'cards_played': sum(len(clash) for clash in p.board)
                }
                for p in gs.players
            ]
        }


class AIBattleRunner:
    """Run AI battles and collect statistics"""
    
    def __init__(self):
        self.engine = AutoGameEngine()
        self.results = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})
    
    def run_battle(self, ai1_type, ai2_type):
        """Run a single battle"""
        result = self.engine.run_automated_game(ai1_type, ai2_type)
        
        # Update statistics
        if result['winner_idx'] == 0:
            self.results[f"{ai1_type}_vs_{ai2_type}"]['wins'] += 1
            self.results[ai1_type]['total_wins'] = self.results[ai1_type].get('total_wins', 0) + 1
            self.results[ai2_type]['total_losses'] = self.results[ai2_type].get('total_losses', 0) + 1
        elif result['winner_idx'] == 1:
            self.results[f"{ai1_type}_vs_{ai2_type}"]['losses'] += 1
            self.results[ai2_type]['total_wins'] = self.results[ai2_type].get('total_wins', 0) + 1
            self.results[ai1_type]['total_losses'] = self.results[ai1_type].get('total_losses', 0) + 1
        else:
            self.results[f"{ai1_type}_vs_{ai2_type}"]['draws'] += 1
            self.results[ai1_type]['total_draws'] = self.results[ai1_type].get('total_draws', 0) + 1
            self.results[ai2_type]['total_draws'] = self.results[ai2_type].get('total_draws', 0) + 1
        
        return result
    
    def run_tournament(self, games_per_matchup=10):
        """Run a complete tournament"""
        ai_types = ['easy', 'medium', 'hard', 'expert']
        total_games = 0
        
        print("AI Battle Tournament")
        print("=" * 60)
        
        for ai1 in ai_types:
            for ai2 in ai_types:
                print(f"\n{ai1.upper()} vs {ai2.upper()} ({games_per_matchup} games)")
                print("-" * 40)
                
                wins = 0
                for game in range(games_per_matchup):
                    result = self.run_battle(ai1, ai2)
                    if result['winner_idx'] == 0:
                        wins += 1
                    print(f"Game {game + 1}: {result['winner']} wins", end="\r")
                    total_games += 1
                
                print(f"Final: {ai1} won {wins}/{games_per_matchup} games")
        
        print("\n" + "=" * 60)
        print("TOURNAMENT RESULTS")
        print("=" * 60)
        
        # Overall performance
        for ai_type in ai_types:
            total_games_played = (self.results[ai_type].get('total_wins', 0) + 
                                self.results[ai_type].get('total_losses', 0) + 
                                self.results[ai_type].get('total_draws', 0))
            
            if total_games_played > 0:
                win_rate = self.results[ai_type].get('total_wins', 0) / total_games_played * 100
                print(f"\n{ai_type.upper()} AI:")
                print(f"  Total Wins: {self.results[ai_type].get('total_wins', 0)}")
                print(f"  Total Losses: {self.results[ai_type].get('total_losses', 0)}")
                print(f"  Total Draws: {self.results[ai_type].get('total_draws', 0)}")
                print(f"  Win Rate: {win_rate:.1f}%")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/ai_battle_results_{timestamp}.json"
        # Ensure directory exists
        os.makedirs("test_results", exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(dict(self.results), f, indent=2)
        print(f"\nDetailed results saved to: {filename}")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            # Quick test
            runner = AIBattleRunner()
            result = runner.run_battle('hard', 'easy')
            print(f"Result: {result['winner']} wins in {result['rounds']} rounds")
        else:
            games = int(sys.argv[1])
            runner = AIBattleRunner()
            runner.run_tournament(games)
    else:
        print("Usage:")
        print("  python ai_battle.py quick        # Run one test game")
        print("  python ai_battle.py 10           # Run tournament with 10 games per matchup")
        runner = AIBattleRunner()
        runner.run_tournament(5)


if __name__ == "__main__":
    main()