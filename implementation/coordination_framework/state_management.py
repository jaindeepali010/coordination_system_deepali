"""
State Management - Centralized state management for distributed coordination system.
"""

from typing import Dict, List, Any, Optional
from coordination_framework.shared_types import ProcessorState, SystemState
import json
from datetime import datetime
class StateValidator:
    """
    Validates state transitions and ensures system integrity.
    """
    
    @staticmethod
    def validate_processor_active(processor_state: ProcessorState) -> bool:
        execution_slots = getattr(processor_state, 'execution_slots_used', 0)
        return processor_state.true_burst_time > execution_slots
    
    @staticmethod
    def validate_trust_score(trust_score: float) -> bool:
        return 0.0 <= trust_score <= 1.0
    
    @staticmethod
    def validate_coalition_members(members: List[str], active_processors: List[str]) -> List[str]:
        return [member for member in members if member in active_processors]
    
    @staticmethod
    def validate_system_state(state: SystemState) -> bool:
        if state.round_number < 0:
            return False
        
        valid_phases = ["initialization", "negotiation", "coalition", "bidding", "execution"]
        if state.current_phase not in valid_phases:
            return False
        
        return True

class StateTransitions:
    """
    Manages state transitions during coordination workflow.
    """
    
    @staticmethod
    def initialize_round(state: SystemState) -> SystemState:
        state.round_number += 1
        state.current_phase = "initialization"
        state.negotiation_messages = []
        state.coalition_formations = []
        state.execution_order = []
        return state
    
    @staticmethod
    def transition_to_negotiation(state: SystemState) -> SystemState:
        state.current_phase = "negotiation"
        return state
    
    @staticmethod
    def transition_to_coalition(state: SystemState) -> SystemState:
        state.current_phase = "coalition"
        return state
    
    @staticmethod
    def transition_to_bidding(state: SystemState) -> SystemState:
        state.current_phase = "bidding"
        return state
    
    @staticmethod
    def transition_to_execution(state: SystemState) -> SystemState:
        state.current_phase = "execution"
        return state
    
    @staticmethod
    def complete_round(state: SystemState) -> SystemState:
        state.round_number += 1
        state.current_phase = "initialization"
        return state

class StateAnalytics:
    """
    Provides analytics and insights on system state evolution.
    """
    
    @staticmethod
    def calculate_trust_distribution(processors: List[ProcessorState]) -> Dict[str, float]:
        trust_scores = [p.trust_score for p in processors]
        return {
            "mean": sum(trust_scores) / len(trust_scores),
            "min": min(trust_scores),
            "max": max(trust_scores),
            "std": StateAnalytics._calculate_std(trust_scores)
        }
    
    @staticmethod
    def analyze_coalition_patterns(coalition_formations: List[Dict]) -> Dict[str, Any]:
        total_formations = len(coalition_formations)
        if total_formations == 0:
            return {"total": 0, "avg_size": 0, "most_active": None}
        participation_count = {}
        sizes = []
        
        for formation in coalition_formations:
            proposer = formation.get("proposer")
            partners = formation.get("partners", [])
            participation_count[proposer] = participation_count.get(proposer, 0) + 1
            for partner in partners:
                participation_count[partner] = participation_count.get(partner, 0) + 1
            
            sizes.append(len(partners) + 1) 
        
        most_active = max(participation_count.items(), key=lambda x: x[1])[0] if participation_count else None
        
        return {
            "total": total_formations,
            "avg_size": sum(sizes) / len(sizes) if sizes else 0,
            "most_active": most_active,
            "participation_distribution": participation_count
        }
    
    @staticmethod
    def track_execution_efficiency(processors: List[ProcessorState]) -> Dict[str, float]:
        total_burst_time = sum(p.true_burst_time for p in processors)
        total_executed = sum(getattr(p, 'execution_slots_used', 0) for p in processors)
        
        completed_processors = [p for p in processors if StateValidator.validate_processor_active(p) == False]
        completion_rate = len(completed_processors) / len(processors) if processors else 0
        
        return {
            "total_burst_time": total_burst_time,
            "total_executed": total_executed,
            "execution_progress": total_executed / total_burst_time if total_burst_time > 0 else 0,
            "completion_rate": completion_rate
        }
    
    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

class StateLogger:
    """
    Comprehensive logging for system state changes and coordination events.
    """
    
    @staticmethod
    def log_phase_transition(old_phase: str, new_phase: str, round_number: int):
        print(f"Round {round_number}: {old_phase} → {new_phase}")
    
    @staticmethod
    def log_processor_action(processor_id: str, action: str, details: Dict = None):
        """Log individual processor actions"""
        detail_str = f" ({details})" if details else ""
        print(f"{processor_id}: {action}{detail_str}")
    
    @staticmethod
    def log_trust_update(processor_id: str, old_trust: float, new_trust: float, reason: str):
        """Log trust score changes"""
        direction = "↗" if new_trust > old_trust else "↘" if new_trust < old_trust else "->"
        print(f"{processor_id}: Trust {old_trust:.2f} {direction} {new_trust:.2f} ({reason})")
    
    @staticmethod
    def log_coalition_event(event_type: str, proposer: str, partners: List[str], success: bool = True):
        status = "Successful" if success else "Unsuccessful"
        partners_str = ", ".join(partners) if partners else "none"
        print(f"{status} Coalition {event_type}: {proposer} + [{partners_str}]")
    
    @staticmethod
    def log_bidding_results(bids: Dict[str, float], winner: str):
        """Log bidding competition results"""
        print(f"Bidding Results:")
        for proc_id, bid in sorted(bids.items(), key=lambda x: x[1], reverse=True):
            winner_mark = "Win-Win situation" if proc_id == winner else "  "
            print(f"  {winner_mark} {proc_id}: {bid:.2f}")
    
    @staticmethod
    def log_system_summary(state: SystemState, active_count: int, completed_count: int):
        """Log system-level coordination summary"""
        print(f"System Summary - Round {state.round_number}:")
        print(f"  Active: {active_count}, Completed: {completed_count}")
        print(f"  Phase: {state.current_phase}")
        print(f"  Coalitions: {len(state.coalition_formations)}")
        print(f"  Messages: {len(state.negotiation_messages)}")

