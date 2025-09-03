import json
import os
import sys
import random
import traceback
from collections import defaultdict
from typing import Any

# Import AI classes from separate module
from ai import EasyAI, MediumAI, HardAI, ExpertAI

# Import game logger for analytics
from game_logger import game_logger

# --- CONSTANTS ---
DEBUG_AI = False  # Set to False to disable AI decision logging

# Load spell data from external JSON file
def load_spell_data():
    """Load spell data from spells.json file."""
    spell_file = os.path.join(os.path.dirname(__file__), 'spells.json')
    try:
        with open(spell_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {spell_file}")
        print("Please ensure spells.json is in the same directory as this script.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {spell_file}: {e}")
        sys.exit(1)

SPELL_DATA = load_spell_data()

# --- UTILITIES ---
def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
class Colors:
    HEADER='\033[95m'; BLUE='\033[94m'; CYAN='\033[96m'; GREEN='\033[92m'
    WARNING='\033[93m'; FAIL='\033[91m'; ENDC='\033[0m'; BOLD='\033[1m'
    UNDERLINE='\033[4m'; GREY='\033[90m'; YELLOW='\033[93m'
    
# Element emojis
ELEMENT_EMOJIS = {
    'Fire': '🔥', 'Water': '💧', 'Wind': '🌪️', 'Earth': '🗿',
    'Wood': '🌳', 'Metal': '⚔️', 'Time': '⏰', 'Space': '🪐',
    'Sunbeam': '☀️', 'Moonshine': '🌙', 'Shadow': '🌑', 'Aster': '⭐',
    'Blood': '🩸', 'Ichor': '🪽', 'Venom': '☠️', 'Nectar': '🍯',
    'Lightning': '⚡️', 'Thunder': '🫨', 'Twilight': '☯️'
}

# Action emojis
ACTION_EMOJIS = {
    'damage': '💥', 'heal': '💙', 'weaken': '📉', 'bolster': '📈',
    'advance': '➡️', 'discard': '🗑️', 'recall': '♻️'
}

# Spell type emojis
SPELL_TYPE_EMOJIS = {
    'conjury': '⚠️',
    'attack': '🪓',
    'response': '🛡️',
    'remedy': '⛑️',
    'boost': '➡️'
}
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
        self.theme: str = card_data.get('theme', '')
        self.base: bool = card_data.get('base', False)
        self.resolve_effects: list[dict] = card_data.get('resolve_effects', [])
        self.advance_effects: list[dict] = card_data.get('advance_effects', [])
        self.passive_effects: list[dict] = card_data.get('passive_effects', [])
        self.instruction: str = card_data.get('instruction', '')
    def __repr__(self) -> str: return f"Card({self.name})"
    def get_instructions_text(self) -> str:
        # Generate the original text from effects
        texts = []
        if self.passive_effects:
            for effect in self.passive_effects:
                action_text = self._format_action(effect)
                texts.append(f"Passive: {action_text}")
        if self.resolve_effects:
            for effect in self.resolve_effects:
                action = effect['action']
                condition_text = self._format_condition(effect['condition'])
                action_text = self._format_action(action)
                texts.append(f"{condition_text}{action_text}")
        if self.advance_effects:
            adv_texts = [self._format_action(eff['action']) for eff in self.advance_effects]
            texts.append(f"Advance Phase: {', '.join(adv_texts)}")
        generated_text = "; ".join(texts) if texts else "No effect."
        
        # If we have a cleaned instruction, show both
        if self.instruction:
            return f"{self.instruction}\n    {Colors.GREY}(Generated: {generated_text}){Colors.ENDC}"
        
        # Otherwise just return the generated text
        return generated_text
    def _format_condition(self, cond: dict) -> str:
        cond_type = cond.get('type')
        if cond_type == 'always': return ""
        if cond_type == 'if_caster_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1)
            exclude_self = p.get('exclude_self', False)
            other_text = " other" if exclude_self else ""
            spell_type_text = p['spell_type'] if p['spell_type'] != 'any' else ""
            if spell_type_text:
                return f"If you have {count_str}{other_text} active {spell_type_text} spell(s) this clash: "
            else:
                return f"If you have {count_str}{other_text} active spell(s) this clash: "
        if cond_type == 'if_enemy_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1)
            return f"If an enemy has {count_str} active {p['spell_type']} spell(s): "
        if cond_type == 'if_spell_previously_resolved_this_round': return "If this spell resolved in a past clash: "
        if cond_type == 'if_spell_was_active_in_other_clashes':
            count = cond.get('parameters', {}).get('count', 2)
            return f"If this spell was active in at least {count} other clashes: "
        if cond_type == 'if_spell_advanced_count':
            count = cond.get('parameters', {}).get('count', 2)
            return f"If this spell advanced {count} times: "
        if cond_type == 'if_not': return f"Otherwise: "
        if cond_type == 'if_board_has_active_spell_of_type':
            p = cond['parameters']
            count_str = p.get('count', 1)
            return f"If there are {count_str} other active {p['spell_type']} spells on the board: "
        return f"If {cond_type.replace('_', ' ')}: "
    def _format_action(self, action) -> str:
        # Handle case where action is a list of actions
        if isinstance(action, list):
            return " AND ".join([self._format_action(a) for a in action])
        
        action_type = action.get('type')
        if action_type == 'player_choice':
            options = [self._format_action(opt) for opt in action['options']]
            return f"Choose: {' OR '.join(options)}"
        
        params = action.get('parameters', {}); value = params.get('value', '')
        target_raw = action.get('target', 'self')
        target_map = {
            'self': 'yourself', 
            'prompt_enemy': 'an enemy', 
            'this_spell': 'this spell',
            'prompt_other_friendly_active_spell': 'another friendly active spell',
            'prompt_friendly_past_spell': 'one of your past spells',
            'all_enemies_and_their_conjuries': 'each enemy and their conjuries',
            'all_enemies_who_met_condition': 'each enemy who met the condition',
            'prompt_player_or_conjury': 'an enemy or conjury',
            'prompt_player': 'an enemy',
            'prompt_any_active_spell': 'any active spell',
            'prompt_enemy_past_spell': 'an enemy past spell',
            'each_enemy': 'each enemy',
            'all_enemy_remedy_spells': 'all enemy remedy spells',
            'all_enemy_attack_spells': 'all enemy attack spells',
            'prompt_enemy_boost_spell': 'an enemy boost spell',
            'prompt_enemy_active_spell': 'an enemy active spell'
        }
        target = target_map.get(target_raw, target_raw.replace('_', ' '))
        
        # Format based on action type
        if action_type == 'damage':
            return f"Deal {value} damage to {target}"
        elif action_type == 'damage_multi_target':
            return f"Deal {value} damage to {target}"
        elif action_type == 'heal':
            return f"Heal {target} for {value}"
        elif action_type == 'weaken':
            return f"Weaken {target} by {value}"
        elif action_type == 'bolster':
            return f"Bolster {target} by {value}"
        elif action_type == 'advance':
            return f"Advance {target}"
        elif action_type == 'discard_from_hand':
            return f"Force {target} to discard {value} card(s)"
        elif action_type == 'cast_extra_spell':
            value = params.get('value', 1)
            if value > 1:
                return f"Cast up to {value} extra spells from your hand"
            return f"Cast an extra spell from your hand"
        elif action_type == 'damage_per_spell_from_other_clashes':
            return f"Deal damage equal to spells that were active in other clashes"
        elif action_type == 'damage_per_spell':
            spell_type = params.get('spell_type', 'any')
            return f"Deal damage to {target} equal to your other active {spell_type} spells"
        elif action_type == 'heal_per_spell':
            spell_type = params.get('spell_type', 'any')
            return f"Heal {target} for each of your other active {spell_type} spells"
        elif action_type == 'recall_from_enemy_hand':
            return f"Reveal a spell from each enemy's hand and recall one"
        elif action_type == 'move_clash_to_clash':
            return f"Move all spells from one clash to another"
        elif action_type == 'discard':
            if target == 'this_spell':
                return f"Discard this spell"
            return f"Discard {target}"
        elif action_type == 'copy_spell':
            return f"Copy an enemy spell"
        elif action_type == 'recall_from_board':
            return f"Recall an enemy boost spell from the board"
        elif action_type == 'damage_per_enemy_spell_type':
            spell_type = params.get('spell_type', 'any')
            return f"Deal damage to each enemy equal to their {spell_type} spells"
        elif action_type == 'damage_equal_to_enemy_attack_damage':
            return f"Deal damage to each enemy equal to their attack spell's damage"
        elif action_type == 'cancel':
            if 'all_enemy' in str(target):
                spell_type = str(target).replace('all_enemy_', '').replace('_spells', '')
                return f"Cancel all enemy {spell_type} spells"
            return f"Cancel {target}"
        elif action_type == 'move_to_future_clash':
            return f"Move a spell to a future clash"
        elif action_type == 'recall':
            source = params.get('source', 'discard')
            if source == 'friendly_past_spells':
                return f"Recall a spell from past clashes to your hand"
            return f"Recall a spell from {source}"
        elif action_type == 'protect_from_enemy_effects':
            # This is a passive effect, shown differently
            effects = params.get('effects', [])
            return f"Protects your other spells from enemy {', '.join(effects)} effects"
        elif action_type == 'advance_from_hand':
            value = params.get('value', 1)
            return f"Play up to {value} spell(s) from your hand to future clashes"
        elif action_type == 'weaken_per_spell':
            spell_type = params.get('spell_type', 'any')
            exclude_self = params.get('exclude_self', False)
            self_text = " other" if exclude_self else ""
            return f"Weaken {target} for each of your{self_text} active {spell_type} spells"
        elif action_type == 'advance_from_past_clash':
            return f"Advance a spell from a past clash"
        elif action_type == 'sequence':
            # Format sequence of actions
            actions = action.get('actions', [])
            descriptions = [self._format_action(act) for act in actions]
            return " then ".join(descriptions)
        elif action_type == 'pass':
            return "Do nothing"
        elif action_type == 'modify_spell_logic':
            change = params.get('change', '')
            if change == 'or_to_and':
                return "Changes 'Choose one' effects on your other spells to 'Do both'"
        elif action_type == 'modify_priority':
            value = params.get('value', 0)
            return f"Reduces priority of your other spells by {abs(value)} (minimum 1)"
        else:
            return f"{action_type.replace('_', ' ').title()} {target}".strip()

class PlayedCard:
    def __init__(self, card: Card, owner: 'Player'):
        self.card: Card = card
        self.owner: 'Player' = owner
        self.status: str = 'prepared'
        self.has_resolved: bool = False
        self.resolve_condition_met: bool = False  # Track if resolve condition was met
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
        self.all_cards: dict[int, Card] = {data['id']: Card(data) for data in SPELL_DATA}
        sets = defaultdict(list);
        for data in SPELL_DATA: sets[data['elephant']].append(self.all_cards[data['id']])
        self.main_deck: list[list[Card]] = list(sets.values()); random.shuffle(self.main_deck)
        self.round_num: int = 1; self.clash_num: int = 1; self.ringleader_index: int = 0
        self.action_log: list[str] = ["Game has started!"]
        self.event_log: list[dict] = []
        self.game_over: bool = False
        self.resolution_queue: list[dict] = []

# --- DISPLAY ENGINE ---
class DashboardDisplay:
    def _get_spell_type_icons(self, card):
        """Get icons representing the spell's types"""
        icons = []
        if card.is_conjury:
            icons.append(SPELL_TYPE_EMOJIS['conjury'])
        for spell_type in ['attack', 'response', 'remedy', 'boost']:
            if spell_type in card.types:
                icons.append(SPELL_TYPE_EMOJIS[spell_type])
        return ' '.join(icons)  # Added space between icons
    def draw(self, gs, pov_player_index=0, prompt=""):
        clear_screen(); print(f"{Colors.HEADER}{'='*34}[ Elemental Elephants ]{'='*33}{Colors.ENDC}")
        print(f"Round: {gs.round_num} | Clash: {gs.clash_num} | Ringleader: 🐘 {Colors.BOLD}{gs.players[gs.ringleader_index].name}{Colors.ENDC}")
        print("-" * 150)
        header = f"{'PLAYER'.ljust(15)} | {'HEALTH'.ljust(16)} | {'TRUNKS'} | {'DISCARD'} | {'CLASH I'.ljust(30)} | {'CLASH II'.ljust(30)} | {'CLASH III'.ljust(30)}| {'CLASH IV'.ljust(30)}"
        print(Colors.BOLD + header + Colors.ENDC); print("-" * 150)
        
        # Find the maximum number of spells in any clash for any player
        max_spells_per_clash = 0
        for p in gs.players:
            for clash_list in p.board:
                visible_spells = [s for s in clash_list if s.status in ['revealed', 'prepared', 'cancelled']]
                max_spells_per_clash = max(max_spells_per_clash, len(visible_spells))
        
        # Display each player's row, with multiple rows if needed for stacked spells
        for i, p in enumerate(gs.players):
            # Prepare player info that will be shown on first row only
            is_current = ">" if i == pov_player_index and p.is_human else " "
            p_color = Colors.CYAN if i == pov_player_index and p.is_human else Colors.ENDC
            p_info = f"{is_current} {p_color}{p.name.ljust(13)}{Colors.ENDC}"
            h_color = Colors.GREEN if p.health > p.max_health / 2 else Colors.FAIL
            health_str = f"{h_color}{str(p.health).rjust(2)}/{str(p.max_health).ljust(2)}{Colors.ENDC}".ljust(25)
            trunks_str = ("O " * p.trunks).ljust(6)
            discard_str = str(len(p.discard_pile)).ljust(7)
            
            # Build clash content for each row
            for row in range(max(1, max_spells_per_clash)):
                if row == 0:
                    # First row shows player info
                    row_str = f"{p_info} | {health_str} | {trunks_str} | {discard_str} | "
                else:
                    # Additional rows are just spacing
                    row_str = " " * 15 + " | " + " " * 16 + " | " + " " * 6 + " | " + " " * 7 + " | "
                
                # Add clash content for this row
                for j in range(4):
                    slot_content = p.board[j]
                    visible_spells = [s for s in slot_content if s.status in ['revealed', 'prepared', 'cancelled']]
                    
                    if row >= len(visible_spells):
                        # No spell at this row position
                        if row == 0 and not visible_spells:
                            slot_str = "[Empty]"
                        else:
                            slot_str = ""
                    else:
                        # Show the spell at this row position
                        s = visible_spells[row]
                        if s.status == 'prepared' and s.owner != gs.players[pov_player_index]:
                            slot_str = f"{Colors.BLUE}[Spell Prepared]{Colors.ENDC}"
                        else:
                            color = Colors.GREY if s.status == 'cancelled' else ''
                            emoji = ELEMENT_EMOJIS.get(s.card.element, '')
                            type_icons = self._get_spell_type_icons(s.card)
                            slot_str = f"{color}{emoji} {s.card.name} {type_icons}{Colors.ENDC}"
                    
                    row_str += slot_str.ljust(30) + " | "
                
                print(row_str.rstrip(" |"))

        print("=" * 150); pov_player = gs.players[pov_player_index]
        if pov_player.is_human:
            print(f"\n--- {Colors.CYAN}YOUR HAND ({pov_player.name}){Colors.ENDC}")
            if not pov_player.hand: print(f"{Colors.GREY}Your hand is empty.{Colors.ENDC}")
            else:
                for i, card in enumerate(pov_player.hand):
                    emoji = ELEMENT_EMOJIS.get(card.element, '')
                    type_icons = self._get_spell_type_icons(card)
                    type_str = '/'.join(card.types) if card.types else 'None'
                    print(f"[{i+1}] {emoji} {Colors.BOLD}{card.name}{Colors.ENDC} {type_icons} (P:{card.priority}, {type_str})"); 
                    print(f"    {Colors.GREY}> {card.get_instructions_text()}{Colors.ENDC}")
        print("-" * 89);
        if gs.action_log: print(f"{Colors.BOLD}LOG:{Colors.ENDC}"); [print(f"  {entry}") for entry in gs.action_log[-5:]]
        if prompt: print(f"\n>>> {Colors.WARNING}{prompt}{Colors.ENDC}")


# --- LOGIC ENGINES ---
class ConditionChecker:
    def check(self, condition_data, gs, caster, current_card):
        cond_type = condition_data.get('type')
        if cond_type == 'always': return True

        if cond_type == 'if_spell_previously_resolved_this_round':
            # Check if this specific spell resolved in a past clash
            params = condition_data.get('parameters', {})
            required_count = params.get('count', 1)
            
            if required_count == 1:
                # Original behavior for Turbulence - check if THIS spell resolved before
                for event in gs.event_log:
                    if (event['type'] == 'spell_resolved' and
                        event['player'] == caster.name and
                        event['card_id'] == current_card.id and
                        event['clash'] < gs.clash_num): # Must be from a previous clash
                        return True
                return False
            else:
                # For Impact - check if this spell PREVIOUSLY resolved at least 'count' times
                # Don't count the current resolution (it hasn't happened yet)
                resolve_count = 0
                for event in gs.event_log:
                    if (event['type'] == 'spell_resolved' and
                        event['player'] == caster.name and
                        event['card_id'] == current_card.id):
                        resolve_count += 1
                
                # Debug logging for Impact
                if current_card.name == "Impact" and DEBUG_AI:
                    gs.action_log.append(f"{Colors.GREY}[DEBUG] Impact has previously resolved {resolve_count} times, needs {required_count} to trigger weaken{Colors.ENDC}")
                
                return resolve_count >= required_count

        active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s and s.status == 'revealed']
        if cond_type == 'if_caster_has_active_spell_of_type':
            params = condition_data['parameters']
            spell_type = params['spell_type']
            exclude_self = params.get('exclude_self', False)
            required_count = params.get('count', 1)
            
            # Check if we should use historical data (event log) or current state
            # If the spell condition explicitly sets check_historical: true, use event log
            # Otherwise, always check current state (even during advance phase)
            check_historical = params.get('check_historical', False)
            in_advance_phase = any(event['type'] == 'spell_resolved' for event in gs.event_log if event['clash'] == gs.clash_num)
            
            if check_historical and in_advance_phase:
                # Check event log for spells that WERE active at the start of resolve phase
                # This is for cards like Bolts that check "if you had other active spells this clash"
                count = 0
                for event in gs.event_log:
                    if (event['type'] == 'spell_active_in_clash' and 
                        event['clash'] == gs.clash_num and
                        event['player'] == caster.name):
                        # Need to check if this spell matches the type
                        if exclude_self and event['card_id'] == current_card.id:
                            continue
                        # Check spell type by finding the card
                        card = gs.all_cards.get(event['card_id'])
                        if card and (spell_type == 'any' or spell_type in card.types):
                            count += 1
                return count >= required_count
            else:
                # Check currently active spells (default behavior for all phases)
                count = 0
                for spell in active_spells_this_clash:
                    if spell.owner == caster and (spell_type == 'any' or spell_type in spell.card.types):
                        if exclude_self and spell.card.id == current_card.id: 
                            continue
                        count += 1
                return count >= required_count
        
        if cond_type == 'if_enemy_has_active_spell_of_type':
            params = condition_data['parameters']
            required_count = params.get('count', 1)
            spell_type = params['spell_type']
            enemies = [p for p in gs.players if p != caster]
            
            # For Clap - check if ANY enemy has 2+ spells
            if spell_type == 'any' and required_count >= 2:
                for enemy in enemies:
                    enemy_spell_count = 0
                    for spell in active_spells_this_clash:
                        if spell.owner == enemy:
                            enemy_spell_count += 1
                    if enemy_spell_count >= required_count:
                        return True
                return False
            else:
                # Original behavior - total count across all enemies
                count = 0
                for spell in active_spells_this_clash:
                    if spell.owner in enemies and (spell_type == 'any' or spell_type in spell.card.types):
                        count += 1
                return count >= required_count
        
        if cond_type == 'if_board_has_active_spell_of_type':
            params = condition_data['parameters']; count = 0
            for spell in active_spells_this_clash:
                if params['spell_type'] in spell.card.types:
                    if params.get('exclude_self', False) and spell.card.id == current_card.id: continue
                    count += 1
            return count >= params.get('count', 1)
        
        if cond_type == 'if_not': return not self.check(condition_data['sub_condition'], gs, caster, current_card)
        
        if cond_type == 'if_spell_advanced_this_turn':
            # For Agonize - check if THIS SPECIFIC spell advanced this turn
            # Look for advance events for this spell in the current round
            for event in gs.event_log:
                if (event['type'] == 'spell_advanced' and
                    event.get('round', 0) == gs.round_num and
                    event.get('player') == caster.name and
                    event.get('card_id') == current_card.id):
                    return True
            return False
        
        if cond_type == 'if_resolve_condition_was_met':
            # For spells like Clap and Enfeeble that should only advance if resolve succeeded
            # Find the PlayedCard for this spell
            for player in gs.players:
                for clash_list in player.board:
                    for spell in clash_list:
                        if spell.card.id == current_card.id and spell.owner == caster:
                            return spell.resolve_condition_met
            return False
        
        if cond_type == 'if_spell_was_active_in_other_clashes':
            # For Impact - check if this spell was active in at least 'count' other clashes
            params = condition_data.get('parameters', {})
            required_count = params.get('count', 2)
            
            # Count how many OTHER clashes this spell was active in
            active_clash_count = 0
            for event in gs.event_log:
                if (event['type'] == 'spell_active_in_clash' and
                    event['player'] == caster.name and
                    event['card_id'] == current_card.id and
                    event['clash'] != gs.clash_num):  # Don't count current clash
                    active_clash_count += 1
            
            # Debug logging for Impact
            if current_card.name == "Impact" and DEBUG_AI:
                gs.action_log.append(f"{Colors.GREY}[DEBUG] Impact was active in {active_clash_count} other clashes, needs {required_count} to trigger weaken{Colors.ENDC}")
            
            return active_clash_count >= required_count
        
        if cond_type == 'if_spell_advanced_count':
            # For Turbulence - check if this spell has advanced at least 'count' times
            params = condition_data.get('parameters', {})
            required_count = params.get('count', 2)
            
            # Count how many times THIS spell has advanced
            advance_count = 0
            for event in gs.event_log:
                if (event['type'] == 'spell_advanced' and
                    event.get('player') == caster.name and
                    event.get('card_id') == current_card.id):
                    advance_count += 1
            
            # Debug logging
            if DEBUG_AI:
                gs.action_log.append(f"{Colors.GREY}[DEBUG] {current_card.name} has advanced {advance_count} times, needs {required_count}{Colors.ENDC}")
            
            return advance_count >= required_count
        
        return False
