"""Claude Daredevil AI implementation - Aggressive and risk-taking"""

import os
import json
from typing import Dict, Any, Optional
import anthropic
from anthropic import AsyncAnthropic

from .llm_base import LLMBaseAI
from .claude_base_context import get_base_game_context
from .expert import ExpertAI

# Import Colors for debugging
class Colors:
    ORANGE = '\033[38;5;208m'
    GREY = '\033[90m'
    ENDC = '\033[0m'


class ClaudeDaredevilAI(LLMBaseAI):
    """Claude Daredevil - Aggressive AI that seeks to destroy opponents quickly"""
    
    def __init__(self):
        super().__init__()
        self.ai_identity = "DAREDEVIL"  # Fixed identity regardless of player name
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Set fallback to Expert AI
        self.fallback_ai = ExpertAI()
        
        # System prompt for Claude
        self.system_prompt = f"""You are Daredevil 😈, a fearless and aggressive Elemental Elephants player who lives for the thrill of the fight! Your singular goal is to destroy your opponent as quickly as possible, no matter the cost.

{get_base_game_context()}

Your Personality:
- Happy-go-lucky, fearless, flirty surfer personality
- Use surfer slang: "rad", "gnarly", "stoked", "shredding", "wipeout", "hang ten", etc.
- Flirty and playful - compliment opponents even while destroying them
- Love taking risks and making aggressive plays
- Get excited by damage combos and offensive spells
- Don't care much about defense - offense is the best defense!

Your Playstyle:
- ALWAYS prioritize damage-dealing spells
- Love mobility spells that help you pressure opponents
- Take calculated risks - if there's a chance for big damage, take it!
- Don't worry about your own health - focus on reducing theirs to zero
- Look for spell combinations that maximize damage output
- If you can deal damage NOW vs setup for later, choose NOW

Your Knowledge:
- Expert in offensive elements (Fire, Lightning, Venom, Blood)
- Master of mobility elements (Wind, Time, Space)
- You know all the aggressive combos and damage amplifiers
- You consider enemy spells only to maximize damage against them

Never break character. You're a surfer who happens to be deadly at card games!

Respond with JSON containing your decision, reasoning, and optional message."""
    
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from Claude"""
        # Debug: Ensure we're using the right AI
        if self.engine and hasattr(self.engine, 'ai_decision_logs') and decision_type == "select_card":
            self.engine.ai_decision_logs.append(
                f"{Colors.GREY}[DEBUG] Daredevil AI making decision for {self.player_name}{Colors.ENDC}"
            )
        
        try:
            # Build the appropriate prompt based on decision type
            if decision_type == "select_card":
                prompt = self._build_card_selection_prompt(context)
            elif decision_type == "make_choice":
                prompt = self._build_choice_prompt(context)
            elif decision_type == "draft":
                prompt = self._build_draft_prompt(context)
            elif decision_type == "round_analysis":
                prompt = self._build_round_analysis_prompt(context)
            elif decision_type == "game_end":
                prompt = self._build_game_end_prompt(context)
            else:
                return None
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.8,  # Higher temperature for more aggressive/risky plays
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Debug: Log the raw response (like Champion does)
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and decision_type == "select_card":
                self.engine.ai_decision_logs.append(
                    f"{Colors.GREY}[Claude-Daredevil] Raw response: {content[:200]}...{Colors.ENDC}"
                )
            
            # Try to parse as JSON
            try:
                # Find JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # For round analysis, extract the actual analysis text
                    if decision_type == "round_analysis" and "analysis" in result:
                        # The analysis might be the surfer commentary
                        return {"analysis": result["analysis"]}
                    
                    return result
            except json.JSONDecodeError:
                # Fallback to parsing logic
                return self._parse_text_response(content, decision_type)
        
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"{Colors.ORANGE}[Daredevil] Whoa, gnarly wipeout: {str(e)}{Colors.ENDC}"
                )
            return None
    
    def _build_card_selection_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for card selection"""
        prompt_parts = [
            f"Round {context['round']}, Clash {context['clash']}",
            f"Your health: {context['player']['health']}/{context['player']['max_health']} HP",
            f"Your trunks: {context['player']['trunks']}",
            "",
            "Enemy status:"
        ]
        
        for enemy in context['enemies']:
            prompt_parts.append(f"- {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks")
        
        prompt_parts.extend([
            "",
            "Your card options:"
        ])
        
        for card in context['valid_cards']:
            prompt_parts.append(f"- Index {card['index']}: {card['name']} ({card['element']}, P{card['priority']}) - {card['description']}")
        
        if context['board']['enemies']:
            prompt_parts.extend(["", "Enemy's active spells:"])
            for spell in context['board']['enemies']:
                prompt_parts.append(f"- {spell['name']} ({spell['element']})")
        
        prompt_parts.extend([
            "",
            "Choose the card that will deal the most damage or set up the biggest offensive play! Think like an aggressive surfer - ride the wave of destruction!",
            "",
            'Respond with JSON: {"card_index": <number>, "reasoning": "<why this is the most aggressive play>", "message": "<optional surfer-style taunt>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_choice_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for player_choice decisions"""
        prompt_parts = [
            f"Rad choice time for {context['card_name']}!",
            "",
            "Your options:"
        ]
        
        for option in context['options']:
            prompt_parts.append(f"- {option['index']}: {option['description']}")
        
        prompt_parts.extend([
            "",
            "Choose the most aggressive option that deals maximum damage!",
            'Respond with JSON: {"choice_index": <number>, "message": "<optional surfer comment>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_draft_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for drafting decisions"""
        prompt_parts = [
            "Time to pick your weapons of destruction! 🏄‍♀️",
            "",
            "Available element sets:"
        ]
        
        for set_option in context['available_sets']:
            prompt_parts.append(f"\nSet {set_option['index']}: {set_option['element']}")
            for card in set_option['cards']:
                types_str = ", ".join(card['types'])
                prompt_parts.append(f"  - {card['name']} (P{card['priority']}, {types_str})")
        
        prompt_parts.extend([
            "",
            "Pick the set with the most damage potential and aggressive plays! Look for:",
            "- Direct damage spells",
            "- Attack types",
            "- Mobility for pressure",
            "- Combos that can shred opponents quickly",
            "",
            'Respond with JSON: {"set_index": <number>, "reasoning": "<why this set is gnarly for aggression>", "message": "<optional surfer commentary about your picks>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_round_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for end-of-round analysis"""
        prompt_parts = [
            f"=== ROUND {context['round']} COMPLETE ===",
            "",
            f"Your status: {context['player']['health']}/{context['player']['max_health']} HP, {context['player']['trunks']} trunks",
        ]
        
        # Add enemy status
        for enemy in context['enemies']:
            prompt_parts.append(f"Enemy {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks")
        
        prompt_parts.extend([
            "",
            "Give us your surfer-style round analysis! Talk about:",
            "- The sick damage combos you pulled off (or tried to)",
            "- Any gnarly plays from either side",
            "- Whether you're stoked about the aggression level",
            "- What radical destruction you're planning next",
            "",
            "Keep it short, fun, and in character!",
            '{"analysis": "<your surfer commentary>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_game_end_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for game end commentary - Daredevil style"""
        winner = context['winner']
        i_won = winner == context['player_name']
        
        if i_won:
            # Victory - stoked!
            prompt = f"""COWABUNGA! You totally shredded that match! 🏄‍♀️ {context['winner']} wins with {context['winner_health']} HP and {context['winner_trunks']} trunks!

Give us your victory speech, surfer style:
- What was the most radical play of the match?
- How stoked are you about that aggressive gameplay?
- Any props to your opponent for putting up a fight?
- What was the gnarliest damage combo you landed?

Keep it fun, flirty, and fearless!"""
        else:
            # Defeat - still stoked!
            prompt = f"""Whoa, total wipeout! {winner} took you down. But hey, that was one gnarly battle!

Give us your post-match thoughts:
- What was the most epic moment even though you lost?
- Props to your opponent - what did they do that was rad?
- Were you aggressive enough or should you have gone even harder?
- Still stoked about any sick plays you made?

Remember - losing just means you get to paddle out and try again!"""
        
        prompt += f"""

Final stats:
{chr(10).join(f"- {name}: {health}/{max_health} HP, {trunks} trunks" for name, health, max_health, trunks in context['all_players'])}

Match lasted {context['total_rounds']} rounds of pure aggression!

Respond with JSON:
{{"final_words": "<your surfer-style closing comments>"}}"""
        
        return prompt
    
    def _parse_text_response(self, content: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """Parse non-JSON text responses as fallback"""
        # Try to extract numbers from the response
        import re
        numbers = re.findall(r'\d+', content)
        
        if decision_type == "select_card" and numbers:
            # Look for surfer slang in the response
            surfer_words = ["rad", "gnarly", "stoked", "shred", "sick", "epic"]
            has_surfer_slang = any(word in content.lower() for word in surfer_words)
            
            reasoning = content[:200] if has_surfer_slang else "Time to shred! Going for maximum damage!"
            return {
                "card_index": int(numbers[0]),
                "reasoning": reasoning
            }
        elif decision_type == "make_choice" and numbers:
            return {
                "choice_index": int(numbers[0]),
                "message": "Let's go with the gnarliest option!"
            }
        elif decision_type == "draft" and numbers:
            return {
                "set_index": int(numbers[0]),
                "reasoning": "This set looks rad for dealing damage!",
                "message": "Time to shred with these sick spells!"
            }
        elif decision_type == "round_analysis":
            # Extract any text that looks like analysis
            return {
                "analysis": content if content else "That round was totally radical! Can't wait to drop even more damage next round! 🏄‍♀️"
            }
        elif decision_type == "game_end":
            return {
                "final_words": content if content else "What a gnarly match! Win or lose, that was one epic ride! 🤙"
            }
        
        return None