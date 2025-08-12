import json
import os
import sys
import random
import traceback
from collections import defaultdict
from typing import Optional, Any, Union

# --- CONSTANTS ---
SPELL_JSON_DATA = """
[
  {"id": 1, "card_name": "Fireball", "elephant": "Elé Phlambé", "element": "Fire", "is_conjury": false, "priority": 4, "spell_types": ["attack"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 2}}}]},
  {"id": 2, "card_name": "Scorch", "elephant": "Elé Phlambé", "element": "Fire", "is_conjury": false, "priority": 4, "spell_types": ["attack", "boost"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "damage_multi_target", "target": "all_enemies_and_their_conjuries", "parameters": {"value": 1}}}]},
  {"id": 3, "card_name": "Ignite", "elephant": "Elé Phlambé", "element": "Fire", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response", "boost"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "attack", "count": 1, "exclude_self": true}}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]},
  {"id": 4, "card_name": "Nourish", "elephant": "Spout Snout", "element": "Water", "is_conjury": false, "priority": 3, "spell_types": ["remedy"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "heal", "target": "self", "parameters": {"value": 2}}}]},
  {"id": 5, "card_name": "Flow", "elephant": "Spout Snout", "element": "Water", "is_conjury": false, "priority": 3, "spell_types": ["remedy", "response", "boost"], "notfirst": 2, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "remedy", "count": 1, "exclude_self": true}}, "action": {"type": "heal", "target": "self", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]},
  {"id": 6, "card_name": "Cleanse", "elephant": "Spout Snout", "element": "Water", "is_conjury": false, "priority": 3, "spell_types": ["attack", "remedy"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "player_choice", "options": [{"label": "Damage an enemy", "type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}, {"label": "Heal yourself", "type": "heal", "target": "self", "parameters": {"value": 1}}]}}]},
  {"id": 7, "card_name": "Turbulence", "elephant": "Dumblo", "element": "Wind", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_spell_previously_resolved_this_round"}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 2}}}, {"condition": {"type": "if_not", "sub_condition": {"type": "if_spell_previously_resolved_this_round"}}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}}]},
  {"id": 8, "card_name": "Blow", "elephant": "Dumblo", "element": "Wind", "is_conjury": false, "priority": "A", "spell_types": ["boost"], "notfirst": 2, "notlast": 0, "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "prompt_friendly_past_spell", "parameters": {"value": 1}}}]},
  {"id": 9, "card_name": "Gust", "elephant": "Dumblo", "element": "Wind", "is_conjury": false, "priority": "A", "spell_types": ["boost"], "notfirst": 0, "notlast": 0, "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "player_choice", "options": [{"label": "Advance this spell", "type": "advance", "target": "this_spell", "parameters": {"value": 1}}, {"label": "Advance another active spell", "type": "advance", "target": "prompt_other_friendly_active_spell", "parameters": {"value": 1}}]}}]},
  {"id": 10, "card_name": "Crush", "elephant": "Columnfoot", "element": "Earth", "is_conjury": false, "priority": 3, "spell_types": ["attack"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "weaken", "target": "prompt_enemy", "parameters": {"value": 1}}}]},
  {"id": 11, "card_name": "Aftershocks", "elephant": "Columnfoot", "element": "Earth", "is_conjury": true, "priority": 5, "spell_types": ["attack", "response", "boost"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "attack", "count": 1, "exclude_self": true}}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 2}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell"}}]},
  {"id": 12, "card_name": "Quake", "elephant": "Columnfoot", "element": "Earth", "is_conjury": false, "priority": 2, "spell_types": ["attack"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "discard_from_hand", "target": "prompt_enemy", "parameters": {"value": 1}}}]},
  {"id": 13, "card_name": "Seed", "elephant": "Trunxie", "element": "Wood", "is_conjury": false, "priority": "A", "spell_types": ["boost"], "notfirst": 2, "notlast": 0, "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "prompt_friendly_past_spell", "parameters": {"value": 1}}}, {"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]},
  {"id": 14, "card_name": "Grow", "elephant": "Trunxie", "element": "Wood", "is_conjury": false, "priority": 3, "spell_types": ["remedy", "response"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "player_choice", "options": [{"label": "Heal for 1", "type": "heal", "target": "self", "parameters": {"value": 1}}, {"label": "Heal for each of your other active spells", "type": "heal_per_spell", "target": "self", "parameters": {"spell_type": "any", "exclude_self": true}}]}}]},
  {"id": 15, "card_name": "Prickle", "elephant": "Trunxie", "element": "Wood", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "player_choice", "options": [{"label": "Damage for 1", "type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}, {"label": "Damage for each of your other active spells", "type": "damage_per_spell", "target": "prompt_enemy", "parameters": {"spell_type": "any", "exclude_self": true}}]}}]},
  {"id": 16, "card_name": "Reinforce", "elephant": "General Guardjendra", "element": "Metal", "is_conjury": false, "priority": 2, "spell_types": ["remedy"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "bolster", "target": "self", "parameters": {"value": 1}}}]},
  {"id": 17, "card_name": "Besiege", "elephant": "General Guardjendra", "element": "Metal", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response", "boost"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "remedy", "count": 1, "exclude_self": false}}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]},
  {"id": 18, "card_name": "Defend", "elephant": "General Guardjendra", "element": "Metal", "is_conjury": false, "priority": 3, "spell_types": ["remedy", "response", "boost"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "attack", "count": 1, "exclude_self": false}}, "action": {"type": "heal", "target": "self", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]},
  {"id": 25, "card_name": "Reflect", "elephant": "Gold Dust", "element": "Sunbeam", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response"], "notfirst": 1, "notlast": 0, "resolve_effects": [{"condition": {"type": "if_enemy_has_active_spell_of_type", "parameters": {"spell_type": "attack", "count": 1}}, "action": {"type": "damage", "target": "all_enemies_who_met_condition", "parameters": {"value": 3}}}]},
  {"id": 26, "card_name": "Glare", "elephant": "Gold Dust", "element": "Sunbeam", "is_conjury": true, "priority": 5, "spell_types": ["attack"], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "weaken", "target": "prompt_enemy", "parameters": {"value": 1}}}, {"condition": {"type": "always"}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}}]},
  {"id": 27, "card_name": "Illuminate", "elephant": "Gold Dust", "element": "Sunbeam", "is_conjury": false, "priority": 1, "spell_types": [], "notfirst": 0, "notlast": 0, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "cast_extra_spell", "target": "self", "parameters": {"source": "hand"}}}]},
  {"id": 28, "card_name": "Slumber", "elephant": "Luna Doze", "element": "Moonshine", "is_conjury": false, "priority": 5, "spell_types": ["remedy", "boost"], "notfirst": 0, "notlast": 1, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "heal", "target": "self", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "always"}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1, "limit": 1}}}]},
  {"id": 29, "card_name": "Nightglow", "elephant": "Luna Doze", "element": "Moonshine", "is_conjury": false, "priority": 2, "spell_types": ["remedy", "response", "boost"], "notfirst": 1, "notlast": 1, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "bolster", "target": "self", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "if_caster_has_active_spell_of_type", "parameters": {"spell_type": "any", "count": 1, "exclude_self": true}}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1, "limit": 1}}}]},
  {"id": 30, "card_name": "Bedim", "elephant": "Luna Doze", "element": "Moonshine", "is_conjury": false, "priority": 4, "spell_types": ["attack", "response", "boost"], "notfirst": 1, "notlast": 1, "resolve_effects": [{"condition": {"type": "always"}, "action": {"type": "damage", "target": "prompt_enemy", "parameters": {"value": 1}}}], "advance_effects": [{"condition": {"type": "if_board_has_active_spell_of_type", "parameters": {"spell_type": "attack", "count": 1, "exclude_self": true}}, "action": {"type": "advance", "target": "this_spell", "parameters": {"value": 1}}}]}
]
"""

