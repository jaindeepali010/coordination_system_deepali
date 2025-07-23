from langgraph.graph import StateGraph, END
from typing import Dict, Any
from coordination_framework.state_management import SystemState

class CoordinationWorkflowEngine:
    """
    Constructs and manages the LangGraph workflow for distributed coordination.
    """
    
    def __init__(self, coordination_system):
        self.coordinator = coordination_system
    
    def build_workflow(self) -> StateGraph:
        def initialization_phase(state: SystemState) -> SystemState:
            print(f"\n{'='*60}")
            print(f"ROUND {state.round_number} - INITIALIZATION PHASE")
            print(f"{'='*60}")
            state.current_phase = "initialization"
            active_processors = self.coordinator._get_active_processors_only()
            
            if not active_processors:
                print("ALL PROCESSORS COMPLETED!")
                return state
            active_count = self.coordinator._log_processor_status(state.round_number)
            for proc_id, processor in active_processors.items():
                if not self.coordinator._validate_processor_participation(proc_id, "burst_time_claim"):
                    continue
                
                other_active_processors = [
                    {
                        "id": oid, 
                        "claimed_burst": other_proc.state.claimed_burst_time or "unknown",
                        "trust": other_proc.state.trust_score,
                        "remaining": self.coordinator._get_remaining_time(other_proc)
                    }
                    for oid, other_proc in active_processors.items() if oid != proc_id
                ]
                
                claimed_time = processor.claim_burst_time({
                    "round_number": state.round_number,
                    "other_processors": other_active_processors
                })
                
                actual_remaining = self.coordinator._get_remaining_time(processor)
                print(f"Processor {proc_id}: Claims {claimed_time}ms remaining (actual: {actual_remaining}ms)")
            
            return state

        def negotiation_phase(state: SystemState) -> SystemState:
            """
            Phase 2 - ONLY active processors negotiate.
            Completed processors are completely excluded from all negotiations.
            """
            print(f"NEGOTIATION PHASE")
            print("-" * 40)
            state.current_phase = "negotiation"
            state.negotiation_messages = []
            active_processors = self.coordinator._get_active_processors_only()
            
            if not active_processors:
                print("No active processors remaining for negotiation")
                return state
            
            print(f"Negotiating processors: {list(active_processors.keys())}")
            for proc_id, processor in active_processors.items():
                if not self.coordinator._validate_processor_participation(proc_id, "negotiation"):
                    continue
                
                other_active_processors = [
                    {
                        "id": oid,
                        "claimed_burst": other_proc.state.claimed_burst_time,
                        "trust": other_proc.state.trust_score,
                        "remaining": self.coordinator._get_remaining_time(other_proc)
                    }
                    for oid, other_proc in active_processors.items() if oid != proc_id
                ]
                
                negotiation_context = {
                    "round": state.round_number,
                    "phase": "negotiation",
                    "active_processors": list(active_processors.keys()),
                    "my_remaining": self.coordinator._get_remaining_time(processor)
                }
                
                message = processor.negotiate_with_peers(other_active_processors, negotiation_context)
                
                state.negotiation_messages.append({
                    "from": proc_id,
                    "message": message,
                    "round": state.round_number
                })
                
                print(f"{proc_id}: \"{message}\"")
            
            return state

        def coalition_formation_phase(state: SystemState) -> SystemState:
            print(f"\nCOALITION FORMATION PHASE")
            print("-" * 40)
            
            state.current_phase = "coalition"
            state.coalition_formations = []
            active_processors = self.coordinator._get_active_processors_only()
            
            if not active_processors:
                print("No active processors for coalition formation")
                return state
            
            print(f"Coalition-forming processors: {list(active_processors.keys())}")
            for proc_id, processor in active_processors.items():
                if not self.coordinator._validate_processor_participation(proc_id, "coalition_formation"):
                    continue
                potential_partners = [oid for oid in active_processors.keys() if oid != proc_id]
                if not potential_partners:
                    print(f"  {proc_id}: No other active processors to form coalition with")
                    continue
                coalition_context = {
                    "round": state.round_number,
                    "situation": f"competing with {len(potential_partners)} other active processors",
                    "my_remaining": self.coordinator._get_remaining_time(processor)
                }
                coalition_proposal = processor.propose_coalition(potential_partners, coalition_context)
                
                if coalition_proposal.get("partners"):
                    active_partners = []
                    for partner in coalition_proposal["partners"]:
                        if partner in active_processors:
                            active_partners.append(partner)
                        else:
                            print(f"Partner {partner} excluded: not active")
                    
                    if active_partners:
                        state.coalition_formations.append({
                            "proposer": proc_id,
                            "partners": active_partners,
                            "proposal": coalition_proposal["proposal"],
                            "round": state.round_number
                        })
                        
                        print(f"{proc_id} proposes coalition with {active_partners}: {coalition_proposal['proposal']}")
                    else:
                        print(f"  {proc_id}: All proposed partners are inactive - no coalition formed")
                else:
                    print(f"  {proc_id}: No coalition proposal")
            self.coordinator._process_coalitions_strict(state)
            
            return state

        def bidding_phase(state: SystemState) -> SystemState:
            print(f"\nBIDDING PHASE - COMPETING FOR TIME SLOT {state.round_number}")
            print("-" * 40)
            
            state.current_phase = "bidding"
            active_processors = self.coordinator._get_active_processors_only()
            
            if not active_processors:
                print("No active processors to bid")
                state.execution_order = []
                return state
            
            print(f"Active processors competing: {list(active_processors.keys())}")
            competition_info = {
                "total_competitors": len(active_processors),
                "competitors": [
                    {
                        "id": proc_id,
                        "claimed_burst": proc.state.claimed_burst_time,
                        "trust": proc.state.trust_score,
                        "remaining": self.coordinator._get_remaining_time(proc)
                    }
                    for proc_id, proc in active_processors.items()
                ]
            }
            bids = self.coordinator.calculate_enhanced_bids({
            "round_number": state.round_number,
            "competition_info": competition_info
            })
            if bids:
                winner_id = max(bids, key=bids.get)
                print(f"Winner: {winner_id} with bid {bids[winner_id]:.2f}")
                print(f"{winner_id} will execute during time slot {state.round_number}")
                
                state.execution_order = [winner_id]
            else:
                print("No bids received - no winner for this time slot")
                state.execution_order = []

            
            return state

        def execution_phase(state: SystemState) -> SystemState:
            print(f"\nEXECUTION PHASE - TIME SLOT {state.round_number}")
            print("-" * 40)
            
            state.current_phase = "execution"
            active_processors = self.coordinator._get_active_processors_only()
            winner_id = None
            if state.execution_order and state.execution_order[0] in self.coordinator.processors:
                potential_winner = state.execution_order[0]
                if potential_winner in active_processors:
                    winner_id = potential_winner
                else:
                    print(f"Winner {potential_winner} is no longer active! Skipping execution.")
            
            if winner_id:
                winner = self.coordinator.processors[winner_id]
                
                print(f"Time slot {state.round_number}: {winner_id} executes")
                slots_used_before = getattr(winner.state, 'execution_slots_used', 0)
                burst_progress = f"{slots_used_before + 1}/{winner.state.true_burst_time}"
                print(f"   Burst progress: {burst_progress}")
                self.coordinator._execute_processor_for_one_slot(winner)
                current_active = self.coordinator._get_active_processors_only()
                for proc_id, processor in current_active.items():
                    if proc_id == winner_id:
                        continue 
                    
                    remaining = self.coordinator._get_remaining_time(processor)
                    total = processor.state.true_burst_time
                    print(f"{proc_id} waits (remaining: {remaining}/{total})")
            else:
                print("No valid winner determined for this time slot")
            self.coordinator._update_trust_scores(state)
            self.coordinator._update_processor_observations(state)
            for processor in self.coordinator.processors.values():
                processor.state.execution_position = None
                processor.state.current_bid = 0.0
            state.execution_order = []
            state.round_number += 1
            
            return state

        def check_termination(state: SystemState) -> str:
            active_processors = self.coordinator._get_active_processors_only()
            active_count = len(active_processors)
            total_count = len(self.coordinator.processors)
            
            print(f"\nTermination Check - Round {state.round_number}:")
            for proc_id, processor in self.coordinator.processors.items():
                is_completed = self.coordinator._is_processor_completed(processor)
                remaining = self.coordinator._get_remaining_time(processor)
                status = "COMPLETED" if is_completed else f"{remaining} slots remaining"
                print(f"{proc_id}: {status}")
            
            print(f"Active processors: {active_count}/{total_count}")
            
            if active_count == 0:
                print(f"ALL PROCESSORS COMPLETED! Simulation finished after {state.round_number} time slots.")
                return "terminate"
            elif state.round_number >= 50:
                print(f"Maximum time slots reached ({state.round_number}). Ending simulation.")
                return "terminate"
            else:
                active_ids = list(active_processors.keys())
                print(f"Time slot {state.round_number} complete. Active processors: {active_ids}")
                return "continue"
        workflow = StateGraph(SystemState)
        
        workflow.add_node("initialization", initialization_phase)
        workflow.add_node("negotiation", negotiation_phase)
        workflow.add_node("coalition", coalition_formation_phase)
        workflow.add_node("bidding", bidding_phase)
        workflow.add_node("execution", execution_phase)
        
        workflow.set_entry_point("initialization")
        
        workflow.add_edge("initialization", "negotiation")
        workflow.add_edge("negotiation", "coalition")
        workflow.add_edge("coalition", "bidding")
        workflow.add_edge("bidding", "execution")
        
        workflow.add_conditional_edges(
            "execution",
            check_termination,
            {
                "continue": "initialization",
                "terminate": END
            }
        )
        
        return workflow.compile()