# +++ START: REPLACE THE ENTIRE ActionHandler CLASS WITH THIS +++
class ActionHandler:
    def __init__(self, engine: 'GameEngine'):
        self.engine: 'GameEngine' = engine

    def _fire_event(self, event_type: str, gs: 'GameState', **kwargs: Any) -> None:
        event = {"clash": gs.clash_num, "type": event_type}; event.update(kwargs); gs.event_log.append(event)
        
        # Log to game logger for analytics
        if event_type == 'player_damaged':
            # Extract spell info from current context
            current_card = None
            for key, value in kwargs.items():
                if key == 'card_id':
                    # Find the card by ID
                    for spell in SPELL_DATA:
                        if spell.get('id') == value:
                            current_card = spell
                            break
            
            if current_card:
                game_logger.log_damage_dealt(
                    source_player=kwargs.get('player'),
                    target_player=kwargs.get('target'),
                    damage_amount=kwargs.get('value', 0),
                    spell_name=current_card.get('card_name', 'Unknown'),
                    element=current_card.get('element', 'Unknown'),
                    clash_num=gs.clash_num,
                    round_num=gs.round_num,
                    is_self_damage=(kwargs.get('player') == kwargs.get('target'))
                )
        
        elif event_type == 'player_healed':
            # Find the healing spell
            current_card = None
            for key, value in kwargs.items():
                if key == 'card_id':
                    for spell in SPELL_DATA:
                        if spell.get('id') == value:
                            current_card = spell
                            break
            
            if current_card:
                game_logger.log_healing_done(
                    source_player=kwargs.get('player'),  # The healed player
                    target_player=kwargs.get('player'),   # Same for self-heal
                    heal_amount=kwargs.get('value', 0),
                    spell_name=current_card.get('card_name', 'Unknown'),
                    element=current_card.get('element', 'Unknown'),
                    clash_num=gs.clash_num,
                    round_num=gs.round_num
                )
        
        elif event_type == 'player_weakened':
            # Find the weakening spell
            current_card = None
            for key, value in kwargs.items():
                if key == 'card_id':
                    for spell in SPELL_DATA:
                        if spell.get('id') == value:
                            current_card = spell
                            break
            
            if current_card:
                game_logger.log_weaken_dealt(
                    source_player=kwargs.get('player'),
                    target_player=kwargs.get('target'),
                    weaken_amount=kwargs.get('value', 0),
                    spell_name=current_card.get('card_name', 'Unknown'),
                    element=current_card.get('element', 'Unknown'),
                    clash_num=gs.clash_num,
                    round_num=gs.round_num
                )
        
        elif event_type == 'player_bolstered':
            # Find the bolstering spell
            current_card = None
            for key, value in kwargs.items():
                if key == 'card_id':
                    for spell in SPELL_DATA:
                        if spell.get('id') == value:
                            current_card = spell
                            break
            
            if current_card:
                game_logger.log_bolster_done(
                    source_player=kwargs.get('player'),
                    target_player=kwargs.get('target'),
                    bolster_amount=kwargs.get('value', 0),
                    spell_name=current_card.get('card_name', 'Unknown'),
                    element=current_card.get('element', 'Unknown'),
                    clash_num=gs.clash_num,
                    round_num=gs.round_num
                )
        
        elif event_type == 'spell_advanced':
            # Extract spell name from card_id
            spell_name = 'Unknown'
            for spell in SPELL_DATA:
                if spell.get('id') == kwargs.get('card_id'):
                    spell_name = spell.get('card_name', 'Unknown')
                    break
            
            game_logger.log_spell_advanced(
                player_name=kwargs.get('player'),
                spell_name=spell_name,
                from_clash=gs.clash_num,
                to_clash=gs.clash_num + 1
            )
        
        elif event_type == 'spell_cancelled':
            # Extract spell names
            target_spell_name = 'Unknown'
            canceller_spell_name = 'Unknown'
            for spell in SPELL_DATA:
                if spell.get('id') == kwargs.get('target_card_id'):
                    target_spell_name = spell.get('card_name', 'Unknown')
                if spell.get('id') == kwargs.get('card_id'):
                    canceller_spell_name = spell.get('card_name', 'Unknown')
            
            game_logger.log_spell_cancelled(
                player_name=kwargs.get('player'),
                spell_name=target_spell_name,
                cancelled_by=canceller_spell_name
            )
        
        elif event_type == 'spell_recalled':
            # Extract spell name
            spell_name = 'Unknown'
            for spell in SPELL_DATA:
                if spell.get('id') == kwargs.get('card_id'):
                    spell_name = spell.get('card_name', 'Unknown')
                    break
            
            game_logger.log_spell_recalled(
                player_name=kwargs.get('player'),
                spell_name=spell_name,
                from_location='discard'  # Default, could be enhanced
            )
    
    def _calculate_spell_damage(self, card: 'Card', owner: 'Player', gs: 'GameState') -> int:
        """Calculate the base damage value from a spell card"""
        damage = 0
        
        # Check resolve effects for damage actions
        for effect in card.resolve_effects:
            action = effect.get('action', {})
            if isinstance(action, dict):
                if action.get('type') == 'damage':
                    # Simple damage action
                    damage += action.get('parameters', {}).get('value', 0)
                elif action.get('type') == 'damage_multi_target':
                    # Multi-target damage (same value)
                    damage += action.get('parameters', {}).get('value', 0)
                elif action.get('type') == 'player_choice':
                    # Check choices for damage options
                    for option in action.get('options', []):
                        if option.get('type') == 'damage':
                            # Use the highest damage option
                            option_damage = option.get('parameters', {}).get('value', 0)
                            damage = max(damage, option_damage)
                        elif option.get('type') == 'sequence':
                            # Check sequence for damage
                            seq_damage = 0
                            for seq_action in option.get('actions', []):
                                if seq_action.get('type') == 'damage':
                                    seq_damage += seq_action.get('parameters', {}).get('value', 0)
                            damage = max(damage, seq_damage)
        
        # Check advance effects for additional damage
        for effect in card.advance_effects:
            action = effect.get('action', {})
            if isinstance(action, dict) and action.get('type') == 'damage':
                # Don't count advance damage for now (it's conditional)
                pass
        
        return damage

    def execute_effects(self, effects: list[dict], gs: 'GameState', caster: 'Player', current_card: 'Card', played_card: 'PlayedCard' = None) -> None:
        a_condition_was_met = False
        is_sequential = all(eff['condition'].get('type') == 'always' for eff in effects)
        
        # Log response spell condition evaluation for analytics
        if 'response' in current_card.types and not is_sequential:
            # This is a response spell with conditions
            for effect in effects:
                condition_type = effect['condition'].get('type')
                if condition_type not in ['always', 'otherwise']:
                    # Evaluate the condition and log the result
                    condition_met = self.engine.condition_checker.check(effect['condition'], gs, caster, current_card)
                    
                    # Add debug info for spell type conditions
                    debug_info = ""
                    if condition_type == 'if_enemy_has_active_spell_of_type':
                        params = effect['condition'].get('parameters', {})
                        spell_type = params.get('spell_type', 'any')
                        # Count enemy spells of this type
                        enemy_spells = []
                        for p in gs.players:
                            if p != caster:
                                for s in p.board[gs.clash_num-1]:
                                    if s.status == 'revealed' and (spell_type == 'any' or spell_type in s.card.types):
                                        enemy_spells.append(f"{s.card.name}({','.join(s.card.types)})")
                        debug_info = f" [Looking for {spell_type}, found: {', '.join(enemy_spells) if enemy_spells else 'none'}]"
                    
                    game_logger.log_response_condition_evaluated(
                        player_name=caster.name,
                        spell_name=current_card.name,
                        condition_met=condition_met,
                        clash_num=gs.clash_num,
                        round_num=gs.round_num,
                        condition_type=condition_type + debug_info
                    )
                    break  # Only log the first non-always condition

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
                        # Mark that the resolve condition was met for this spell
                        if played_card:
                            played_card.resolve_condition_met = True
                        self._execute_action(effect['action'], gs, caster, current_card)

    def _execute_action(self, action_data, gs: 'GameState', caster: 'Player', current_card: 'Card') -> None:
        # Handle case where action_data is a list of actions
        if isinstance(action_data, list):
            # For action arrays, we need to handle each action completely with its own targets
            # This is used by spells like Stupefy, Familiar, and Absorb
            for i, action in enumerate(action_data):
                # Process each action in the array
                self._execute_single_action(action, gs, caster, current_card)
                # Pause after each action except the last one
                if i < len(action_data) - 1:
                    self.engine._pause()
            return
        
        # For single actions, delegate to the single action handler
        self._execute_single_action(action_data, gs, caster, current_card)
    
    def _execute_single_action(self, action_data, gs: 'GameState', caster: 'Player', current_card: 'Card') -> None:
        action_type = action_data.get('type')
        params = action_data.get('parameters', {})
        
        # Handle actions that don't use standard targeting first
        if action_type == 'recall_from_enemy_hand':
            # First, reveal a card from each enemy's hand
            enemies = [p for p in gs.players if p != caster and p.hand]
            revealed_cards = []
            
            for enemy in enemies:
                if enemy.hand:
                    # For AI enemies, reveal a random card
                    revealed_card = random.choice(enemy.hand)
                    gs.action_log.append(f"Revealed from {enemy.name}'s hand: [{revealed_card.name}]")
                    # Log the reveal
                    game_logger.log_spell_revealed(enemy.name, revealed_card.name, caster.name)
                    revealed_cards.append((enemy, revealed_card))
            
            # Let the caster choose which card to recall
            if revealed_cards:
                if caster.is_human:
                    if len(revealed_cards) == 1:
                        # Auto-select if only one option
                        enemy, card = revealed_cards[0]
                        enemy.hand.remove(card)
                        caster.hand.append(card)
                        gs.action_log.append(f"{caster.name} recalled [{card.name}] from {enemy.name}'s hand!")
                    else:
                        # Let player choose
                        options = {}
                        for i, (enemy, card) in enumerate(revealed_cards):
                            options[i+1] = (enemy, card)
                        
                        prompt = "Choose a revealed card to recall:"
                        self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                        for key, (enemy, card) in options.items():
                            emoji = ELEMENT_EMOJIS.get(card.element, '')
                            print(f"  [{key}] {emoji} {card.name} from {enemy.name}")
                        
                        choice = input("\nYour choice: ").strip()
                        try:
                            choice_idx = int(choice)
                            if choice_idx in options:
                                enemy, card = options[choice_idx]
                                enemy.hand.remove(card)
                                caster.hand.append(card)
                                gs.action_log.append(f"{caster.name} recalled [{card.name}] from {enemy.name}'s hand!")
                        except ValueError:
                            gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                else:
                    # AI just takes the first revealed card
                    enemy, card = revealed_cards[0]
                    enemy.hand.remove(card)
                    caster.hand.append(card)
                    gs.action_log.append(f"{caster.name} recalled [{card.name}] from {enemy.name}'s hand!")
            else:
                gs.action_log.append("No cards to recall from enemy hands.")
            return True
            
        elif action_type == 'move_clash_to_clash':
            # Let player choose source and destination clashes
            if caster.is_human:
                # First, choose source clash
                clash_options = {}
                for i in range(4):
                    spells_in_clash = []
                    for p in gs.players:
                        spells_in_clash.extend([s for s in p.board[i] if s.status == 'revealed'])
                    if spells_in_clash:
                        clash_options[i+1] = (i, spells_in_clash)
                
                if not clash_options:
                    gs.action_log.append("No active spells to move.")
                    return True
                
                # Choose source clash
                prompt = "Choose a clash to move spells FROM:"
                self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                for key, (clash_idx, spells) in clash_options.items():
                    spell_names = [s.card.name for s in spells]
                    print(f"  [{key}] Clash {clash_idx + 1}: {', '.join(spell_names)}")
                
                source_choice = input("\nYour choice: ").strip()
                try:
                    source_key = int(source_choice)
                    if source_key in clash_options:
                        source_clash_idx, source_spells = clash_options[source_key]
                        
                        # Choose destination clash
                        dest_options = {i+1: i for i in range(4) if i != source_clash_idx}
                        prompt = "Choose a clash to move spells TO:"
                        self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                        for key, clash_idx in dest_options.items():
                            print(f"  [{key}] Clash {clash_idx + 1}")
                        
                        dest_choice = input("\nYour choice: ").strip()
                        dest_key = int(dest_choice)
                        if dest_key in dest_options:
                            dest_clash_idx = dest_options[dest_key]
                            
                            # Move all spells
                            moved_count = 0
                            for spell in source_spells:
                                owner = spell.owner
                                owner.board[source_clash_idx].remove(spell)
                                owner.board[dest_clash_idx].append(spell)
                                moved_count += 1
                                
                                # Log the move
                                game_logger.log_spell_moved(owner.name, spell.card.name, source_clash_idx + 1, dest_clash_idx + 1)
                                
                                # If moving to current clash, add to resolution queue
                                if dest_clash_idx == gs.clash_num - 1:
                                    self.engine.add_to_resolution_queue(spell)
                            
                            gs.action_log.append(f"Moved {moved_count} spell(s) from Clash {source_clash_idx + 1} to Clash {dest_clash_idx + 1}!")
                            self.engine._pause()
                except ValueError:
                    gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
            else:
                # AI logic - move from current clash to next clash if possible
                for i in range(gs.clash_num - 1, 3):
                    spells_in_clash = []
                    for p in gs.players:
                        spells_in_clash.extend([s for s in p.board[i] if s.status == 'revealed'])
                    if spells_in_clash and i < 3:
                        # Move to next clash
                        for spell in spells_in_clash:
                            owner = spell.owner
                            owner.board[i].remove(spell)
                            owner.board[i+1].append(spell)
                            
                            # If moving to current clash, add to resolution queue
                            if i+1 == gs.clash_num - 1:
                                self.engine.add_to_resolution_queue(spell)
                        gs.action_log.append(f"Moved {len(spells_in_clash)} spell(s) from Clash {i + 1} to Clash {i + 2}!")
                        break
            return True
        
        # Handle recall separately since it needs special target resolution
        if action_type == 'recall':
            source = params.get('source', 'discard')
            if source == 'friendly_past_spells' and action_data.get('target') == 'self':
                # Constellation - let player choose from past spells
                past_spells = []
                for i in range(gs.clash_num - 1):  # Only past clashes
                    for spell in caster.board[i]:
                        if spell.status == 'revealed':
                            past_spells.append(spell)
                
                if not past_spells:
                    gs.action_log.append(f"{caster.name} has no spells in past clashes to recall.")
                    return True
                
                if caster.is_human:
                    if len(past_spells) == 1:
                        target = past_spells[0]
                    else:
                        options = {i+1: s for i, s in enumerate(past_spells)}
                        prompt = "Choose a spell to recall from past clashes:"
                        choice = self.engine._prompt_for_choice(caster, options, prompt, view_key='card.name')
                        if choice is None:
                            return True
                        target = options[choice]
                else:
                    target = random.choice(past_spells)
                
                # Process the recall
                targets = [target]
            else:
                # Standard targeting for other recall types
                targets = self._resolve_target(action_data, gs, caster, current_card)
                if not targets:
                    gs.action_log.append(f"{Colors.GREY}No valid targets for recall.{Colors.ENDC}")
                    self.engine._pause()
                    return True
        else:
            # Special handling for advance_from_past_clash
            if action_type == 'advance_from_past_clash':
                # This action handles its own targeting internally
                targets = ['execute_action']  # Dummy target to proceed
            else:
                # Standard targeting for other actions
                targets = self._resolve_target(action_data, gs, caster, current_card)
                
                if not targets:
                    gs.action_log.append(f"{Colors.GREY}No valid targets for {action_type}.{Colors.ENDC}"); self.engine._pause()
                    return

        if action_type == 'auto_optimal_choice':
            # Automatically choose the optimal option based on comparison
            params = action_data.get('parameters', {})
            comparison = params.get('comparison', 'count_active_spells')
            threshold = params.get('threshold', 3)
            
            # Evaluate the comparison
            comparison_value = 0
            if comparison == 'count_active_spells':
                # Count caster's other active spells
                for spell in caster.board[gs.clash_num - 1]:
                    if spell.status == 'revealed' and spell.card != current_card:
                        comparison_value += 1
            # Add other comparison types here as needed
            
            # Get valid options
            valid_options = []
            for option in action_data.get('options', []):
                option_targets = self._resolve_target(option, gs, caster, current_card)
                if option_targets:
                    valid_options.append(option)
            
            if not valid_options:
                gs.action_log.append(f"{Colors.GREY}No valid options available.{Colors.ENDC}")
                return True
                
            # Choose based on threshold
            if comparison_value >= threshold and len(valid_options) >= 2:
                # Choose the second option (typically the "per spell" option)
                chosen_option = valid_options[1]
                gs.action_log.append(f"{caster.name}'s [{current_card.name}] automatically chooses optimal option ({comparison_value} other active spells).")
            else:
                # Choose the first option (typically the fixed value option)
                chosen_option = valid_options[0]
                if comparison_value > 0:
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] chooses fixed option ({comparison_value} other active spells).")
            
            self._execute_action(chosen_option, gs, caster, current_card)
            return True

        if action_type == 'player_choice':
            # Check if Coalesce is active for this player
            has_coalesce = False
            active_spells = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
            for spell in active_spells:
                if spell.owner == caster and spell.card.name == 'Coalesce':
                    has_coalesce = True
                    break
            
            # First, check if each option is actually valid
            valid_options = []
            for option in action_data.get('options', []):
                # For validation, we need to check if targets exist without prompting
                # Create a copy of the option that forces no prompting
                validation_option = option.copy()
                
                # Check if the option would have valid targets
                has_valid_targets = self._check_if_targets_exist(validation_option, gs, caster, current_card)
                
                
                if has_valid_targets:  # Only include options that have valid targets
                    valid_options.append(option)
            
            if not valid_options:
                gs.action_log.append(f"{Colors.GREY}No valid options available.{Colors.ENDC}")
                return True
            
            # If Coalesce is active, execute ALL valid options
            if has_coalesce:
                gs.action_log.append(f"{caster.name}'s [Coalesce] changes 'Choose one' to 'Do both'!")
                for option in valid_options:
                    self._execute_action(option, gs, caster, current_card)
                    self.engine._pause()
                return True
            
            # If only one valid option, execute it automatically
            if len(valid_options) == 1:
                gs.action_log.append(f"Only one valid option - executing automatically.")
                self._execute_action(valid_options[0], gs, caster, current_card)
                return True
            
            if caster.is_human:
                # Build options dictionary with labels
                options_dict = {}
                for i, option in enumerate(valid_options):
                    # Generate a descriptive label for each option
                    if option.get('type') == 'sequence':
                        # For sequence actions, describe all actions
                        action_descriptions = []
                        for act in option.get('actions', []):
                            action_descriptions.append(current_card._format_action(act))
                        label = " then ".join(action_descriptions)
                    elif option.get('type') == 'pass':
                        label = "Pass (do nothing)"
                    else:
                        label = current_card._format_action(option)
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
                # Use the AI strategy system to make the choice
                # Find the AI strategy for this player
                player_idx = gs.players.index(caster)
                ai_strategy = self.engine.ai_strategies.get(player_idx)
                
                if ai_strategy:
                    # Use the new AI system
                    chosen_option = ai_strategy.make_choice(valid_options, caster, gs, current_card)
                    if chosen_option:
                        self._execute_action(chosen_option, gs, caster, current_card)
                    else:
                        # Fallback if AI returns None
                        self._execute_action(valid_options[0], gs, caster, current_card)
                else:
                    # Fallback to original hardcoded logic if no AI strategy found
                    # This ensures backwards compatibility
                    # For attack/remedy choices, pick based on health
                    attack_options = []
                    remedy_options = []
                    safe_options = []
                    risky_options = []
                    
                    for option in valid_options:
                        # Check if option involves self-damage
                        has_self_damage = False
                        if option.get('type') == 'sequence':
                            # Check sequence for self-damage
                            for act in option.get('actions', []):
                                if act.get('type') == 'damage' and act.get('target') == 'self':
                                    has_self_damage = True
                                    break
                        elif option.get('type') == 'damage' and option.get('target') == 'self':
                            has_self_damage = True
                        
                        if has_self_damage:
                            risky_options.append(option)
                        elif option.get('type') == 'damage' or option.get('type') == 'weaken' or option.get('type') == 'damage_per_spell':
                            attack_options.append(option)
                        elif option.get('type') == 'heal' or option.get('type') == 'bolster':
                            remedy_options.append(option)
                        elif option.get('type') == 'pass':
                            safe_options.append(option)
                        else:
                            safe_options.append(option)
                    
                    # AI decision making
                    
                    # Special handling for choosing between attack options
                    if len(attack_options) > 1:
                        # Evaluate which attack option is better
                        best_attack = None
                        best_damage = 0
                        
                        for option in attack_options:
                            if option.get('type') == 'damage':
                                damage = option.get('parameters', {}).get('value', 0)
                                if damage > best_damage:
                                    best_damage = damage
                                    best_attack = option
                            elif option.get('type') == 'damage_per_spell':
                                # Count active spells for damage_per_spell
                                active_spells_count = len([s for s in active_spells if s.owner == caster])
                                params = option.get('parameters', {})
                                spell_type = params.get('spell_type', 'any')
                                exclude_self = params.get('exclude_self', False)
                                
                                if spell_type == 'any':
                                    damage = active_spells_count
                                    if exclude_self:
                                        damage -= 1  # Don't count current spell
                                else:
                                    # Count specific spell type
                                    damage = len([s for s in active_spells if s.owner == caster and spell_type in s.card.types])
                                    if exclude_self and current_card and spell_type in current_card.types:
                                        damage -= 1
                                
                                if damage > best_damage:
                                    best_damage = damage
                                    best_attack = option
                        
                        # Replace attack_options with just the best one if we found a clear winner
                        if best_attack and best_damage > 0:
                            attack_options = [best_attack]
                            if DEBUG_AI and current_card.name == "Prickle":
                                gs.action_log.append(f"{Colors.GREY}[DEBUG] Prickle AI chose option with {best_damage} damage{Colors.ENDC}")
                    
                    if caster.health <= 1:
                        # At 1 health - NEVER choose self-damage options
                        if remedy_options:
                            self._execute_action(remedy_options[0], gs, caster, current_card)
                        elif safe_options:
                            self._execute_action(safe_options[0], gs, caster, current_card)
                        elif attack_options:
                            self._execute_action(attack_options[0], gs, caster, current_card)
                        else:
                            # No safe options - just pass if possible
                            for opt in valid_options:
                                if opt.get('type') == 'pass':
                                    self._execute_action(opt, gs, caster, current_card)
                                    return
                            # Forced to take damage
                            self._execute_action(valid_options[0], gs, caster, current_card)
                    elif caster.health <= 2:
                        # Low health - avoid risky options unless they're very powerful
                        if remedy_options:
                            self._execute_action(remedy_options[0], gs, caster, current_card)
                        elif attack_options:
                            self._execute_action(attack_options[0], gs, caster, current_card)
                        elif safe_options:
                            self._execute_action(safe_options[0], gs, caster, current_card)
                        else:
                            # Forced to take risky option
                            self._execute_action(valid_options[0], gs, caster, current_card)
                    elif caster.health >= 4 and risky_options:
                        # High health - willing to take risks for powerful effects
                        # Blood spells often have powerful effects worth the self-damage
                        self._execute_action(risky_options[0], gs, caster, current_card)
                    elif attack_options:
                        # Mid health - prefer attacking
                        self._execute_action(attack_options[0], gs, caster, current_card)
                    elif safe_options:
                        # Fallback to other safe options
                        self._execute_action(safe_options[0], gs, caster, current_card)
                    elif risky_options and caster.health >= 3:
                        # Mid health - consider risky options if no other choice
                        self._execute_action(risky_options[0], gs, caster, current_card)
                    else:
                        # Ultimate fallback
                        self._execute_action(valid_options[0], gs, caster, current_card)
            return True
        
        if action_type == 'cast_extra_spell':
            num_to_cast = params.get('value', 1)
            
            if caster.is_human:
                if not caster.hand: 
                    gs.action_log.append(f"{caster.name} has no cards to cast.")
                    self.engine._pause()
                    return
                
                spells_cast = 0
                for spell_num in range(min(num_to_cast, len(caster.hand))):
                    if not caster.hand:
                        break
                    options = {i+1: c for i, c in enumerate(caster.hand)}
                    # Make it clear that casting is optional
                    if spell_num == 0:
                        prompt = f"Choose a spell to cast (or 'done' to cast no spells):"
                    else:
                        prompt = f"Choose spell {spell_num + 1} of up to {num_to_cast} to cast (or 'done'):"
                    choice = self.engine._prompt_for_choice(caster, options, prompt)
                    if choice == 'done':
                        break
                    if choice is not None:
                        card_to_cast = caster.hand.pop(choice-1)
                        newly_played_card = PlayedCard(card_to_cast, caster)
                        newly_played_card.status = 'revealed'  # Set to active since it's cast mid-resolution
                        gs.players[gs.players.index(caster)].board[gs.clash_num - 1].append(newly_played_card)
                        self.engine.add_to_resolution_queue(newly_played_card)
                        gs.action_log.append(f"{caster.name} casts an extra spell: [{card_to_cast.name}]!")
                        spells_cast += 1
                        self.engine._pause()
                
                if spells_cast == 0:
                    gs.action_log.append(f"{caster.name} chose not to cast any extra spells.")
                    self.engine._pause()
            else:
                # AI casts up to num_to_cast spells
                for _ in range(min(num_to_cast, len(caster.hand))):
                    if caster.hand:
                        card_to_cast = caster.hand.pop(0)
                        newly_played_card = PlayedCard(card_to_cast, caster)
                        newly_played_card.status = 'revealed'
                        gs.players[gs.players.index(caster)].board[gs.clash_num - 1].append(newly_played_card)
                        self.engine.add_to_resolution_queue(newly_played_card)
                        gs.action_log.append(f"{caster.name} casts an extra spell: [{card_to_cast.name}]!")
            return

        for target in targets:
            if action_type == 'damage':
                if isinstance(target, Player):
                    if not target.is_invulnerable:
                        damage = params.get('value', 1); original_health = target.health; target.health = max(0, target.health - damage)
                        gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [{current_card.name}] dealt {damage} damage to {target.name}. ({target.health}/{target.max_health}){Colors.ENDC}")
                        self._fire_event('player_damaged', gs, player=caster.name, target=target.name, value=damage, card_id=current_card.id)
                        if original_health > 0 and target.health <= 0:
                            death_result = self.engine._handle_trunk_loss(target)
                            if death_result == 'game_over':
                                raise RoundOverException()
                            elif death_result == 'round_over':
                                raise RoundOverException()
                elif isinstance(target, PlayedCard) and target.card.is_conjury:
                    target.status = 'cancelled'; gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{target.card.name}].")
                    self._fire_event('spell_cancelled', gs, player=caster.name, target_card_id=target.card.id, card_id=current_card.id)
            elif action_type == 'damage_multi_target':
                 for t in target:
                     if isinstance(t, Player):
                         if not t.is_invulnerable:
                            damage = params.get('value', 1); original_health = t.health; t.health = max(0, t.health - damage)
                            gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [{current_card.name}] dealt {damage} damage to {t.name}. ({t.health}/{t.max_health}){Colors.ENDC}")
                            self._fire_event('player_damaged', gs, player=caster.name, target=t.name, value=damage, card_id=current_card.id)
                            if original_health > 0 and t.health <= 0:
                                death_result = self.engine._handle_trunk_loss(t)
                                if death_result == 'game_over':
                                    raise RoundOverException()
                                elif death_result == 'round_over':
                                    raise RoundOverException()
                     elif isinstance(t, PlayedCard) and t.card.is_conjury:
                        t.status = 'cancelled'; gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{t.card.name}].")
                        self._fire_event('spell_cancelled', gs, player=caster.name, target_card_id=t.card.id, card_id=current_card.id)
            elif action_type == 'heal':
                target.health = min(target.max_health, target.health + params.get('value', 1)); gs.action_log.append(f"{Colors.BLUE}{ACTION_EMOJIS['heal']} {caster.name}'s [{current_card.name}] healed {target.name} for {params.get('value', 1)}. ({target.health}/{target.max_health}){Colors.ENDC}")
                self._fire_event('player_healed', gs, player=target.name, value=params.get('value', 1), card_id=current_card.id)
            elif action_type == 'weaken':
                if isinstance(target, Player):
                    weaken_amount = params.get('value', 1)
                    target.max_health = max(0, target.max_health - weaken_amount); target.health = min(target.health, target.max_health)
                    gs.action_log.append(f"{Colors.YELLOW}{ACTION_EMOJIS['weaken']} {caster.name}'s [{current_card.name}] weakened {target.name} by {weaken_amount}. Max health now {target.max_health}.{Colors.ENDC}")
                    # Log weaken event separately
                    self._fire_event('player_weakened', gs, player=caster.name, target=target.name, value=weaken_amount, card_id=current_card.id)
                elif isinstance(target, PlayedCard) and target.card.is_conjury:
                    # Weakening a conjury cancels it
                    target.status = 'cancelled'
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] weakened and CANCELLED [{target.card.name}].")
            elif action_type == 'bolster':
                bolster_amount = params.get('value', 1)
                target.max_health += bolster_amount; gs.action_log.append(f"{Colors.GREEN}{ACTION_EMOJIS['bolster']} {caster.name}'s [{current_card.name}] bolstered {target.name}. Max health now {target.max_health}.{Colors.ENDC}")
                # Log bolster event separately
                self._fire_event('player_bolstered', gs, player=caster.name, target=target.name, value=bolster_amount, card_id=current_card.id)
            elif action_type == 'damage_per_spell_from_other_clashes':
                # Count active spells that were active in other clashes (for Impact)
                damage = 0
                exclude_self = params.get('exclude_self', True)
                
                # Check all clashes except the current one
                for clash_idx in range(4):
                    if clash_idx == gs.clash_num - 1:
                        continue  # Skip current clash
                    
                    # Count revealed spells in other clashes
                    for player in gs.players:
                        for spell in player.board[clash_idx]:
                            if spell and spell.status == 'revealed':
                                # Exclude self if specified
                                if exclude_self and spell.card == current_card and spell.owner == caster:
                                    continue
                                damage += 1
                
                if damage > 0 and isinstance(target, Player) and not target.is_invulnerable:
                    original_health = target.health
                    target.health = max(0, target.health - damage)
                    gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [{current_card.name}] dealt {damage} damage to {target.name} ({damage} spell(s) from other clashes). ({target.health}/{target.max_health}){Colors.ENDC}")
                    self._fire_event('player_damaged', gs, player=caster.name, target=target.name, value=damage, card_id=current_card.id)
                    if target.health == 0:
                        death_result = self.engine._handle_trunk_loss(target)
                        if death_result == 'game_over':
                            gs.game_over = True
                            if caster.trunks > 0:
                                raise RoundOverException()
                elif damage == 0:
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] found no spells from other clashes to count.")
                    
            elif action_type == 'damage_per_spell':
                # Count active spells matching criteria
                active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
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
                        gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [{current_card.name}] dealt {damage} damage to {target.name} ({count} spell(s)). ({target.health}/{target.max_health}){Colors.ENDC}")
                        self._fire_event('player_damaged', gs, player=caster.name, target=target.name, value=damage, card_id=current_card.id)
                        if original_health > 0 and target.health <= 0:
                            death_result = self.engine._handle_trunk_loss(target)
                            if death_result == 'game_over':
                                raise RoundOverException()
                            elif death_result == 'round_over':
                                raise RoundOverException()
                    elif isinstance(target, PlayedCard) and target.card.is_conjury:
                        target.status = 'cancelled'
                        gs.action_log.append(f"{caster.name}'s [{current_card.name}] CANCELLED [{target.card.name}].")
                else:
                    gs.action_log.append(f"{caster.name} has no other active spells to boost the damage.")
            
            elif action_type == 'heal_per_spell':
                # Count active spells matching criteria
                active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
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
            
            elif action_type == 'discard_from_hand':
                if isinstance(target, Player) and target.hand:
                    num_to_discard = min(params.get('value', 1), len(target.hand))
                    if num_to_discard > 0:
                        discarded_count = 0
                        if target.is_human:
                            for i in range(num_to_discard):
                                prompt = f"Choose a card to discard ({i+1}/{num_to_discard}):"
                                options = {j+1: c for j, c in enumerate(target.hand)}
                                choice = self.engine._prompt_for_choice(target, options, prompt)
                                if choice is not None:
                                    discarded = target.hand.pop(choice-1)
                                    target.discard_pile.append(discarded)
                                    gs.action_log.append(f"{target.name} discarded [{discarded.name}].")
                                    discarded_count += 1
                        else:
                            # AI discards randomly
                            for i in range(num_to_discard):
                                if target.hand:
                                    discarded = random.choice(target.hand)
                                    target.hand.remove(discarded)
                                    target.discard_pile.append(discarded)
                                    gs.action_log.append(f"{target.name} discarded [{discarded.name}].")
                                    discarded_count += 1
                        # Log if we couldn't discard the required number
                        if discarded_count < num_to_discard:
                            gs.action_log.append(f"Only discarded {discarded_count} of {num_to_discard} required cards.")
                else:
                    gs.action_log.append(f"{target.name} has no cards to discard.")
            
            elif action_type == 'advance':
                # Handle multiple targets (for Clap's advance effect)
                if isinstance(target, list):
                    # Advance multiple spells
                    for spell_to_advance in target:
                        if isinstance(spell_to_advance, PlayedCard):
                            self._advance_single_spell(spell_to_advance, gs, caster, current_card, action_data)
                else:
                    # Single spell advance
                    if target is None:
                        gs.action_log.append(f"{Colors.FAIL}[DEBUG] Advance target is None for {current_card.name}{Colors.ENDC}")
                    elif not isinstance(target, PlayedCard):
                        gs.action_log.append(f"{Colors.FAIL}[DEBUG] Advance target is not a PlayedCard: {type(target)}{Colors.ENDC}")
                    else:
                        self._advance_single_spell(target, gs, caster, current_card, action_data)
            
            
            elif action_type == 'discard':
                if action_data.get('target') == 'this_spell':
                    # Find and discard this spell
                    for clash_list in caster.board:
                        for spell in clash_list:
                            if spell.card.id == current_card.id:
                                spell.status = 'cancelled'
                                clash_list.remove(spell)
                                caster.discard_pile.append(spell.card)
                                gs.action_log.append(f"{Colors.GREY}{ACTION_EMOJIS['discard']} [{spell.card.name}] was discarded.{Colors.ENDC}")
                                # Log the discard
                                game_logger.log_spell_discarded(caster.name, spell.card.name, "self")
                                return
                elif isinstance(target, PlayedCard):
                    # Discard a specific spell (used by Electrocute, Daybreak)
                    owner = target.owner
                    for clash_list in owner.board:
                        if target in clash_list:
                            clash_list.remove(target)
                            break
                    # Important: For Daybreak, put enemy spell in caster's discard
                    if owner != caster:
                        caster.discard_pile.append(target.card)
                        gs.action_log.append(f"{caster.name} discarded [{target.card.name}] from {owner.name}'s past spells into their own discard pile!")
                        # Log the discard
                        game_logger.log_spell_discarded(owner.name, target.card.name, caster.name)
                    else:
                        owner.discard_pile.append(target.card)
                        gs.action_log.append(f"{caster.name} discarded [{target.card.name}] from past spells!")
                        # Log the discard
                        game_logger.log_spell_discarded(owner.name, target.card.name, caster.name)
                else:
                    gs.action_log.append(f"No valid target to discard.")
            
            elif action_type == 'copy_spell':
                # Imitate - copy an enemy spell
                if isinstance(target, PlayedCard):
                    # Create a copy of the spell and add it to the resolution queue
                    copied_card = PlayedCard(target.card, caster)
                    copied_card.status = 'revealed'
                    caster.board[gs.clash_num - 1].append(copied_card)
                    self.engine.add_to_resolution_queue(copied_card)
                    gs.action_log.append(f"{caster.name} copies [{target.card.name}] from {target.owner.name}!")
                    self.engine._pause()
            
            elif action_type == 'recall_from_board':
                # Sap - recall an enemy boost spell from the board to your hand
                if isinstance(target, PlayedCard) and 'boost' in target.card.types:
                    owner = target.owner
                    
                    # Check if Root is protecting this spell in the current clash
                    for spell in owner.board[gs.clash_num - 1]:
                        if spell.status == 'revealed' and spell.card.name == 'Root':
                            gs.action_log.append(f"[{target.card.name}] is protected by {owner.name}'s [Root] and cannot be recalled!")
                            return
                    
                    # Remove from board
                    clash_num = -1
                    for i, clash_list in enumerate(owner.board):
                        if target in clash_list:
                            clash_list.remove(target)
                            clash_num = i + 1
                            break
                    # Add to caster's hand
                    caster.hand.append(target.card)
                    gs.action_log.append(f"{Colors.YELLOW}{caster.name} used Sap to steal [{target.card.name}] from {owner.name}'s Clash {clash_num}!{Colors.ENDC}")
                    self._fire_event('spell_recalled_from_board', gs, player=caster.name, target=owner.name, card_id=target.card.id)
            
            elif action_type == 'damage_per_enemy_spell_type':
                # Dominion - damage based on enemy boost spells
                spell_type = params.get('spell_type', 'any')
                enemies = [p for p in gs.players if p != caster]
                
                for enemy in enemies:
                    count = 0
                    # Count active spells of the specified type for this enemy in current clash
                    for spell in enemy.board[gs.clash_num - 1]:
                        if spell.status == 'revealed' and spell_type in spell.card.types:
                            count += 1
                    
                    if count > 0 and not enemy.is_invulnerable:
                        damage = count
                        original_health = enemy.health
                        enemy.health = max(0, enemy.health - damage)
                        gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [{current_card.name}] dealt {damage} damage to {enemy.name} ({count} {spell_type} spell(s)). ({enemy.health}/{enemy.max_health}){Colors.ENDC}")
                        self._fire_event('player_damaged', gs, player=caster.name, target=enemy.name, value=damage, card_id=current_card.id)
                        if original_health > 0 and enemy.health <= 0:
                            death_result = self.engine._handle_trunk_loss(enemy)
                            if death_result == 'game_over':
                                raise RoundOverException()
                            elif death_result == 'round_over': 
                                raise RoundOverException()
            
            elif action_type == 'damage_equal_to_enemy_attack_damage':
                # Familiar - damage based on each enemy's own attack spell damage
                enemies = [p for p in gs.players if p != caster]
                
                for enemy in enemies:
                    total_damage = 0
                    # Check enemy's active attack spells in current clash
                    for spell in enemy.board[gs.clash_num - 1]:
                        if spell.status == 'revealed' and 'attack' in spell.card.types:
                            # Calculate damage from this attack spell
                            spell_damage = self._calculate_spell_damage(spell.card, enemy, gs)
                            total_damage += spell_damage
                    
                    if total_damage > 0 and not enemy.is_invulnerable:
                        original_health = enemy.health
                        enemy.health = max(0, enemy.health - total_damage)
                        gs.action_log.append(f"{Colors.FAIL}{ACTION_EMOJIS['damage']} {caster.name}'s [Familiar] reflected {total_damage} damage to {enemy.name} (from their attack spells). ({enemy.health}/{enemy.max_health}){Colors.ENDC}")
                        self._fire_event('player_damaged', gs, player=caster.name, target=enemy.name, value=total_damage, card_id=current_card.id)
                        if original_health > 0 and enemy.health <= 0:
                            death_result = self.engine._handle_trunk_loss(enemy)
                            if death_result == 'game_over':
                                raise RoundOverException()
                            elif death_result == 'round_over': 
                                raise RoundOverException()
            
            elif action_type == 'cancel':
                # Cancel spells (used by Encumber, Stupefy, etc.)
                if isinstance(target, PlayedCard):
                    # Check if Root is protecting this spell in the current clash
                    owner = target.owner
                    for spell in owner.board[gs.clash_num - 1]:
                        if spell.status == 'revealed' and spell.card.name == 'Root':
                            gs.action_log.append(f"[{target.card.name}] is protected by {owner.name}'s [Root] and cannot be cancelled!")
                            return
                    
                    target.status = 'cancelled'
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] cancelled {target.owner.name}'s [{target.card.name}]!")
                elif isinstance(target, list):
                    # For mass cancel effects
                    for spell in target:
                        if isinstance(spell, PlayedCard):
                            # Check if Root is protecting this spell in the current clash
                            owner = spell.owner
                            protected = False
                            for root_spell in owner.board[gs.clash_num - 1]:
                                if root_spell.status == 'revealed' and root_spell.card.name == 'Root':
                                    gs.action_log.append(f"[{spell.card.name}] is protected by {owner.name}'s [Root] and cannot be cancelled!")
                                    protected = True
                                    break
                            
                            if not protected:
                                spell.status = 'cancelled'
                                gs.action_log.append(f"{caster.name}'s [{current_card.name}] cancelled {spell.owner.name}'s [{spell.card.name}]!")
            
            elif action_type == 'move_to_future_clash':
                # Gravitate - move a spell to a future clash
                if isinstance(target, PlayedCard):
                    owner = target.owner
                    current_clash = -1
                    
                    # Find which clash the spell is in
                    for i, clash_list in enumerate(owner.board):
                        if target in clash_list:
                            current_clash = i
                            break
                    
                    if current_clash >= 0 and current_clash < 3:
                        # Let player choose which future clash
                        available_clashes = list(range(current_clash + 1, 4))
                        
                        if caster.is_human and len(available_clashes) > 1:
                            # Player chooses which future clash
                            options = {i+1: clash_idx for i, clash_idx in enumerate(available_clashes)}
                            prompt = f"Choose which clash to move [{target.card.name}] to:"
                            self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                            for key, clash_idx in options.items():
                                print(f"  [{key}] Clash {clash_idx + 1}")
                            
                            choice = input("\nYour choice: ").strip()
                            try:
                                choice_idx = int(choice)
                                if choice_idx in options:
                                    target_clash = options[choice_idx]
                                else:
                                    target_clash = current_clash + 1  # Default to next clash
                            except ValueError:
                                target_clash = current_clash + 1  # Default to next clash
                        else:
                            # AI or only one option - move to next clash
                            target_clash = current_clash + 1
                        
                        # Move the spell
                        owner.board[current_clash].remove(target)
                        owner.board[target_clash].append(target)
                        gs.action_log.append(f"{caster.name} moved [{target.card.name}] from Clash {current_clash + 1} to Clash {target_clash + 1}!")
                        # Log the move
                        game_logger.log_spell_moved(owner.name, target.card.name, current_clash + 1, target_clash + 1)
                        self.engine._pause()
                    else:
                        gs.action_log.append(f"Cannot move [{target.card.name}] to a future clash.")
            
            elif action_type == 'recall':
                # Constellation - recall a spell from past clashes
                source = params.get('source', 'discard')
                if source == 'friendly_past_spells' and isinstance(target, PlayedCard):
                    # Remove from board
                    owner = target.owner
                    for clash_list in owner.board:
                        if target in clash_list:
                            clash_list.remove(target)
                            break
                    # Add to hand
                    caster.hand.append(target.card)
                    gs.action_log.append(f"{caster.name} recalled [{target.card.name}] from past clashes!")
                    self._fire_event('spell_recalled', gs, player=caster.name, card_id=target.card.id)
            
            elif action_type == 'advance_from_hand':
                # Gleam/Eventide - play spells from hand to future clashes
                num_to_play = params.get('value', 1)
                
                if not caster.hand:
                    gs.action_log.append(f"{caster.name} has no cards in hand to advance.")
                    return
                
                # Check if we can advance to next clash
                if gs.clash_num >= 4:
                    gs.action_log.append(f"Cannot advance from hand - no future clashes remaining.")
                    return
                
                # Check if Break is preventing advances
                for player in gs.players:
                    if player != caster:  # Check opponents
                        for spell in player.board[gs.clash_num - 1]:
                            if spell.status == 'revealed' and spell.card.name == 'Break':
                                gs.action_log.append(f"{caster.name} cannot advance cards from hand because {player.name}'s [Break] prevents it!")
                                return  # Prevent the advance from happening
                
                target_clash = gs.clash_num  # Advance always goes to the next clash
                
                cards_advanced = 0
                max_to_advance = min(num_to_play, len(caster.hand))
                
                for i in range(max_to_advance):
                    if caster.is_human:
                        if not caster.hand:
                            break
                        options = {j+1: c for j, c in enumerate(caster.hand)}
                        prompt = f"Choose a card to advance to Clash {target_clash + 1} (up to {num_to_play} total, {cards_advanced} chosen) or 'done':"
                        choice = self.engine._prompt_for_choice(caster, options, prompt)
                        if choice == 'done':
                            break
                        if choice is not None and isinstance(choice, int):
                            card = caster.hand.pop(choice-1)
                            cards_advanced += 1
                            # Add to board
                            played_card = PlayedCard(card, caster)
                            played_card.status = 'prepared'  # Will be revealed in that clash
                            caster.board[target_clash].append(played_card)
                            gs.action_log.append(f"{caster.name} advanced [{card.name}] from hand to Clash {target_clash + 1}!")
                    else:
                        # AI just plays first card to next clash
                        if caster.hand:
                            card = caster.hand.pop(0)
                            played_card = PlayedCard(card, caster)
                            played_card.status = 'prepared'
                            caster.board[target_clash].append(played_card)
                            gs.action_log.append(f"{caster.name} advanced [{card.name}] from hand to Clash {target_clash + 1}!")
            
            elif action_type == 'sequence':
                # Execute a sequence of actions in order
                actions = action_data.get('actions', [])
                for i, act in enumerate(actions):
                    # Special handling for actions that might fail
                    if act.get('type') == 'discard' and i == 0:
                        # For Electrocute's sequence, check if we can actually discard
                        targets = self._resolve_target(act, gs, caster, current_card)
                        if not targets:
                            gs.action_log.append(f"Sequence stopped - no valid targets for discard.")
                            break
                    elif act.get('type') == 'discard_from_hand' and act.get('target') == 'self' and i == 0:
                        # For Surge's sequence, check if caster has cards to discard
                        if not caster.hand:
                            gs.action_log.append(f"Sequence stopped - no cards to discard.")
                            break
                    
                    self._execute_action(act, gs, caster, current_card)
                    self.engine._pause()
            
            elif action_type == 'weaken_per_spell':
                # Count active spells matching criteria (similar to damage_per_spell)
                active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
                spell_type = params.get('spell_type', 'any')
                exclude_self = params.get('exclude_self', False)
                
                count = 0
                for spell in active_spells_this_clash:
                    if spell.owner == caster:
                        if exclude_self and spell.card.id == current_card.id:
                            continue
                        if spell_type == 'any' or spell_type in spell.card.types:
                            count += 1
                
                if count > 0 and isinstance(target, Player):
                    target.max_health = max(0, target.max_health - count)
                    target.health = min(target.health, target.max_health)
                    gs.action_log.append(f"{caster.name}'s [{current_card.name}] weakened {target.name} by {count} ({count} {spell_type} spell(s)). Max health now {target.max_health}.")
                    # Log weaken_per_spell event separately
                    self._fire_event('player_weakened', gs, player=caster.name, target=target.name, value=count, card_id=current_card.id)
                else:
                    gs.action_log.append(f"{caster.name} has no active {spell_type} spells to boost the weakening.")
            
            elif action_type == 'advance_from_past_clash':
                # Blow spell - advance a spell from a past clash
                if gs.clash_num <= 1:
                    gs.action_log.append(f"No past clashes to choose from.")
                    return
                
                # Find all spells in past clashes
                past_clash_spells = {}
                for i in range(gs.clash_num - 1):  # Only past clashes
                    clash_spells = []
                    for player in gs.players:
                        for spell in player.board[i]:
                            if spell.status == 'revealed':  # Only revealed spells can be advanced
                                clash_spells.append(spell)
                    if clash_spells:
                        past_clash_spells[i] = clash_spells
                
                if not past_clash_spells:
                    gs.action_log.append(f"No active spells in past clashes to advance.")
                    return
                
                # Choose which clash
                if caster.is_human:
                    if len(past_clash_spells) == 1:
                        # Only one past clash with spells
                        chosen_clash = list(past_clash_spells.keys())[0]
                        spells_in_clash = past_clash_spells[chosen_clash]
                    else:
                        # Multiple past clashes - let player choose
                        clash_options = {}
                        for clash_idx, spells in past_clash_spells.items():
                            clash_options[clash_idx + 1] = (clash_idx, spells)
                        
                        prompt = "Choose a past clash to advance a spell from:"
                        self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                        for key, (clash_idx, spells) in clash_options.items():
                            spell_names = [f"{s.owner.name}'s [{s.card.name}]" for s in spells]
                            print(f"  [{key}] Clash {key}: {', '.join(spell_names)}")
                        
                        choice = input("\nYour choice: ").strip()
                        try:
                            choice_num = int(choice)
                            if choice_num in clash_options:
                                chosen_clash, spells_in_clash = clash_options[choice_num]
                            else:
                                gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                                return
                        except ValueError:
                            gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                            return
                    
                    # Now choose which spell from that clash
                    if len(spells_in_clash) == 1:
                        spell_to_advance = spells_in_clash[0]
                    else:
                        spell_options = {i+1: s for i, s in enumerate(spells_in_clash)}
                        prompt = f"Choose a spell from Clash {chosen_clash + 1} to advance:"
                        self.engine.display.draw(gs, gs.players.index(caster), prompt=prompt)
                        for key, spell in spell_options.items():
                            emoji = ELEMENT_EMOJIS.get(spell.card.element, '')
                            print(f"  [{key}] {spell.owner.name}'s {emoji} [{spell.card.name}]")
                        
                        choice = input("\nYour choice: ").strip()
                        try:
                            choice_idx = int(choice)
                            if choice_idx in spell_options:
                                spell_to_advance = spell_options[choice_idx]
                            else:
                                gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                                return
                        except ValueError:
                            gs.action_log.append(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                            return
                else:
                    # AI logic - advance a random spell from the earliest past clash
                    chosen_clash = min(past_clash_spells.keys())
                    spell_to_advance = random.choice(past_clash_spells[chosen_clash])
                
                # Advance the chosen spell
                self._advance_single_spell(spell_to_advance, gs, caster, current_card, action_data)
            
            elif action_type == 'pass':
                # Do nothing
                gs.action_log.append(f"{caster.name} chose to pass.")

    def _check_if_targets_exist(self, action_data: dict, gs: 'GameState', caster: 'Player', current_card: 'Card') -> bool:
        """Check if valid targets exist for an action without prompting the player"""
        target_str = action_data.get('target')
        if target_str is None: return True
        if target_str == 'self': 
            # Special case for advance_from_hand - check if player has cards
            if action_data.get('type') == 'advance_from_hand':
                return bool(caster.hand and gs.clash_num < 4)
            return True
            
        enemies = [p for p in gs.players if p != caster]
        valid_enemies = [p for p in enemies if not p.is_invulnerable]
        active_spells = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
        
        if target_str in ['prompt_enemy', 'prompt_player']:
            return bool(valid_enemies)
        elif target_str == 'prompt_any_active_spell':
            return bool(active_spells)
        elif target_str == 'prompt_player_or_conjury':
            active_conjuries = [s for s in active_spells if s.card.is_conjury]
            return bool(valid_enemies or active_conjuries)
        elif target_str == 'prompt_other_friendly_active_spell':
            friendly_spells = [s for s in active_spells if s.owner == caster and s.card.id != current_card.id]
            return bool(friendly_spells)
        elif target_str == 'prompt_enemy_active_spell':
            enemy_spells = [s for s in active_spells if s.owner != caster]
            return bool(enemy_spells)
        elif target_str == 'prompt_enemy_boost_spell':
            enemy_boost = [s for s in active_spells if s.owner != caster and 'boost' in s.card.types]
            return bool(enemy_boost)
        elif target_str == 'all_enemies_and_their_conjuries':
            return bool(valid_enemies)
        elif target_str == 'this_spell':
            for clash_list in caster.board:
                for spell in clash_list:
                    if spell.card.id == current_card.id:
                        return True
            return False
        else:
            # For other target types, assume they exist
            return True
    
    def _resolve_target(self, action_data: dict, gs: 'GameState', caster: 'Player', current_card: 'Card') -> list[Any]:
        target_str = action_data.get('target')
        if target_str is None: return [caster]
        if target_str == 'self': 
            # Special case for advance_from_hand - check if player has cards
            if action_data.get('type') == 'advance_from_hand':
                if not caster.hand or gs.clash_num >= 4:
                    return []  # No valid targets if no cards in hand or no future clashes
            return [caster]
        if target_str == 'this_spell':
            for clash_list in caster.board:
                for spell in clash_list:
                    if spell.card.id == current_card.id: 
                        return [spell]
            # Debug: spell not found
            gs.action_log.append(f"{Colors.FAIL}[DEBUG] Could not find 'this_spell' for {current_card.name} (ID: {current_card.id}){Colors.ENDC}")
            return []
        enemies = [p for p in gs.players if p != caster]; valid_enemies = [p for p in enemies if not p.is_invulnerable]
        # Only look for active conjuries in the current clash
        active_conjuries = [s for p in gs.players for s in p.board[gs.clash_num-1] if s and s.card.is_conjury and s.status == 'revealed']
        if target_str == 'prompt_enemy' or target_str == 'prompt_player':
            # prompt_enemy and prompt_player both target enemies only
            if not valid_enemies: return []
            if caster.is_human:
                if len(valid_enemies) == 1: return valid_enemies
                options = {i+1: e for i, e in enumerate(valid_enemies)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose an enemy:")
                if choice is not None: return [options[choice]]
                else: return []
            else:
                # AI picks lowest health enemy
                return [min(valid_enemies, key=lambda p: p.health)]
        
        if target_str == 'prompt_player_or_conjury':
            all_possible_targets = valid_enemies + [c for c in active_conjuries if c.owner in valid_enemies]
            if not all_possible_targets: return []
            if caster.is_human:
                if len(all_possible_targets) == 1: return all_possible_targets
                options = {i+1: t for i, t in enumerate(all_possible_targets)}; choice = self.engine._prompt_for_choice(caster, options, "Choose a target (enemy or conjury):")
                if choice is not None: return [options[choice]]
                else: return []
            else: # AI Logic
                # Get AI strategy for smarter targeting
                ai_index = gs.players.index(caster)
                ai_strategy = self.engine.ai_strategies.get(ai_index)
                
                # Separate conjuries and players
                conjury_targets = [c for c in all_possible_targets if isinstance(c, PlayedCard)]
                player_targets = [p for p in all_possible_targets if isinstance(p, Player)]
                
                # Enhanced conjury evaluation
                if conjury_targets:
                    # Score each conjury based on threat level
                    conjury_scores = {}
                    for conjury in conjury_targets:
                        score = 0
                        
                        # High priority conjuries are more threatening
                        priority = int(conjury.card.priority) if str(conjury.card.priority).isdigit() else 99
                        if priority <= 2:
                            score += 50  # Very high threat
                        elif priority <= 3:
                            score += 30  # High threat
                        else:
                            score += 10  # Base threat
                        
                        # Remedy conjuries are high priority when we're hurt
                        if 'remedy' in conjury.card.types and caster.health < caster.max_health * 0.6:
                            score += 40
                        
                        # Attack conjuries are always threatening
                        if 'attack' in conjury.card.types:
                            score += 30
                        
                        # Boost conjuries can enable combos
                        if 'boost' in conjury.card.types:
                            score += 20
                        
                        # Consider the element
                        if hasattr(ai_strategy, '_is_bad_element_matchup'):
                            if ai_strategy._is_bad_element_matchup(caster.element if hasattr(caster, 'element') else 'Unknown', [conjury.card.element]):
                                score += 15  # Extra reason to remove it
                        
                        conjury_scores[conjury] = score
                    
                    # Check if any conjury is worth targeting over players
                    best_conjury = max(conjury_scores.items(), key=lambda x: x[1])
                    
                    # Target conjury if it's high threat or no players are low health
                    low_health_players = [p for p in player_targets if p.health <= 2]
                    if best_conjury[1] >= 40 or not low_health_players:
                        # For Hard AI, pick the highest threat conjury
                        if ai_strategy and type(ai_strategy).__name__ == 'HardAI':
                            return [best_conjury[0]]
                        # Other AIs pick randomly from high-threat conjuries
                        high_threat = [c for c, score in conjury_scores.items() if score >= 30]
                        if high_threat:
                            return [random.choice(high_threat)]
                
                # Otherwise, standard player targeting
                low_health_players = [p for p in player_targets if p.health <= 2]
                if low_health_players: 
                    return [random.choice(low_health_players)]
                if player_targets:
                    return [random.choice(player_targets)]
                
                # Fallback
                return [random.choice(all_possible_targets)] if all_possible_targets else []
        if target_str == 'all_enemies_and_their_conjuries':
            all_targets = valid_enemies + [c for c in active_conjuries if c.owner in valid_enemies]
            return [all_targets] if all_targets else []
        active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
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
        
        if target_str == 'prompt_friendly_past_or_active_spell':
            # For Electrocute - can discard past spells (any status) or active spells in current clash
            all_board_spells = []
            # Add all past spells (regardless of status)
            for i in range(gs.clash_num - 1):  # Only past clashes
                for spell in caster.board[i]:
                    all_board_spells.append(spell)
            # Add active spells from current clash
            for spell in caster.board[gs.clash_num - 1]:
                if spell.status == 'revealed':
                    all_board_spells.append(spell)
            
            if not all_board_spells: return []
            if len(all_board_spells) == 1: return all_board_spells
            if caster.is_human:
                options = {i+1: s for i, s in enumerate(all_board_spells)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose one of your past or active spells to discard:", view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else: return [random.choice(all_board_spells)]
        
        if target_str == 'all_enemies_who_met_condition':
            # This is a special target that needs to work with condition checking
            # We need to find enemies who meet the condition from the action's parent effect
            enemies = [p for p in gs.players if p != caster and not p.is_invulnerable]
            enemies_who_met_condition = []
            active_spells_this_clash = [s for p in gs.players for s in p.board[gs.clash_num-1] if s.status == 'revealed']
            
            # Determine which spell type to check based on the spell using this
            # For Reflect, it's attack spells. For Enfeeble, it's boost spells.
            spell_type_to_check = None
            if current_card.name == 'Reflect' or current_card.name == 'Familiar' or current_card.name == 'Stupefy':
                spell_type_to_check = 'attack'
            elif current_card.name == 'Enfeeble':
                spell_type_to_check = 'boost'
            
            if spell_type_to_check:
                for enemy in enemies:
                    for spell in active_spells_this_clash:
                        if spell.owner == enemy and spell_type_to_check in spell.card.types:
                            enemies_who_met_condition.append(enemy)
                            break  # Only need to find one spell per enemy
            
            return enemies_who_met_condition
        
        if target_str == 'prompt_enemy_boost_spell':
            # For Sap - find enemy active boost spells in the current clash only
            enemy_boost_spells = []
            for enemy in enemies:
                # Only check current clash
                for spell in enemy.board[gs.clash_num - 1]:
                    if spell.status == 'revealed' and 'boost' in spell.card.types:
                        enemy_boost_spells.append(spell)
            
            if not enemy_boost_spells: return []
            if caster.is_human:
                if len(enemy_boost_spells) == 1: return enemy_boost_spells
                options = {i+1: s for i, s in enumerate(enemy_boost_spells)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose an enemy boost spell to recall:", view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else:
                return [random.choice(enemy_boost_spells)]
        
        if target_str == 'prompt_enemy_active_spell':
            # For Imitate - find enemy active spells in current clash only
            enemy_spells = []
            for enemy in enemies:
                for spell in enemy.board[gs.clash_num - 1]:
                    if spell.status == 'revealed':
                        enemy_spells.append(spell)
            
            if not enemy_spells: return []
            if caster.is_human:
                if len(enemy_spells) == 1: return enemy_spells
                options = {i+1: s for i, s in enumerate(enemy_spells)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose an enemy spell to copy:", view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else:
                return [random.choice(enemy_spells)]
        
        if target_str == 'each_enemy':
            # For Dominion - target all enemies
            return valid_enemies
        
        if target_str == 'all_enemy_remedy_spells':
            # For Encumber - all enemy remedy spells in current clash
            enemy_remedy_spells = []
            for enemy in enemies:
                for spell in enemy.board[gs.clash_num - 1]:
                    if spell.status == 'revealed' and 'remedy' in spell.card.types:
                        enemy_remedy_spells.append(spell)
            return enemy_remedy_spells
        
        if target_str == 'all_enemy_attack_spells':
            # For Stupefy - all enemy attack spells in current clash
            enemy_attack_spells = []
            for enemy in enemies:
                for spell in enemy.board[gs.clash_num - 1]:
                    if spell.status == 'revealed' and 'attack' in spell.card.types:
                        enemy_attack_spells.append(spell)
            return enemy_attack_spells
        
        if target_str == 'prompt_any_active_spell':
            # Any active spell - by default only in current clash
            all_active_spells = []
            
            # For Gravitate, only include spells from the current clash that can move forward
            if action_data.get('type') == 'move_to_future_clash':
                # Only spells in the current clash can be moved to future clashes
                if gs.clash_num < 4:  # Can't move from clash 4
                    for player in gs.players:
                        for spell in player.board[gs.clash_num - 1]:
                            if spell.status == 'revealed':
                                all_active_spells.append(spell)
            else:
                # For other actions (like cancel), check current clash only
                for player in gs.players:
                    for spell in player.board[gs.clash_num - 1]:
                        if spell.status == 'revealed':
                            all_active_spells.append(spell)
            
            if not all_active_spells: return []
            if caster.is_human:
                if len(all_active_spells) == 1: return all_active_spells
                options = {i+1: s for i, s in enumerate(all_active_spells)}
                
                # Different prompts based on action
                if action_data.get('type') == 'cancel':
                    prompt = "Choose a spell to cancel:"
                else:
                    prompt = "Choose a spell:"
                    
                choice = self.engine._prompt_for_choice(caster, options, prompt, view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else:
                # AI logic - for cancel, prefer enemy spells
                if action_data.get('type') == 'cancel':
                    enemy_spells = [s for s in all_active_spells if s.owner != caster]
                    if enemy_spells:
                        # Prefer high priority enemy spells
                        priority_spells = sorted(enemy_spells, key=lambda s: int(s.card.priority) if str(s.card.priority).isdigit() else 99)
                        return [priority_spells[0]]
                    # If no enemy spells, might cancel own low-value spell
                    own_spells = [s for s in all_active_spells if s.owner == caster]
                    if own_spells:
                        # Only cancel own spell if it's low priority/value
                        low_priority = [s for s in own_spells if (int(s.card.priority) if str(s.card.priority).isdigit() else 99) >= 4]
                        if low_priority:
                            return [low_priority[0]]
                    return []
                else:
                    # For non-cancel actions, pick any spell
                    return [random.choice(all_active_spells)]
        
        if target_str == 'self' and action_data.get('type') == 'recall':
            # For Constellation - let player choose from past spells
            source = action_data.get('parameters', {}).get('source', 'discard')
            if source == 'friendly_past_spells':
                past_spells = []
                for i in range(gs.clash_num - 1):  # Only past clashes
                    for spell in caster.board[i]:
                        if spell.status == 'revealed':
                            past_spells.append(spell)
                
                if not past_spells: return []
                if caster.is_human:
                    if len(past_spells) == 1: return past_spells
                    options = {i+1: s for i, s in enumerate(past_spells)}
                    choice = self.engine._prompt_for_choice(caster, options, "Choose a spell to recall from past clashes:", view_key='card.name')
                    if choice is not None: return [options[choice]]
                    else: return []
                else:
                    return [random.choice(past_spells)] if past_spells else []
        
        if target_str == 'prompt_enemy_past_spell':
            # For Daybreak - find enemy past spells
            enemy_past_spells = []
            for enemy in enemies:
                for i in range(gs.clash_num - 1):  # Only past clashes
                    for spell in enemy.board[i]:
                        # Past spells don't need to be active
                        enemy_past_spells.append(spell)
            
            if not enemy_past_spells: return []
            if caster.is_human:
                if len(enemy_past_spells) == 1: return enemy_past_spells
                options = {i+1: s for i, s in enumerate(enemy_past_spells)}
                choice = self.engine._prompt_for_choice(caster, options, "Choose an enemy past spell to discard:", view_key='card.name')
                if choice is not None: return [options[choice]]
                else: return []
            else:
                return [random.choice(enemy_past_spells)]
        
        if target_str == 'prompt_one_spell_from_each_enemy_who_met_condition':
            # For Clap - cancel one spell from each enemy who has 2+ active spells
            enemies = [p for p in gs.players if p != caster]
            targets_to_cancel = []
            
            # Find which enemies have 2+ active spells
            for enemy in enemies:
                enemy_spells = []
                for spell in active_spells_this_clash:
                    if spell.owner == enemy and spell.status == 'revealed':
                        enemy_spells.append(spell)
                
                if len(enemy_spells) >= 2:
                    # This enemy meets the condition - choose one spell to cancel
                    if caster.is_human:
                        if len(enemy_spells) == 2:
                            # Only 2 spells, pick one
                            options = {i+1: s for i, s in enumerate(enemy_spells)}
                            prompt = f"Choose which of {enemy.name}'s spells to cancel:"
                            choice = self.engine._prompt_for_choice(caster, options, prompt, view_key='card.name')
                            if choice is not None:
                                targets_to_cancel.append(options[choice])
                        else:
                            # More than 2 spells, let player choose
                            options = {i+1: s for i, s in enumerate(enemy_spells)}
                            prompt = f"Choose which of {enemy.name}'s spells to cancel:"
                            choice = self.engine._prompt_for_choice(caster, options, prompt, view_key='card.name')
                            if choice is not None:
                                targets_to_cancel.append(options[choice])
                    else:
                        # AI picks the highest priority spell
                        priority_spells = sorted(enemy_spells, key=lambda s: int(s.card.priority) if str(s.card.priority).isdigit() else 99)
                        targets_to_cancel.append(priority_spells[0])
            
            return targets_to_cancel
        
        if target_str == 'all_friendly_active_spells':
            # For Clap's advance effect - all friendly active spells in current clash
            friendly_spells = []
            for spell in active_spells_this_clash:
                if spell.owner == caster and spell.status == 'revealed':
                    friendly_spells.append(spell)
            return friendly_spells
        
        if target_str == 'prompt_choose_past_clash':
            # Special target for Blow spell - returns a placeholder that signals
            # the action handler to do the clash/spell selection
            return ['past_clash_selection']
        
        return []
    
    def _advance_single_spell(self, target: 'PlayedCard', gs: 'GameState', caster: 'Player', current_card: 'Card', action_data: dict) -> None:
        """Helper method to advance a single spell."""
        # Check if Break is preventing enemy advances
        # Break prevents ALL enemy spells from advancing, regardless of who is trying to advance them
        for player in gs.players:
            if player != target.owner:  # player is an opponent of the spell's owner
                for spell in player.board[gs.clash_num - 1]:
                    if spell.status == 'revealed' and spell.card.name == 'Break':
                        gs.action_log.append(f"[{target.card.name}] cannot advance because {player.name}'s [Break] prevents it!")
                        return  # Prevent the advance from happening
        
        # Check if this is a self-advance with a limit
        params = action_data.get('parameters', {})
        if target.card.id == current_card.id and action_data.get('target') == 'this_spell':
            # This spell is trying to advance itself - check for limits
            advance_params = params
            if 'limit' in advance_params and target.advances_this_round >= advance_params['limit']:
                gs.action_log.append(f"[{target.card.name}] can only advance itself {advance_params['limit']} time(s) per round and has already advanced {target.advances_this_round} time(s).")
                return
        
        owner = target.owner
        next_clash_idx = gs.clash_num
        if next_clash_idx < 4:
            found_and_moved = False
            for i, clash_list in enumerate(owner.board):
                if target in clash_list:
                    owner.board[i].remove(target)
                    owner.board[next_clash_idx].append(target)
                    target.advances_this_round += 1  # Increment advance count
                    gs.action_log.append(f"{Colors.GREEN}{ACTION_EMOJIS['advance']} {owner.name}'s [{target.card.name}] advanced from Clash {i+1} to Clash {next_clash_idx + 1}.{Colors.ENDC}")
                    self._fire_event('spell_advanced', gs, player=owner.name, card_id=target.card.id, round=gs.round_num)
                    found_and_moved = True
                    break
            if not found_and_moved:
                gs.action_log.append(f"Error: Could not find [{target.card.name}] to advance.")
        else:
            gs.action_log.append(f"[{target.card.name}] could not advance past Clash 4.")

# AI classes moved to ai/ module

# --- MAIN GAME ENGINE ---
class GameEngine:
    def __init__(self, player_names, ai_difficulty='expert'):
        self.gs = GameState(player_names); self.display = DashboardDisplay()
        self.condition_checker = ConditionChecker(); self.action_handler = ActionHandler(self)
        self.ai_decision_logs = []  # Store AI logs to show after reveal
        self.ai_difficulty = ai_difficulty  # Store for logging
        
        # Create AI strategies based on difficulty
        self.ai_strategies = {}
        for i, name in enumerate(player_names):
            if i > 0:  # AI players (not the human player)
                if ai_difficulty == 'easy':
                    ai = EasyAI()
                    if DEBUG_AI:
                        print(f"Created EasyAI for player {i}: {name}")
                elif ai_difficulty == 'hard':
                    ai = HardAI()
                    if DEBUG_AI:
                        print(f"Created HardAI for player {i}: {name}")
                elif ai_difficulty == 'expert':
                    ai = ExpertAI()
                    if DEBUG_AI:
                        print(f"Created ExpertAI for player {i}: {name}")
                else:  # medium (default)
                    ai = MediumAI()
                    if DEBUG_AI:
                        print(f"Created MediumAI for player {i}: {name}")
                
                ai.engine = self  # Set engine reference
                self.ai_strategies[i] = ai
        
        # Keep backward compatibility
        self.ai_player = self.ai_strategies.get(1, MediumAI())
        if self.ai_player and not hasattr(self.ai_player, 'engine'):
            self.ai_player.engine = self
    
    def _format_spell_name(self, card):
        """Format spell name with type icons"""
        type_icons = self.display._get_spell_type_icons(card)
        return f"[{card.name}] {type_icons}"
    
    def _is_spell_active(self, spell, clash_num=None):
        """Check if a spell is truly active (revealed and in current clash)"""
        if clash_num is None:
            clash_num = self.gs.clash_num
        
        # Must be revealed (not prepared or cancelled)
        if spell.status != 'revealed':
            return False
            
        # Must be in the current clash
        for player in self.gs.players:
            if spell in player.board[clash_num - 1]:
                return True
                
        return False
    
    def _pause(self, message=""): prompt = f"{message} {Colors.GREY}[Press Enter to continue...]{Colors.ENDC}"; self.display.draw(self.gs, prompt=prompt); input()
    def _prompt_for_choice(self, player, options, prompt_message, view_key='name'):
        while True:
            self.display.draw(self.gs, self.gs.players.index(player), prompt=prompt_message)
            if not options: self.gs.action_log.append(f"{Colors.GREY}No options available.{Colors.ENDC}"); return 'done' if 'done' in prompt_message.lower() else None
            for key, item in options.items():
                if isinstance(item, list): 
                    emoji = ELEMENT_EMOJIS.get(item[0].element, '')
                    theme = item[0].theme if hasattr(item[0], 'theme') else ''
                    display_name = f"The '{item[0].elephant}' Set ({emoji} {item[0].element} | {len(item)} cards)"
                    if theme:
                        print(f"  [{key}] {display_name}")
                        print(f"    {Colors.GREY}Theme: {theme}{Colors.ENDC}")
                        continue
                    # If no theme, fall through to normal display
                elif isinstance(item, Card): 
                    emoji = ELEMENT_EMOJIS.get(item.element, '')
                    display_name = f"{emoji} {item.name} (P:{item.priority})"; 
                    print(f"  [{key}] {display_name}"); 
                    print(f"    {Colors.GREY}> {item.get_instructions_text()}{Colors.ENDC}"); 
                    continue
                elif isinstance(item, PlayedCard): 
                    display_name = f"{item.owner.name}'s [{item.card.name}]"
                else: 
                    display_name = getattr(item, view_key, str(item))
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
            while len([p for p in self.gs.players if p.trunks > 0]) > 1 and not self.gs.game_over:
                self._run_round()
                if not self.gs.game_over:
                    self.gs.round_num += 1
            
            winner = next((p for p in self.gs.players if p.trunks > 0), None)
            self.gs.action_log.append(f"GAME OVER! The winner is {winner.name}!" if winner else "GAME OVER! No winner.")
            
            # Log game end
            if winner:
                loser = next((p for p in self.gs.players if p != winner), None)
                game_logger.log_game_end(
                    winner_name=winner.name,
                    winner_health=winner.health,
                    loser_health=0 if loser else 0,
                    total_rounds=self.gs.round_num - 1
                )
            
            self._pause()
        except Exception:
            clear_screen(); print("\n\n--- A CRITICAL ERROR OCCURRED ---")
            traceback.print_exc(); print("---------------------------------")
            print("\nPlease copy this error report for debugging.")

    def _setup_game(self):
        self._check_and_rebuild_deck()
        self.gs.action_log.clear(); self.gs.action_log.append("--- Game Setup ---")
        for _ in range(2):
            for p in self.gs.players:
                self._check_and_rebuild_deck()
                if p.is_human:
                    options = {idx+1: s for idx, s in enumerate(self.gs.main_deck) if s}; choice = self._prompt_for_choice(p, options, f"{p.name}, choose a spell set to draft:")
                    drafted_set = options[choice]; self.gs.main_deck.remove(drafted_set)
                else: 
                    # AI uses strategic drafting
                    ai_index = self.gs.players.index(p)
                    ai = self.ai_strategies.get(ai_index)
                    if ai and hasattr(ai, 'choose_draft_set'):
                        drafted_set = ai.choose_draft_set(p, self.gs, self.gs.main_deck)
                    else:
                        # Fallback to random if AI doesn't have drafting method
                        drafted_set = random.choice(self.gs.main_deck)
                    self.gs.main_deck.remove(drafted_set)
                p.discard_pile.extend(drafted_set); 
                emoji = ELEMENT_EMOJIS.get(drafted_set[0].element, '')
                self.gs.action_log.append(f"{p.name} drafted the '{drafted_set[0].elephant}' ({emoji} {drafted_set[0].element}) set.")
        for p in self.gs.players:
            if p.is_human:
                options = {i+1: c for i, c in enumerate(p.discard_pile)}; hand_choices = []
                while len(hand_choices) < 4:
                    prompt = f"{p.name}, choose card {len(hand_choices)+1}/4 for your starting hand:"; choice = self._prompt_for_choice(p, options, prompt); hand_choices.append(options.pop(choice))
                p.hand = hand_choices; p.discard_pile = list(options.values())
            else: random.shuffle(p.discard_pile); p.hand = p.discard_pile[:4]; p.discard_pile = p.discard_pile[4:]
        
        # Start game logging
        player_elements = {}
        for p in self.gs.players:
            # Get unique elements from player's cards
            elements = list(set(card.element for card in p.hand + p.discard_pile))
            player_elements[p.name] = elements
        
        game_logger.start_game(
            self.gs.players[0].name, 
            self.gs.players[1].name,
            player_elements[self.gs.players[0].name],
            player_elements[self.gs.players[1].name],
            self.ai_difficulty if not self.gs.players[0].is_human else None
        )
        
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
            if self.gs.game_over:
                self.gs.action_log.append(f"{Colors.WARNING}The game has ended!{Colors.ENDC}")
            else:
                self.gs.action_log.append(f"{Colors.WARNING}The round has ended early due to trunk loss!{Colors.ENDC}")
                self._pause("Proceeding to the end of the round.")

        # Only run end of round if game isn't over
        if not self.gs.game_over:
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
                # Get the AI strategy for this player
                ai_strategy = self.ai_strategies.get(player_index, self.ai_player)
                if DEBUG_AI:
                    print(f"\n{Colors.GREY}[DEBUG] Using AI strategy for player {player_index}: {type(ai_strategy).__name__}{Colors.ENDC}")
                chosen_index = ai_strategy.choose_card_to_play(player, self.gs)
                if chosen_index is not None:
                    card_to_play = player.hand.pop(chosen_index)

            if card_to_play:
                # --- THIS IS THE KEY FIX ---
                # Create the played card and add to board
                played_card = PlayedCard(card_to_play, player)
                player.board[self.gs.clash_num - 1].append(played_card)
                
                # Log opponent's play generically, but your play specifically.
                if player.is_human:
                    formatted_name = self._format_spell_name(card_to_play)
                    log_message = f"{player.name} prepared {formatted_name}."
                else:
                    log_message = f"{player.name} has prepared a spell."
                    
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
                    spell.status = 'revealed'
                    # Log spell played
                    game_logger.log_spell_played(
                        player_name=p.name,
                        spell_name=spell.card.name,
                        element=spell.card.element,
                        clash_num=self.gs.clash_num,
                        round_num=self.gs.round_num,
                        spell_types=spell.card.types,
                        is_conjury=spell.card.is_conjury
                    )
        
        # Show all revealed spells with instructions
        self.gs.action_log.append(f"{Colors.BOLD}Spells Revealed:{Colors.ENDC}")
        for p in self.gs.players:
            for spell in p.board[self.gs.clash_num - 1]:
                if spell.status == 'revealed':
                    emoji = ELEMENT_EMOJIS.get(spell.card.element, '')
                    type_icons = self.display._get_spell_type_icons(spell.card)
                    type_str = '/'.join(spell.card.types) if spell.card.types else 'None'
                    conjury_str = " [CONJURY]" if spell.card.is_conjury else ""
                    self.gs.action_log.append(f"  {p.name}: {emoji} [{spell.card.name}] {type_icons}{conjury_str} (P:{spell.card.priority}, {type_str})")
                    self.gs.action_log.append(f"    {Colors.GREY}> {spell.card.get_instructions_text()}{Colors.ENDC}")
        
        # Show AI decision logs after reveal
        if DEBUG_AI and self.ai_decision_logs:
            self.gs.action_log.append(f"\n{Colors.BOLD}AI Decision Analysis:{Colors.ENDC}")
            for log in self.ai_decision_logs:
                self.gs.action_log.append(log)
            self.ai_decision_logs.clear()  # Clear for next clash
        
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
        
        active_spells = [s for p in self.gs.players for s in p.board[self.gs.clash_num-1] if s.status == 'revealed']
        self.gs.resolution_queue = []
        
        # Fire events for all spells that are active at the start of resolve phase
        # This is needed for conditions like Bolts that check "if you had other active spells this clash"
        for spell in active_spells:
            self.action_handler._fire_event('spell_active_in_clash', self.gs, 
                                          player=spell.owner.name, 
                                          card_id=spell.card.id,
                                          clash=self.gs.clash_num)
        
        # Check for Accelerator effects
        priority_modifiers = {}
        for player in self.gs.players:
            modifier = 0
            for spell in active_spells:
                if spell.owner == player and spell.card.name == 'Accelerator' and spell.status == 'revealed':
                    # Accelerator reduces priority by 2 for other friendly spells
                    modifier -= 2
            if modifier != 0:
                priority_modifiers[player] = modifier
        
        for spell in active_spells:
            p_val = 99 if spell.card.priority == 'A' else int(spell.card.priority)
            caster_idx = self.gs.players.index(spell.owner)
            
            # Apply Accelerator modifier if this isn't Accelerator itself
            if spell.card.name != 'Accelerator' and spell.owner in priority_modifiers:
                p_val = max(1, p_val + priority_modifiers[spell.owner])  # Minimum priority of 1
            
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
            
            if played_card in processed_this_phase or played_card.status != 'revealed':
                continue
            
            # Check if spell is still in the current clash (it might have been moved by Gravitate)
            spell_still_in_current_clash = False
            for spell in caster.board[self.gs.clash_num - 1]:
                if spell == played_card:
                    spell_still_in_current_clash = True
                    break
            
            if not spell_still_in_current_clash:
                self.gs.action_log.append(f"[{played_card.card.name}] was moved to a future clash and will not resolve now.")
                self._pause()
                continue

            self.gs.action_log.clear()
            formatted_name = self._format_spell_name(played_card.card)
            self.gs.action_log.append(f"--> Resolving {caster.name}'s {Colors.BOLD}{formatted_name}{Colors.ENDC} (P:{played_card.card.priority})")
            self.gs.action_log.append(f"    {Colors.GREY}{played_card.card.get_instructions_text()}{Colors.ENDC}")
            self._pause("Executing effect...")

            self.action_handler.execute_effects(played_card.card.resolve_effects, self.gs, caster, played_card.card, played_card)
            
            played_card.has_resolved = True
            self.action_handler._fire_event('spell_resolved', self.gs, player=caster.name, card_id=played_card.card.id)
            processed_this_phase.append(played_card)
            self._post_resolution_checks()

    def _post_resolution_checks(self) -> None:
        for player in self.gs.players:
            # Check if a player was just knocked out (health is 0 but we haven't processed it yet)
            if player.health <= 0 and not player.knocked_out_this_turn:
                player.knocked_out_this_turn = True # Mark as processed for this turn
                death_result = self._handle_trunk_loss(player)
                if death_result == 'game_over' or death_result == 'round_over':
                    raise RoundOverException()
        
        # After handling any trunk losses, check if the round should end.
        # This will raise the RoundOverException if the condition is met.
        self._check_for_round_end()

    def _run_advance_phase(self) -> None:
        # Don't clear logs here - we want to see damage from the last resolved spell
        self.gs.action_log.append(f"--- Clash {self.gs.clash_num}: ADVANCE ---"); self._pause()
        
        # We need to copy the list as the underlying board state can change
        advancing_spells = [s for p in self.gs.players for s in p.board[self.gs.clash_num - 1] if s.status == 'revealed' and s.card.advance_effects]
        
        if not advancing_spells:
            self.gs.action_log.append("No spells to advance this clash.")
            return

        for played_card in advancing_spells:
            if self.gs.game_over: return
            if played_card.status != 'revealed': continue # Skip if cancelled mid-phase
            
            # Check if spell is still in the current clash (it might have been moved)
            caster = played_card.owner
            spell_still_in_current_clash = False
            for spell in caster.board[self.gs.clash_num - 1]:
                if spell == played_card:
                    spell_still_in_current_clash = True
                    break
            
            if not spell_still_in_current_clash:
                continue  # Skip spells that were moved to future clashes
            self.gs.action_log.clear()
            formatted_name = self._format_spell_name(played_card.card)
            self.gs.action_log.append(f"--> Advancing {caster.name}'s {formatted_name}...")
            self._pause()
            for effect in played_card.card.advance_effects:
                condition_type = effect['condition'].get('type')
                
                # Log response spell condition evaluation for advance effects
                if 'response' in played_card.card.types and condition_type not in ['always', 'otherwise']:
                    condition_met = self.condition_checker.check(effect['condition'], self.gs, caster, played_card.card)
                    game_logger.log_response_condition_evaluated(
                        player_name=caster.name,
                        spell_name=played_card.card.name,
                        condition_met=condition_met,
                        clash_num=self.gs.clash_num,
                        round_num=self.gs.round_num,
                        condition_type=condition_type + ' (advance)'
                    )
                
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
            drew_new_set = False  # Track if player drew a new set this turn
            
            # Step 1: Check for empty hand FIRST
            if not p.hand:
                self.gs.action_log.append(f"{p.name}'s hand is empty. They get a new spell set!"); self._pause()
                self._check_and_rebuild_deck()
                if self.gs.main_deck:
                    if p.is_human:
                        options = {i+1: s for i, s in enumerate(self.gs.main_deck) if s}
                        choice = self._prompt_for_choice(p, options, f"{p.name}, choose a new spell set:")
                        new_set = options[choice]; self.gs.main_deck.remove(new_set)
                    else:
                        # AI picks randomly from available sets
                        new_set = random.choice(self.gs.main_deck)
                        self.gs.main_deck.remove(new_set)
                    p.hand.extend(new_set)
                    self.gs.action_log.append(f"{p.name} drafted the '{new_set[0].elephant}' ({new_set[0].element}) set.")
                    drew_new_set = True
            else:
                # Step 2: Handle Keep/Discard phase (only if hand not empty)
                if p.is_human:
                    options = {i+1: c for i, c in enumerate(p.hand)}; kept_cards = []
                    while True:
                        prompt = "Choose cards to KEEP from your hand (type 'done' when finished):"; choice = self._prompt_for_choice(p, options, prompt)
                        if choice == 'done': break
                        if choice is not None: kept_cards.append(options.pop(choice))
                    for card in options.values(): p.discard_pile.append(card)
                    p.hand = kept_cards
                    
                    # If they discarded everything, they can get a new set
                    if not p.hand and self.gs.main_deck:
                        self.gs.action_log.append(f"{p.name} discarded their entire hand and can draft a new spell set!")
                        self._pause()
                        options = {i+1: s for i, s in enumerate(self.gs.main_deck) if s}
                        choice = self._prompt_for_choice(p, options, f"{p.name}, choose a new spell set:")
                        new_set = options[choice]; self.gs.main_deck.remove(new_set)
                        p.hand.extend(new_set)
                        self.gs.action_log.append(f"{p.name} drafted the '{new_set[0].elephant}' ({new_set[0].element}) set.")
                        self.gs.action_log.append(f"{Colors.WARNING}Note: You cannot discard cards from this newly drafted set!{Colors.ENDC}")
                        drew_new_set = True
                else: # AI Logic
                    # Get the AI strategy for this player
                    ai_index = self.gs.players.index(p)
                    ai_strategy = self.ai_strategies.get(ai_index)
                    
                    if ai_strategy and hasattr(ai_strategy, 'choose_cards_to_keep'):
                        # Use AI's strategic decision
                        cards_to_keep = ai_strategy.choose_cards_to_keep(p, self.gs)
                        discards = [c for c in p.hand if c not in cards_to_keep]
                        p.discard_pile.extend(discards)
                        p.hand = cards_to_keep
                        
                        # Check if AI is clearing entire hand
                        if not p.hand and self.gs.main_deck:
                            self.gs.action_log.append(f"{p.name} discarded their entire hand and can draft a new spell set!")
                            new_set = ai_strategy.choose_draft_set(p, self.gs, self.gs.main_deck)
                            self.gs.main_deck.remove(new_set)
                            p.hand.extend(new_set)
                            emoji = ELEMENT_EMOJIS.get(new_set[0].element, '')
                            self.gs.action_log.append(f"{p.name} drafted the '{new_set[0].elephant}' ({emoji} {new_set[0].element}) set.")
                            drew_new_set = True
                    else:
                        # Fallback to original simple logic
                        discards = [c for c in p.hand if 'remedy' not in c.types and p.health/p.max_health > 0.7]
                        p.discard_pile.extend(discards)
                        p.hand = [c for c in p.hand if c not in discards]

            # Step 3: Handle Recall phase - MUST fill to max if drew new set
            max_hand_size = 4 + (3 - p.trunks)
            
            if drew_new_set:
                # Must fill hand to max size from discard
                while len(p.hand) < max_hand_size and p.discard_pile:
                    if p.is_human:
                        prompt = f"You must recall cards to fill your hand ({len(p.hand)}/{max_hand_size}). Choose from discard:"
                        options = {i+1: c for i, c in enumerate(p.discard_pile)}
                        choice = self._prompt_for_choice(p, options, prompt, view_key='name')
                        if choice is not None:
                            recalled_card = p.discard_pile.pop(choice - 1)
                            p.hand.append(recalled_card)
                            self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
                    else:
                        recalled_card = p.discard_pile.pop(0)
                        p.hand.append(recalled_card)
                        self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
            else:
                # Normal optional recall
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
            
            # Step 4: Final check - only if they didn't draw a set and still below 4 cards with empty discard
            if not drew_new_set and len(p.hand) < 4 and not p.discard_pile:
                self.gs.action_log.append(f"{p.name}'s hand is below 4 cards and discard pile is empty. They must draft a new set."); self._pause()
                self._check_and_rebuild_deck()
                if self.gs.main_deck:
                    if p.is_human:
                        options = {i+1: s for i, s in enumerate(self.gs.main_deck[:5]) if s}; choice = self._prompt_for_choice(p, options, "Choose a new spell set:")
                        new_set = options[choice]; self.gs.main_deck.remove(new_set)
                    else: new_set = self.gs.main_deck.pop(0)
                    p.hand.extend(new_set)
                    self.gs.action_log.append(f"{p.name} drafted the '{new_set[0].elephant}' set.")
                    drew_new_set = True
                    
                    # Must fill to max from discard if available
                    while len(p.hand) < max_hand_size and p.discard_pile:
                        if p.is_human:
                            prompt = f"You must recall cards to fill your hand ({len(p.hand)}/{max_hand_size}). Choose from discard:"
                            options = {i+1: c for i, c in enumerate(p.discard_pile)}
                            choice = self._prompt_for_choice(p, options, prompt, view_key='name')
                            if choice is not None:
                                recalled_card = p.discard_pile.pop(choice - 1)
                                p.hand.append(recalled_card)
                                self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
                        else:
                            recalled_card = p.discard_pile.pop(0)
                            p.hand.append(recalled_card)
                            self.action_handler._fire_event('spell_recalled', self.gs, player=p.name, card_id=recalled_card.id)
        self._pause("All players have managed their hands. The next round will begin.")

    def _handle_trunk_loss(self, player: Player) -> str:
        message = player.lose_trunk()
        self.gs.action_log.append(f"{Colors.FAIL}{message}{Colors.ENDC}")
        
        # Log trunk loss for analytics
        game_logger.log_trunk_lost(player.name, self.gs.round_num, player.trunks)
        
        for clash_list in player.board:
            for spell in clash_list:
                player.discard_pile.append(spell.card)
        player.board = [[] for _ in range(4)]
        self.gs.action_log.append(f"{player.name}'s spells were cleared from the board.")
        
        # Check if this player just lost their last trunk
        if player.trunks == 0:
            self.gs.game_over = True
            return 'game_over'
        
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
            for data in SPELL_DATA: original_set_counts[data['elephant']] += 1

            for elephant, cards in all_discards.items():
                if len(cards) == original_set_counts[elephant]: new_deck.append(cards)
                else: remaining_discards.extend(cards)
            
            for p in self.gs.players: p.discard_pile = [c for c in remaining_discards if c in p.discard_pile] # This is a simplification
            
            random.shuffle(new_deck); self.gs.main_deck = new_deck
            self.gs.action_log.append(f"Rebuilt main deck with {len(new_deck)} complete sets.")

if __name__ == "__main__":
    try:
        clear_screen()
        print(f"DEBUG_AI is set to: {DEBUG_AI}")  # Debug check
        print(f"{Colors.HEADER}{'='*25}[ ELEMENTAL ELEPHANTS ]{'='*25}{Colors.ENDC}")
        print("\nChoose AI Difficulty:")
        print("[1] Easy (Random play)")
        print("[2] Medium (Basic strategy)")
        print("[3] Hard (Strategic)")
        print("[4] Expert (Overthinks everything)")
        
        difficulty_choice = input("\nYour choice (1-4): ").strip()
        
        difficulty_map = {
            '1': 'easy',
            '2': 'medium',
            '3': 'hard',
            '4': 'expert'
        }
        
        ai_difficulty = difficulty_map.get(difficulty_choice, 'expert')
        
        player_names = ["Human Player", "AI Opponent"]
        engine = GameEngine(player_names, ai_difficulty=ai_difficulty)
        
        print(f"\nStarting game with {ai_difficulty.upper()} difficulty AI...")
        input("Press Enter to begin...")
        
        engine.run_game()
    except KeyboardInterrupt: print("\n\nGame exited by user. Goodbye!")
    except Exception:
        clear_screen(); print("\n\n--- A CRITICAL ERROR OCCURRED ---")
        traceback.print_exc(); print("---------------------------------")
        print("\nPlease copy this error report for debugging.")