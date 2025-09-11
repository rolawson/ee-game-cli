"""Base class for LLM-powered AI players"""

import json
import asyncio
from abc import abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import BaseAI

# Import Colors from main game
try:
    from elephants_prototype import Colors
except ImportError:
    # Fallback if Colors not available
    class Colors:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        GREY = '\033[90m'
        ENDC = '\033[0m'
        WARNING = '\033[93m'
        YELLOW = '\033[93m'
        FAIL = '\033[91m'
        BLUEGREEN = '\033[38;5;49m'  # Custom blue-green for Savant


class LLMBaseAI(BaseAI):
    """Base class for all LLM-powered AI implementations"""
    
    def __init__(self):
        super().__init__()
        self.communication_enabled = True
        self.response_cache = {}  # Cache for similar game states
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.fallback_ai = None  # Will be set to a traditional AI for fallback
        self.timeout_seconds = 10  # API timeout
        self.last_communication = ""  # Store last message for display
        self.round_history = []  # Track plays for end-of-round analysis
        self.player_name = None  # Track which player this AI controls
        
    def _select_card(self, player, gs, valid_indices):
        """Select a card using LLM reasoning"""
        # Track player name for this AI
        if not self.player_name:
            self.player_name = player.name
        
        # Set current player for board state filtering
        self.current_player = player
            
        # Build game state context
        context = self._build_game_context(player, gs, valid_indices)
        
        # Show loading indicator (without blocking input since AI is processing)
        if self.engine and hasattr(self.engine, 'display'):
            # Find POV player index
            pov_index = next((i for i, p in enumerate(gs.players) if p.is_human), 0)
            self.engine.display.draw(gs, pov_player_index=pov_index, 
                                   prompt=f"{Colors.GREY}{player.name} is contemplating their next move...{Colors.ENDC}")
        
        # Get LLM decision
        try:
            # Run async operation in thread pool
            future = self.executor.submit(self._get_llm_decision_sync, context, "select_card")
            decision = future.result(timeout=self.timeout_seconds)
            
            # Parse decision
            if decision and isinstance(decision, dict):
                chosen_index = decision.get("card_index")
                reasoning = decision.get("reasoning", "")
                message = decision.get("message", "")
                
                # We don't need per-move messages anymore since we do end-of-round analysis
                
                # Log reasoning with color based on AI type
                if reasoning and self.engine and hasattr(self.engine, 'ai_decision_logs'):
                    # Check for Champion or Savant in player name (case insensitive)
                    player_name_upper = self.player_name.upper()
                    if 'CHAMPION' in player_name_upper:
                        color = Colors.YELLOW
                        emoji = "🏆 "
                    elif 'SAVANT' in player_name_upper:
                        color = Colors.BLUEGREEN  # Blue-green for Savant
                        emoji = "🧬 "
                    else:
                        color = Colors.BLUE  # Use blue instead of grey
                        emoji = ""
                    
                    self.engine.ai_decision_logs.append(
                        f"{color}{emoji}[{self.player_name}] {reasoning}{Colors.ENDC}"
                    )
                
                # Validate choice
                if chosen_index in valid_indices:
                    # Track the play for end-of-round analysis
                    self.round_history.append({
                        'round': gs.round_num,
                        'clash': gs.clash_num,
                        'card': player.hand[chosen_index].name,
                        'reasoning': reasoning
                    })
                    return chosen_index
        
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"{Colors.WARNING}[{self.player_name}] Error: {str(e)}, falling back{Colors.ENDC}"
                )
        
        # Fallback to traditional AI
        return self._fallback_decision(player, gs, valid_indices)
    
    def make_choice(self, valid_options, caster, gs, current_card):
        """Make a choice using LLM reasoning"""
        # Build choice context
        context = self._build_choice_context(valid_options, caster, gs, current_card)
        
        try:
            # Get LLM decision
            future = self.executor.submit(self._get_llm_decision_sync, context, "make_choice")
            decision = future.result(timeout=self.timeout_seconds)
            
            # Parse decision
            if decision and isinstance(decision, dict):
                choice_index = decision.get("choice_index", 0)
                message = decision.get("message", "")
                
                # Don't display messages during gameplay
                # Messages should only appear at end of round
                
                # Validate choice
                if 0 <= choice_index < len(valid_options):
                    return valid_options[choice_index]
        
        except Exception:
            pass
        
        # Fallback to traditional AI or first option
        if self.fallback_ai and hasattr(self.fallback_ai, 'make_choice'):
            return self.fallback_ai.make_choice(valid_options, caster, gs, current_card)
        
        # Ultimate fallback - choose first option
        return valid_options[0] if valid_options else None
    
    def choose_draft_set(self, player, gs, available_sets):
        """Choose a spell set during drafting using LLM reasoning"""
        # Set player name if not already set (important for drafting)
        if not self.player_name and player:
            self.player_name = player.name
            
        # Build draft context
        context = self._build_draft_context(player, gs, available_sets)
        
        try:
            # Get LLM decision
            future = self.executor.submit(self._get_llm_decision_sync, context, "draft")
            decision = future.result(timeout=self.timeout_seconds)
            
            # Parse decision
            if decision and isinstance(decision, dict):
                set_index = decision.get("set_index", 0)
                message = decision.get("message", "")
                reasoning = decision.get("reasoning", "")
                
                # Add draft commentary to action log with appropriate color
                if (message or reasoning) and hasattr(gs, 'action_log'):
                    # Use player.name for identification since it's more reliable during drafting
                    player_name_upper = player.name.upper()
                    if 'CHAMPION' in player_name_upper:
                        color = Colors.YELLOW
                        emoji = "🏆 "
                    elif 'SAVANT' in player_name_upper:
                        color = Colors.BLUEGREEN  # Blue-green for Savant
                        emoji = "🧬 "
                    else:
                        color = Colors.BLUE
                        emoji = ""
                    
                    comment = message if message else reasoning
                    gs.action_log.append(f"{color}{emoji}[{player.name}] Draft analysis: {comment}{Colors.ENDC}")
                
                # Validate choice
                if 0 <= set_index < len(available_sets):
                    return available_sets[set_index]
        
        except Exception:
            pass
        
        # Fallback to traditional AI or random choice
        if self.fallback_ai and hasattr(self.fallback_ai, 'choose_draft_set'):
            return self.fallback_ai.choose_draft_set(player, gs, available_sets)
        
        # Ultimate fallback - choose randomly
        import random
        return random.choice(available_sets) if available_sets else None
    
    def _build_game_context(self, player, gs, valid_indices) -> Dict[str, Any]:
        """Build a structured context for the LLM"""
        # Get valid cards
        valid_cards = [player.hand[i] for i in valid_indices]
        
        # Build player state
        player_state = {
            "name": player.name,
            "health": player.health,
            "max_health": player.max_health,
            "hand_size": len(player.hand),
            "trunks": player.trunks
        }
        
        # Build enemy states
        enemies = []
        for p in gs.players:
            if p != player:
                enemies.append({
                    "name": p.name,
                    "health": p.health,
                    "max_health": p.max_health,
                    "hand_size": len(p.hand),
                    "trunks": p.trunks
                })
        
        # Build board state
        board_state = self._summarize_board_state(gs)
        
        # Build card options
        card_options = []
        for i, idx in enumerate(valid_indices):
            card = player.hand[idx]
            card_options.append({
                "index": idx,
                "name": card.name,
                "element": card.element,
                "types": card.types,
                "priority": card.priority,
                "is_conjury": card.is_conjury,
                "description": self._summarize_card_effects(card)
            })
        
        # Get recent action log entries (filter out hidden info)
        recent_actions = self._get_filtered_action_log(gs, player)
        
        return {
            "round": gs.round_num,
            "clash": gs.clash_num,
            "player": player_state,
            "enemies": enemies,
            "board": board_state,
            "valid_cards": card_options,
            "recent_actions": recent_actions
        }
    
    def _get_filtered_action_log(self, gs, player) -> list[str]:
        """Get recent action log entries, filtering out hidden opponent information"""
        if not hasattr(gs, 'action_log'):
            return []
        
        # Get last 30 entries to ensure we capture the full round
        recent_entries = gs.action_log[-30:]
        
        # Filter out entries that reveal hidden information
        filtered = []
        for entry in recent_entries:
            # Skip entries that reveal cards in opponent hands (before they're played)
            if "Revealed from" in entry and "hand:" in entry:
                # Only show if it's about the current player
                if player.name in entry:
                    filtered.append(entry)
            else:
                # Include most other entries (damage, healing, cancellations, etc.)
                filtered.append(entry)
        
        return filtered
    
    def _build_choice_context(self, valid_options, caster, gs, current_card) -> Dict[str, Any]:
        """Build context for player_choice decisions"""
        # Summarize options
        options = []
        for i, option in enumerate(valid_options):
            option_summary = self._summarize_option(option)
            options.append({
                "index": i,
                "description": option_summary
            })
        
        return {
            "card_name": current_card.name,
            "options": options,
            "player_health": caster.health,
            "player_max_health": caster.max_health,
            "round": gs.round_num,
            "clash": gs.clash_num
        }
    
    def _build_draft_context(self, player, gs, available_sets) -> Dict[str, Any]:
        """Build context for drafting decisions"""
        # Summarize available sets
        sets = []
        for i, spell_set in enumerate(available_sets):
            element = spell_set[0].element
            cards = []
            for card in spell_set:
                cards.append({
                    "name": card.name,
                    "types": card.types,
                    "priority": card.priority,
                    "is_conjury": card.is_conjury
                })
            
            sets.append({
                "index": i,
                "element": element,
                "cards": cards
            })
        
        return {
            "available_sets": sets,
            "round": gs.round_num
        }
    
    def _summarize_board_state(self, gs) -> Dict[str, Any]:
        """Summarize the current board state"""
        active_spells = {
            "player": [],
            "enemies": []
        }
        
        # Count active spells by type
        for player in gs.players:
            spells = []
            for clash_idx in range(len(player.board)):
                for spell in player.board[clash_idx]:
                    # Only include this spell if:
                    # 1. It's revealed (everyone can see it)
                    # 2. OR it's our own spell (we can see our own prepared spells)
                    if spell.status == 'revealed' or (hasattr(self, 'current_player') and spell.owner == self.current_player):
                        spells.append({
                            "name": spell.card.name,
                            "types": spell.card.types,
                            "element": spell.card.element,
                            "clash": clash_idx + 1,
                            "status": spell.status
                        })
            
            if hasattr(self, 'current_player') and player == self.current_player:
                active_spells["player"] = spells
            else:
                # For enemies, filter out prepared spells
                enemy_spells = [s for s in spells if s.get('status') == 'revealed']
                active_spells["enemies"].extend(enemy_spells)
        
        return active_spells
    
    def _summarize_card_effects(self, card) -> str:
        """Create a brief summary of what a card does"""
        summary_parts = []
        
        # Check resolve effects
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict):
                action_type = action.get('type', '')
                params = action.get('parameters', {})
                
                if action_type == 'damage':
                    summary_parts.append(f"Deal {params.get('value', 0)} damage")
                elif action_type == 'heal':
                    summary_parts.append(f"Heal {params.get('value', 0)}")
                elif action_type == 'weaken':
                    summary_parts.append(f"Weaken {params.get('value', 0)}")
                elif action_type == 'bolster':
                    summary_parts.append(f"Bolster {params.get('value', 0)}")
        
        # Note if it has advance effects
        if card.advance_effects:
            summary_parts.append("Has advance effects")
        
        return "; ".join(summary_parts) if summary_parts else "Complex effects"
    
    def _summarize_option(self, option) -> str:
        """Summarize a player_choice option"""
        if isinstance(option, dict):
            option_type = option.get('type', '')
            params = option.get('parameters', {})
            
            if option_type == 'damage':
                return f"Deal {params.get('value', 0)} damage"
            elif option_type == 'heal':
                return f"Heal {params.get('value', 0)}"
            elif option_type == 'advance':
                return "Advance a spell"
            elif option_type == 'cancel':
                return "Cancel a spell"
            elif option_type == 'discard':
                return "Force discard"
            else:
                return option_type.replace('_', ' ').title()
        
        return str(option)
    
    def _store_communication(self, message: str):
        """Store AI communication for display"""
        self.last_communication = message
        
        # Add to game action log so it's always visible
        if self.engine and hasattr(self.engine, 'gs') and hasattr(self.engine.gs, 'action_log'):
            self.engine.gs.action_log.append(
                f"{Colors.HEADER}[Claude]: {message}{Colors.ENDC}"
            )
            
            # Also show as a pause message so it's immediately visible
            if hasattr(self.engine, '_pause'):
                self.engine._pause(f"{Colors.HEADER}[Claude speaks]: {message}{Colors.ENDC}")
    
    def _fallback_decision(self, player, gs, valid_indices):
        """Fallback to a traditional AI when LLM fails"""
        if self.fallback_ai:
            return self.fallback_ai._select_card(player, gs, valid_indices)
        
        # Ultimate fallback - random choice
        import random
        return random.choice(valid_indices)
    
    def _get_llm_decision_sync(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for async LLM calls"""
        # Create new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._get_llm_decision(context, decision_type))
        finally:
            loop.close()
    
    @abstractmethod
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from the LLM - must be implemented by subclasses"""
        raise NotImplementedError
    
    def provide_round_analysis(self, gs):
        """Provide teaching analysis at the end of each round"""
        # Debug output only if verbose mode or if DEBUG_AI is set
        if getattr(self.engine, 'verbose', False) or os.environ.get('DEBUG_AI'):
            print(f"\n>>> LLMBaseAI.provide_round_analysis called")
            print(f">>> self.player_name = {self.player_name}")
            print(f">>> Players in game: {[p.name for p in gs.players]}")
            print(f">>> Is Human flags: {[p.is_human for p in gs.players]}")
        
        # Get the AI player
        ai_player = next((p for p in gs.players if p.name == self.player_name), None)
        
        if not ai_player:
            print(f">>> ERROR: Could not find player '{self.player_name}' in game!")
            return
        
        if getattr(self.engine, 'verbose', False) or os.environ.get('DEBUG_AI'):
            print(f">>> Found AI player: {ai_player.name}, proceeding with analysis...")
        # Only pause in interactive mode (when there's a human player)
        if any(p.is_human for p in gs.players):
            input(">>> Press Enter to continue...")  # Give time to read debug info
        
        # Build context for round analysis - include ALL the rich context
        # Build player state (same as card selection)
        player_state = {
            "name": ai_player.name,
            "health": ai_player.health,
            "max_health": ai_player.max_health,
            "hand_size": len(ai_player.hand),
            "trunks": ai_player.trunks
        }
        
        # Build enemy states (same as card selection)
        enemies = []
        for p in gs.players:
            if p != ai_player:
                enemies.append({
                    "name": p.name,
                    "health": p.health,
                    "max_health": p.max_health,
                    "hand_size": len(p.hand),
                    "trunks": p.trunks
                })
        
        # Build board state (what spells were active during the round)
        board_state = self._summarize_board_state(gs)
        
        # Get the FULL action log for this round (unfiltered for round analysis)
        full_round_actions = []
        for action in gs.action_log:
            # Include all actions from this round
            if "--- Round" in action and str(gs.round_num) in action:
                full_round_actions = []  # Start fresh from this round marker
            full_round_actions.append(action)
        
        context = {
            'round': gs.round_num,
            'round_plays': [h for h in self.round_history if h['round'] == gs.round_num],
            'player': player_state,
            'enemies': enemies,
            'board': board_state,
            'player_health': [(p.name, p.health, p.max_health, p.trunks) for p in gs.players],
            'game_state': gs,  # Pass full game state for element tracking
            'action_log': full_round_actions,  # Full unfiltered log for round analysis
            'recent_actions': self._get_filtered_action_log(gs, ai_player)[-10:] if ai_player else []
        }
        
        # Add trunk changes if any
        trunk_changes = []
        for player in gs.players:
            # Check if player lost a trunk this round (would need tracking)
            # For now, we'll note if health is 0
            if player.health == 0:
                trunk_changes.append({'player': player.name, 'lost_trunk': True})
        
        if trunk_changes:
            context['trunk_changes'] = trunk_changes
        
        # Debug log what we're sending
        print(f">>> Context action_log has {len(context['action_log'])} entries")
        if context['action_log']:
            print(">>> Sample actions:")
            for action in context['action_log'][-5:]:  # Last 5 actions
                print(f"    - {action[:80]}...")
        
        # Debug log
        if self.engine and hasattr(self.engine, 'ai_decision_logs'):
            # Use color based on AI type
            player_name_upper = self.player_name.upper()
            if 'CHAMPION' in player_name_upper:
                color = Colors.YELLOW
                emoji = "🏆 "
            elif 'SAVANT' in player_name_upper:
                color = Colors.GREEN  # Green for better distinction
                emoji = "🧬 "
            else:
                color = Colors.BLUE
                emoji = ""
            
            self.engine.ai_decision_logs.append(
                f"{color}{emoji}[{self.player_name}] Requesting round {gs.round_num} analysis...{Colors.ENDC}"
            )
        
        try:
            # Get analysis from LLM
            future = self.executor.submit(self._get_llm_decision_sync, context, "round_analysis")
            result = future.result(timeout=self.timeout_seconds)
            
            if result and isinstance(result, dict):
                message = result.get("analysis", "")
                if message:
                    # Always add to action log first so it's preserved
                    if hasattr(gs, 'action_log'):
                        # Use different colors for different AIs
                        player_name_upper = self.player_name.upper()
                        if 'CHAMPION' in player_name_upper:
                            color = Colors.YELLOW  # Yellow for Champion
                            emoji = "🏆 "
                        elif 'SAVANT' in player_name_upper:
                            color = Colors.GREEN    # Green for Savant (more distinct from blue)
                            emoji = "🧬 "
                        else:
                            color = Colors.HEADER  # Default purple/magenta
                            emoji = ""
                        
                        gs.action_log.append(f"\n{color}{emoji}=== {self.player_name}'s Round {gs.round_num} Analysis ==={Colors.ENDC}")
                        # Split message into lines to ensure all are visible
                        for line in message.split('\n'):
                            if line.strip():
                                gs.action_log.append(f"{color}{line}{Colors.ENDC}")
                else:
                    print(f">>> WARNING: {self.player_name} returned empty analysis!")
                
                # Then pause to show it (only if there was a message)
                if message and self.engine and hasattr(self.engine, '_pause'):
                    self.engine._pause("")  # Empty pause since message is in log
        except Exception as e:
            # Log the error
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"{Colors.WARNING}[{self.player_name}] Round analysis error: {str(e)}{Colors.ENDC}"
                )
    
    def provide_game_end_analysis(self, gs, winner):
        """Provide final commentary when the game ends"""
        # Build context for game end analysis
        context = {
            'winner': winner.name if winner else 'No one',
            'winner_health': winner.health if winner else 0,
            'winner_trunks': winner.trunks if winner else 0,
            'total_rounds': gs.round_num,
            'player_name': self.player_name,
            'final_board': self._summarize_board_state(gs),
            'all_players': [(p.name, p.health, p.max_health, p.trunks) for p in gs.players]
        }
        
        try:
            # Get analysis from LLM
            future = self.executor.submit(self._get_llm_decision_sync, context, "game_end")
            result = future.result(timeout=self.timeout_seconds)
            
            if result and isinstance(result, dict):
                message = result.get("final_words", "")
                if message:
                    # Always add to action log first
                    if hasattr(gs, 'action_log'):
                        # Use different colors for different AIs
                        player_name_upper = self.player_name.upper()
                        if 'CHAMPION' in player_name_upper:
                            color = Colors.YELLOW  # Yellow for Champion
                            emoji = "🏆 "
                        elif 'SAVANT' in player_name_upper:
                            color = Colors.GREEN    # Green for Savant (more distinct from blue)
                            emoji = "🧬 "
                        else:
                            color = Colors.HEADER  # Default purple/magenta
                            emoji = ""
                        
                        gs.action_log.append(f"\n{color}{emoji}=== {self.player_name}'s Final Words ==={Colors.ENDC}")
                        gs.action_log.append(f"{color}{message}{Colors.ENDC}")
                    
                    # Then pause to show it
                    if self.engine and hasattr(self.engine, '_pause'):
                        self.engine._pause("")  # Empty pause since message is in log
        except Exception:
            pass  # Silent fail for game end commentary