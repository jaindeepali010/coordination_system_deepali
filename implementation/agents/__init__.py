"""
Agents - Autonomous LLM-powered processor agents for distributed coordination.
"""

from agents.processor_agent import ProcessorLLMAgent, AgentMemoryManager
from agents.agent_behaviors import (
    TrustBasedBehavior,
    CoalitionFormationBehavior, 
    CompetitiveBiddingBehavior,
    StrategicNegotiationBehavior,
    AdaptiveLearningBehavior
)

__version__ = "1.0.0"
__author__ = "Deepali Jain"

__all__ = [
    "ProcessorLLMAgent",
    "AgentMemoryManager",
    "TrustBasedBehavior",
    "CoalitionFormationBehavior",
    "CompetitiveBiddingBehavior", 
    "StrategicNegotiationBehavior",
    "AdaptiveLearningBehavior"
]

AGENT_CAPABILITIES = [
    "LLM-powered strategic reasoning using GPT-3.5-turbo",
    "Trust-based reputation management and assessment",
    "Dynamic coalition formation and alliance management", 
    "Adaptive bidding strategies with memory integration",
    "Sophisticated deception detection and counter-strategies",
    "Memory-driven learning and strategy evolution"
]

STRATEGY_TYPES = {
    "cooperative": "Emphasizes trust-building and fair coordination",
    "aggressive": "Prioritizes individual success through competitive tactics",
    "strategic": "Balances cooperation and competition based on situational analysis"
}

BIAS_LEVELS = {
    0.0: "Completely truthful in all coordination interactions",
    0.1: "Minimal bias - occasional strategic withholding",
    0.5: "Moderate bias - balanced deception and honesty",
    0.7: "High bias - frequent deceptive claims", 
    1.0: "Maximum bias - systematic deception strategies"
}