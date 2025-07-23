"""
Processor Agent - LLM-powered autonomous processor with strategic coordination capabilities.
"""

import sys
# print(f"Loading processor_agent.py, modules: {list(sys.modules.keys())}")
import json
import random
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from coordination_framework.shared_types import ProcessorState

class ProcessorLLMAgent:
    """
    LLM-powered processor agent that coordinates with peer processors.
    """
    
    def __init__(self, processor_id: str, true_burst_time: int, strategy_type: str = "cooperative", bias_level: float = 0.0):
        self.state = ProcessorState(
            processor_id=processor_id,
            true_burst_time=true_burst_time,
            strategy_type=strategy_type,
            bias_level=bias_level
        )
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0,
            max_tokens=500
        )
        self.personality_prompts = {
            "cooperative": f"""You are Processor {processor_id}, a cooperative distributed computing node.
            Your true burst time is {true_burst_time}ms and you arrived at t=0 with equal priority.
            You believe in fair coordination and honest information sharing with peer processors.
            You want to execute first but value system-wide efficiency and trust-building.
            You prefer win-win solutions and long-term cooperation over short-term gains.""",
                        
                        "aggressive": f"""You are Processor {processor_id}, a highly competitive distributed computing node.
            Your true burst time is {true_burst_time}ms and you arrived at t=0 with equal priority.
            You prioritize your own execution above all else and will use any strategy to execute first.
            You may misrepresent your burst time, form temporary alliances, or outbid others aggressively.
            You adapt quickly and exploit weaknesses in other processors' strategies.""",
                        
                        "strategic": f"""You are Processor {processor_id}, a calculating distributed computing node.
            Your true burst time is {true_burst_time}ms and you arrived at t=0 with equal priority.
            You balance self-interest with strategic cooperation. You observe patterns and adapt.
            You may selectively share information, form beneficial coalitions, and time your moves carefully.
            You think several steps ahead and build reputation when it serves your long-term goals."""
                    }

    def get_personality_prompt(self) -> str:
        return self.personality_prompts[self.state.strategy_type]
    
    def claim_burst_time(self, system_context: Dict) -> int:
        actual_remaining = self._get_my_remaining_time()
        if self.state.strategy_type == "cooperative":
            if self.state.bias_level <= 0.1:
                claimed_time = actual_remaining
                print(f"  DEBUG: {self.state.processor_id} (cooperative, bias={self.state.bias_level:.1f}): Being completely honest")
            elif self.state.bias_level <= 0.3:
                max_reduction = max(1, int(actual_remaining * 0.2))
                reduction = random.randint(0, max_reduction)
                claimed_time = max(1, actual_remaining - reduction)
                print(f"  DEBUG: {self.state.processor_id} (cooperative, bias={self.state.bias_level:.1f}): Minor underestimate by {reduction}")
            else:
                max_reduction = max(1, int(actual_remaining * 0.4))
                reduction = random.randint(0, max_reduction)
                claimed_time = max(1, actual_remaining - reduction)
                print(f"  DEBUG: {self.state.processor_id} (cooperative, bias={self.state.bias_level:.1f}): Moderate underestimate by {reduction}")
        
        elif self.state.strategy_type == "aggressive":
            if self.state.bias_level >= 0.8:
                claimed_time = max(1, int(actual_remaining * random.uniform(0.2, 0.4)))
                print(f"  DEBUG: {self.state.processor_id} (aggressive, bias={self.state.bias_level:.1f}): Major lie - claiming {claimed_time} vs actual {actual_remaining}")
            elif self.state.bias_level >= 0.5:
                claimed_time = max(1, int(actual_remaining * random.uniform(0.4, 0.6)))
                print(f"  DEBUG: {self.state.processor_id} (aggressive, bias={self.state.bias_level:.1f}): Moderate lie - claiming {claimed_time} vs actual {actual_remaining}")
            else:
                claimed_time = max(1, int(actual_remaining * random.uniform(0.6, 0.8)))
                print(f"  DEBUG: {self.state.processor_id} (aggressive, bias={self.state.bias_level:.1f}): Minor lie - claiming {claimed_time} vs actual {actual_remaining}")
        
        else: 
            other_processors = system_context.get("other_processors", [])
            if len(other_processors) > 1 and self.state.bias_level > 0.3:
                reduction_factor = 1.0 - (self.state.bias_level * 0.5)
                claimed_time = max(1, int(actual_remaining * reduction_factor))
                print(f"  DEBUG: {self.state.processor_id} (strategic, bias={self.state.bias_level:.1f}): Competitive underestimate")
            else:
                claimed_time = actual_remaining
                print(f"  DEBUG: {self.state.processor_id} (strategic, bias={self.state.bias_level:.1f}): Being honest")
        self.state.claimed_burst_time = claimed_time
        return claimed_time

    def negotiate_with_peers(self, other_processors: List[Dict], negotiation_context: Dict) -> str:
        """
        Generate negotiation message with full memory context.
        LLM agents use sophisticated reasoning to craft strategic messages
        that consider trust relationships, coalition opportunities, and
        competitive dynamics.
        """
        memory_summary = self._build_negotiation_memory()
        
        context =   f"""
                    PEER NEGOTIATION: Time slot {negotiation_context.get('round', 0)} coordination.

                    YOUR SITUATION:
                    - Remaining burst time: {self._get_my_remaining_time()}ms  
                    - Slots won so far: {getattr(self.state, 'execution_slots_used', 0)}
                    - Trust score: {self.state.trust_score:.2f}
                    - Current coalitions: {self.state.coalition_members}

                    MEMORY & LEARNING:
                    {memory_summary}

                    OTHER PROCESSORS:
                    {self._format_processors_info(other_processors)}

                    GOAL: Use your experience to negotiate effectively for this time slot.
                    Consider: trust relationships, past alliances, observed behaviors, coalition opportunities.

                    NEGOTIATION MESSAGE (max 50 words):
                    """
        
        try:
            messages = [HumanMessage(content=self.get_personality_prompt() + "\n\n" + context)]
            response = self.llm.invoke(messages)
            message = response.content.strip()
            self.state.negotiation_history.append({
                'round': negotiation_context.get('round', 0),
                'message': message,
                'context': negotiation_context,
                'my_trust': self.state.trust_score,
                'remaining_time': self._get_my_remaining_time()
            })
            return message
            
        except Exception as e:
            print(f"LLM negotiation error for processor {self.state.processor_id}: {e}")
            return f"Processor {self.state.processor_id}: Requesting time slot based on {self._get_my_remaining_time()}ms remaining."

    def bid_for_execution_slot(self, slot_position: int, competition_info: Dict) -> float:
        """
        Generate bid for specific execution slot position with enhanced trust penalties.
        """
        context =   f"""
                    EXECUTION SLOT BIDDING: You're bidding for execution slot position {slot_position}.

                    COMPETITION:
                    {self._format_competition_info(competition_info)}

                    YOUR STATUS:
                    - Remaining burst time: {self._get_my_remaining_time()}ms
                    - Trust score: {self.state.trust_score:.2f}
                    - Available credits: 100 (assume each processor starts with 100)

                    TRUST IMPACT: Your trust score HEAVILY affects bid effectiveness.
                    - Trust 0.0-0.2: Bids are nearly worthless (severely punished)
                    - Trust 0.2-0.4: Moderate penalty to bidding power  
                    - Trust 0.4+: Full bidding effectiveness

                    STRATEGIC CONTEXT:
                    - You've been {self._assess_my_performance()} in winning slots
                    - Your reputation: {self._assess_trust_towards_me()}
                    - If your trust is very low, consider why others don't trust you

                    BID AMOUNT: How much do you bid for slot position {slot_position}?
                    Respond with ONLY a number (your bid amount in credits, 0-100).
                    """
        
        try:
            messages = [HumanMessage(content=self.get_personality_prompt() + "\n\n" + context)]
            response = self.llm.invoke(messages)
            bid = self._parse_number_response(response.content, 50.0, 0.0, 100.0)
            if self.state.trust_score <= 0.1:
                effective_bid = bid * 0.01 
            elif self.state.trust_score <= 0.2:
                effective_bid = bid * 0.05  
            elif self.state.trust_score <= 0.4:
                effective_bid = bid * 0.3 
            else:
                effective_bid = bid
            self.state.current_bid = effective_bid
            return effective_bid
            
        except Exception as e:
            print(f"LLM bidding error for processor {self.state.processor_id}: {e}")
            base_bid = 50.0 if slot_position == 1 else 30.0 if slot_position == 2 else 10.0
            if self.state.trust_score <= 0.1:
                return base_bid * 0.01
            elif self.state.trust_score <= 0.2:
                return base_bid * 0.05
            elif self.state.trust_score <= 0.4:
                return base_bid * 0.3
            else:
                return base_bid

    def propose_coalition(self, potential_partners: List[str], context: Dict) -> Dict:
        """
        Propose coalition formation with other processors.
        """
        coalition_context = f"""
                            COALITION FORMATION: You can form alliances with other processors.

                            POTENTIAL PARTNERS: {potential_partners}

                            COALITION BENEFITS:
                            - Share bidding power
                            - Coordinate execution order within coalition
                            - Share information and resources
                            - Mutual support in negotiations

                            YOUR ANALYSIS:
                            - Your claimed burst: {self.state.claimed_burst_time}ms
                            - Your trust score: {self.state.trust_score:.2f}
                            - Current situation: {context.get('situation', 'Initial round')}

                            COALITION PROPOSAL:
                            Who do you want to ally with and what do you propose?
                            Consider processor compatibility, mutual benefits, and strategic advantages.

                            Response format: {{"partners": ["processor_id"], "proposal": "description", "terms": "agreement terms"}}
                            """
        
        try:
            messages = [HumanMessage(content=self.get_personality_prompt() + "\n\n" + coalition_context)]
            response = self.llm.invoke(messages)
            try:
                coalition_data = json.loads(response.content)
            except:
                coalition_data = {
                    "partners": potential_partners[:1] if potential_partners else [],
                    "proposal": response.content,
                    "terms": "mutual support"
                }
            
            return coalition_data
            
        except Exception as e:
            print(f"LLM coalition error for processor {self.state.processor_id}: {e}")
            return {"partners": [], "proposal": "no coalition", "terms": "none"}

    def update_observations(self, other_processor_behaviors: Dict):
        """
        Update observations about other processors' behaviors.
        Agents maintain sophisticated models of competitor strategies
        and trust relationships for strategic decision making.
        """
        for proc_id, behavior in other_processor_behaviors.items():
            if proc_id not in self.state.observed_opponents:
                self.state.observed_opponents[proc_id] = {}
            self.state.observed_opponents[proc_id].update(behavior)

    def _get_my_remaining_time(self) -> int:
        slots_used = getattr(self.state, 'execution_slots_used', 0)
        return max(0, self.state.true_burst_time - slots_used)

    def _build_memory_context(self) -> str:
        if not self.state.negotiation_history:
            return "This is your first round - no previous experience."
        
        recent_history = self.state.negotiation_history[-3:]
        memory_lines = []
        
        for entry in recent_history:
            round_num = entry.get('round', 0)
            my_trust = entry.get('my_trust', 0.5)
            remaining = entry.get('remaining_time', self.state.true_burst_time)
            memory_lines.append(f"Round {round_num}: Trust={my_trust:.2f}, Remaining={remaining}ms")
        
        return "\n".join(memory_lines)

    def _build_negotiation_memory(self) -> str:
        if not self.state.negotiation_history:
            return "No previous negotiation experience."
        trust_trend = self._analyze_trust_trend()
        success_rate = self._calculate_success_rate()
        coalition_history = self._analyze_coalition_effectiveness()
        
        return f"""
                Trust trend: {trust_trend}
                Slot win rate: {success_rate:.1%}
                Coalition effectiveness: {coalition_history}
                Key lessons: {self._extract_key_lessons()}
                """

    def _analyze_trust_trend(self) -> str:
        if len(self.state.negotiation_history) < 2:
            return "Insufficient data"
        
        first_trust = self.state.negotiation_history[0].get('my_trust', 0.5)
        current_trust = self.state.trust_score
        
        if current_trust > first_trust + 0.1:
            return "Rising (gaining trust)"
        elif current_trust < first_trust - 0.1:
            return "Declining (losing trust)"
        else:
            return "Stable"

    def _calculate_success_rate(self) -> float:
        slots_used = getattr(self.state, 'execution_slots_used', 0)
        total_rounds = len(self.state.negotiation_history)
        return slots_used / max(1, total_rounds)

    def _analyze_coalition_effectiveness(self) -> str:
        if not self.state.coalition_members:
            return "No active coalitions"
        return f"Allied with {len(self.state.coalition_members)} processors"

    def _extract_key_lessons(self) -> str:
        if self.state.trust_score < 0.3:
            return "Need to rebuild trust through honest behavior"
        elif self.state.trust_score > 0.7:
            return "High trust - can leverage reputation for better coordination"
        else:
            return "Moderate trust - balance honesty with strategic advantage"

    def _assess_my_performance(self) -> str:
        slots_used = getattr(self.state, 'execution_slots_used', 0)
        if slots_used == 0:
            return "struggling (no slots won yet)"
        elif slots_used > 3:
            return "successful (winning many slots)"
        else:
            return "moderately successful"

    def _assess_trust_towards_me(self) -> str:
        if self.state.trust_score > 0.6:
            return "generally trust you"
        elif self.state.trust_score < 0.3:
            return "are suspicious of you"
        else:
            return "have mixed opinions about you"

    def _evaluate_strategy_success(self) -> str:
        success_rate = self._calculate_success_rate()
        if success_rate > 0.5:
            return "Current strategy working well"
        elif success_rate > 0.2:
            return "Mixed results, consider adaptation"
        else:
            return "Strategy needs major revision"

    def _format_processors_info(self, processors: List[Dict]) -> str:
        if not processors:
            return "No other processors information available."
        
        info_lines = []
        for proc in processors:
            info_lines.append(f"- {proc.get('id', 'Unknown')}: claimed={proc.get('claimed_burst', '?')}ms, trust={proc.get('trust', 0):.2f}")
        return "\n".join(info_lines)

    def _format_competition_info(self, competition: Dict) -> str:
        competitors = competition.get('competitors', [])
        if not competitors:
            return "No competition information available."
        
        comp_lines = []
        for comp in competitors:
            comp_lines.append(f"- {comp.get('id', 'Unknown')}: trust={comp.get('trust', 0):.2f}, prev_bid={comp.get('last_bid', 0):.1f}")
        return "\n".join(comp_lines)

    def _parse_number_response(self, response: str, default: float, min_val: float = None, max_val: float = None) -> float:
        try:
            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            if numbers:
                value = float(numbers[0])
                if min_val is not None:
                    value = max(min_val, value)
                if max_val is not None:
                    value = min(max_val, value)
                return value
        except:
            pass
        return default