# --- UTILITIES ---
def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
class Colors:
    HEADER='\033[95m'; BLUE='\033[94m'; CYAN='\033[96m'; GREEN='\033[92m'
    WARNING='\033[93m'; FAIL='\033[91m'; ENDC='\033[0m'; BOLD='\033[1m'
    UNDERLINE='\033[4m'; GREY='\033[90m'
class RoundOverException(Exception):
    """Custom exception to signal the end of the current round immediately."""
    pass

# --- DATA MODELS ---
class Card:
    def __init__(self, card_data: dict):
        self.id: int = card_data.get('id')
        self.name: str = card_data.get('card_name')
        self.elephant: str = card_data.get('elephant')
        self.element: str = card_data.get('element')
        self.priority = card_data.get('priority')
        self.types: list[str] = card_data.get('spell_types', [])
        self.is_conjury: bool = card_data.get('is_conjury', False)
        self.notfirst: int = card_data.get('notfirst', 0)
        self.notlast: int = card_data.get('notlast', 0)
        self.resolve_effects: list[dict] = card_data.get('resolve_effects', [])
        self.advance_effects: list[dict] = card_data.get('advance_effects', [])
    def __repr__(self) -> str: return f"Card({self.name})"
    def get_instructions_text(self) -> str:
        texts = []
        if self.resolve_effects:
            for effect in self.resolve_effects:
                action = effect['action']
                condition_text = self._format_condition(effect['condition'])
                action_text = self._format_action(action)
                texts.append(f"{condition_text}{action_text}")
        if self.advance_effects:
            adv_texts = [self._format_action(eff['action']) for eff in self.advance_effects]
            texts.append(f"Advance Phase: {', '.join(adv_texts)}")
        return "; ".join(texts) if texts else "No effect."
    def _format_condition(self, cond: dict) -> str:
        cond_type = cond.get('type')
        if cond_type == 'always': return ""
        if cond_type == 'if_caster_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1) 
            return f"If you have {count_str} other active {p['spell_type']} spell(s): "
        if cond_type == 'if_enemy_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1)
            return f"If an enemy has {count_str} active {p['spell_type']} spell(s): "
        if cond_type == 'if_spell_previously_resolved_this_round': return "If this spell resolved in a past clash: "
        if cond_type == 'if_not': return f"Otherwise: "
        if cond_type == 'if_board_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1)
            return f"If there are {count_str} other active {p['spell_type']} spells on the board: "
        return f"If {cond_type.replace('_', ' ')}: "
    def _format_action(self, action: dict) -> str:
        action_type = action.get('type')
        if action_type == 'player_choice':
            options = [self._format_action(opt) for opt in action['options']]
            return f"Choose to: {' or '.join(options)}"
        params = action.get('parameters', {}); value = params.get('value', '')
        target_raw = action.get('target', 'self')
        target_map = {
            'self': 'yourself', 'prompt_enemy': 'an enemy', 'this_spell': 'this spell',
            'prompt_other_friendly_active_spell': 'another friendly active spell',
            'prompt_friendly_past_spell': 'one of your past spells',
            'all_enemies_and_their_conjuries': 'each enemy and their conjuries',
            'all_enemies_who_met_condition': 'each enemy who met the condition',
            'prompt_player_or_conjury': 'an enemy or conjury'
        }
        target = target_map.get(target_raw, target_raw.replace('_', ' '))
        return f"{action_type.replace('_', ' ').title()} {target} for {value}".strip()

class PlayedCard:
    def __init__(self, card: Card, owner: 'Player'):
        self.card: Card = card
        self.owner: 'Player' = owner
        self.status: str = 'prepared'
        self.has_resolved: bool = False
        self.advances_this_round: int = 0  # Track number of advances
class Player:
    def __init__(self, name: str, is_human: bool = True):
        self.name: str = name
        self.is_human: bool = is_human
        self.health: int = 5
        self.max_health: int = 5
        self.trunks: int = 3
        self.hand: list[Card] = []
        self.discard_pile: list[Card] = []
        self.board: list[list[PlayedCard]] = [[] for _ in range(4)]
        self.is_invulnerable: bool = False
        self.knocked_out_this_turn: bool = False
    def lose_trunk(self) -> str:
        if self.trunks > 0:
            self.trunks -= 1; self.is_invulnerable = True
            if self.max_health <= 3: self.max_health = 4
            elif self.max_health >= 7: self.max_health = 6
            self.health = self.max_health; return f"{self.name} lost a trunk!"
        return f"{self.name} has no trunks to lose."
    def __repr__(self) -> str: return f"Player({self.name})"
class GameState:
    def __init__(self, player_names: list[str]):
        self.players: list[Player] = [Player(name, is_human=(i==0)) for i, name in enumerate(player_names)]
        self.all_cards: dict[int, Card] = {data['id']: Card(data) for data in json.loads(SPELL_JSON_DATA)}
        sets = defaultdict(list);
        for data in json.loads(SPELL_JSON_DATA): sets[data['elephant']].append(self.all_cards[data['id']])
        self.main_deck: list[list[Card]] = list(sets.values()); random.shuffle(self.main_deck)
        self.round_num: int = 1; self.clash_num: int = 1; self.ringleader_index: int = 0
        self.action_log: list[str] = ["Game has started!"]
        self.event_log: list[dict] = []
        self.game_over: bool = False
        self.resolution_queue: list[dict] = []

