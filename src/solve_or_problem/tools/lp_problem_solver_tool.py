from typing import Type, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel
from ortools.linear_solver import pywraplp
import json
from solve_or_problem.schema import LinearProgrammingComponents

class LpProblemSolverTool(BaseTool):
    name: str = "Linear Programming Solver Tool"
    description: str = (
        "This tool solves linear programming problems by taking the components of the problem, "
        "such as decision variables, constraints, and objective function, and returning a solution. "
        "To achieve this, it uses the provided components in conjunction with the Google OR-Tools library."
    )
    args_schema: Type[BaseModel] = LinearProgrammingComponents
    
    def _run(self, **kwargs) -> str:
        try:
            # Extract components from kwargs
            components = LinearProgrammingComponents(**kwargs)
            
            # Create the solver
            solver = pywraplp.Solver.CreateSolver('SCIP')
            if not solver:
                return json.dumps({
                    "status": "error",
                    "message": "Could not create solver. Make sure OR-Tools is properly installed."
                })
            
            # Create decision variables
            variables = self._create_variables(solver, components.decision_variables)
            
            # Add constraints
            self._add_constraints(solver, variables, components.constraints)
            
            # Set objective function
            self._set_objective(solver, variables, components.objective_function)
            
            # Solve the problem
            status = solver.Solve()
            
            # Process and return results
            return self._format_results(solver, variables, status)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error solving LP problem: {str(e)}"
            })
    
    def _create_variables(self, solver, decision_vars) -> Dict[str, Any]:
        """Create decision variables in the solver."""
        variables = {}
        
        for var_name in decision_vars.variables:
            var_type = decision_vars.types.get(var_name, "NUM")
            
            if var_type == "NUM":
                # Continuous variable with bounds from -infinity to +infinity
                variables[var_name] = solver.NumVar(-solver.infinity(), solver.infinity(), var_name)
            elif var_type == "INT":
                # Integer variable with bounds from -infinity to +infinity
                variables[var_name] = solver.IntVar(-solver.infinity(), solver.infinity(), var_name)
            elif var_type == "BIN":
                # Binary variable (0 or 1)
                variables[var_name] = solver.BoolVar(var_name)
            else:
                raise ValueError(f"Unknown variable type: {var_type}")
            
        return variables
    
    def _add_constraints(self, solver, variables, constraints):
        """Add constraints to the solver."""
        for i, constraint in enumerate(constraints.equations):
            # Create the constraint
            if constraint.operator == "<=":
                ct = solver.Constraint(-solver.infinity(), constraint.rhs, f"constraint_{i}")
            elif constraint.operator == ">=":
                ct = solver.Constraint(constraint.rhs, solver.infinity(), f"constraint_{i}")
            elif constraint.operator == "=":
                ct = solver.Constraint(constraint.rhs, constraint.rhs, f"constraint_{i}")
            else:
                raise ValueError(f"Unknown constraint operator: {constraint.operator}")
            
            # Add terms to the constraint
            for term in constraint.lhs:
                if term.variable not in variables:
                    raise ValueError(f"Variable {term.variable} not found in decision variables")
                ct.SetCoefficient(variables[term.variable], term.coefficient)
    
    def _set_objective(self, solver, variables, objective):
        """Set the objective function."""
        objective_expr = solver.Objective()
        
        # Add terms to objective
        for term in objective.terms:
            if term.variable not in variables:
                raise ValueError(f"Variable {term.variable} not found in decision variables")
            objective_expr.SetCoefficient(variables[term.variable], term.coefficient)
        
        # Set optimization direction
        if objective.type == "maximize":
            objective_expr.SetMaximization()
        elif objective.type == "minimize":
            objective_expr.SetMinimization()
        else:
            raise ValueError(f"Unknown objective type: {objective.type}")
    
    def _format_results(self, solver, variables, status) -> str:
        """Format the solver results as a JSON string."""
        # Map OR-Tools status codes to readable strings
        status_map = {
            pywraplp.Solver.OPTIMAL: "optimal",
            pywraplp.Solver.FEASIBLE: "feasible",
            pywraplp.Solver.INFEASIBLE: "infeasible",
            pywraplp.Solver.UNBOUNDED: "unbounded",
            pywraplp.Solver.ABNORMAL: "abnormal",
            pywraplp.Solver.NOT_SOLVED: "not_solved"
        }
        
        result = {
            "status": status_map.get(status, "unknown"),
            "solver_info": {
                "solver_name": solver.SolverVersion(),
                "wall_time_ms": solver.wall_time(),
                "iterations": solver.iterations() if hasattr(solver, 'iterations') else None
            }
        }
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            # Extract variable values
            variable_values = {}
            for var_name, var_obj in variables.items():
                variable_values[var_name] = var_obj.solution_value()
            
            result.update({
                "objective_value": solver.Objective().Value(),
                "variables": variable_values,
                "is_optimal": status == pywraplp.Solver.OPTIMAL
            })
            
            # Add summary message
            if status == pywraplp.Solver.OPTIMAL:
                result["message"] = "Optimal solution found"
            else:
                result["message"] = "Feasible solution found (may not be optimal)"
        
        elif status == pywraplp.Solver.INFEASIBLE:
            result["message"] = "The problem is infeasible - no solution exists"
        
        elif status == pywraplp.Solver.UNBOUNDED:
            result["message"] = "The problem is unbounded - objective can be improved infinitely"
        
        else:
            result["message"] = f"Solver finished with status: {status_map.get(status, 'unknown')}"
        
        return json.dumps(result, indent=2)