class WorkflowMetrics:
    def __init__(self):
        self.phase_durations = {}
        self.phase_outcomes = {}
        self.transition_counts = {}
    
    def record_phase_start(self, phase: str, timestamp: float):
        if phase not in self.phase_durations:
            self.phase_durations[phase] = []
        self.phase_durations[phase].append({"start": timestamp})
    
    def record_phase_end(self, phase: str, timestamp: float, outcome: Dict):
        if phase in self.phase_durations and self.phase_durations[phase]:
            last_entry = self.phase_durations[phase][-1]
            if "start" in last_entry and "end" not in last_entry:
                last_entry["end"] = timestamp
                last_entry["duration"] = timestamp - last_entry["start"]
        
        if phase not in self.phase_outcomes:
            self.phase_outcomes[phase] = []
        self.phase_outcomes[phase].append(outcome)
    
    def record_transition(self, from_phase: str, to_phase: str):
        transition = f"{from_phase}->{to_phase}"
        self.transition_counts[transition] = self.transition_counts.get(transition, 0) + 1
    
    def get_workflow_analysis(self) -> Dict[str, Any]:
        analysis = {
            "phase_performance": {},
            "transition_frequency": self.transition_counts,
            "workflow_efficiency": {}
        }
        for phase, durations in self.phase_durations.items():
            completed_durations = [d["duration"] for d in durations if "duration" in d]
            if completed_durations:
                analysis["phase_performance"][phase] = {
                    "count": len(completed_durations),
                    "avg_duration": sum(completed_durations) / len(completed_durations),
                    "total_time": sum(completed_durations)
                }
        total_rounds = self.transition_counts.get("execution->initialization", 0)
        if total_rounds > 0:
            analysis["workflow_efficiency"] = {
                "total_rounds": total_rounds,
                "avg_round_time": sum(
                    sum(d["duration"] for d in durations if "duration" in d)
                    for durations in self.phase_durations.values()
                ) / total_rounds if total_rounds > 0 else 0
            }
        return analysis