# --- DISPLAY ENGINE ---
class DashboardDisplay:
    def draw(self, gs, pov_player_index=0, prompt=""):
        clear_screen(); print(f"{Colors.HEADER}{'='*34}[ Elemental Elephants ]{'='*33}{Colors.ENDC}")
        print(f"Round: {gs.round_num} | Clash: {gs.clash_num} | Ringleader: {Colors.BOLD}{gs.players[gs.ringleader_index].name}{Colors.ENDC}")
        print("-" * 150)
        header = f"{'PLAYER'.ljust(15)} | {'HEALTH'.ljust(16)} | {'TRUNKS'} | {'DISCARD'} | {'CLASH I'.ljust(30)} | {'CLASH II'.ljust(30)} | {'CLASH III'.ljust(30)}| {'CLASH IV'.ljust(30)}"
        print(Colors.BOLD + header + Colors.ENDC); print("-" * 150)
        for i, p in enumerate(gs.players):
            is_current = ">" if i == pov_player_index and p.is_human else " "; p_color = Colors.CYAN if i == pov_player_index and p.is_human else Colors.ENDC
            p_info = f"{is_current} {p_color}{p.name.ljust(13)}{Colors.ENDC}"
            h_color = Colors.GREEN if p.health > p.max_health / 2 else Colors.FAIL
            health_str = f"{h_color}{str(p.health).rjust(2)}/{str(p.max_health).ljust(2)}{Colors.ENDC}".ljust(25)
            trunks_str = ("O " * p.trunks).ljust(6); discard_str = str(len(p.discard_pile)).ljust(7)
            clash_slots_str = ""
            for j in range(4):
                slot_content = p.board[j]
                if not slot_content: slot_str = "[Empty]"
                else:
                    # --- NEW: Display face-down spells ---
                    card_names = []
                    for s in slot_content:
                        if s.status == 'prepared' and s.owner != gs.players[pov_player_index]:
                            card_names.append(f"{Colors.BLUE}[Spell Prepared]{Colors.ENDC}")
                        else:
                            color = Colors.GREY if s.status == 'cancelled' else ''
                            card_names.append(f"{color}{s.card.name}{Colors.ENDC}")
                    slot_str = ", ".join(card_names)
                width = 30; clash_slots_str += slot_str.ljust(width) + " | "
            print(f"{p_info} | {health_str} | {trunks_str} | {discard_str} | {clash_slots_str.strip().rstrip('|')}")

        print("=" * 150); pov_player = gs.players[pov_player_index]
        if pov_player.is_human:
            print(f"\n--- {Colors.CYAN}YOUR HAND ({pov_player.name}){Colors.ENDC}")
            if not pov_player.hand: print(f"{Colors.GREY}Your hand is empty.{Colors.ENDC}")
            else:
                for i, card in enumerate(pov_player.hand):
                    print(f"[{i+1}] {Colors.BOLD}{card.name} (P:{card.priority}){Colors.ENDC}"); print(f"    {Colors.GREY}> {card.get_instructions_text()}{Colors.ENDC}")
        print("-" * 89);
        if gs.action_log: print(f"{Colors.BOLD}LOG:{Colors.ENDC}"); [print(f"  {entry}") for entry in gs.action_log[-5:]]
        if prompt: print(f"\n>>> {Colors.WARNING}{prompt}{Colors.ENDC}")
# --- LOGIC ENGINES ---
class ConditionChecker:
    def check(self, condition_data, gs, caster, current_card):
        cond_type = condition_data.get('type')
        if cond_type == 'always': return True

        if cond_type == 'if_spell_previously_resolved_this_round':
            # --- TURBULENCE FIX: Check the log for a past event ---
            for event in gs.event_log:
                if (event['type'] == 'spell_resolved' and
                    event['player'] == caster.name and
                    event['card_id'] == current_card.id and
                    event['clash'] < gs.clash_num): # Must be from a previous clash
                    return True
            return False

        active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s and s.status == 'active']
        if cond_type == 'if_caster_has_active_spell_of_type':
            params = condition_data['parameters']; count = 0
            for spell in active_spells_this_clash:
                if spell.owner == caster and params['spell_type'] in spell.card.types:
                    if params.get('exclude_self', False) and spell.card.id == current_card.id: continue
                    count += 1
            return count >= params.get('count', 1)
        
        if cond_type == 'if_enemy_has_active_spell_of_type':
            params = condition_data['parameters']; count = 0
            enemies = [p for p in gs.players if p != caster]
            for spell in active_spells_this_clash:
                if spell.owner in enemies and params['spell_type'] in spell.card.types:
                    count += 1
            return count >= params.get('count', 1)
        
        if cond_type == 'if_board_has_active_spell_of_type':
            params = condition_data['parameters']; count = 0
            for spell in active_spells_this_clash:
                if params['spell_type'] in spell.card.types:
                    if params.get('exclude_self', False) and spell.card.id == current_card.id: continue
                    count += 1
            return count >= params.get('count', 1)
        
        if cond_type == 'if_not': return not self.check(condition_data['sub_condition'], gs, caster, current_card)
        return False
