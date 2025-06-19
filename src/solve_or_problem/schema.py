from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Union
from enum import Enum

class ProblemClassificationResult(BaseModel):
    """Model for operations research problem classification."""
    is_operations_research: bool = Field(..., description="Whether the problem belongs to the operations research field.")
    category: str = Field(..., description="Main category of the problem. One of: 'Network Flow', 'Linear Programming', 'Integer Programming'.")
    subcategory: Optional[str] = Field(None, description="For 'Network Flow': 'Max Flow' or 'Min Cost Flow'. For other categories: None.")
    explanation: str = Field(..., description="Brief explanation justifying the classification.")

class LinearExpressionTerm(BaseModel):
    """Represents a single term in a linear expression (e.g., 3*x)."""
    variable: str = Field(..., description="Variable name (e.g., 'x')")
    coefficient: float = Field(..., description="Coefficient of the variable")


class DecisionVariables(BaseModel):
    """Model for decision variables in the mathematical problem."""
    variables: List[str] = Field(..., description="List of variable names (e.g., ['x', 'y'])")
    types: Optional[Dict[str, Literal["NUM", "INT", "BIN"]]] = Field(
        default_factory=dict,
        description="Variable type: 'NUM' for continuous, 'INT' for integer, 'BIN' for binary (as used in OR-Tools)"
    )

class Constraint(BaseModel):
    """Represents a single linear constraint (e.g., 3*x + 2*y <= 10)."""
    lhs: List[LinearExpressionTerm] = Field(..., description="Left-hand side linear expression")
    operator: Literal["<=", ">=", "="] = Field(..., description="Constraint operator")
    rhs: float = Field(..., description="Right-hand side constant value")


class Constraints(BaseModel):
    """Model for all constraints."""
    equations: List[Constraint] = Field(..., description="List of structured constraints")


class ObjectiveFunction(BaseModel):
    """Model for the objective function."""
    type: Literal["maximize", "minimize"] = Field(..., description="Optimization direction")
    terms: List[LinearExpressionTerm] = Field(..., description="Terms in the objective function")

class LpProblemSolution(BaseModel):
    """Model for the solution of a linear programming problem."""
    optimal_variable_values: Dict[str, float] = Field(..., description="Optimal values for each variable (e.g., {'x': 6.0, 'y': 4.0})")
    optimal_objective_value: float = Field(..., description="Optimal value of the objective function")

class LinearProgrammingComponents(BaseModel):
    """Complete model for LP/IP problems with structured expressions."""
    decision_variables: DecisionVariables
    constraints: Constraints
    objective_function: ObjectiveFunction
    solution: Optional[LpProblemSolution] = Field(
        default=None,
        description="Not populated until the problem is solved"
    )

# Models for Network Flow Problems

class ProblemType(str, Enum):
    """Enumeration for network flow problem types."""
    MAX_FLOW = "maxflow"
    MIN_COST_FLOW = "mincostflow"

class Node(BaseModel):
    """
    Model for a node in a network flow graph.
    
    For max flow problems:
        - Only source and sink nodes are special (identified by problem-level attributes)
        - supply should be None for intermediate nodes
    
    For min cost flow problems:
        - supply > 0: supply node (produces material)
        - supply < 0: demand node (consumes material) 
        - supply = 0: intermediate node (transshipment)
    """
    id: int = Field(..., description="Unique identifier for the node")
    supply: Optional[int] = Field(
        None, 
        description="Supply/demand value. Positive: supply, Negative: demand, Zero/None: intermediate node"
    )
    label: Optional[str] = Field(None, description="Optional human-readable label for the node")

class NodeList(BaseModel):
    """Model for a list of nodes in a network flow graph."""
    nodes: List[Node] = Field(..., description="List of nodes in the network")

