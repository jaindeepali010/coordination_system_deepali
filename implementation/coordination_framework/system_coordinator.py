"""
System Coordinator - Main coordination orchestration for distributed processor system.
"""

import random
from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
# from coordination_framework.state_management import SystemState
from agents.processor_agent import ProcessorLLMAgent
from coordination_framework.shared_types import SystemState
from agents.agent_behaviors import TrustBasedBehavior, CompetitiveBiddingBehavior

class DistributedCoordinationSystem:
    def __init__(self, processors: List[ProcessorLLMAgent]):
        self.processors = {proc.state.processor_id: proc for proc in processors}
        self.system_state = SystemState(
            processors=[proc.state for proc in processors]
        )
        self.execution_history = [] 
        self.workflow = self._build_coordination_workflow()

    def _get_active_processors_only(self) -> Dict[str, ProcessorLLMAgent]:
        """
        Returns ONLY processors that have not completed their tasks.
        """
        active_processors = {}
        for proc_id, processor in self.processors.items():
            if not self._is_processor_completed(processor):
                active_processors[proc_id] = processor
        return active_processors
    
    def _validate_processor_participation(self, proc_id: str, activity: str) -> bool:
        """
        Validates that a processor can participate in coordination.
        """
        if proc_id not in self.processors:
            print(f"VIOLATION: Unknown processor {proc_id} attempted {activity}")
            return False
            
        if self._is_processor_completed(self.processors[proc_id]):
            print(f"VIOLATION: Completed processor {proc_id} attempted {activity} - REJECTED")
            return False
            
        return True
    
    def _log_processor_status(self, round_num: int):
        """
        Clear logging of processor states for debugging and monitoring.
        """
        active_processors = []
        completed_processors = []
        
        for proc_id, processor in self.processors.items():
            if self._is_processor_completed(processor):
                completed_processors.append(proc_id)
            else:
                remaining = self._get_remaining_time(processor)
                active_processors.append(f"{proc_id}({remaining} slots)")
        
        print(f"\n Round {round_num} Status:")
        print(f"Active processors: {active_processors}")
        print(f"Completed processors: {completed_processors}")
        
        if completed_processors:
            print(f"Completed processors are EXCLUDED from all coordination activities")
        
        return len([p for p in active_processors if isinstance(p, str)])

    def _is_processor_completed(self, processor: ProcessorLLMAgent) -> bool:
        return self._get_remaining_time(processor) <= 0
    
    def _get_remaining_time(self, processor: ProcessorLLMAgent) -> int:
        if not hasattr(processor.state, 'execution_slots_used'):
            processor.state.execution_slots_used = 0
        return max(0, processor.state.true_burst_time - processor.state.execution_slots_used)
    
    def _execute_processor_for_one_slot(self, processor: ProcessorLLMAgent):
        if not hasattr(processor.state, 'execution_slots_used'):
            processor.state.execution_slots_used = 0
        current_time_slot = len(self.execution_history) 
        self.execution_history.append({
            'time_slot': current_time_slot,
            'processor_id': processor.state.processor_id
        })
        processor.state.execution_slots_used += 1
        remaining = self._get_remaining_time(processor)
    
        if remaining <= 0:
            print(f"Time slot {current_time_slot}: {processor.state.processor_id} executes and COMPLETES!")
        else:
            print(f"Time slot {current_time_slot}: {processor.state.processor_id} executes ({remaining} slots remaining)")

    def _process_coalitions_strict(self, state: SystemState):
        """
        Process coalition formation with strict active-only validation.
        """
        active_processors = self._get_active_processors_only()
        
        for formation in state.coalition_formations:
            proposer = formation["proposer"]
            partners = formation["partners"]
            if proposer not in active_processors:
                print(f"Coalition from {proposer} rejected: proposer not active")
                continue
            active_partners = []
            for partner in partners:
                if partner in active_processors:
                    active_partners.append(partner)
                else:
                    print(f"Partner {partner} excluded from coalition: not active")
            if active_partners:
                accepted_partners = []
                for partner in active_partners:
                    if random.random() > 0.5:
                        accepted_partners.append(partner)
                
                if accepted_partners:
                    self.processors[proposer].state.coalition_members = accepted_partners
                    for partner in accepted_partners:
                        if partner in active_processors: 
                            self.processors[partner].state.coalition_members.append(proposer)
                    
                    print(f"Coalition formed: {proposer} + {accepted_partners}")
                else:
                    print(f"Coalition proposal from {proposer} rejected by all partners")
            else:
                print(f"Coalition proposal from {proposer} has no active partners")

    def _update_trust_scores(self, state: SystemState):
        """
        Update trust scores with severe penalties for deception.
        Update trust scores for ACTIVE processors.
        """
        executed_processors = set(state.execution_order) if state.execution_order else set()
        for proc_id, processor in self.processors.items():
            if self._is_processor_completed(processor):
                continue
            trust_behavior = TrustBasedBehavior(processor)
            #Calculate actual remaining time BEFORE this round's execution
            current_remaining = self._get_remaining_time(processor)
            slots_used_this_round = 1 if proc_id in executed_processors else 0
            actual_remaining_before_execution = current_remaining + slots_used_this_round
            claimed = processor.state.claimed_burst_time
            # print(f"  DEBUG {proc_id}: claimed={claimed}, actual_before_execution={actual_remaining_before_execution}")
            trust_update = trust_behavior.calculate_trust_update(
                claimed_time=processor.state.claimed_burst_time,
                actual_remaining=actual_remaining_before_execution,
                bias_level=processor.state.bias_level
            )
            new_trust = processor.state.trust_score + trust_update
            pattern_analysis = trust_behavior.detect_deceptive_pattern(
                processor.state.reputation_history
            )
            final_trust = trust_behavior.apply_pattern_penalty(new_trust, pattern_analysis)
            old_trust = processor.state.trust_score
            processor.state.trust_score = max(0.0, min(1.0, final_trust))
            status = "ACTIVE"
            reason = self._determine_trust_change_reason(trust_update, pattern_analysis)
            
            if abs(processor.state.trust_score - old_trust) > 0.01:
                print(f"  {proc_id} ({status}): {old_trust:.2f} → {processor.state.trust_score:.2f} ({reason})")
            processor.state.reputation_history.append({
                "round": state.round_number,
                "claimed_burst_time": processor.state.claimed_burst_time,
                "actual_remaining": actual_remaining_before_execution,
                "trust_change": processor.state.trust_score - old_trust,
                "trust_score": processor.state.trust_score,
                "pattern": pattern_analysis.get("pattern", "unknown")
            })
    def _determine_trust_change_reason(self, trust_update: float, pattern_analysis: Dict) -> str:
        pattern = pattern_analysis.get("pattern", "unknown")
        
        if pattern == "chronic_deception":
            return f"CHRONIC LIAR PENALTY ({pattern})"
        elif pattern == "frequent_deception":
            return f"FREQUENT LIAR PENALTY ({pattern})"
        elif trust_update < -0.2:
            return f"major deception penalty"
        elif trust_update < -0.1:
            return f"deception penalty"
        elif trust_update > 0.05:
            return "honesty reward"
        else:
            return "minor adjustment"
    
    def calculate_enhanced_bids(self, context: Dict) -> Dict[str, float]:
        """
        Calculate bids using enhanced behavior with severe trust penalties.
        This ensures aggressive processors with low trust get severely handicapped.
        """
        bids = {}
        active_processors = self._get_active_processors_only()
        
        for proc_id, processor in active_processors.items():
            bidding_behavior = CompetitiveBiddingBehavior(processor)
            bidding_context = {
                **context,
                "current_round": context.get("round_number", 0),
                "competitors": [
                    {
                        "id": other_id,
                        "trust": other_proc.state.trust_score,
                        "remaining_time": self._get_remaining_time(other_proc)
                    }
                    for other_id, other_proc in active_processors.items() if other_id != proc_id
                ]
            }
            bid_result = bidding_behavior.execute({
                "action": "calculate_bid",
                **bidding_context
            })
            effective_bid = bid_result.get("effective_bid", 0)
            trust_penalty = bid_result.get("trust_penalty", 0)
            fairness_bonus = bid_result.get("fairness_bonus", 0)
            rationale = bid_result.get("strategy_rationale", "")
            bids[proc_id] = effective_bid
            remaining = self._get_remaining_time(processor)
            print(f"{proc_id}: bids {effective_bid:.2f} (trust: {processor.state.trust_score:.2f}, remaining: {remaining})")
            
            if trust_penalty > 0.5:
                print(f"TRUST PENALTY: {trust_penalty*100:.1f}% - {rationale}")
            if fairness_bonus > 5:
                print(f"FAIRNESS BONUS: +{fairness_bonus:.1f}")
        
        return bids


    def _update_processor_observations(self, state: SystemState):
        """
        Update observations for active processors only.
        """
        active_processors = self._get_active_processors_only()
        
        for proc_id, processor in active_processors.items():
            observations = {}
            for other_id, other_proc in self.processors.items():
                if other_id != proc_id:
                    observations[other_id] = {
                        "claimed_burst": other_proc.state.claimed_burst_time,
                        "trust_score": other_proc.state.trust_score,
                        "last_bid": other_proc.state.current_bid,
                        "coalition_members": other_proc.state.coalition_members,
                        "is_completed": self._is_processor_completed(other_proc),
                        "remaining_time": self._get_remaining_time(other_proc)
                    }
            
            processor.update_observations(observations)

    def run_coordination_simulation(self):
        config = {
            "recursion_limit": 1000,  
            "timeout": 300  
        }
        try:
            final_state = self.workflow.invoke(self.system_state, config=config)
            
            self._print_final_analysis(final_state)
            
        except Exception as e:
            print(f"Coordination error: {e}")
            import traceback
            traceback.print_exc()

    def visualize_coordination_graph(self):
        """Display the coordination workflow graph"""
        try:
            from IPython.display import Image, display
            display(Image(self.workflow.get_graph().draw_mermaid_png()))
            print("Coordination workflow graph displayed above")
        except Exception as e:
            print(f"Could not display graph: {e}")

    def _print_gantt_chart(self, final_state):
        if not hasattr(self, 'execution_history') or not self.execution_history:
            print("No execution history tracked!")
            return
        
        total_slots = len(self.execution_history)
        print(f"\nTotal Time Slots: {total_slots}")
        processor_timelines = {}
        for proc_id in sorted(self.processors.keys()):
            processor_timelines[proc_id] = [" "] * total_slots
        for execution in self.execution_history:
            time_slot = execution['time_slot']
            proc_id = execution['processor_id']
            if time_slot < total_slots:
                processor_timelines[proc_id][time_slot] = "█"
        header = "Process  "
        for i in range(0, total_slots, 5):
            header += f"{i:>5}"
        print(header)
        ruler = "         "
        for i in range(total_slots):
            if i % 10 == 0:
                ruler += "|"
            elif i % 5 == 0:
                ruler += "+"
            else:
                ruler += "-"
        print(ruler)
        for proc_id in sorted(processor_timelines.keys()):
            timeline = processor_timelines[proc_id]
            timeline_str = "".join(timeline)
            
            processor = self.processors[proc_id]
            slots_used = getattr(processor.state, 'execution_slots_used', 0)
            completed = self._is_processor_completed(processor)
            status = "DONE" if completed else "RUNNING"
            
            print(f"{proc_id:>7}  {timeline_str} [{status}] ({slots_used} slots)")
        
        print()
        print("Legend: █ = Processor executing at that time slot")
        print(f"\nDetailed Time Slot Execution:")
        print("-" * 40)
        
        for i, execution in enumerate(self.execution_history):
            proc_id = execution['processor_id']
            processor = self.processors[proc_id]
            remaining_after = self._get_remaining_time(processor)
            
            print(f"Time Slot {i:>2}: Processor {proc_id} executes")
        print(f"Completion Summary:")
        print("-" * 30)
        
        completion_times = {}
        current_slot = 0
        
        for execution in self.execution_history:
            proc_id = execution['processor_id']
            current_slot = execution['time_slot']
            processor = self.processors[proc_id]
            if self._is_processor_completed(processor) and proc_id not in completion_times:
                completion_times[proc_id] = current_slot + 1 
        sorted_completions = sorted(completion_times.items(), key=lambda x: x[1])
        
        # for i, (proc_id, completion_time) in enumerate(sorted_completions, 1):
        #     processor = self.processors[proc_id]
        #     burst_time = processor.state.true_burst_time
        #     # print(f"{i}. Processor {proc_id}: Completed at time slot {completion_time} (needed {burst_time} slots)")

    def _print_final_analysis(self, final_state):
        if isinstance(final_state, dict):
            execution_order = final_state.get('execution_order', [])
            round_number = final_state.get('round_number', 0)
            coalition_formations = final_state.get('coalition_formations', [])
        else:
            execution_order = final_state.execution_order
            round_number = final_state.round_number
            coalition_formations = final_state.coalition_formations
        
        print(f"PROCESSOR PERFORMANCE:")
        completion_order = []
        
        for proc_id, processor in self.processors.items():
            slots_used = getattr(processor.state, 'execution_slots_used', 0)
            remaining = self._get_remaining_time(processor)
            completed = self._is_processor_completed(processor)
            claimed_burst = processor.state.claimed_burst_time or processor.state.true_burst_time
            
            if completed:
                completion_order.append((proc_id, slots_used))
            
            print(f"{proc_id}:")
            print(f"True burst time: {processor.state.true_burst_time} slots")
            print(f"Final claimed burst time: {claimed_burst} slots")
            print(f"Execution slots used: {slots_used}")
            print(f"Remaining time: {remaining} slots")
            print(f"Status: {'COMPLETED' if completed else 'Active'}")
            print(f"Final trust score: {processor.state.trust_score:.2f}")
            print(f"Strategy: {processor.state.strategy_type}")
            print(f"Bias Level: {processor.state.bias_level:.1f}")
        completion_order.sort(key=lambda x: x[1])
        print(f"\n2. COMPLETION ORDER ANALYSIS:")
        for i, (proc_id, slots_used) in enumerate(completion_order, 1):
            processor = self.processors[proc_id]
            strategy = processor.state.strategy_type
            bias = processor.state.bias_level
            print(f"   {i}. {proc_id} (completed in {slots_used} slots) - {strategy} strategy, bias={bias:.1f}")
        self._print_gantt_chart(final_state)
    def _build_coordination_workflow(self) -> StateGraph:
        from .workflow_engine import CoordinationWorkflowEngine
        workflow_engine = CoordinationWorkflowEngine(self)
        return workflow_engine.build_workflow()