# +++ START: REPLACE THE ENTIRE ActionHandler CLASS WITH THIS +++
class ActionHandler:
    def __init__(self, engine: 'GameEngine'):
        self.engine: 'GameEngine' = engine

    def _fire_event(self, event_type: str, gs: 'GameState', **kwargs: Any) -> None:
        event = {"clash": gs.clash_num, "type": event_type}; event.update(kwargs); gs.event_log.append(event)

    def execute_effects(self, effects: list[dict], gs: 'GameState', caster: 'Player', current_card: 'Card') -> None:
        a_condition_was_met = False
        is_sequential = all(eff['condition'].get('type') == 'always' for eff in effects)

        if is_sequential:
            for effect in effects:
                self._execute_action(effect['action'], gs, caster, current_card)
                self.engine._pause()  # Add pause between sequential effects
        else:
            for effect in effects:
                condition_type = effect['condition'].get('type')
                if condition_type == 'otherwise':
                    if not a_condition_was_met:
                        self._execute_action(effect['action'], gs, caster, current_card)
                elif not a_condition_was_met:
                    if self.engine.condition_checker.check(effect['condition'], gs, caster, current_card):
                        a_condition_was_met = True
                        self._execute_action(effect['action'], gs, caster, current_card)

    def _execute_action(self, action_data: dict, gs: 'GameState', caster: 'Player', current_card: 'Card') -> None:
        action_type = action_data.get('type')
        params = action_data.get('parameters', {})
        targets = self._resolve_target(action_data, gs, caster, current_card)
        
        if not targets:
            gs.action_log.append(f"{Colors.GREY}No valid targets for {action_type}.{Colors.ENDC}"); self.engine._pause()
            return

        if action_type == 'player_choice':
            # First, check if each option is actually valid
            valid_options = []
            for option in action_data.get('options', []):
                # Check if the option has valid targets
                option_targets = self._resolve_target(option, gs, caster, current_card)
                if option_targets:  # Only include options that have valid targets
                    valid_options.append(option)
            
            if not valid_options:
                gs.action_log.append(f"{Colors.GREY}No valid options available.{Colors.ENDC}")
                return
            
            # If only one valid option, execute it automatically
            if len(valid_options) == 1:
                gs.action_log.append(f"Only one valid option - executing automatically.")
                self._execute_action(valid_options[0], gs, caster, current_card)
                return
            
            if caster.is_human:
                # Build options dictionary with labels
                options_dict = {}
                for i, option in enumerate(valid_options):
                    label = option.get('label', f"Option {i+1}")
                    options_dict[i+1] = {'label': label, 'action': option}
                
                # Display options to player
                prompt = "Choose an option:"
                self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                for key, opt in options_dict.items():
                    print(f"  [{key}] {opt['label']}")
                
                choice = input("\nYour choice: ").strip()
                try:
                    choice_idx = int(choice)
                    if choice_idx in options_dict:
                        chosen_action = options_dict[choice_idx]['action']
                        self._execute_action(chosen_action, gs, caster, current_card)
                except ValueError:
                    gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
            else:
                # AI just picks the first valid option
                self._execute_action(valid_options[0], gs, caster, current_card)
            return
        
        if action_type == 'cast_extra_spell':
            if caster.is_human:
                if not caster.hand: gs.action_log.append(f"{caster.name} has no cards to cast."); self.engine._pause(); return
                options = {i+1: c for i, c in enumerate(caster.hand)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose an extra spell to cast:")
                if choice is not None:
                    card_to_cast = caster.hand.pop(choice-1)
                    newly_played_card = PlayedCard(card_to_cast, caster)
                    newly_played_card.status = 'active'  # Set to active since it's cast mid-resolution
                    gs.players[gs.players.index(caster)].board[gs.clash_num - 1].append(newly_played_card)
                    self.engine.add_to_resolution_queue(newly_played_card)
                    gs.action_log.append(f"{caster.name} casts an extra spell: [{card_to_cast.name}]!")
                    self.engine._pause()
            return

        for target in targets:
            if action_type == 'damage':
                if isinstance(target, Player):
                    if not target.is_invulnerable:
                        damage = params.get('value', 1); original_health = target.health; target.health = max(0, target.health - damage)
                        gs.action_log.append(f"{caster.name}'s [{current_card.name}] dealt {damage} damage to {target.name}. ({target.health}/{target.max_health})")
                        self._fire_event('player_damaged', gs, player=caster.name, target=target.name, value=damage, card_id=current_card.id)
                        if original_health > 0 and target.health <= 0:
                            if self.engine._handle_trunk_loss(target) == 'round_over': raise RoundOverException()
                elif isinstance(target, PlayedCard) and target.card.is_conjury:
                    target.status = 'cancelled'; gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{target.card.name}].")
                    self._fire_event('spell_cancelled', gs, player=caster.name, target_card_id=target.card.id, card_id=current_card.id)
            elif action_type == 'damage_multi_target':
                 for t in target:
                     if isinstance(t, Player):
                         if not t.is_invulnerable:
                            damage = params.get('value', 1); original_health = t.health; t.health = max(0, t.health - damage)
                            gs.action_log.append(f"{caster.name}'s [{current_card.name}] dealt {damage} damage to {t.name}. ({t.health}/{t.max_health})")
                            self._fire_event('player_damaged', gs, player=caster.name, target=t.name, value=damage, card_id=current_card.id)
                            if original_health > 0 and t.health <= 0:
                                if self.engine._handle_trunk_loss(t) == 'round_over': raise RoundOverException()
                     elif isinstance(t, PlayedCard) and t.card.is_conjury:
                        t.status = 'cancelled'; gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{t.card.name}].")
                        self._fire_event('spell_cancelled', gs, player=caster.name, target_card_id=t.card.id, card_id=current_card.id)
            elif action_type == 'heal':
                target.health = min(target.max_health, target.health + params.get('value', 1)); gs.action_log.append(f"{caster.name}'s [{current_card.name}] healed {target.name} for {params.get('value', 1)}. ({target.health}/{target.max_health})")
                self._fire_event('player_healed', gs, player=target.name, value=params.get('value', 1), card_id=current_card.id)
            elif action_type == 'weaken':
                target.max_health = max(0, target.max_health - params.get('value', 1)); target.health = min(target.health, target.max_health)
                gs.action_log.append(f"{caster.name}'s [{current_card.name}] weakened {target.name} by {params.get('value', 1)}. Max health now {target.max_health}.")
            elif action_type == 'bolster':
                target.max_health += params.get('value', 1); gs.action_log.append(f"{caster.name}'s [{current_card.name}] bolstered {target.name}. Max health now {target.max_health}.")
            elif action_type == 'damage_per_spell':
                # Count active spells matching criteria
                active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'active']
                spell_type = params.get('spell_type', 'any')
                exclude_self = params.get('exclude_self', False)
                
                count = 0
                for spell in active_spells_this_clash:
                    if spell.owner == caster:
                        if exclude_self and spell.card.id == current_card.id:
                            continue
                        if spell_type == 'any' or spell_type in spell.card.types:
                            count += 1
                
                if count > 0:
                    if isinstance(target, Player) and not target.is_invulnerable:
                        damage = count
                        original_health = target.health
                        target.health = max(0, target.health - damage)
                        gs.action_log.append(f"{caster.name}'s [{current_card.name}] dealt {damage} damage to {target.name} ({count} spell(s)). ({target.health}/{target.max_health})")
                        self._fire_event('player_damaged', gs, player=caster.name, target=target.name, value=damage, card_id=current_card.id)
                        if original_health > 0 and target.health <= 0:
                            if self.engine._handle_trunk_loss(target) == 'round_over': raise RoundOverException()
                    elif isinstance(target, PlayedCard) and target.card.is_conjury:
                        target.status = 'cancelled'
                        gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{target.card.name}].")
                else:
                    gs.action_log.append(f"{caster.name} has no other active spells to boost the damage.")
            
            elif action_type == 'heal_per_spell':
                # Count active spells matching criteria
                active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'active']
                spell_type = params.get('spell_type', 'any')
                exclude_self = params.get('exclude_self', False)
                
                count = 0
                for spell in active_spells_this_clash:
                    if spell.owner == caster:
                        if exclude_self and spell.card.id == current_card.id:
                            continue
                        if spell_type == 'any' or spell_type in spell.card.types:
                            count += 1
                
                if count > 0:
                    healing = count
                    target.health = min(target.max_health, target.health + healing)
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] healed {target.name} for {healing} ({count} spell(s)). ({target.health}/{target.max_health})")
                    self._fire_event('player_healed', gs, player=target.name, value=healing, card_id=current_card.id)
                else:
                    gs.action_log.append(f"{caster.name} has no other active spells to boost the healing.")
            
            elif action_type == 'advance':
                # Check if this advance action has a per-round limit
                if 'limit' in params:
                    advance_limit = params['limit']
                    if target.advances_this_round >= advance_limit:
                        gs.action_log.append(f"[{target.card.name}] can only advance {advance_limit} time(s) per round and has already advanced {target.advances_this_round} time(s).")
                        continue
                
                owner = target.owner; next_clash_idx = gs.clash_num
                if next_clash_idx < 4:
                    found_and_moved = False
                    for i, clash_list in enumerate(owner.board):
                        if target in clash_list:
                            owner.board[i].remove(target); owner.board[next_clash_idx].append(target)
                            target.advances_this_round += 1  # Increment advance count
                            gs.action_log.append(f"{owner.name}'s [{target.card.name}] advanced from Clash {i+1} to Clash {next_clash_idx + 1}.")
                            self._fire_event('spell_advanced', gs, player=owner.name, card_id=target.card.id); found_and_moved = True; break
                    if not found_and_moved: gs.action_log.append(f"Error: Could not find [{target.card.name}] to advance.")
                else: gs.action_log.append(f"[{target.card.name}] could not advance past Clash 4.")

    def _resolve_target(self, action_data: dict, gs: 'GameState', caster: 'Player', current_card: 'Card') -> list[Any]:
        target_str = action_data.get('target')
        if target_str is None: return [caster]
        if target_str == 'self': return [caster]
        if target_str == 'this_spell':
            for clash_list in caster.board:
                for spell in clash_list:
                    if spell.card.id == current_card.id: return [spell]
            return []
        enemies = [p for p in gs.players if p != caster]; valid_enemies = [p for p in enemies if not p.is_invulnerable]
        active_conjuries = [s for p in gs.players for clash_list in p.board for s in clash_list if s and s.card.is_conjury and s.status == 'active']
        if target_str == 'prompt_enemy' or target_str == 'prompt_player_or_conjury':
            all_possible_targets = valid_enemies + [c for c in active_conjuries if c.owner in valid_enemies]
            if not all_possible_targets: return []
            if caster.is_human:
                if len(all_possible_targets) == 1: return all_possible_targets
                options = {i+1: t for i, t in enumerate(all_possible_targets)}; choice = self.engine._prompt_for_choice(caster, options, "Choose a target (enemy or conjury):")
                if choice is not None: return [options[choice]]
                else: return []
            else: # AI Logic
                high_threat_conjuries = [c for c in all_possible_targets if isinstance(c, PlayedCard) and (int(c.card.priority) if str(c.card.priority).isdigit() else 5) <= 2]
                if high_threat_conjuries: return [random.choice(high_threat_conjuries)]
                low_health_players = [p for p in all_possible_targets if isinstance(p, Player) and p.health <= 2]
                if low_health_players: return [random.choice(low_health_players)]
                player_targets = [t for t in all_possible_targets if isinstance(t, Player)]
                return [random.choice(player_targets)] if player_targets else [random.choice(all_possible_targets)]
        if target_str == 'all_enemies_and_their_conjuries':
            all_targets = valid_enemies + [c for c in active_conjuries if c.owner in valid_enemies]
            return [all_targets] if all_targets else []
        active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'active']
        if target_str == 'prompt_other_friendly_active_spell':
            options_list = [s for s in active_spells_this_clash if s.owner == caster and s.card.id != current_card.id]
            if not options_list: return []
            if len(options_list) == 1: return options_list
            if caster.is_human:
                options = {i+1: s for i, s in enumerate(options_list)}; choice = self.engine._prompt_for_choice(caster, options, "Choose another of your spells:", view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else: return [random.choice(options_list)]
        past_spells = [s for clash_list in caster.board[:gs.clash_num-1] for s in clash_list]
        if target_str == 'prompt_friendly_past_spell':
            if not past_spells: return []
            if len(past_spells) == 1: return past_spells
            if caster.is_human:
                options = {i+1: s for i, s in enumerate(past_spells)}; choice = self.engine._prompt_for_choice(caster, options, "Choose one of your past spells:")
                if choice is not None: return [options[choice]]
                else: return []
            else: return [random.choice(past_spells)]
        
        if target_str == 'all_enemies_who_met_condition':
            # This is a special target that needs to work with condition checking
            # We need to find enemies who have attack spells (for Reflect)
            enemies = [p for p in gs.players if p != caster and not p.is_invulnerable]
            enemies_with_attack_spells = []
            active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'active']
            
            for enemy in enemies:
                for spell in active_spells_this_clash:
                    if spell.owner == enemy and 'attack' in spell.card.types:
                        enemies_with_attack_spells.append(enemy)
                        break  # Only need to find one attack spell per enemy
            
            return enemies_with_attack_spells
        
        return []
