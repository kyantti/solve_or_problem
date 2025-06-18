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
class Node(BaseModel):
    """Model for a node in a network flow graph."""
    id: int
    supply: Optional[int] = Field(None, description="Supply/demand value (positive: supply, negative: demand)")


class Arc(BaseModel):
    """Model for an arc between two nodes."""
    source: int
    target: int
    capacity: int
    cost: Optional[int] = Field(None, description="Applicable only for Min Cost Flow")


class MaxFlowComponents(BaseModel):
    """Structured model for Max Flow problems."""
    problem_type: Literal["max_flow"] = Field(default="max_flow")
    source: int
    sink: int
    nodes: List[Node]
    arcs: List[Arc]


class MinCostFlowComponents(BaseModel):
    """Structured model for Min Cost Flow problems."""
    problem_type: Literal["min_cost_flow"] = Field(default="min_cost_flow")
    nodes: List[Node]
    arcs: List[Arc]

class SolutionResult(BaseModel):
    """Model for the solution result."""
    solution_found: bool = Field(..., description="Whether a solution was found")
    solution_summary: str = Field(..., description="Human-readable summary of the solution including optimal values and interpretation")

class ProblemModel(BaseModel):
    components: Optional[
        Union[LinearProgrammingComponents, MaxFlowComponents, MinCostFlowComponents]
    ] = None
