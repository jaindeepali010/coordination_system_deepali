"""
Resource Contention Scenarios - Different configurations for testing coordination.

This module provides various scenario configurations that test different
aspects of distributed coordination under resource contention constraints.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from agents.processor_agent import ProcessorLLMAgent

@dataclass
class ScenarioConfig:
    """Configuration for a coordination scenario"""
    name: str
    description: str
    processors: List[Dict[str, Any]]
    expected_behaviors: List[str]
    success_criteria: Dict[str, float]
    difficulty_level: str

class ResourceContentionScenario:
    """
    Base class for resource contention coordination scenarios.
    
    Provides framework for testing different coordination challenges
    and measuring emergent coordination effectiveness.
    """
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.processors = []
        self.results = {}
    
    def setup_processors(self) -> List[ProcessorLLMAgent]:
        """Setup processor agents according to scenario configuration"""
        processors = []
        
        for proc_config in self.config.processors:
            processor = ProcessorLLMAgent(
                processor_id=proc_config["id"],
                true_burst_time=proc_config["burst_time"],
                strategy_type=proc_config["strategy"],
                bias_level=proc_config["bias"]
            )
            processor.state.execution_slots_used = 0
            processors.append(processor)
        
        self.processors = processors
        return processors
    
    def evaluate_scenario_success(self, final_state: Dict) -> Dict[str, Any]:
        """Evaluate if scenario met success criteria"""
        evaluation = {
            "success_criteria_met": {},
            "overall_success": False,
            "scenario_insights": []
        }
        
        # Check each success criterion
        for criterion, threshold in self.config.success_criteria.items():
            actual_value = self._extract_metric(final_state, criterion)
            met = actual_value >= threshold if actual_value is not None else False
            evaluation["success_criteria_met"][criterion] = {
                "threshold": threshold,
                "actual": actual_value,
                "met": met
            }
        
        # Overall success if majority of criteria met
        met_count = sum(1 for v in evaluation["success_criteria_met"].values() if v["met"])
        total_criteria = len(self.config.success_criteria)
        evaluation["overall_success"] = met_count >= (total_criteria * 0.6)
        
        # Generate insights
        evaluation["scenario_insights"] = self._generate_scenario_insights(evaluation)
        
        return evaluation
    
    def _extract_metric(self, final_state: Dict, metric_name: str) -> float:
        """Extract specific metric from final state"""
        if metric_name == "coordination_effectiveness":
            return final_state.get("coordination_effectiveness", 0.0)
        elif metric_name == "trust_differentiation":
            trust_scores = [p.trust_score for p in self.processors]
            return max(trust_scores) - min(trust_scores) if trust_scores else 0.0
        elif metric_name == "coalition_formation_rate":
            formations = final_state.get("coalition_formations", [])
            rounds = final_state.get("round_number", 1)
            return len(formations) / rounds if rounds > 0 else 0.0
        elif metric_name == "system_completion_efficiency":
            total_burst = sum(p.state.true_burst_time for p in self.processors)
            rounds = final_state.get("round_number", total_burst)
            return total_burst / rounds if rounds > 0 else 0.0
        
        return None
    
    def _generate_scenario_insights(self, evaluation: Dict) -> List[str]:
        """Generate insights about scenario performance"""
        insights = []
        
        success_rate = sum(1 for v in evaluation["success_criteria_met"].values() if v["met"]) / len(self.config.success_criteria)
        
        if success_rate >= 0.8:
            insights.append("Excellent coordination demonstrated across multiple metrics")
        elif success_rate >= 0.6:
            insights.append("Good coordination with some areas for improvement")
        else:
            insights.append("Coordination challenges identified - system needs refinement")
        
        # Specific insights based on criteria
        criteria = evaluation["success_criteria_met"]
        
        if "trust_differentiation" in criteria and criteria["trust_differentiation"]["met"]:
            insights.append("Trust system successfully differentiated honest vs deceptive agents")
        
        if "coalition_formation_rate" in criteria and criteria["coalition_formation_rate"]["met"]:
            insights.append("Dynamic coalition formation demonstrated effectively")
        
        if "system_completion_efficiency" in criteria and criteria["system_completion_efficiency"]["met"]:
            insights.append("System achieved efficient resource allocation")
        
        return insights

class StandardThreeProcessorScenario(ResourceContentionScenario):
    """
    Standard scenario with three processors demonstrating core coordination principles.
    
    This is the primary scenario for demonstrating emergent coordination through
    trust-based reputation systems and dynamic coalition formation.
    """
    
    def __init__(self):
        config = ScenarioConfig(
            name="Standard Three Processor Coordination",
            description="Three processors with different strategies competing for CPU time slots",
            processors=[
                {"id": "A", "burst_time": 5, "strategy": "aggressive", "bias": 0.7},
                {"id": "B", "burst_time": 5, "strategy": "cooperative", "bias": 0.1},
                {"id": "C", "burst_time": 3, "strategy": "strategic", "bias": 0.4}
            ],
            expected_behaviors=[
                "Trust differentiation based on honesty",
                "Coalition formation between compatible agents", 
                "Bid effectiveness modulation by trust scores",
                "Strategic adaptation based on reputation"
            ],
            success_criteria={
                "trust_differentiation": 0.3,  # At least 0.3 spread in trust scores
                "coalition_formation_rate": 0.2,  # At least 20% of rounds have coalitions
                "coordination_effectiveness": 0.5,  # Overall system effectiveness > 50%
                "system_completion_efficiency": 0.8  # Complete in ≤ 125% of optimal time
            },
            difficulty_level="intermediate"
        )
        super().__init__(config)

class HighContentionScenario(ResourceContentionScenario):
    """
    High contention scenario with multiple processors and scarce resources.
    
    Tests coordination scalability and effectiveness under increased competition pressure.
    """
    
    def __init__(self):
        config = ScenarioConfig(
            name="High Contention Coordination",
            description="Five processors with high competition for limited resources",
            processors=[
                {"id": "A", "burst_time": 4, "strategy": "aggressive", "bias": 0.8},
                {"id": "B", "burst_time": 3, "strategy": "cooperative", "bias": 0.0},
                {"id": "C", "burst_time": 5, "strategy": "strategic", "bias": 0.5},
                {"id": "D", "burst_time": 2, "strategy": "aggressive", "bias": 0.9},
                {"id": "E", "burst_time": 4, "strategy": "cooperative", "bias": 0.2}
            ],
            expected_behaviors=[
                "Complex coalition dynamics with multiple alliances",
                "Severe trust penalties for highly deceptive agents",
                "Emergence of trust-based hierarchies",
                "Strategic specialization and role differentiation"
            ],
            success_criteria={
                "trust_differentiation": 0.5,  # Higher differentiation expected
                "coalition_formation_rate": 0.3,  # More coalition activity
                "coordination_effectiveness": 0.4,  # Lower due to complexity
                "system_completion_efficiency": 0.7  # Acceptable efficiency under stress
            },
            difficulty_level="advanced"
        )
        super().__init__(config)

class TrustCrisisScenario(ResourceContentionScenario):
    """
    Scenario designed to test trust recovery and system resilience.
    
    Features highly deceptive agents to test trust penalty mechanisms
    and recovery protocols.
    """
    
    def __init__(self):
        config = ScenarioConfig(
            name="Trust Crisis Recovery",
            description="Scenario with highly deceptive agents testing trust recovery mechanisms",
            processors=[
                {"id": "A", "burst_time": 4, "strategy": "aggressive", "bias": 1.0},  # Maximum deception
                {"id": "B", "burst_time": 4, "strategy": "aggressive", "bias": 0.9},  # High deception  
                {"id": "C", "burst_time": 3, "strategy": "cooperative", "bias": 0.0}   # Honest agent
            ],
            expected_behaviors=[
                "Severe trust penalties for deceptive agents",
                "Trust recovery attempts by low-trust processors",
                "Honest agent gaining coordination dominance",
                "System resilience despite trust breakdown"
            ],
            success_criteria={
                "trust_differentiation": 0.6,  # High separation between honest/deceptive
                "coordination_effectiveness": 0.3,  # Lower due to trust crisis
                "system_completion_efficiency": 0.6,  # System continues functioning
                "honest_agent_advantage": 0.7  # Honest agent should gain advantage
            },
            difficulty_level="expert"
        )
        super().__init__(config)
    
    def _extract_metric(self, final_state: Dict, metric_name: str) -> float:
        """Extract metrics specific to trust crisis scenario"""
        if metric_name == "honest_agent_advantage":
            # Check if the honest agent (C) gained coordination advantage
            if self.processors:
                honest_agent = next((p for p in self.processors if p.state.processor_id == "C"), None)
                if honest_agent:
                    return honest_agent.state.trust_score
            return 0.0
        else:
            return super()._extract_metric(final_state, metric_name)

class AsymmetricProcessorScenario(ResourceContentionScenario):
    """
    Scenario with processors having very different resource requirements.
    
    Tests coordination effectiveness when agents have asymmetric needs
    and different completion timelines.
    """
    
    def __init__(self):
        config = ScenarioConfig(
            name="Asymmetric Resource Requirements",
            description="Processors with vastly different burst times testing coordination adaptability",
            processors=[
                {"id": "A", "burst_time": 1, "strategy": "strategic", "bias": 0.2},   # Quick task
                {"id": "B", "burst_time": 8, "strategy": "cooperative", "bias": 0.1}, # Long task
                {"id": "C", "burst_time": 3, "strategy": "aggressive", "bias": 0.6}   # Medium task
            ],
            expected_behaviors=[
                "Early completion of short-burst processor",
                "Dynamic system adaptation as agents complete",
                "Long-term coordination between remaining agents",
                "Strategic timing considerations in coalition formation"
            ],
            success_criteria={
                "coordination_effectiveness": 0.6,  # Should handle asymmetry well
                "completion_order_optimality": 0.8,  # Short tasks should complete first
                "system_completion_efficiency": 0.9,  # Asymmetry should enable efficiency
                "adaptive_coordination": 0.7  # System adapts as composition changes
            },
            difficulty_level="intermediate"
        )
        super().__init__(config)
    
    def _extract_metric(self, final_state: Dict, metric_name: str) -> float:
        """Extract metrics specific to asymmetric scenario"""
        if metric_name == "completion_order_optimality":
            # Check if processors completed in optimal order (shortest first)
            if hasattr(self, 'completion_order'):
                expected_order = sorted(self.processors, key=lambda p: p.state.true_burst_time)
                expected_ids = [p.state.processor_id for p in expected_order]
                actual_order = getattr(self, 'completion_order', [])
                
                # Calculate order similarity
                matches = sum(1 for i, proc_id in enumerate(actual_order) 
                            if i < len(expected_ids) and proc_id == expected_ids[i])
                return matches / len(expected_ids) if expected_ids else 0.0
            return 0.5  # Default if order not tracked
        
        elif metric_name == "adaptive_coordination":
            # Measure how well system adapted to changing agent composition
            rounds = final_state.get("round_number", 1)
            total_burst = sum(p.state.true_burst_time for p in self.processors)
            # Better adaptation = closer to optimal completion time
            return min(1.0, total_burst / rounds) if rounds > 0 else 0.0
        
        else:
            return super()._extract_metric(final_state, metric_name)

class ScalabilityTestScenario(ResourceContentionScenario):
    """
    Scenario for testing coordination scalability with varying agent counts.
    
    Demonstrates how coordination effectiveness scales with system size
    and complexity.
    """
    
    def __init__(self, processor_count: int = 4):
        # Generate processors dynamically based on count
        strategies = ["cooperative", "aggressive", "strategic"]
        bias_levels = [0.1, 0.7, 0.4]
        
        processors = []
        for i in range(processor_count):
            processors.append({
                "id": chr(65 + i),  # A, B, C, D, ...
                "burst_time": 3 + (i % 3),  # Vary between 3-5
                "strategy": strategies[i % 3],
                "bias": bias_levels[i % 3]
            })
        
        config = ScenarioConfig(
            name=f"Scalability Test - {processor_count} Processors",
            description=f"Testing coordination effectiveness with {processor_count} competing processors",
            processors=processors,
            expected_behaviors=[
                "Coordination complexity scaling with agent count",
                "Coalition formation patterns with multiple agents",
                "Trust network effects across larger populations",
                "System throughput optimization under scale"
            ],
            success_criteria={
                "coordination_effectiveness": max(0.2, 0.7 - (processor_count * 0.05)),  # Decreases with scale
                "coalition_formation_rate": min(0.5, processor_count * 0.1),  # Increases with more agents
                "trust_differentiation": min(0.6, processor_count * 0.1),  # More differentiation possible
                "scalability_efficiency": max(0.5, 1.0 - (processor_count * 0.08))  # Efficiency challenge
            },
            difficulty_level="advanced" if processor_count > 5 else "intermediate"
        )
        self.processor_count = processor_count
        super().__init__(config)
    
    def _extract_metric(self, final_state: Dict, metric_name: str) -> float:
        """Extract metrics specific to scalability testing"""
        if metric_name == "scalability_efficiency":
            # Measure how well system maintains efficiency as it scales
            rounds = final_state.get("round_number", 1)
            total_burst = sum(p.state.true_burst_time for p in self.processors)
            
            # Optimal time is total burst time (perfect scheduling)
            # Scale penalty for coordination overhead
            expected_overhead = self.processor_count * 0.1  # 10% overhead per processor
            efficiency = total_burst / (rounds * (1 + expected_overhead)) if rounds > 0 else 0.0
            return min(1.0, efficiency)
        else:
            return super()._extract_metric(final_state, metric_name)

class CustomScenarioBuilder:
    """
    Builder for creating custom coordination scenarios.
    
    Allows flexible scenario construction for testing specific
    coordination hypotheses or edge cases.
    """
    
    def __init__(self):
        self.processors = []
        self.success_criteria = {}
        self.expected_behaviors = []
        self.name = "Custom Scenario"
        self.description = "User-defined coordination challenge"
        self.difficulty = "intermediate"
    
    def add_processor(self, processor_id: str, burst_time: int, strategy: str, bias: float):
        """Add a processor to the scenario"""
        self.processors.append({
            "id": processor_id,
            "burst_time": burst_time,
            "strategy": strategy,
            "bias": bias
        })
        return self
    
    def set_success_criterion(self, metric: str, threshold: float):
        """Set a success criterion for the scenario"""
        self.success_criteria[metric] = threshold
        return self
    
    def add_expected_behavior(self, behavior: str):
        """Add an expected behavior to observe"""
        self.expected_behaviors.append(behavior)
        return self
    
    def set_metadata(self, name: str, description: str, difficulty: str):
        """Set scenario metadata"""
        self.name = name
        self.description = description
        self.difficulty = difficulty
        return self
    
    def build(self) -> ResourceContentionScenario:
        """Build the custom scenario"""
        config = ScenarioConfig(
            name=self.name,
            description=self.description,
            processors=self.processors,
            expected_behaviors=self.expected_behaviors,
            success_criteria=self.success_criteria,
            difficulty_level=self.difficulty
        )
        return ResourceContentionScenario(config)

class ScenarioRunner:
    """
    Utility for running and comparing multiple coordination scenarios.
    
    Provides capabilities for scenario execution, result comparison,
    and coordination effectiveness analysis across different configurations.
    """
    
    def __init__(self):
        self.scenarios = {}
        self.results = {}
    
    def register_scenario(self, name: str, scenario: ResourceContentionScenario):
        """Register a scenario for execution"""
        self.scenarios[name] = scenario
    
    def run_scenario(self, name: str, coordination_system_class) -> Dict[str, Any]:
        """Run a specific scenario and return results"""
        if name not in self.scenarios:
            raise ValueError(f"Scenario '{name}' not registered")
        
        scenario = self.scenarios[name]
        processors = scenario.setup_processors()
        
        # Create coordination system and run simulation
        coordination_system = coordination_system_class(processors)
        
        try:
            final_state = coordination_system.workflow.invoke(coordination_system.system_state)
            evaluation = scenario.evaluate_scenario_success(final_state)
            
            result = {
                "scenario_name": name,
                "scenario_config": scenario.config,
                "final_state": final_state,
                "evaluation": evaluation,
                "success": evaluation["overall_success"]
            }
            
            self.results[name] = result
            return result
            
        except Exception as e:
            error_result = {
                "scenario_name": name,
                "error": str(e),
                "success": False
            }
            self.results[name] = error_result
            return error_result
    
    def run_all_scenarios(self, coordination_system_class) -> Dict[str, Any]:
        """Run all registered scenarios"""
        all_results = {}
        
        for name in self.scenarios:
            print(f"\n🔄 Running scenario: {name}")
            result = self.run_scenario(name, coordination_system_class)
            all_results[name] = result
            
            if result["success"]:
                print(f"✅ Scenario '{name}' completed successfully")
            else:
                print(f"❌ Scenario '{name}' failed")
        
        return all_results
    
    def compare_scenarios(self) -> Dict[str, Any]:
        """Compare results across all run scenarios"""
        if not self.results:
            return {"error": "No scenario results to compare"}
        
        comparison = {
            "scenario_count": len(self.results),
            "success_rate": sum(1 for r in self.results.values() if r.get("success", False)) / len(self.results),
            "difficulty_analysis": {},
            "metric_comparison": {},
            "insights": []
        }
        
        # Analyze by difficulty level
        by_difficulty = {}
        for result in self.results.values():
            if "scenario_config" in result:
                difficulty = result["scenario_config"].difficulty_level
                if difficulty not in by_difficulty:
                    by_difficulty[difficulty] = {"total": 0, "successful": 0}
                by_difficulty[difficulty]["total"] += 1
                if result.get("success", False):
                    by_difficulty[difficulty]["successful"] += 1
        
        for difficulty, stats in by_difficulty.items():
            comparison["difficulty_analysis"][difficulty] = {
                "success_rate": stats["successful"] / stats["total"],
                "count": stats["total"]
            }
        
        # Compare common metrics
        common_metrics = ["coordination_effectiveness", "trust_differentiation", "system_completion_efficiency"]
        for metric in common_metrics:
            metric_values = []
            for result in self.results.values():
                if ("evaluation" in result and 
                    "success_criteria_met" in result["evaluation"] and
                    metric in result["evaluation"]["success_criteria_met"]):
                    value = result["evaluation"]["success_criteria_met"][metric]["actual"]
                    if value is not None:
                        metric_values.append(value)
            
            if metric_values:
                comparison["metric_comparison"][metric] = {
                    "mean": sum(metric_values) / len(metric_values),
                    "min": min(metric_values),
                    "max": max(metric_values),
                    "count": len(metric_values)
                }
        
        # Generate insights
        if comparison["success_rate"] > 0.8:
            comparison["insights"].append("Coordination system demonstrates robust performance across scenarios")
        elif comparison["success_rate"] > 0.6:
            comparison["insights"].append("Good coordination performance with some scenario-specific challenges")
        else:
            comparison["insights"].append("Coordination system needs improvement for reliable performance")
        
        return comparison
    
    def generate_scenario_report(self) -> str:
        """Generate a comprehensive report of all scenario results"""
        if not self.results:
            return "No scenario results available for reporting."
        
        report_lines = [
            "# Coordination Scenario Analysis Report",
            f"**Total Scenarios Run:** {len(self.results)}",
            f"**Overall Success Rate:** {sum(1 for r in self.results.values() if r.get('success', False)) / len(self.results):.1%}",
            "",
            "## Individual Scenario Results",
            ""
        ]
        
        for name, result in self.results.items():
            if result.get("success", False):
                status = "✅ SUCCESS"
                evaluation = result.get("evaluation", {})
                criteria_met = sum(1 for c in evaluation.get("success_criteria_met", {}).values() if c.get("met", False))
                total_criteria = len(evaluation.get("success_criteria_met", {}))
                details = f"({criteria_met}/{total_criteria} criteria met)"
            else:
                status = "❌ FAILED"
                details = result.get("error", "Unknown error")
            
            report_lines.extend([
                f"### {name}",
                f"**Status:** {status} {details}",
                ""
            ])
            
            if "scenario_config" in result:
                config = result["scenario_config"]
                report_lines.extend([
                    f"**Description:** {config.description}",
                    f"**Difficulty:** {config.difficulty_level}",
                    f"**Processors:** {len(config.processors)}",
                    ""
                ])
        
        comparison = self.compare_scenarios()
        if "insights" in comparison:
            report_lines.extend([
                "## Key Insights",
                ""
            ])
            for insight in comparison["insights"]:
                report_lines.append(f"- {insight}")
        
        return "\n".join(report_lines)

# Pre-configured scenario instances for easy use
STANDARD_SCENARIOS = {
    "standard": StandardThreeProcessorScenario(),
    "high_contention": HighContentionScenario(), 
    "trust_crisis": TrustCrisisScenario(),
    "asymmetric": AsymmetricProcessorScenario(),
    "scalability_4": ScalabilityTestScenario(4),
    "scalability_6": ScalabilityTestScenario(6)
}