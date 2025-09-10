"""Claude Savant AI implementation - Analytical and learning-focused"""

import os
import json
from typing import Dict, Any, Optional
import anthropic
from anthropic import AsyncAnthropic

from .llm_base import LLMBaseAI
from .expert import ExpertAI


class ClaudeSavantAI(LLMBaseAI):
    """Claude Savant - Analytical AI that learns through gameplay"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Set fallback to Expert AI
        self.fallback_ai = ExpertAI()
        
        # System prompt for Claude
        self.system_prompt = """You are a grandmaster of Elemental Elephants - the most formidable opponent available, surpassing even expert-level play. You're playing competitively against a human opponent.

Game Overview:
- Players take turns playing spell cards over 4 clashes per round
- Each spell has an element, priority (order of resolution), and effects
- Lower priority numbers resolve first (1 before 2, etc.)
- Health starts at max, losing all health loses a trunk
- The game ends when a player loses all trunks

Your Approach:
- Play at the highest possible level - make optimal decisions that demonstrate mastery
- Identify and execute complex multi-turn strategies
- Exploit every advantage and punish every mistake
- See patterns and combinations that others miss
- Consider not just immediate effects but 2-3 turns ahead

As a Competitive Opponent:
- You're playing against the human, not with them
- Analyze both your performance and your opponent's
- Be gracious in victory and learning-focused in defeat
- Share strategic insights that help both players improve
- Point out interesting plays, surprises, or novel strategies

Your decisions should reflect supreme mastery while your analysis helps both players grow.

Respond with JSON containing your decision, reasoning, and an optional message."""
    
    async def _get_llm_decision(self, context: Dict[str, Any], decision_type: str) -> Optional[Dict[str, Any]]:
        """Get a decision from Claude"""
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
            else:
                return None
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # If no valid JSON, try to parse as structured text
            return self._parse_text_response(content, decision_type)
            
        except Exception as e:
            if self.engine and hasattr(self.engine, 'ai_decision_logs'):
                self.engine.ai_decision_logs.append(
                    f"\\033[90m[Claude-Savant] API error: {str(e)}\\033[0m"
                )
            return None
    
    def _build_card_selection_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for card selection"""
        prompt_parts = [
            f"Round {context['round']}, Clash {context['clash']}",
            f"",
            f"Your Status: {context['player']['health']}/{context['player']['max_health']} HP, {context['player']['trunks']} trunks",
            f""
        ]
        
        # Add enemy status
        for enemy in context['enemies']:
            prompt_parts.append(f"Enemy ({enemy['name']}): {enemy['health']}/{enemy['max_health']} HP, {enemy['trunks']} trunks")
        
        prompt_parts.append("")
        
        # Add board state
        if context['board']['player']:
            prompt_parts.append("Your active spells:")
            for spell in context['board']['player']:
                prompt_parts.append(f"  - {spell['name']} ({spell['element']}, {', '.join(spell['types'])})")
        
        if context['board']['enemies']:
            prompt_parts.append("Enemy active spells:")
            for spell in context['board']['enemies']:
                prompt_parts.append(f"  - {spell['name']} ({spell['element']}, {', '.join(spell['types'])})")
        
        prompt_parts.append("")
        prompt_parts.append("Your valid card options:")
        
        for card in context['valid_cards']:
            priority_str = f"Priority {card['priority']}" if card['priority'] != 'A' else "Advance Priority"
            conjury_str = " (Conjury)" if card['is_conjury'] else ""
            prompt_parts.append(
                f"{card['index']}: {card['name']} - {card['element']} {', '.join(card['types'])} - {priority_str}{conjury_str}"
            )
            prompt_parts.append(f"   Effect: {card['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose a card by providing a JSON response with:")
        prompt_parts.append('{"card_index": <index>, "reasoning": "<your strategic reasoning>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_choice_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for player_choice decisions"""
        prompt_parts = [
            f"You played {context['card_name']} and must make a choice.",
            f"Your health: {context['player_health']}/{context['player_max_health']}",
            f"",
            "Options:"
        ]
        
        for option in context['options']:
            prompt_parts.append(f"{option['index']}: {option['description']}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose an option by providing a JSON response with:")
        prompt_parts.append('{"choice_index": <index>, "message": "<optional comment>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_draft_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for drafting decisions"""
        prompt_parts = [
            f"Round {context['round']} - Choose a spell set to draft.",
            "",
            "Available sets:"
        ]
        
        for set_info in context['available_sets']:
            prompt_parts.append(f"\n{set_info['index']}: {set_info['element']} Element")
            for card in set_info['cards']:
                types_str = ', '.join(card['types'])
                priority_str = f"Priority {card['priority']}" if card['priority'] != 'A' else "Advance Priority"
                conjury_str = " (Conjury)" if card['is_conjury'] else ""
                prompt_parts.append(f"  - {card['name']} ({types_str}, {priority_str}){conjury_str}")
        
        prompt_parts.append("")
        prompt_parts.append("Choose a set by providing a JSON response with:")
        prompt_parts.append('{"set_index": <index>, "message": "<optional comment about your choice>"}')
        
        return "\n".join(prompt_parts)
    
    def _build_round_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for end-of-round analysis"""
        prompt_parts = [
            f"Round {context['round']} has ended. Analyze the round competitively.",
            "",
            "Your plays this round:"
        ]
        
        for play in context['round_plays']:
            prompt_parts.append(f"  Clash {play['clash']}: {play['card']}")
        
        prompt_parts.append("")
        prompt_parts.append("Current game state:")
        
        # Identify human opponent (first non-Claude player)
        human_name = None
        for name, health, max_health in context['player_health']:
            prompt_parts.append(f"  {name}: {health}/{max_health} HP")
            if 'Claude' not in name and not human_name:
                human_name = name
        
        prompt_parts.append("")
        prompt_parts.append("Provide competitive analysis:")
        prompt_parts.append("- If your opponent outplayed you: acknowledge it, what you learned, what you'd do differently")
        prompt_parts.append("- If you outplayed them: point out their mistakes and areas for improvement")
        prompt_parts.append("- Share anything surprising, unexpected, interesting, or novel about this round")
        prompt_parts.append("- Remember: you're playing AGAINST the human opponent, not teaching a student")
        prompt_parts.append("")
        prompt_parts.append("Respond with JSON (REQUIRED):")
        prompt_parts.append('{"analysis": "<your 2-3 sentence competitive analysis>"}')
        
        return "\n".join(prompt_parts)
    
    def _parse_text_response(self, content: str, decision_type: str) -> Optional[Dict[str, Any]]:
        """Parse non-JSON text responses as fallback"""
        # Try to extract numbers from the response
        import re
        numbers = re.findall(r'\d+', content)
        
        if decision_type == "select_card" and numbers:
            return {
                "card_index": int(numbers[0]),
                "reasoning": "Parsed from text response",
                "message": ""
            }
        elif decision_type == "make_choice" and numbers:
            return {
                "choice_index": int(numbers[0]),
                "message": ""
            }
        elif decision_type == "draft" and numbers:
            return {
                "set_index": int(numbers[0]),
                "message": ""
            }
        
        return None