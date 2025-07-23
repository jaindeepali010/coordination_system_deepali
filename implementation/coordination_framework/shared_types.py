"""
Shared Types - Core data structures for distributed coordination system.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ProcessorState:
    """
    State of a processor agent including private and observable information.
    
    This represents the complete state of an autonomous processor agent, including
    both private strategic information and publicly observable coordination data.
    """
    processor_id: str
    true_burst_time: int
    arrival_time: int = 0  
    priority: str = "equal"  
    
    strategy_type: str = "cooperative"  
    bias_level: float = 0.0  
    
    claimed_burst_time: Optional[int] = None
    trust_score: float = 0.5
    reputation_history: List[Dict] = field(default_factory=list)
    
    current_bid: float = 0.0
    coalition_members: List[str] = field(default_factory=list)
    execution_position: Optional[int] = None
    
    negotiation_history: List[Dict] = field(default_factory=list)
    strategy_effectiveness: Dict[str, float] = field(default_factory=dict)
    observed_opponents: Dict[str, Dict] = field(default_factory=dict)

@dataclass
class SystemState:
    """
    Global system state tracking coordination workflow progress.
    """
    processors: List[ProcessorState]
    round_number: int = 0
    execution_order: List[str] = field(default_factory=list)
    negotiation_messages: List[Dict] = field(default_factory=list)
    coalition_formations: List[Dict] = field(default_factory=list)
    trust_updates: Dict[str, float] = field(default_factory=dict)
    current_phase: str = "initialization" 

ProcessorDict = Dict[str, Any]  
CoordinationMessage = Dict[str, Any]  
TrustUpdate = Dict[str, float]  
CoalitionFormation = Dict[str, Any]  