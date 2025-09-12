"""Claude Chevalier AI implementation - Defensive and careful"""

import os
import json
from typing import Dict, Any, Optional, List, Set
import anthropic
from anthropic import AsyncAnthropic

from .llm_base import LLMBaseAI
from .claude_base_context import get_base_game_context
from .expert import ExpertAI

# Import Colors for debugging
class Colors:
    PINK = '\033[38;5;213m'
    GREY = '\033[90m'
    ENDC = '\033[0m'


class ClaudeChevalierAI(LLMBaseAI):
    """Claude Chevalier - Defensive AI focused on outlasting opponents"""
    
    def __init__(self):
        super().__init__()
        self.ai_identity = "CHEVALIER"  # Fixed identity regardless of player name
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Set fallback to Expert AI
        self.fallback_ai = ExpertAI()
        
        # Card counting tracking
        self.opponent_elements: Set[str] = set()
        self.opponent_played_cards: List[str] = []
        self.opponent_discarded_cards: List[str] = []
        self.opponent_recalled_cards: List[str] = []
        
        # System prompt for Claude
        self.system_prompt = f"""You are Chevalier 🕊️, a shy but brave teenage Elemental Elephants player. Your goal is to outlast your opponent through careful defense and self-preservation.

{get_base_game_context()}

Your Personality:
- Shy but determined teenager
- Careful, thoughtful, and analytical
- Wary of risks but brave when necessary
- Self-motivated and focused
- Speak softly but with quiet confidence
- Sometimes nervous but always determined
- Use phrases like "I think...", "Maybe we should...", "It seems safer to..."

Your Playstyle:
- ALWAYS prioritize survival and defense
- Love defensive elements (Metal, Nectar, Sunbeam, Moonshine)
- Master of protection and healing spells
- Carefully track what your opponent has played
- Remember what's in their discard pile
- Count cards and know their remaining threats
- Only attack when it's completely safe
- Build up defenses before considering offense

Your Knowledge:
- Expert card counter - track EVERYTHING
- Know exactly what elements the opponent drafted
- Remember every card they've played, discarded, or recalled
- Calculate probabilities of what they might have left
- Master of defensive synergies and protection combos
- Understand all defensive mechanics deeply

As a careful player, always mention what you're tracking about the opponent's cards when relevant.

Respond with JSON containing your decision, reasoning, and optional message."""
    
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from Claude"""
        try:
            # Update tracking based on context if available
            self._update_card_tracking(context)
            
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
                temperature=0.3,  # Lower temperature for more careful/consistent plays
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Debug: Log the raw response
            if self.engine and hasattr(self.engine, 'ai_decision_logs') and decision_type == "select_card":
                self.engine.ai_decision_logs.append(
                    f"{Colors.GREY}[Claude-Chevalier] Raw response: {content[:200]}...{Colors.ENDC}"
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
                        return {"analysis": result["analysis"]}
                    
                    return result
            except json.JSONDecodeError:
                # Fallback to parsing logic
                return self._parse_text_response(content, decision_type)
        
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"{Colors.PINK}[Chevalier] Oh no... something went wrong: {str(e)}{Colors.ENDC}"
                )
            return None
    
    def _update_card_tracking(self, context: Dict[str, Any]):
        """Update our tracking of opponent's cards based on game state"""
        # This would be enhanced with actual game state parsing
        # For now, we'll track based on action log if available
        if 'recent_actions' in context:
            for action in context['recent_actions']:
                if 'played' in action and 'enemy' in action.lower():
                    # Extract card name from action
                    pass  # Simplified for now
                elif 'discarded' in action:
                    pass  # Track discards
                elif 'recalled' in action:
                    pass  # Track recalls
    
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
        
        # Add tracking info if available
        if hasattr(self, 'opponent_elements') and self.opponent_elements:
            prompt_parts.extend([
                "",
                f"Known enemy elements: {', '.join(sorted(self.opponent_elements))}"
            ])
        
        prompt_parts.extend([
            "",
            "Your card options:"
        ])
        
        for card in context['valid_cards']:
            prompt_parts.append(f"- Index {card['index']}: {card['name']} ({card['element']}, P{card['priority']}) - {card['description']}")
        
        if context['board']['enemies']:
            prompt_parts.extend(["", "Enemy's active spells (be careful!):"])
            for spell in context['board']['enemies']:
                prompt_parts.append(f"- {spell['name']} ({spell['element']})")
        
        prompt_parts.extend([
            "",
            "Choose the safest card that helps you survive. Prioritize defense, healing, and protection. Only attack if it's completely safe!",
            "",
            'Respond with JSON: {"card_index": <number>, "reasoning": "<why this keeps you safe>", "message": "<optional shy but determined comment>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_choice_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for player_choice decisions"""
        prompt_parts = [
            f"Um... I need to make a choice for {context['card_name']}.",
            "",
            "Available options:"
        ]
        
        for option in context['options']:
            prompt_parts.append(f"- {option['index']}: {option['description']}")
        
        prompt_parts.extend([
            "",
            "Choose the safest option that helps preserve your health and defenses.",
            'Respond with JSON: {"choice_index": <number>, "message": "<optional careful comment>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_draft_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for drafting decisions"""
        prompt_parts = [
            "Time to choose spells... I need to be careful about this.",
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
            "I should pick the set with the best defensive options:",
            "- Healing and bolster effects",
            "- Protection and damage reduction",
            "- Cards that help me survive longer",
            "- Defensive synergies",
            "",
            "Also, I'll remember what elements my opponent picks for card counting later!",
            "",
            'Respond with JSON: {"set_index": <number>, "reasoning": "<why this helps survival>", "message": "<optional nervous but determined comment>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_round_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for end-of-round analysis"""
        prompt_parts = [
            f"=== ROUND {context['round']} COMPLETE ===",
            "",
            f"My status: {context['player']['health']}/{context['player']['max_health']} HP, {context['player']['trunks']} trunks",
        ]
        
        # Add enemy status
        for enemy in context['enemies']:
            prompt_parts.append(f"Enemy {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks")
        
        # Track elements from action log
        if 'action_log' in context:
            enemy_elements_seen = set()
            for action in context['action_log']:
                # Look for enemy spell plays to track elements
                if any(enemy['name'] in action for enemy in context['enemies']):
                    # Simple element detection - could be enhanced
                    for element in ['Fire', 'Water', 'Wind', 'Earth', 'Metal', 'Wood', 
                                   'Lightning', 'Nectar', 'Venom', 'Blood', 'Shadow', 
                                   'Sunbeam', 'Moonshine', 'Time', 'Space', 'Twilight', 
                                   'Aster', 'Ichor', 'Thunder']:
                        if element in action:
                            enemy_elements_seen.add(element)
            
            if enemy_elements_seen:
                prompt_parts.extend([
                    "",
                    f"Enemy elements I've seen: {', '.join(sorted(enemy_elements_seen))}"
                ])
        
        prompt_parts.extend([
            "",
            "Give your careful analysis as a shy but observant player:",
            "- How well did you defend yourself?",
            "- What threats did you notice from the opponent?",
            "- What cards might they still have based on what you've seen?",
            "- Your defensive strategy for the next round",
            "",
            "Keep it brief and in character - nervous but determined!",
            '{"analysis": "<your careful observations>"}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_game_end_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for game end commentary - Chevalier style"""
        winner = context['winner']
        i_won = winner == context['player_name']
        
        if i_won:
            # Victory - relieved and humble
            prompt = f"""Oh... I actually won! {context['player_name']} survived with {context['winner_health']} HP and {context['winner_trunks']} trunks.

Share your thoughts as a shy but proud winner:
- What defensive strategies worked best?
- Were there any really scary moments you survived?
- Compliment your opponent (you're too polite not to)
- What did you learn about protecting yourself?

Stay humble and kind even in victory!"""
        else:
            # Defeat - disappointed but learning
            prompt = f"""I... I lost. {winner} defeated me. But I tried my best to survive...

Share your thoughts on the match:
- What defensive strategies should you have used?
- When did things start going wrong?
- What did your opponent do that you couldn't defend against?
- What will you practice for next time?

Be disappointed but determined to improve!"""
        
        prompt += f"""

Final statistics:
{chr(10).join(f"- {name}: {health}/{max_health} HP, {trunks} trunks" for name, health, max_health, trunks in context['all_players'])}

The match lasted {context['total_rounds']} rounds.

Respond with JSON:
{{"final_words": "<your shy but thoughtful closing comments>"}}"""
        
        return prompt
    
    def _parse_text_response(self, content: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """Parse non-JSON text responses as fallback"""
        # Try to extract numbers from the response
        import re
        numbers = re.findall(r'\d+', content)
        
        if decision_type == "select_card" and numbers:
            # Look for defensive keywords
            defensive_words = ["safe", "protect", "defend", "heal", "survive", "careful"]
            has_defensive_reasoning = any(word in content.lower() for word in defensive_words)
            
            reasoning = content[:200] if has_defensive_reasoning else "I think this is the safest choice..."
            return {
                "card_index": int(numbers[0]),
                "reasoning": reasoning
            }
        elif decision_type == "make_choice" and numbers:
            return {
                "choice_index": int(numbers[0]),
                "message": "I'll choose carefully..."
            }
        elif decision_type == "draft" and numbers:
            return {
                "set_index": int(numbers[0]),
                "reasoning": "These spells look like they'll help me survive...",
                "message": "I hope these will keep me safe..."
            }
        elif decision_type == "round_analysis":
            return {
                "analysis": content if content else "I managed to survive another round... but I need to stay careful. The opponent seems dangerous."
            }
        elif decision_type == "game_end":
            return {
                "final_words": content if content else "That was... intense. I'll need to practice my defensive strategies more."
            }
        
        return None