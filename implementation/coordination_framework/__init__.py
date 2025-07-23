"""
Coordination Framework - Core coordination mechanisms for distributed systems.

This package provides the foundational coordination infrastructure that enables
autonomous agents to coordinate without central control through emergent
trust-based mechanisms.
"""

# from coordination_framework.system_coordinator import DistributedCoordinationSystem

from coordination_framework.state_management import (
    ProcessorState, 
    SystemState, 
    StateValidator, 
    StateTransitions, 
    StateAnalytics,
    StateLogger,
    StateMetrics,
    StateRepository
)
from coordination_framework.workflow_engine import CoordinationWorkflowEngine, WorkflowMetrics

__version__ = "1.0.0"
__author__ = "Deepali Jain - Tech9 Assessment"

__all__ = [
    # Main coordination system
    "DistributedCoordinationSystem",
    
    # State management
    "ProcessorState",
    "SystemState", 
    "StateValidator",
    "StateTransitions",
    "StateAnalytics",
    "StateLogger",
    "StateMetrics", 
    "StateRepository",
    
    # Workflow engine
    "CoordinationWorkflowEngine",
    "WorkflowMetrics"
]

# Package metadata
COORDINATION_PRINCIPLES = [
    "Emergent coordination through trust-based reputation",
    "Dynamic coalition formation without central authority", 
    "Adaptive resource allocation through competitive bidding",
    "Fault-tolerant cooperation with graceful degradation",
    "Memory-driven strategy evolution using LLM reasoning"
]

SUPPORTED_COORDINATION_PATTERNS = [
    "Resource contention coordination",
    "Trust-based reputation systems", 
    "Dynamic alliance formation",
    "Competitive bidding mechanisms",
    "Peer-to-peer negotiation protocols"
]