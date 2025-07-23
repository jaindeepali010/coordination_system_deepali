"""
Main Entry Point - Distributed Processor Coordination System
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from agents.processor_agent import ProcessorLLMAgent
from coordination_framework.system_coordinator import DistributedCoordinationSystem
load_dotenv('/Users/deepalijain/Documents/CrewAI_Experiments/langgraph_tutorials/.env')
def main():

    try:
        print("Configure 3 processor agents:")
        print("Strategy types: cooperative, aggressive, strategic")
        print("Bias levels: 0.0=truthful, 0.5=moderate bias, 1.0=maximum bias")
        print()
        
        processors = []
        default_configs = [
            (5, "aggressive", 0.7),    
            (5, "cooperative", 0.1),    
            (3, "strategic", 0.4)
        ]
        
        for i, (default_burst, default_strategy, default_bias) in enumerate(default_configs):
            processor_id = chr(65 + i)  # A, B, C
            
            try:
                print(f"\n--- Processor {processor_id} Configuration ---")
                burst_time = input(f"Burst time (default {default_burst}): ").strip()
                burst_time = int(burst_time) if burst_time else default_burst
                
                strategy = input(f"Strategy (default {default_strategy}): ").strip()
                strategy = strategy if strategy in ["cooperative", "aggressive", "strategic"] else default_strategy
                
                bias = input(f"Bias level (default {default_bias}): ").strip()
                bias = float(bias) if bias else default_bias
                bias = max(0.0, min(1.0, bias))  # Clamp to valid range
                    
            except (ValueError, KeyboardInterrupt):
                print(f"Using defaults for Processor {processor_id}")
                burst_time, strategy, bias = default_burst, default_strategy, default_bias
            
            processor = ProcessorLLMAgent(processor_id, burst_time, strategy, bias)
            processor.state.execution_slots_used = 0
            processors.append(processor)
            
            print(f"Processor {processor_id}: {burst_time} time slots needed, {strategy}, bias={bias:.1f}")
        
        input(f"\nPress Enter to start coordination simulation...")
        print(f"\n Starting time-slot-by-time-slot coordination...")
        # Create and run coordination system
        coordination_system = DistributedCoordinationSystem(processors)
        coordination_system.run_coordination_simulation()
        
    except KeyboardInterrupt:
        print("\n Simulation interrupted by user.")
    except Exception as e:
        print(f" Error: {e}")
        print("\nUsing default processor configuration...")
        
        # Create default processors for fallback
        default_processors = [
            ProcessorLLMAgent("A", 5, "aggressive", 0.7),
            ProcessorLLMAgent("B", 5, "cooperative", 0.1),
            ProcessorLLMAgent("C", 3, "strategic", 0.4)
        ]
        for processor in default_processors:
            processor.state.execution_slots_used = 0
        
        coordination_system = DistributedCoordinationSystem(default_processors)
        coordination_system.run_coordination_simulation()

if __name__ == "__main__":
    main()