class Arc(BaseModel):
    """
    Model for an arc between two nodes in a network flow graph.
    
    Represents a directed arc from source to target with capacity and optional cost.
    """
    source: int = Field(..., description="Source node ID")
    target: int = Field(..., description="Target node ID")
    capacity: int = Field(..., description="Maximum flow capacity of the arc")
    unit_cost: Optional[int] = Field(
        None,
        description="Unit cost for transporting one unit of flow across this arc (required for min-cost flow)"
    )
    label: Optional[str] = Field(None, description="Optional human-readable label for the arc")

class ArcList(BaseModel):
    """Model for a list of arcs in a network flow graph."""
    arcs: List[Arc] = Field(..., description="List of arcs in the network")

class NetworkFlowProblem(BaseModel):
    """
    Comprehensive model for network flow problems supporting both max-flow and min-cost flow formulations.
    
    This model can represent:
    1. Maximum Flow Problems: Find the maximum flow from source to sink
    2. Minimum Cost Flow Problems: Find the minimum cost flow satisfying supply/demand constraints
    """
    problem_type: ProblemType = Field(..., description="Type of network flow problem")
    nodes: NodeList = Field(..., description="List of nodes in the network")
    arcs: ArcList = Field(..., description="List of directed arcs in the network")
    
    # Max flow specific attributes
    source_node: Optional[int] = Field(
        None,
        description="Source node ID for max flow problems (where flow originates)"
    )
    sink_node: Optional[int] = Field(
        None,
        description="Sink node ID for max flow problems (where flow terminates)"
    )
    
    # Add solution field to store results directly
    solution: Optional["NetworkFlowSolution"] = Field(
        None,
        description="Solution to the network flow problem"
    )

class ArcFlow(BaseModel):
    """Represents the flow on a single arc in the solution."""
    source: int = Field(..., description="Source node ID")
    target: int = Field(..., description="Target node ID")
    flow: int = Field(..., description="Amount of flow on this arc")
    capacity: int = Field(..., description="Maximum capacity of the arc")
    unit_cost: Optional[int] = Field(None, description="Unit cost for min-cost flow problems")
    arc_label: Optional[str] = Field(None, description="Optional label for the arc")

class MaxFlowSolution(BaseModel):
    """Solution details specific to maximum flow problems."""
    max_flow_value: int = Field(..., description="Maximum flow value from source to sink")
    arc_flows: List[ArcFlow] = Field(..., description="Flow values for each arc in the network")
    source_side_mincut: List[int] = Field(..., description="Nodes on the source side of the minimum cut")
    sink_side_mincut: List[int] = Field(..., description="Nodes on the sink side of the minimum cut")

class MinCostFlowSolution(BaseModel):
    """Solution details specific to minimum cost flow problems."""
    min_cost_value: int = Field(..., description="Total minimum cost of the flow")
    arc_flows: List[ArcFlow] = Field(..., description="Flow values for each arc in the network")
    total_flow_satisfied: int = Field(..., description="Total amount of flow that was moved through the network")

class NetworkFlowSolution(BaseModel):
    """Unified model for solutions to network flow problems."""
    problem_type: ProblemType = Field(..., description="Type of network flow problem that was solved")
    max_flow_solution: Optional[MaxFlowSolution] = Field(None, description="Solution details for max flow problems")
    min_cost_flow_solution: Optional[MinCostFlowSolution] = Field(None, description="Solution details for min cost flow problems")
    solution_summary: str = Field(..., description="Human-readable summary of the solution")

class SolutionResult(BaseModel):
    """Model for the solution result."""
    solution_found: bool = Field(..., description="Whether a solution was found")
    solution_summary: str = Field(..., description="Human-readable summary of the solution including optimal values and interpretation")
    flow_solution: Optional[NetworkFlowSolution] = Field(None, description="Detailed solution for network flow problems")
    lp_solution: Optional[LpProblemSolution] = Field(None, description="Solution for linear/integer programming problems")

class ProblemModel(BaseModel):
    components: Optional[
        Union[LinearProgrammingComponents, NetworkFlowProblem]
    ] = None
    solution: Optional[SolutionResult] = None