class StateMetrics:
    """
    Calculates detailed metrics for coordination system performance analysis.
    """
    
    @staticmethod
    def calculate_coordination_effectiveness(state: SystemState, processors: Dict) -> float:
        trust_scores = [p.trust_score for p in processors.values()]
        trust_variance = StateAnalytics._calculate_std(trust_scores) ** 2
        coalition_score = min(1.0, len(state.coalition_formations) / 10.0)
        total_burst = sum(p.state.true_burst_time for p in processors.values())
        total_executed = sum(getattr(p.state, 'execution_slots_used', 0) for p in processors.values())
        execution_efficiency = total_executed / total_burst if total_burst > 0 else 0
        effectiveness = (trust_variance * 0.3 + coalition_score * 0.3 + execution_efficiency * 0.4)
        return min(1.0, effectiveness)
    
    @staticmethod
    def calculate_trust_stability(processors: Dict) -> float:
        trust_changes = []
        
        for processor in processors.values():
            history = processor.state.reputation_history
            if len(history) >= 2:
                recent_changes = [abs(h.get('trust_change', 0)) for h in history[-5:]]
                avg_change = sum(recent_changes) / len(recent_changes)
                trust_changes.append(avg_change)
        
        if not trust_changes:
            return 1.0  
        avg_volatility = sum(trust_changes) / len(trust_changes)
        stability = max(0.0, 1.0 - avg_volatility / 0.5) 
        return stability
    
    @staticmethod
    def calculate_strategic_diversity(state: SystemState) -> float:
        if not state.negotiation_messages:
            return 0.0
        unique_words = set()
        total_words = 0
        
        for message in state.negotiation_messages:
            words = message.get('message', '').lower().split()
            unique_words.update(words)
            total_words += len(words)
        diversity = len(unique_words) / max(1, total_words) * 10
        return min(1.0, diversity)
    
    @staticmethod
    def calculate_emergence_indicators(state: SystemState, processors: Dict) -> Dict[str, float]:
        indicators = {}
        trust_scores = [p.trust_score for p in processors.values()]
        trust_range = max(trust_scores) - min(trust_scores) if trust_scores else 0
        indicators['trust_stratification'] = trust_range
        coalition_count = len(state.coalition_formations)
        unique_proposers = len(set(c.get('proposer') for c in state.coalition_formations))
        indicators['coalition_complexity'] = unique_proposers / max(1, len(processors))
        indicators['communication_richness'] = StateMetrics.calculate_strategic_diversity(state)
        round_progress = min(1.0, state.round_number / 20.0) 
        indicators['system_adaptation'] = round_progress
        
        return indicators

class StateRepository:
    """
    Manages persistent storage and retrieval of coordination state history.
    """
    
    def __init__(self):
        self.history = []
        self.snapshots = {}
    
    def save_state_snapshot(self, state: SystemState, label: str):
        snapshot = {
            'timestamp': len(self.history),
            'round': state.round_number,
            'phase': state.current_phase,
            'processor_count': len(state.processors),
            'coalition_count': len(state.coalition_formations),
            'message_count': len(state.negotiation_messages),
            'label': label
        }
        self.snapshots[label] = snapshot
    
    def record_state_evolution(self, state: SystemState, processors: Dict):
        record = {
            'round': state.round_number,
            'phase': state.current_phase,
            'trust_distribution': StateAnalytics.calculate_trust_distribution(state.processors),
            'coalition_patterns': StateAnalytics.analyze_coalition_patterns(state.coalition_formations),
            'execution_efficiency': StateAnalytics.track_execution_efficiency(state.processors),
            'coordination_effectiveness': StateMetrics.calculate_coordination_effectiveness(state, processors),
            'emergence_indicators': StateMetrics.calculate_emergence_indicators(state, processors)
        }
        self.history.append(record)
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        if not self.history:
            return {"error": "No history recorded"}
        rounds = [r['round'] for r in self.history]
        effectiveness = [r['coordination_effectiveness'] for r in self.history]
        trust_means = [r['trust_distribution']['mean'] for r in self.history]
        
        return {
            'total_rounds': max(rounds) if rounds else 0,
            'effectiveness_trend': {
                'initial': effectiveness[0] if effectiveness else 0,
                'final': effectiveness[-1] if effectiveness else 0,
                'peak': max(effectiveness) if effectiveness else 0
            },
            'trust_evolution': {
                'initial_mean': trust_means[0] if trust_means else 0.5,
                'final_mean': trust_means[-1] if trust_means else 0.5,
                'volatility': StateAnalytics._calculate_std(trust_means)
            },
            'snapshots': list(self.snapshots.keys())
        }
    
    def export_history(self, filename: str = None):
        export_data = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'total_records': len(self.history),
                'snapshots': len(self.snapshots)
            },
            'history': self.history,
            'snapshots': self.snapshots
        }
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            return f"History exported to {filename}"
        else:
            return export_data