class AI_Player:
    def choose_card_to_play(self, player, gs):
        # --- Filter by clash rules ---
        valid_plays_indices = list(range(len(player.hand))) # Start with all indices as valid
        if gs.clash_num == 1:
            valid_plays_indices = [i for i in valid_plays_indices if player.hand[i].notfirst < 2]
        if gs.clash_num == 4:
            valid_plays_indices = [i for i in valid_plays_indices if player.hand[i].notlast < 2]
        
        if not valid_plays_indices:
            return None # No valid card to play

        # --- High-level situational logic ---
        low_health_enemies = [p for p in gs.players if p != player and p.health <= 2]
        
        # Survival: Find the best heal card among valid plays
        if player.health <= 2:
            heal_options = [(i, player.hand[i]) for i in valid_plays_indices if 'remedy' in player.hand[i].types]
            if heal_options:
                # Sort by priority (lower is better)
                heal_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 99)
                return heal_options[0][0] # Return the index of the best heal card

        # Finisher: Find the best damage card among valid plays
        if low_health_enemies:
            damage_options = [(i, player.hand[i]) for i in valid_plays_indices if 'attack' in player.hand[i].types]
            if damage_options:
                # Sort by priority (higher is better for attacks)
                damage_options.sort(key=lambda x: int(x[1].priority) if str(x[1].priority).isdigit() else 0, reverse=True)
                return damage_options[0][0] # Return the index of the best damage card
        
        # Default to a random valid card index
        return random.choice(valid_plays_indices)