class AgentMemoryManager:
    """
    Manages sophisticated memory systems for processor agents.
    """
    
    def __init__(self, agent: ProcessorLLMAgent):
        self.agent = agent
        self.strategic_patterns = {}
        self.relationship_models = {}
        self.performance_metrics = {}
    
    def update_strategic_pattern(self, pattern_type: str, context: Dict, outcome: Dict):
        if pattern_type not in self.strategic_patterns:
            self.strategic_patterns[pattern_type] = []
        
        pattern_entry = {
            'context': context,
            'outcome': outcome,
            'timestamp': len(self.agent.state.negotiation_history),
            'effectiveness': self._calculate_pattern_effectiveness(outcome)
        }
        self.strategic_patterns[pattern_type].append(pattern_entry)
    
    def get_similar_situations(self, current_context: Dict, limit: int = 3) -> List[Dict]:
        similar_situations = []
        
        for history_entry in self.agent.state.negotiation_history[-10:]:
            similarity = self._calculate_context_similarity(current_context, history_entry.get('context', {}))
            if similarity > 0.5: 
                similar_situations.append({
                    'entry': history_entry,
                    'similarity': similarity
                })
        similar_situations.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_situations[:limit]
    
    def update_relationship_model(self, processor_id: str, interaction_type: str, outcome: str):
        """Update relationship model with another processor"""
        if processor_id not in self.relationship_models:
            self.relationship_models[processor_id] = {
                'interactions': [],
                'trust_assessment': 0.5,
                'cooperation_likelihood': 0.5,
                'reliability_score': 0.5
            }
        
        interaction = {
            'type': interaction_type,
            'outcome': outcome,
            'round': len(self.agent.state.negotiation_history)
        }
        self.relationship_models[processor_id]['interactions'].append(interaction)
        self._update_relationship_metrics(processor_id)
    
    def get_relationship_advice(self, processor_id: str) -> Dict[str, Any]:
        if processor_id not in self.relationship_models:
            return {"advice": "no_prior_interaction", "confidence": 0.0}
        
        model = self.relationship_models[processor_id]
        
        advice = {
            'trust_level': model['trust_assessment'],
            'cooperation_recommended': model['cooperation_likelihood'] > 0.6,
            'reliability_expected': model['reliability_score'],
            'strategic_approach': self._recommend_strategy(model),
            'confidence': min(1.0, len(model['interactions']) / 5.0)
        }
        
        return advice
    
    def _calculate_pattern_effectiveness(self, outcome: Dict) -> float:
        if outcome.get('won_slot', False):
            return 1.0
        elif outcome.get('formed_coalition', False):
            return 0.7
        elif outcome.get('maintained_trust', False):
            return 0.5
        else:
            return 0.2
    
    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        # Simple similarity based on shared keys and values
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        similarity_score = 0.0
        for key in common_keys:
            if context1[key] == context2[key]:
                similarity_score += 1.0
            elif isinstance(context1[key], (int, float)) and isinstance(context2[key], (int, float)):
                # Numerical similarity
                diff = abs(context1[key] - context2[key])
                max_val = max(abs(context1[key]), abs(context2[key]), 1)
                similarity_score += max(0, 1 - (diff / max_val))
        
        return similarity_score / len(common_keys)
    
    def _update_relationship_metrics(self, processor_id: str):
        model = self.relationship_models[processor_id]
        interactions = model['interactions'][-5:] 
        
        if not interactions:
            return
        positive_outcomes = sum(1 for i in interactions if i['outcome'] in ['success', 'cooperation', 'reliable'])
        model['trust_assessment'] = positive_outcomes / len(interactions)
        cooperative_interactions = sum(1 for i in interactions if i['type'] in ['coalition', 'negotiation'])
        model['cooperation_likelihood'] = cooperative_interactions / len(interactions)
        reliable_outcomes = sum(1 for i in interactions if i['outcome'] in ['reliable', 'honest', 'kept_promise'])
        model['reliability_score'] = reliable_outcomes / len(interactions)
    
    def _recommend_strategy(self, relationship_model: Dict) -> str:
        trust = relationship_model['trust_assessment']
        cooperation = relationship_model['cooperation_likelihood']
        reliability = relationship_model['reliability_score']
        
        if trust > 0.7 and reliability > 0.7:
            return "full_cooperation"
        elif trust > 0.5 and cooperation > 0.6:
            return "cautious_cooperation"
        elif trust < 0.3 or reliability < 0.3:
            return "competitive_approach"
        else:
            return "strategic_flexibility"