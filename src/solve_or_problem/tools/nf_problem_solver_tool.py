from typing import Type, Dict, Any, Union, List
from crewai.tools import BaseTool
from pydantic import BaseModel
from ortools.graph.python import max_flow, min_cost_flow
import json
from solve_or_problem.schema import (
    NetworkFlowProblem, 
    NetworkFlowSolution, 
    ProblemType, 
    MaxFlowSolution, 
    MinCostFlowSolution, 
    ArcFlow
)

class NfProblemSolverTool(BaseTool):
    name: str = "Network Flow Solver Tool"
    description: str = (
        "This tool solves network flow problems by taking a network flow problem specification "
        "(nodes, arcs, and problem type) and returning a Solution object with the optimal flow "
        "using Google OR-Tools."
    )
    args_schema: Type[BaseModel] = NetworkFlowProblem
    
    def _run(self, **kwargs) -> Union[NetworkFlowSolution, str]:
        try:
            print("[DEBUG] Starting Network Flow problem solver")
            print(f"[DEBUG] Input kwargs: {kwargs}")
            
            # Extract components from kwargs
            problem = NetworkFlowProblem(**kwargs)
            print(f"[DEBUG] Parsed problem: {problem}")
            
            # Solve the appropriate problem type
            if problem.problem_type == ProblemType.MAX_FLOW:
                print("[DEBUG] Solving Maximum Flow Problem")
                return self._solve_max_flow(problem)
            elif problem.problem_type == ProblemType.MIN_COST_FLOW:
                print("[DEBUG] Solving Minimum Cost Flow Problem")
                return self._solve_min_cost_flow(problem)
            else:
                error_msg = f"Unsupported problem type: {problem.problem_type}"
                print(f"[DEBUG] ERROR: {error_msg}")
                return error_msg
            
        except Exception as e:
            print(f"[DEBUG] ERROR: Exception occurred: {str(e)}")
            return f"Error solving Network Flow problem: {str(e)}"
    
    def _solve_max_flow(self, problem: NetworkFlowProblem) -> Union[NetworkFlowSolution, str]:
        """Solve a maximum flow problem using OR-Tools."""
        try:
            # Validate input
            if problem.source_node is None or problem.sink_node is None:
                return "Error: Source and sink nodes must be specified for max flow problems."
            
            print(f"[DEBUG] Setting up max flow solver with source={problem.source_node}, sink={problem.sink_node}")
            
            # Create a max flow solver
            smf = max_flow.SimpleMaxFlow()
            
            # Add arcs to the network
            for arc in problem.arcs.arcs:
                smf.add_arc_with_capacity(arc.source, arc.target, arc.capacity)
                print(f"[DEBUG] Added arc {arc.source}->{arc.target} with capacity {arc.capacity}")
            
            # Solve the max flow problem
            print("[DEBUG] Solving max flow problem")
            status = smf.solve(problem.source_node, problem.sink_node)
            print(f"[DEBUG] Solver status: {status}")
            
            # Process the results based on status
            if status == max_flow.SimpleMaxFlow.OPTIMAL:
                print("[DEBUG] Optimal solution found")
                max_flow_value = smf.optimal_flow()
                print(f"[DEBUG] Maximum flow: {max_flow_value}")
                
                # Extract arc flows
                arc_flows = []
                for i, arc in enumerate(problem.arcs.arcs):
                    flow = smf.flow(i)
                    print(f"[DEBUG] Flow on arc {arc.source}->{arc.target}: {flow}/{arc.capacity}")
                    arc_flows.append(ArcFlow(
                        source=arc.source,
                        target=arc.target,
                        flow=flow,
                        capacity=arc.capacity,
                        unit_cost=None,
                        arc_label=arc.label
                    ))
                
                # Extract min cut information
                # Get source side of min cut using OR-Tools API
                source_side = list(smf.get_source_side_min_cut())
                all_node_ids = [node.id for node in problem.nodes.nodes]
                sink_side = [node_id for node_id in all_node_ids if node_id not in source_side]
                
                print(f"[DEBUG] Source side of min cut: {source_side}")
                print(f"[DEBUG] Sink side of min cut: {sink_side}")
                
                # Create solution object
                max_flow_solution = MaxFlowSolution(
                    max_flow_value=max_flow_value,
                    arc_flows=arc_flows,
                    source_side_mincut=source_side,
                    sink_side_mincut=sink_side
                )
                
                # Create summary
                summary = (
                    f"Maximum flow from node {problem.source_node} to node {problem.sink_node}: {max_flow_value}.\n"
                    f"Min-cut: nodes {source_side} on source side, nodes {sink_side} on sink side.\n"
                    "Arc flows (source -> target: flow/capacity):\n"
                )
                for af in arc_flows:
                    label = f" ({af.arc_label})" if af.arc_label else ""
                    summary += f"  • {af.source} -> {af.target}{label}: {af.flow}/{af.capacity}\n"
                
                return NetworkFlowSolution(
                    problem_type=ProblemType.MAX_FLOW,
                    max_flow_solution=max_flow_solution,
                    min_cost_flow_solution=None,
                    solution_summary=summary
                )
                
            elif status == max_flow.SimpleMaxFlow.POSSIBLE_OVERFLOW:
                return "Error: There was a possible overflow in the algorithm. The capacities or flow values are too large."
                
            elif status == max_flow.SimpleMaxFlow.BAD_INPUT:
                return "Error: Bad input to the max flow algorithm. Check the network structure and capacities."
                
            elif status == max_flow.SimpleMaxFlow.BAD_RESULT:
                return "Error: Bad result from the max flow algorithm. This could indicate a bug in the solver."
                
            else:
                return f"Error: Unknown status from the max flow algorithm: {status}"
                
        except Exception as e:
            print(f"[DEBUG] ERROR in _solve_max_flow: {str(e)}")
            return f"Error solving max flow problem: {str(e)}"
    
    def _solve_min_cost_flow(self, problem: NetworkFlowProblem) -> Union[NetworkFlowSolution, str]:
        """Solve a minimum cost flow problem using OR-Tools."""
        try:
            # Create a min cost flow solver
            print("[DEBUG] Setting up min cost flow solver")
            mcf = min_cost_flow.SimpleMinCostFlow()
            
            # Add nodes with supplies/demands
            for node in problem.nodes.nodes:
                if node.supply is not None:
                    mcf.set_node_supply(node.id, node.supply)
                    status = "supply" if node.supply > 0 else "demand" if node.supply < 0 else "transshipment"
                    print(f"[DEBUG] Added node {node.id} with {status} {node.supply}")
            
            # Add arcs with capacities and unit costs
            for arc in problem.arcs.arcs:
                if arc.unit_cost is None:
                    return f"Error: Unit cost is required for all arcs in min cost flow problems. Missing for arc {arc.source}->{arc.target}."
                
                # Add the arc with its capacity and unit cost
                mcf.add_arc_with_capacity_and_unit_cost(
                    arc.source, 
                    arc.target, 
                    arc.capacity, 
                    arc.unit_cost
                )
                print(f"[DEBUG] Added arc {arc.source}->{arc.target} with capacity {arc.capacity} and unit cost {arc.unit_cost}")
            
            # Solve the min cost flow problem
            print("[DEBUG] Solving min cost flow problem")
            status = mcf.solve()
            print(f"[DEBUG] Solver status: {status}")
            
            # Process the results based on status
            if status == min_cost_flow.SimpleMinCostFlow.OPTIMAL:
                print("[DEBUG] Optimal solution found")
                optimal_cost = mcf.optimal_cost()
                print(f"[DEBUG] Minimum cost: {optimal_cost}")
                
                # Extract arc flows
                arc_flows = []
                total_flow = 0
                
                for i in range(mcf.num_arcs()):
                    tail = mcf.tail(i)
                    head = mcf.head(i)
                    flow = mcf.flow(i)
                    capacity = mcf.capacity(i)
                    unit_cost = mcf.unit_cost(i)
                    
                    # Find corresponding arc in original problem to get label
                    arc_label = None
                    for arc in problem.arcs.arcs:
                        if arc.source == tail and arc.target == head:
                            arc_label = arc.label
                            break
                            
                    print(f"[DEBUG] Flow on arc {tail}->{head}: {flow}/{capacity} (cost: {unit_cost})")
                    arc_flows.append(ArcFlow(
                        source=tail,
                        target=head,
                        flow=flow,
                        capacity=capacity,
                        unit_cost=unit_cost,
                        arc_label=arc_label
                    ))
                    
                    if flow > 0:
                        total_flow += flow
                
                # The total flow is half the sum of all flows (since we count both incoming and outgoing flows)
                total_flow = total_flow // 2
                
                # Create solution object
                min_cost_solution = MinCostFlowSolution(
                    min_cost_value=optimal_cost,
                    arc_flows=arc_flows,
                    total_flow_satisfied=total_flow
                )
                
                # Create summary
                summary = (
                    f"Minimum cost flow solution with total cost: {optimal_cost}.\n"
                    f"Total flow satisfied: {total_flow} units.\n"
                    "Arc flows (source -> target: flow/capacity at unit cost):\n"
                )
                for af in arc_flows:
                    if af.flow > 0:  # Only show arcs with positive flow
                        label = f" ({af.arc_label})" if af.arc_label else ""
                        summary += f"  • {af.source} -> {af.target}{label}: {af.flow}/{af.capacity} at cost {af.unit_cost}\n"
                
                return NetworkFlowSolution(
                    problem_type=ProblemType.MIN_COST_FLOW,
                    max_flow_solution=None,
                    min_cost_flow_solution=min_cost_solution,
                    solution_summary=summary
                )
                
            elif status == min_cost_flow.SimpleMinCostFlow.FEASIBLE:
                return "A feasible solution was found, but it may not be optimal."
                
            elif status == min_cost_flow.SimpleMinCostFlow.INFEASIBLE:
                return "The problem is infeasible. There is no flow that satisfies all the supplies and demands."
                
            elif status == min_cost_flow.SimpleMinCostFlow.UNBALANCED:
                return "The problem is unbalanced. Total supply does not equal total demand."
                
            elif status == min_cost_flow.SimpleMinCostFlow.BAD_RESULT:
                return "The solver encountered a bad result, which could indicate a bug."
                
            elif status == min_cost_flow.SimpleMinCostFlow.BAD_COST_RANGE:
                return "The costs are too large, causing a numeric overflow."
                
            else:
                return f"Error: Unknown status from the min cost flow algorithm: {status}"
                
        except Exception as e:
            print(f"[DEBUG] ERROR in _solve_min_cost_flow: {str(e)}")
            return f"Error solving min cost flow problem: {str(e)}"
