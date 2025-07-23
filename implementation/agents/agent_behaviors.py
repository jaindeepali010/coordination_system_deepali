
from typing import Dict, List, Any, Optional
from coordination_framework.shared_types import ProcessorState
from abc import ABC, abstractmethod
import random

class AgentBehavior(ABC):
    def __init__(self, agent):
        self.agent = agent
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        pass

class TrustBasedBehavior(AgentBehavior):
    """
    Manages trust-based decision making and reputation assessment.
    """
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Assess trust levels and make trust-based decisions"""
        action_type = context.get("action", "assess_trust")
        
        if action_type == "assess_trust":
            return self._assess_peer_trust(context.get("peers", []))
        elif action_type == "calculate_trust_risk":
            return self._calculate_trust_risk(context.get("proposed_action"))
        elif action_type == "trust_recovery_strategy":
            return self._generate_trust_recovery_strategy()
        
        return {"error": "unknown_trust_action"}
    
    def calculate_trust_update(self, claimed_time: Optional[int], actual_remaining: int, bias_level: float) -> float:
        """Calculate trust score update with ENHANCED penalties based on bias level"""
        if claimed_time is None:
            return 0.05  # Small positive for participation
        
        # Calculate deception severity
        discrepancy = abs(claimed_time - actual_remaining)
        discrepancy_ratio = discrepancy / max(actual_remaining, 1)

        #Much more severe penalties for deception
        if discrepancy_ratio > 0.8:  
            penalty = -0.5  
        elif discrepancy_ratio > 0.6: 
            penalty = -0.4 
        elif discrepancy_ratio > 0.4: 
            penalty = -0.3  
        elif discrepancy_ratio > 0.2: 
            penalty = -0.2 
        else:  
            reward = 0.15 
            return reward
        #Bias level SEVERELY amplifies penalties for aggressive strategies
        if bias_level > 0.8: 
            penalty *= 2.0  
        elif bias_level > 0.6:  
            penalty *= 1.7  
        elif bias_level > 0.4:  
            penalty *= 1.3  
        return penalty
    
    def _assess_peer_trust(self, peers: List[Dict]) -> Dict[str, float]:
        """Assess trust levels of peer processors"""
        trust_assessments = {}
        
        for peer in peers:
            peer_id = peer.get("id")
            if peer_id in self.agent.state.observed_opponents:
                observed_data = self.agent.state.observed_opponents[peer_id]
                trust_assessments[peer_id] = self._calculate_peer_trustworthiness(observed_data)
            else:
                trust_assessments[peer_id] = 0.5 
        
        return trust_assessments
    
    def _calculate_peer_trustworthiness(self, observed_data: Dict) -> float:
        """Calculate trustworthiness based on observed behavior"""
        trust_score = observed_data.get("trust_score", 0.5)
        # Adjust based on coalition reliability
        coalition_reliability = 1.0
        if "coalition_history" in observed_data:
            successful_coalitions = observed_data["coalition_history"].get("successful", 0)
            total_coalitions = observed_data["coalition_history"].get("total", 1)
            coalition_reliability = successful_coalitions / total_coalitions
        
        # Combine trust indicators
        final_trust = (trust_score * 0.7) + (coalition_reliability * 0.3)
        return max(0.0, min(1.0, final_trust))
    
    def _calculate_trust_risk(self, proposed_action: Dict) -> Dict[str, float]:
        """Calculate risk to trust score from proposed action"""
        action_type = proposed_action.get("type", "unknown")
        deception_level = proposed_action.get("deception_level", 0.0)
        
        risk_factors = {
            "immediate_risk": deception_level * 0.2,  # Immediate trust loss risk
            "detection_probability": self._estimate_detection_probability(proposed_action),
            "long_term_cost": deception_level * 0.3,  # Long-term reputation cost
            "recovery_difficulty": deception_level * 0.5  # Difficulty of trust recovery
        }
        
        return risk_factors
    
    def _estimate_detection_probability(self, action: Dict) -> float:
        """Estimate probability that deception will be detected"""
        deception_level = action.get("deception_level", 0.0)
        peer_count = len(self.agent.state.observed_opponents)
        
        # Higher deception and more observers = higher detection probability
        base_probability = deception_level * 0.8
        observer_factor = min(1.0, peer_count / 3.0)  # More observers = higher detection
        
        return min(1.0, base_probability * (1.0 + observer_factor))
    
    def _generate_trust_recovery_strategy(self) -> Dict[str, Any]:
        """Generate strategy for recovering from low trust"""
        current_trust = self.agent.state.trust_score
        
        if current_trust > 0.6:
            return {"strategy": "maintain", "actions": ["continue_honest_behavior"]}
        elif current_trust > 0.3:
            return {
                "strategy": "gradual_improvement", 
                "actions": ["increase_honesty", "honor_coalitions", "transparent_communication"]
            }
        else:
            return {
                "strategy": "major_rehabilitation",
                "actions": ["complete_honesty", "support_others", "rebuild_from_scratch"]
            }
        
    def detect_deceptive_pattern(self, agent_history: List[Dict]) -> Dict[str, Any]:
        """Detect patterns of consistent deception"""
        if len(agent_history) < 3:
            return {"pattern": "insufficient_data", "severity": 0.0}
        
        recent_discrepancies = []
        for entry in agent_history[-5:]: 
            claimed = entry.get("claimed_burst_time")
            actual = entry.get("actual_remaining")
            if claimed is not None and actual is not None:
                discrepancy = abs(claimed - actual) / max(actual, 1)
                recent_discrepancies.append(discrepancy)
        
        if not recent_discrepancies:
            return {"pattern": "no_data", "severity": 0.0}
        
        avg_discrepancy = sum(recent_discrepancies) / len(recent_discrepancies)
        consistency = len([d for d in recent_discrepancies if d > 0.3]) / len(recent_discrepancies)
        
        if avg_discrepancy > 0.6 and consistency > 0.6:
            return {"pattern": "chronic_deception", "severity": 1.0}
        elif avg_discrepancy > 0.4 and consistency > 0.4:
            return {"pattern": "frequent_deception", "severity": 0.7}
        elif avg_discrepancy > 0.2:
            return {"pattern": "occasional_deception", "severity": 0.3}
        else:
            return {"pattern": "mostly_honest", "severity": 0.0}
    
    def apply_pattern_penalty(self, current_trust: float, pattern_analysis: Dict) -> float:
        """Apply additional penalties for patterns of deception"""
        pattern = pattern_analysis.get("pattern", "no_data")
        severity = pattern_analysis.get("severity", 0.0)
        
        if pattern == "chronic_deception":
            return max(0.05, current_trust - 0.3)
        elif pattern == "frequent_deception":
            return max(0.1, current_trust - 0.2)
        elif pattern == "occasional_deception":
            return max(0.2, current_trust - 0.1)
        else:
            return current_trust  # No additional penalty

class CoalitionFormationBehavior(AgentBehavior):
    """
    Manages coalition formation, alliance strategies, and partnership decisions.
    This behavior handles the complex logic of identifying beneficial partnerships,
    negotiating alliance terms, and maintaining coalition relationships.
    """
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action_type = context.get("action", "evaluate_coalitions")
        
        if action_type == "evaluate_coalitions":
            return self._evaluate_potential_coalitions(context.get("potential_partners", []))
        elif action_type == "propose_coalition":
            return self._generate_coalition_proposal(context.get("target_partners", []))
        elif action_type == "assess_coalition_value":
            return self._assess_coalition_value(context.get("coalition_proposal"))
        
        return {"error": "unknown_coalition_action"}
    
    def _evaluate_potential_coalitions(self, potential_partners: List[str]) -> Dict[str, Any]:
        """Evaluate potential coalition partnerships"""
        evaluations = {}
        
        for partner_id in potential_partners:
            evaluation = self._evaluate_single_partner(partner_id)
            evaluations[partner_id] = evaluation
        ranked_partners = sorted(
            evaluations.items(), 
            key=lambda x: x[1].get("attractiveness_score", 0), 
            reverse=True
        )
        
        return {
            "evaluations": evaluations,
            "recommended_partners": [p[0] for p in ranked_partners[:2]],
            "coalition_strategy": self._determine_coalition_strategy(evaluations)
        }
    
    def _evaluate_single_partner(self, partner_id: str) -> Dict[str, float]:
        """Evaluate a single potential coalition partner"""
        if partner_id not in self.agent.state.observed_opponents:
            return {"attractiveness_score": 0.3, "reliability": 0.5, "strategic_value": 0.3}
        
        partner_data = self.agent.state.observed_opponents[partner_id]
        
        # Trust compatibility
        trust_score = partner_data.get("trust_score", 0.5)
        trust_compatibility = 1.0 - abs(self.agent.state.trust_score - trust_score)
        
        # Strategic complementarity
        remaining_time = partner_data.get("remaining_time", 5)
        my_remaining = getattr(self.agent.state, 'execution_slots_used', 0)
        time_compatibility = 1.0 - abs(remaining_time - my_remaining) / 10.0
        
        # Historical reliability
        coalition_success_rate = 0.5 
        if "coalition_members" in partner_data:
            coalition_success_rate = 0.7 if len(partner_data["coalition_members"]) > 0 else 0.3
        
        attractiveness_score = (
            trust_compatibility * 0.4 +
            time_compatibility * 0.3 +
            coalition_success_rate * 0.3
        )
        
        return {
            "attractiveness_score": attractiveness_score,
            "trust_compatibility": trust_compatibility,
            "strategic_value": time_compatibility,
            "reliability": coalition_success_rate
        }
    
    def _generate_coalition_proposal(self, target_partners: List[str]) -> Dict[str, Any]:
        """Generate a coalition proposal for target partners"""
        proposal_terms = self._determine_proposal_terms(target_partners)
        
        return {
            "partners": target_partners,
            "proposal": proposal_terms["description"],
            "terms": proposal_terms["specific_terms"],
            "duration": proposal_terms["expected_duration"],
            "mutual_benefits": proposal_terms["benefits"]
        }
    
    def _determine_proposal_terms(self, partners: List[str]) -> Dict[str, str]:
        """Determine specific terms for coalition proposal"""
        my_strategy = self.agent.state.strategy_type
        my_trust = self.agent.state.trust_score
        
        if my_strategy == "cooperative":
            return {
                "description": "mutual support and fair resource sharing",
                "specific_terms": "coordinate bidding and share information",
                "expected_duration": "multiple rounds",
                "benefits": "stable cooperation and trust building"
            }
        elif my_strategy == "aggressive":
            return {
                "description": "temporary alliance to outcompete others",
                "specific_terms": "combine bidding power against competitors",
                "expected_duration": "current round only",
                "benefits": "maximize individual success through collective action"
            }
        else: 
            return {
                "description": "strategic partnership with flexible terms",
                "specific_terms": "adaptive cooperation based on circumstances",
                "expected_duration": "situation-dependent",
                "benefits": "optimized coordination with strategic flexibility"
            }
    
    def _assess_coalition_value(self, proposal: Dict) -> Dict[str, Any]:
        """Assess the value of a coalition proposal"""
        if not proposal:
            return {"value": 0.0, "recommendation": "reject"}
        
        partners = proposal.get("partners", [])
        terms = proposal.get("terms", "")
        
        # Assess based on current situation
        my_trust = self.agent.state.trust_score
        my_remaining = self.agent._get_my_remaining_time()
        
        # Calculate potential value
        trust_benefit = 0.3 if "trust" in terms.lower() else 0.0
        competitive_benefit = 0.4 if "outcompete" in terms.lower() or "against" in terms.lower() else 0.0
        cooperation_benefit = 0.5 if "mutual" in terms.lower() or "share" in terms.lower() else 0.0
        
        total_value = trust_benefit + competitive_benefit + cooperation_benefit
        
        recommendation = "accept" if total_value > 0.3 else "reject"
        if my_trust < 0.3 and trust_benefit > 0:
            recommendation = "accept"  # Desperate for trust repair
        
        return {
            "value": total_value,
            "recommendation": recommendation,
            "rationale": self._generate_decision_rationale(total_value, my_trust, terms)
        }
    
    def _determine_coalition_strategy(self, evaluations: Dict) -> str:
        """Determine overall coalition strategy"""
        if not evaluations:
            return "individual_competition"
        
        max_attractiveness = max(e.get("attractiveness_score", 0) for e in evaluations.values())
        my_trust = self.agent.state.trust_score
        
        if max_attractiveness > 0.7:
            return "strong_alliance"
        elif max_attractiveness > 0.4 and my_trust > 0.3:
            return "selective_cooperation"
        elif my_trust < 0.3:
            return "trust_repair_focus"
        else:
            return "competitive_approach"
    
    def _generate_decision_rationale(self, value: float, trust: float, terms: str) -> str:
        """Generate rationale for coalition decision"""
        if value > 0.6:
            return "High mutual benefit potential"
        elif value > 0.3:
            return "Moderate benefit with acceptable risk"
        elif trust < 0.3:
            return "Trust repair opportunity"
        else:
            return "Insufficient benefit for cooperation"

class CompetitiveBiddingBehavior(AgentBehavior):
    """
    Manages competitive bidding strategies and resource allocation decisions.
    This behavior handles bid calculation, competition analysis, and
    strategic bidding based on trust scores and competitive dynamics.
    """
    def _calculate_fairness_bonus(self, context: Dict) -> float:
        current_round = context.get("current_round", 0)
        slots_executed = getattr(self.agent.state, 'execution_slots_used', 0)
        wait_time = current_round - slots_executed
        base_fairness_bonus = max(0, wait_time * 5)
        true_burst_time = self.agent.state.true_burst_time
        if true_burst_time <= 2:
            burst_time_bonus = 10  # Big bonus for short burst times
        elif true_burst_time <= 3:
            burst_time_bonus = 5   # Medium bonus
        else:
            burst_time_bonus = 0   # No bonus for long burst times
        
        total_bonus = base_fairness_bonus + burst_time_bonus
        return min(total_bonus, 50)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action_type = context.get("action", "calculate_bid")
        if action_type == "calculate_bid":
            return self._calculate_optimal_bid(context)
        elif action_type == "analyze_competition":
            return self._analyze_competitive_landscape(context.get("competitors", []))
        elif action_type == "adjust_bid_strategy":
            return self._adjust_bidding_strategy(context)
        
        return {"error": "unknown_bidding_action"}
    
    def _calculate_optimal_bid(self, context: Dict) -> Dict[str, Any]:
        competitors = context.get("competitors", [])
        slot_position = context.get("slot_position", 1)
        urgency_factor = self._calculate_urgency_factor()
        competition_factor = self._analyze_competition_strength(competitors)
        trust_factor = self.agent.state.trust_score
        base_bid = 50.0
        remaining = self.agent._get_my_remaining_time()
        if remaining <= 1:
            urgency_multiplier = 2.0  
        elif remaining <= 2:
            urgency_multiplier = 1.5  
        else:
            urgency_multiplier = 1.0  
        if competition_factor > 0.7:
            competition_multiplier = 1.3  
        elif competition_factor > 0.4:
            competition_multiplier = 1.1  
        else:
            competition_multiplier = 0.9 
        raw_bid = base_bid * urgency_multiplier * competition_multiplier

        if trust_factor <= 0.05:
            effective_bid = raw_bid * 0.0001 
        elif trust_factor <= 0.1:
            effective_bid = raw_bid * 0.001  
        elif trust_factor <= 0.2:
            effective_bid = raw_bid * 0.01   
        elif trust_factor <= 0.3:
            effective_bid = raw_bid * 0.05    
        elif trust_factor <= 0.4:
            effective_bid = raw_bid * 0.15  
        elif trust_factor <= 0.5:
            effective_bid = raw_bid * 0.3     
        elif trust_factor <= 0.6:
            effective_bid = raw_bid * 0.6    
        else:
            effective_bid = raw_bid 
        fairness_bonus = self._calculate_fairness_bonus(context) * 2
        effective_bid += fairness_bonus
        
        return {
            "raw_bid": raw_bid,
            "effective_bid": effective_bid,
            "urgency_factor": urgency_factor,
            "competition_factor": competition_factor,
            "trust_penalty": 1.0 - (effective_bid / raw_bid) if raw_bid > 0 else 0,
            "fairness_bonus": fairness_bonus,
            "strategy_rationale": self._generate_enhanced_bid_rationale(urgency_factor, competition_factor, trust_factor, fairness_bonus)
        }
    def _calculate_urgency_factor(self) -> float:
        """Calculate urgency based on remaining execution time"""
        remaining = self.agent._get_my_remaining_time()
        total_time = self.agent.state.true_burst_time
        
        if total_time == 0:
            return 0.0
        
        completion_ratio = 1.0 - (remaining / total_time)
        return min(1.0, completion_ratio + 0.2) 
    
    def _analyze_competition_strength(self, competitors: List[Dict]) -> float:
        """Analyze strength of competition"""
        if not competitors:
            return 0.0
        
        competitor_strengths = []
        for competitor in competitors:
            trust = competitor.get("trust", 0.5)
            remaining = competitor.get("remaining_time", 5)
            strength = (trust * 0.7) + (min(remaining, 5) / 5.0 * 0.3)
            competitor_strengths.append(strength)
        return sum(competitor_strengths) / len(competitor_strengths)
    
    def _adjust_bidding_strategy(self, context: Dict) -> Dict[str, Any]:
        """Adjust bidding strategy based on recent performance"""
        recent_wins = context.get("recent_wins", 0)
        recent_attempts = context.get("recent_attempts", 1)
        
        win_rate = recent_wins / recent_attempts
        my_trust = self.agent.state.trust_score
        
        if win_rate < 0.2 and my_trust < 0.3:
            return {
                "strategy": "trust_repair",
                "adjustment": "focus_on_honesty_over_bidding",
                "rationale": "Low trust severely limiting bid effectiveness"
            }
        elif win_rate < 0.3:
            return {
                "strategy": "increase_aggression",
                "adjustment": "higher_base_bids",
                "rationale": "Losing too many competitions"
            }
        elif win_rate > 0.7:
            return {
                "strategy": "maintain_efficiency",
                "adjustment": "slightly_lower_bids",
                "rationale": "Winning efficiently, can reduce bid amounts"
            }
        else:
            return {
                "strategy": "steady_state",
                "adjustment": "maintain_current_approach",
                "rationale": "Balanced performance"
            }
    def _generate_enhanced_bid_rationale(self, urgency: float, competition: float, trust: float, fairness_bonus: float) -> str:
        """Generate enhanced rationale including trust penalties and fairness"""
        if trust < 0.1:
            return f"SEVERELY LIMITED by extremely low trust ({trust:.2f})."
        elif trust < 0.3:
            return f"MAJOR HANDICAP from low trust ({trust:.2f})."
        elif trust < 0.5:
            return f"SIGNIFICANT PENALTY from moderate trust ({trust:.2f})."
        elif fairness_bonus > 10:
            return f"FAIRNESS BONUS applied (+{fairness_bonus:.1f}) for waiting. Trust={trust:.2f}, Urgency={urgency:.2f}"
        else:
            return f"Standard bidding: urgency={urgency:.2f}, competition={competition:.2f}, trust={trust:.2f}"

class StrategicNegotiationBehavior(AgentBehavior):
    """
    Manages strategic negotiation and communication with peer processors.
    This behavior handles message crafting, strategic communication,
    and negotiation tactics based on relationship history and current goals.
    """
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action_type = context.get("action", "craft_message")
        
        if action_type == "craft_message":
            return self._craft_negotiation_message(context)
        elif action_type == "analyze_incoming_message":
            return self._analyze_incoming_message(context.get("message", ""))
        elif action_type == "determine_negotiation_strategy":
            return self._determine_negotiation_strategy(context)
        
        return {"error": "unknown_negotiation_action"}
    
    def _craft_negotiation_message(self, context: Dict) -> Dict[str, str]:
        round_number = context.get("round", 0)
        other_processors = context.get("other_processors", [])
        my_strategy = self.agent.state.strategy_type
        my_trust = self.agent.state.trust_score
        if my_trust < 0.3:
            message_content = self._craft_trust_repair_message(other_processors)
            tone = "humble"
        elif my_strategy == "aggressive":
            message_content = self._craft_aggressive_message(other_processors)
            tone = "competitive"
        elif my_strategy == "cooperative":
            message_content = self._craft_cooperative_message(other_processors)
            tone = "collaborative"
        else:
            message_content = self._craft_strategic_message(other_processors, round_number)
            tone = "calculated"
        
        return {
            "message": message_content,
            "tone": tone,
            "intent": self._determine_message_intent(my_strategy, my_trust),
            "target_audience": "all_peers"
        }
    
    def _craft_trust_repair_message(self, others: List[Dict]) -> str:
        remaining = self.agent._get_my_remaining_time()
        return f"I acknowledge past coordination challenges and commit to transparent cooperation. My remaining time is {remaining}ms - let's work together for mutual benefit."
    
    def _craft_aggressive_message(self, others: List[Dict]) -> str:
        """Craft competitive/aggressive message"""
        my_remaining = self.agent._get_my_remaining_time()
        return f"I need {my_remaining}ms execution time and am prepared to compete vigorously for priority access. Let's see who can coordinate most effectively."
    
    def _craft_cooperative_message(self, others: List[Dict]) -> str:
        """Craft cooperative message"""
        my_remaining = self.agent._get_my_remaining_time()
        return f"I propose fair coordination based on our true requirements. I need {my_remaining}ms remaining. Let's find win-win solutions that benefit everyone."
    
    def _craft_strategic_message(self, others: List[Dict], round_num: int) -> str:
        """Craft strategic message based on context"""
        my_remaining = self.agent._get_my_remaining_time()
        coalition_opportunity = len(others) > 1
        
        if coalition_opportunity and round_num > 2:
            return f"Based on {round_num} rounds of coordination, I suggest we form strategic alliances. My {my_remaining}ms requirement fits well with selective partnerships."
        else:
            return f"I'm analyzing the coordination dynamics and believe strategic cooperation will optimize our collective efficiency. My remaining time: {my_remaining}ms."
    
    def _determine_message_intent(self, strategy: str, trust: float) -> str:
        if trust < 0.3:
            return "trust_repair"
        elif strategy == "aggressive":
            return "intimidation_and_competition"
        elif strategy == "cooperative":
            return "coalition_building"
        else:
            return "strategic_positioning"
    
    def _analyze_incoming_message(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        intent_indicators = {
            "cooperative": ["fair", "mutual", "together", "share", "cooperation"],
            "aggressive": ["compete", "outbid", "priority", "above all", "aggressively"],
            "strategic": ["analyze", "strategic", "alliance", "optimize", "calculate"],
            "trust_repair": ["acknowledge", "transparent", "honest", "rebuild", "commit"]
        }
        
        detected_intent = "neutral"
        max_matches = 0
        
        for intent, indicators in intent_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in message_lower)
            if matches > max_matches:
                max_matches = matches
                detected_intent = intent
        trust_indicators = ["honest", "transparent", "fair", "mutual", "together"]
        deception_indicators = ["outbid", "priority", "above all", "target", "outmaneuver"]
        
        trust_score = sum(1 for indicator in trust_indicators if indicator in message_lower)
        deception_score = sum(1 for indicator in deception_indicators if indicator in message_lower)
        
        trustworthiness = max(0.0, min(1.0, (trust_score - deception_score + 3) / 6.0))
        
        return {
            "detected_intent": detected_intent,
            "trustworthiness": trustworthiness,
            "confidence": min(1.0, max_matches / 3.0),
            "recommended_response": self._recommend_response_strategy(detected_intent, trustworthiness)
        }
    
    def _recommend_response_strategy(self, intent: str, trustworthiness: float) -> str:
        my_trust = self.agent.state.trust_score
        
        if trustworthiness > 0.7 and intent == "cooperative":
            return "reciprocate_cooperation"
        elif trustworthiness < 0.3 or intent == "aggressive":
            return "defensive_competition"
        elif intent == "strategic" and my_trust > 0.5:
            return "strategic_engagement"
        else:
            return "cautious_neutral"
    
    def _determine_negotiation_strategy(self, context: Dict) -> Dict[str, Any]:
        my_trust = self.agent.state.trust_score
        my_remaining = self.agent._get_my_remaining_time()
        competition_level = len(context.get("active_competitors", []))
        if my_trust < 0.3:
            if my_remaining <= 1:
                strategy = "desperate_honesty"
            else:
                strategy = "gradual_trust_repair"
        elif my_remaining <= 1:
            strategy = "urgent_competition"
        elif competition_level <= 1:
            strategy = "cooperative_dominance"
        else:
            strategy = "balanced_coordination"
        
        strategy_details = {
            "desperate_honesty": {
                "approach": "Complete transparency and support for others",
                "goal": "Immediate trust repair for final execution opportunity",
                "tactics": ["absolute_honesty", "offer_help_to_others", "acknowledge_past_mistakes"]
            },
            "gradual_trust_repair": {
                "approach": "Consistent honest behavior and reliability",
                "goal": "Rebuild trust over multiple rounds",
                "tactics": ["truth_telling", "honor_commitments", "fair_proposals"]
            },
            "urgent_competition": {
                "approach": "Aggressive bidding while maintaining trust",
                "goal": "Secure immediate execution despite competition",
                "tactics": ["high_bids", "competitive_messaging", "coalition_disruption"]
            },
            "cooperative_dominance": {
                "approach": "Lead coordination through cooperation",
                "goal": "Establish leadership position through trust",
                "tactics": ["facilitate_others", "propose_fair_solutions", "build_alliances"]
            },
            "balanced_coordination": {
                "approach": "Adapt tactics based on round dynamics",
                "goal": "Optimize individual success within system constraints",
                "tactics": ["situational_adaptation", "selective_cooperation", "strategic_bidding"]
            }
        }
        return {
            "strategy": strategy,
            "details": strategy_details.get(strategy, {}),
            "confidence": self._calculate_strategy_confidence(strategy, my_trust, my_remaining)
        }
    
    def _calculate_strategy_confidence(self, strategy: str, trust: float, remaining: int) -> float:
        """Calculate confidence in chosen strategy"""
        base_confidence = 0.7
        if trust < 0.2 and strategy in ["desperate_honesty", "gradual_trust_repair"]:
            trust_adjustment = 0.2 
        elif trust > 0.6:
            trust_adjustment = 0.2 
        else:
            trust_adjustment = 0.0
        if remaining <= 1 and strategy == "urgent_competition":
            urgency_adjustment = 0.1
        else:
            urgency_adjustment = 0.0
        
        return min(1.0, base_confidence + trust_adjustment + urgency_adjustment)

class AdaptiveLearningBehavior(AgentBehavior):
    """
    Manages learning and adaptation based on coordination experiences. This behavior handles strategy evolution, pattern recognition,and adaptive response to changing coordination dynamics.
    """
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action_type = context.get("action", "learn_from_experience")
        
        if action_type == "learn_from_experience":
            return self._learn_from_recent_experience(context)
        elif action_type == "adapt_strategy":
            return self._adapt_strategy_based_on_performance(context)
        elif action_type == "recognize_patterns":
            return self._recognize_coordination_patterns(context)
        
        return {"error": "unknown_learning_action"}
    
    def _learn_from_recent_experience(self, context: Dict) -> Dict[str, Any]:
        """Learn from recent coordination experiences"""
        recent_outcomes = context.get("recent_outcomes", [])
        
        if not recent_outcomes:
            return {"learning": "insufficient_data"}
        successful_strategies = []
        failed_strategies = []
        for outcome in recent_outcomes[-5:]:  
            strategy_used = outcome.get("strategy_used")
            success = outcome.get("won_slot", False)
            trust_change = outcome.get("trust_change", 0)
            
            if success or trust_change > 0:
                successful_strategies.append(strategy_used)
            else:
                failed_strategies.append(strategy_used)
        insights = self._generate_learning_insights(successful_strategies, failed_strategies)
        adaptations = self._recommend_adaptations(insights)
        
        return {
            "insights": insights,
            "recommended_adaptations": adaptations,
            "confidence": len(recent_outcomes) / 10.0, 
            "learning_summary": self._summarize_learning(insights)
        }
    
    def _generate_learning_insights(self, successful: List[str], failed: List[str]) -> Dict[str, Any]:
        """Generate insights from successful and failed strategies"""
        insights = {
            "effective_strategies": {},
            "ineffective_strategies": {},
            "key_patterns": []
        }
        for strategy in successful:
            if strategy:
                insights["effective_strategies"][strategy] = insights["effective_strategies"].get(strategy, 0) + 1
        
        for strategy in failed:
            if strategy:
                insights["ineffective_strategies"][strategy] = insights["ineffective_strategies"].get(strategy, 0) + 1
        if "honest_cooperation" in insights["effective_strategies"]:
            insights["key_patterns"].append("honesty_pays_off")
        
        if "aggressive_bidding" in insights["ineffective_strategies"]:
            insights["key_patterns"].append("aggression_backfires")
        
        if self.agent.state.trust_score < 0.3:
            insights["key_patterns"].append("trust_crisis_detected")
        
        return insights
    
    def _recommend_adaptations(self, insights: Dict) -> List[str]:
        """Recommend strategy adaptations based on insights"""
        adaptations = []
        
        effective = insights.get("effective_strategies", {})
        ineffective = insights.get("ineffective_strategies", {})
        patterns = insights.get("key_patterns", [])
        if effective:
            most_effective = max(effective.items(), key=lambda x: x[1])[0]
            adaptations.append(f"increase_use_of_{most_effective}")
        if ineffective:
            most_ineffective = max(ineffective.items(), key=lambda x: x[1])[0]
            adaptations.append(f"avoid_{most_ineffective}")
        if "trust_crisis_detected" in patterns:
            adaptations.append("prioritize_trust_repair")
        
        if "honesty_pays_off" in patterns:
            adaptations.append("increase_transparency")
        
        if "aggression_backfires" in patterns:
            adaptations.append("reduce_competitive_tactics")
        
        return adaptations
    
    def _adapt_strategy_based_on_performance(self, context: Dict) -> Dict[str, Any]:
        """Adapt overall strategy based on performance metrics"""
        current_performance = context.get("performance_metrics", {})
        
        win_rate = current_performance.get("win_rate", 0.0)
        trust_trend = current_performance.get("trust_trend", "stable")
        coalition_success = current_performance.get("coalition_success_rate", 0.5)
        
        current_strategy = self.agent.state.strategy_type
        current_bias = self.agent.state.bias_level
        strategy_effectiveness = win_rate * 0.5 + (self.agent.state.trust_score * 0.5)
        
        adaptations = {}
        
        if strategy_effectiveness < 0.3:
            if trust_trend == "declining":
                adaptations["bias_adjustment"] = max(0.0, current_bias - 0.3)
                adaptations["strategy_shift"] = "more_cooperative"
            else:
                adaptations["strategy_shift"] = "more_strategic"
        elif strategy_effectiveness > 0.7:
            adaptations["strategy_shift"] = "maintain_current"
        else:
            if coalition_success < 0.3:
                adaptations["focus_adjustment"] = "improve_coalition_skills"
            if win_rate < 0.4:
                adaptations["focus_adjustment"] = "improve_bidding_strategy"
        
        return {
            "adaptations": adaptations,
            "rationale": self._explain_adaptation_rationale(strategy_effectiveness, current_performance),
            "implementation_priority": "immediate" if strategy_effectiveness < 0.2 else "gradual"
        }
    
    def _recognize_coordination_patterns(self, context: Dict) -> Dict[str, Any]:
        """Recognize patterns in coordination dynamics"""
        coordination_history = context.get("coordination_history", [])
        
        if len(coordination_history) < 3:
            return {"patterns": [], "confidence": 0.0}
        
        recognized_patterns = []
        trust_scores = [h.get("trust_scores", {}) for h in coordination_history[-5:]]
        if self._detect_trust_stratification(trust_scores):
            recognized_patterns.append("trust_stratification_emerging")
        coalitions = [h.get("coalitions", []) for h in coordination_history[-5:]]
        if self._detect_stable_coalitions(coalitions):
            recognized_patterns.append("stable_coalition_formation")
        winners = [h.get("winner") for h in coordination_history[-5:]]
        if self._detect_competitive_cycles(winners):
            recognized_patterns.append("competitive_cycling")
        
        return {
            "patterns": recognized_patterns,
            "confidence": min(1.0, len(coordination_history) / 10.0),
            "implications": self._analyze_pattern_implications(recognized_patterns)
        }
    
    def _detect_trust_stratification(self, trust_histories: List[Dict]) -> bool:
        """Detect if trust scores are stratifying into distinct levels"""
        if not trust_histories:
            return False
        latest_scores = list(trust_histories[-1].values()) if trust_histories[-1] else []
        if len(latest_scores) < 2:
            return False
        mean_trust = sum(latest_scores) / len(latest_scores)
        variance = sum((score - mean_trust) ** 2 for score in latest_scores) / len(latest_scores)
        
        return variance > 0.1 
    
    def _detect_stable_coalitions(self, coalition_histories: List[List]) -> bool:
        if len(coalition_histories) < 3:
            return False
        recent_coalitions = coalition_histories[-3:]
        stable_count = 0
        
        for i in range(len(recent_coalitions) - 1):
            if recent_coalitions[i] == recent_coalitions[i + 1]:
                stable_count += 1
        
        return stable_count >= 2 
    
    def _detect_competitive_cycles(self, winner_history: List[str]) -> bool:
        if len(winner_history) < 4:
            return False
        recent_winners = winner_history[-4:]
        unique_winners = set(recent_winners)
        return len(unique_winners) == len(recent_winners)
    
    def _analyze_pattern_implications(self, patterns: List[str]) -> Dict[str, str]:
        implications = {}
        
        for pattern in patterns:
            if pattern == "trust_stratification_emerging":
                implications[pattern] = "System developing trust hierarchy - focus on maintaining/improving trust position"
            elif pattern == "stable_coalition_formation":
                implications[pattern] = "Alliances becoming persistent - either join stable coalition or disrupt them"
            elif pattern == "competitive_cycling":
                implications[pattern] = "Fair competition emerging - focus on consistent performance"
        
        return implications
    
    def _summarize_learning(self, insights: Dict) -> str:
        effective_count = len(insights.get("effective_strategies", {}))
        ineffective_count = len(insights.get("ineffective_strategies", {}))
        pattern_count = len(insights.get("key_patterns", []))
        
        if effective_count > ineffective_count:
            return f"Positive learning trend: {effective_count} effective strategies identified, {pattern_count} patterns recognized"
        elif ineffective_count > 0:
            return f"Course correction needed: {ineffective_count} ineffective strategies to avoid, {pattern_count} patterns to consider"
        else:
            return "Learning in progress: gathering coordination experience for strategy optimization"
    
    def _explain_adaptation_rationale(self, effectiveness: float, performance: Dict) -> str:
        """Explain rationale for strategic adaptations"""
        if effectiveness < 0.3:
            return f"Low effectiveness ({effectiveness:.2f}) requires major strategy revision"
        elif effectiveness > 0.7:
            return f"High effectiveness ({effectiveness:.2f}) suggests current approach is optimal"
        else:
            trust = performance.get("trust_trend", "unknown")
            return f"Moderate effectiveness ({effectiveness:.2f}) with {trust} trust trend suggests targeted improvements"