# --- MAIN GAME ENGINE ---
class GameEngine:
    def __init__(self, player_names):
        self.gs = GameState(player_names); self.display = DashboardDisplay()
        self.condition_checker = ConditionChecker(); self.action_handler = ActionHandler(self)
        self.ai_player = AI_Player()
    def _pause(self, message=""): prompt = f"{message} {Colors.GREY}[Press Enter to continue...]{Colors.ENDC}"; self.display.draw(self.gs, prompt=prompt); input()
    def _prompt_for_choice(self, player, options, prompt_message, view_key='name'):
        while True:
            self.display.draw(self.gs, self.gs.players.index(player), prompt=prompt_message)
            if not options: self.gs.action_log.append(f"{Colors.GREY}No options available.{Colors.ENDC}"); return 'done' if 'done' in prompt_message.lower() else None
            for key, item in options.items():
                if isinstance(item, list): display_name = f"The '{item[0].elephant}' Set ({item[0].element} | {len(item)} cards)"
                elif isinstance(item, Card): display_name = f"{item.name} (P:{item.priority})"; print(f"  [{key}] {display_name}"); print(f"    {Colors.GREY}> {item.get_instructions_text()}{Colors.ENDC}"); continue
                elif isinstance(item, PlayedCard): display_name = f"{item.owner.name}'s [{item.card.name}]"
                else: display_name = getattr(item, view_key, str(item))
                print(f"  [{key}] {display_name}")
            if 'done' in prompt_message.lower(): print("\n  [done] Finish selection")
            choice = input("\nYour choice: ").lower().strip()
            if choice == 'done': return 'done'
            try:
                choice_idx = int(choice)
                if choice_idx in options: return choice_idx
                else: self.gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
            except ValueError: self.gs.action_log.append(f"{Colors.FAIL}Invalid input.{Colors.ENDC}")
    def run_game(self) -> None:
        try:
            self._setup_game()
            while len([p for p in self.gs.players if p.trunks > 0]) > 1:
                self._run_round()
                self.gs.round_num += 1
            
            winner = next((p for p in self.gs.players if p.trunks > 0), None)
            self.gs.action_log.append(f"GAME OVER! The winner is {winner.name}!" if winner else "GAME OVER! No winner.")
            self._pause()
        except Exception:
            clear_screen(); print("\n\n--- A CRITICAL ERROR OCCURRED ---")
            traceback.print_exc(); print("---------------------------------")
            print("\nPlease copy this error report for debugging.")

    def _setup_game(self):
        self._check_and_rebuild_deck()
        self.gs.action_log.clear(); self.gs.action_log.append("--- Game Setup ---")
        for _ in range(2):
            for i, p in enumerate(self.gs.players):
                self._check_and_rebuild_deck()
                if p.is_human:
                    options = {i+1: s for i, s in enumerate(self.gs.main_deck) if s}; choice = self._prompt_for_choice(p, options, f"{p.name}, choose a spell set to draft:")
                    drafted_set = options[choice]; self.gs.main_deck.remove(drafted_set)
                else: 
                    # AI picks randomly from available sets
                    drafted_set = random.choice(self.gs.main_deck)
                    self.gs.main_deck.remove(drafted_set)
                p.discard_pile.extend(drafted_set); self.gs.action_log.append(f"{p.name} drafted the '{drafted_set[0].elephant}' ({drafted_set[0].element}) set.")
        for p in self.gs.players:
            if p.is_human:
                options = {i+1: c for i, c in enumerate(p.discard_pile)}; hand_choices = []
                while len(hand_choices) < 4:
                    prompt = f"{p.name}, choose card {len(hand_choices)+1}/4 for your starting hand:"; choice = self._prompt_for_choice(p, options, prompt); hand_choices.append(options.pop(choice))
                p.hand = hand_choices; p.discard_pile = list(options.values())
            else: random.shuffle(p.discard_pile); p.hand = p.discard_pile[:4]; p.discard_pile = p.discard_pile[4:]
        self._pause("Setup complete. The first round is about to begin.")
    def _run_round(self) -> None:
        self.gs.action_log.clear()
        self.gs.action_log.append(f"--- Round {self.gs.round_num} Begins ---")
        self.gs.event_log.clear()
        for p in self.gs.players: 
            p.is_invulnerable = False
            p.knocked_out_this_turn = False
            # Reset advancement counts for all spells on the board
            for clash_list in p.board:
                for spell in clash_list:
                    spell.advances_this_round = 0
        
        try:
            for i in range(1, 5):
                self.gs.clash_num = i
                self._run_clash()
        except RoundOverException:
            self.gs.action_log.append(f"{Colors.WARNING}The round has ended early due to trunk loss!{Colors.ENDC}")
            self._pause("Proceeding to the end of the round.")

        self._run_end_of_round()
    def _run_clash(self):
        self._run_prepare_phase()
        if self.gs.game_over: return # Check after prepare phase in case a player couldn't play

        self._run_cast_phase()
        if self.gs.game_over: return

        self._run_resolve_phase()
        if self.gs.game_over: return

        # Only run the Advance Phase if it's not the final clash.
        if self.gs.clash_num < 4:
            self._run_advance_phase()
            if self.gs.game_over: return

    def _run_prepare_phase(self) -> None:
        self.gs.action_log.clear()
        self.gs.action_log.append(f"--- Clash {self.gs.clash_num}: PREPARE ---")
        
        turn_order_indices = [(self.gs.ringleader_index + i) % len(self.gs.players) for i in range(len(self.gs.players))]

        for player_index in turn_order_indices:
            player: Player = self.gs.players[player_index]
            
            if player.is_invulnerable or not player.hand:
                self.gs.action_log.append(f"{player.name} cannot play a spell.")
                self._pause()
                continue

            card_to_play: Card | None = None
            if player.is_human:
                if len(player.hand) == 1:
                    card_to_play = player.hand.pop(0)
                    self.gs.action_log.append(f"You only have one card in hand. Automatically preparing [{card_to_play.name}].")
                else:
                    options = {i+1: c for i, c in enumerate(player.hand)}
                    choice = self._prompt_for_choice(player, options, f"{player.name}, choose a card to prepare:")
                    if choice is not None:
                        card_to_play = player.hand.pop(choice-1)
            else: # AI logic
                chosen_index = self.ai_player.choose_card_to_play(player, self.gs)
                if chosen_index is not None:
                    card_to_play = player.hand.pop(chosen_index)

            if card_to_play:
                # --- THIS IS THE KEY FIX ---
                # Log opponent's play generically, but your play specifically.
                if player.is_human:
                    log_message = f"{player.name} prepared [{card_to_play.name}]."
                else:
                    log_message = f"{player.name} has prepared a spell."
                
                player.board[self.gs.clash_num - 1].append(PlayedCard(card_to_play, player))
                self.gs.action_log.append(log_message)
            else:
                self.gs.action_log.append(f"{player.name} did not play a spell.")

            self._pause()

    def _run_cast_phase(self):
        self.gs.action_log.clear(); self.gs.action_log.append(f"--- Clash {self.gs.clash_num}: CAST ---")
        # --- NEW: Flip all prepared cards to active ---
        for p in self.gs.players:
            for spell in p.board[self.gs.clash_num - 1]:
                if spell.status == 'prepared':
                    spell.status = 'active'
        self._pause("All spells are revealed simultaneously!")
    
    def _handle_priority_choices(self) -> None:
        """Allow human players to choose resolution order for their same-priority spells."""
        # Group spells by priority and owner
        priority_groups = {}
        for spell_info in self.gs.resolution_queue:
            key = (spell_info['p_val'], spell_info['caster_idx'])
            if key not in priority_groups:
                priority_groups[key] = []
            priority_groups[key].append(spell_info)
        
        # Rebuild queue with player choices
        new_queue = []
        for key in sorted(priority_groups.keys()):
            group = priority_groups[key]
            if len(group) > 1 and self.gs.players[key[1]].is_human:
                # Human player has multiple spells at same priority
                self.gs.action_log.append(f"You have multiple spells with priority {key[0]}. Choose resolution order:")
                remaining = group.copy()
                ordered = []
                
                while remaining:
                    if len(remaining) == 1:
                        ordered.append(remaining[0])
                        break
                    
                    options = {i+1: info['played_card'] for i, info in enumerate(remaining)}
                    prompt = f"Choose which spell to resolve {'first' if not ordered else 'next'}:"
                    choice = self._prompt_for_choice(self.gs.players[key[1]], options, prompt, view_key='card.name')
                    
                    if choice is not None:
                        chosen_spell = options[choice]
                        for info in remaining:
                            if info['played_card'] == chosen_spell:
                                ordered.append(info)
                                remaining.remove(info)
                                break
                
                new_queue.extend(ordered)
            else:
                # AI or single spell - keep original order
                new_queue.extend(group)
        
        self.gs.resolution_queue = new_queue

    def add_to_resolution_queue(self, played_card: PlayedCard) -> None:
        """Adds a newly cast spell to the current resolution queue and resorts it."""
        caster_idx = self.gs.players.index(played_card.owner)
        p_val = 99 if played_card.card.priority == 'A' else int(played_card.card.priority)
        
        new_spell_info = {'p_val': p_val, 'caster_idx': caster_idx, 'played_card': played_card}
        self.gs.resolution_queue.append(new_spell_info)
        # Re-sort the queue to respect priority
        self.gs.resolution_queue.sort(key=lambda x: (x['p_val'], x['caster_idx']))

    def _run_resolve_phase(self) -> None:
        self.gs.action_log.clear(); self.gs.action_log.append(f"--- Clash {self.gs.clash_num}: RESOLVE ---")
        
        active_spells = [s for p in self.gs.players for s in p.board[self.gs.clash_num-1] if s.status == 'active']
        self.gs.resolution_queue = []
        for spell in active_spells:
            p_val = 99 if spell.card.priority == 'A' else int(spell.card.priority)
            caster_idx = self.gs.players.index(spell.owner)
            self.gs.resolution_queue.append({'p_val': p_val, 'caster_idx': caster_idx, 'played_card': spell})
        
        self.gs.resolution_queue.sort(key=lambda x: (x['p_val'], x['caster_idx']))
        
        # Let human players choose order for same-priority spells
        self._handle_priority_choices()
        
        processed_this_phase = []
        
        # Use a while loop because the queue can change during resolution (e.g., Illuminate)
        while self.gs.resolution_queue:
            spell_info = self.gs.resolution_queue.pop(0)
            caster: Player = self.gs.players[spell_info['caster_idx']]
            played_card: PlayedCard = spell_info['played_card']
            
            if played_card in processed_this_phase or played_card.status != 'active':
                continue

            self.gs.action_log.clear()
            self.gs.action_log.append(f"--> Resolving {caster.name}'s [{Colors.BOLD}{played_card.card.name}{Colors.ENDC}] (P:{played_card.card.priority})")
            self.gs.action_log.append(f"    {Colors.GREY}{played_card.card.get_instructions_text()}{Colors.ENDC}")
            self._pause("Executing effect...")

            self.action_handler.execute_effects(played_card.card.resolve_effects, self.gs, caster, played_card.card)
            
            played_card.has_resolved = True
            self.action_handler._fire_event('spell_resolved', self.gs, player=caster.name, card_id=played_card.card.id)
            processed_this_phase.append(played_card)
            self._post_resolution_checks()

    def _post_resolution_checks(self) -> None:
        for player in self.gs.players:
            # Check if a player was just knocked out (health is 0 but we haven't processed it yet)
            if player.health <= 0 and not player.knocked_out_this_turn:
                player.knocked_out_this_turn = True # Mark as processed for this turn
                if self._handle_trunk_loss(player) == 'round_over':
                    raise RoundOverException()
        
        # After handling any trunk losses, check if the round should end.
        # This will raise the RoundOverException if the condition is met.
        self._check_for_round_end()

    def _run_advance_phase(self) -> None:
        self.gs.action_log.clear(); self.gs.action_log.append(f"--- Clash {self.gs.clash_num}: ADVANCE ---"); self._pause()
        
        # We need to copy the list as the underlying board state can change
        advancing_spells = [s for p in self.gs.players for s in p.board[self.gs.clash_num - 1] if s.status == 'active' and s.card.advance_effects]
        
        if not advancing_spells:
            self.gs.action_log.append("No spells to advance this clash.")
            return

        for played_card in advancing_spells:
            if self.gs.game_over: return
            if played_card.status != 'active': continue # Skip if cancelled mid-phase

            caster = played_card.owner
            prompt = f"--> Advancing {caster.name}'s [{played_card.card.name}]..."; self._pause(prompt)
            for effect in played_card.card.advance_effects:
                # Call the correct method: _execute_action for a single effect
                if self.condition_checker.check(effect['condition'], self.gs, caster, played_card.card):
                    self.action_handler._execute_action(effect['action'], self.gs, caster, played_card.card)
                    if self.gs.game_over: return
                    self._pause()

    def _run_end_of_round(self) -> None:
        self.gs.action_log.clear(); self.gs.action_log.append(f"--- End of Round {self.gs.round_num} ---")
        for p in self.gs.players:
            for clash_list in p.board:
                for spell in clash_list: p.discard_pile.append(spell.card)
            p.board = [[] for _ in range(4)]
        self.gs.ringleader_index = (self.gs.ringleader_index + 1) % len(self.gs.players)
        self.gs.action_log.append(f"Board cleared. The new Ringleader is {self.gs.players[self.gs.ringleader_index].name}."); self._pause()
        
        for p in self.gs.players:
            # Step 1: Handle Keep/Discard phase
            if p.is_human:
                if p.hand:
                    options = {i+1: c for i, c in enumerate(p.hand)}; kept_cards = []
                    while True:
                        prompt = "Choose cards to KEEP from your hand (type 'done' when finished):"; choice = self._prompt_for_choice(p, options, prompt)
                        if choice == 'done': break
                        if choice is not None: kept_cards.append(options.pop(choice))
                    for card in options.values(): p.discard_pile.append(card)
                    p.hand = kept_cards
            else: # AI Logic
                if p.hand:
                    discards = [c for c in p.hand if 'remedy' not in c.types and p.health/p.max_health > 0.7]
                    p.discard_pile.extend(discards); p.hand = [c for c in p.hand if c not in discards]

            # Step 2: Handle Recall phase
            max_hand_size = 4 + (3 - p.trunks)
            while len(p.hand) < max_hand_size:
                if not p.discard_pile: break
                if p.is_human:
                    prompt = f"Recall up to {max_hand_size - len(p.hand)} more card(s). Choose from discard (or 'done'):"
                    options = {i+1: c for i, c in enumerate(p.discard_pile)}; choice = self._prompt_for_choice(p, options, prompt, view_key='name');
                    if choice == 'done': break
                    if choice is not None: 
                        recalled_card = p.discard_pile.pop(choice - 1)
                        p.hand.append(recalled_card)
                        self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
                else: 
                    recalled_card = p.discard_pile.pop(0)
                    p.hand.append(recalled_card)
                    self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
            
            # Step 3: Final check for hand size and force draft if needed
            if len(p.hand) < 4:
                self.gs.action_log.append(f"{p.name}'s hand is below 4 cards. They must draft a new set."); self._pause()
                self._check_and_rebuild_deck()
                if self.gs.main_deck:
                    if p.is_human:
                        options = {i+1: s for i, s in enumerate(self.gs.main_deck[:5]) if s}; choice = self._prompt_for_choice(p, options, "Choose a new spell set:")
                        new_set = options[choice]; self.gs.main_deck.remove(new_set)
                    else: new_set = self.gs.main_deck.pop(0)
                    p.hand.extend(new_set)
                    self.gs.action_log.append(f"{p.name} drafted the '{new_set[0].elephant}' set.")
                    
                    # Discard down if necessary
                    while len(p.hand) > max_hand_size:
                        self.gs.action_log.append(f"{p.name}'s hand is over max size ({max_hand_size}).")
                        self._pause()
                        if p.is_human:
                            prompt = f"Choose a card to discard:"; options = {i+1: c for i, c in enumerate(p.hand)}; choice = self._prompt_for_choice(p, options, prompt)
                            p.discard_pile.append(p.hand.pop(choice-1))
                        else: p.discard_pile.append(p.hand.pop())
        self._pause("All players have managed their hands. The next round will begin.")

    def _handle_trunk_loss(self, player: Player) -> str:
        message = player.lose_trunk()
        self.gs.action_log.append(f"{Colors.FAIL}{message}{Colors.ENDC}")
        for clash_list in player.board:
            for spell in clash_list:
                player.discard_pile.append(spell.card)
        player.board = [[] for _ in range(4)]
        self.gs.action_log.append(f"{player.name}'s spells were cleared from the board.")
        
        # Check for sudden death - if only one player is not invulnerable, round ends
        vulnerable_players = [p for p in self.gs.players if not p.is_invulnerable]
        if len(vulnerable_players) <= 1:
            return 'round_over'
        return 'continue'

    def _check_for_round_end(self) -> None:
        # Round ends if only one player is not invulnerable (can still play)
        vulnerable_players = [p for p in self.gs.players if not p.is_invulnerable]
        if len(vulnerable_players) <= 1:
            raise RoundOverException()
    def _check_for_game_end(self) -> bool:
        active_players = [p for p in self.gs.players if p.trunks > 0]
        if len(active_players) < 2:
            self.gs.game_over = True
            return True
        return False
    def _check_and_rebuild_deck(self):
        if not self.gs.main_deck:
            self.gs.action_log.append(f"{Colors.WARNING}Main deck is empty! Rebuilding from discards...{Colors.ENDC}"); self._pause()
            all_discards = defaultdict(list)
            for p in self.gs.players:
                for card in p.discard_pile: all_discards[card.elephant].append(card)
            
            new_deck = []; remaining_discards = []
            original_set_counts = defaultdict(int)
            for data in json.loads(SPELL_JSON_DATA): original_set_counts[data['elephant']] += 1

            for elephant, cards in all_discards.items():
                if len(cards) == original_set_counts[elephant]: new_deck.append(cards)
                else: remaining_discards.extend(cards)
            
            for p in self.gs.players: p.discard_pile = [c for c in remaining_discards if c in p.discard_pile] # This is a simplification
            
            random.shuffle(new_deck); self.gs.main_deck = new_deck
            self.gs.action_log.append(f"Rebuilt main deck with {len(new_deck)} complete sets.")

if __name__ == "__main__":
    try:
        player_names = ["Human Player", "AI Opponent"]; engine = GameEngine(player_names); engine.run_game()
    except KeyboardInterrupt: print("\n\nGame exited by user. Goodbye!")
    except Exception:
        clear_screen(); print("\n\n--- A CRITICAL ERROR OCCURRED ---")
        traceback.print_exc(); print("---------------------------------")
        print("\nPlease copy this error report for debugging.")