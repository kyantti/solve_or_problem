from typing import Type, Dict, Any, Union
from crewai.tools import BaseTool
from pydantic import BaseModel
from ortools.linear_solver import pywraplp
import json
from solve_or_problem.schema import LinearProgrammingComponents, LpProblemSolution

class LpProblemSolverTool(BaseTool):
    name: str = "Linear Programming Solver Tool"
    description: str = (
        "This tool solves linear programming problems by taking the components of the problem, "
        "such as decision variables, constraints, and objective function, and returning a Solution "
        "object with the optimal values using Google OR-Tools GLOP solver."
    )
    args_schema: Type[BaseModel] = LinearProgrammingComponents
    
    def _run(self, **kwargs) -> Union[LpProblemSolution, str]:
        try:
            print("[DEBUG] Starting LP problem solver")
            print(f"[DEBUG] Input kwargs: {kwargs}")
            
            # Extract components from kwargs
            components = LinearProgrammingComponents(**kwargs)
            print(f"[DEBUG] Parsed components: {components}")
            
            # Create the GLOP solver (optimized for LP)
            print("[DEBUG] Creating GLOP solver")
            solver = pywraplp.Solver.CreateSolver('GLOP')
            if not solver:
                print("[DEBUG] ERROR: Could not create GLOP solver")
                return "Error: Could not create GLOP solver. Make sure OR-Tools is properly installed."
            print("[DEBUG] GLOP solver created successfully")
            
            # Create decision variables
            print("[DEBUG] Creating decision variables")
            variables = self._create_variables(solver, components.decision_variables)
            print(f"[DEBUG] Created {len(variables)} decision variables")
            
            # Add constraints
            print("[DEBUG] Adding constraints")
            self._add_constraints(solver, variables, components.constraints)
            print(f"[DEBUG] Added {len(components.constraints.equations)} constraints")
            
            # Set objective function
            print("[DEBUG] Setting objective function")
            self._set_objective(solver, variables, components.objective_function)
            print(f"[DEBUG] Objective function set (type: {components.objective_function.type})")
            
            # Solve the problem
            print("[DEBUG] Solving the problem")
            status = solver.Solve()
            print(f"[DEBUG] Solver finished with status: {status}")
            
            # Process and return results
            print("[DEBUG] Processing solution")
            solution = self._format_solution(solver, variables, status, components)
            print(f"[DEBUG] Solution processed: {solution}")
            return solution
            
        except Exception as e:
            print(f"[DEBUG] ERROR: Exception occurred: {str(e)}")
            return f"Error solving LP problem: {str(e)}"
    
    def _create_variables(self, solver, decision_vars) -> Dict[str, Any]:
        """Create decision variables in the solver."""
        print(f"[DEBUG] Creating variables with types: {decision_vars.types}")
        variables = {}
        
        for var_name in decision_vars.variables:
            var_type = decision_vars.types.get(var_name, "NUM")
            print(f"[DEBUG] Creating variable: {var_name} of type {var_type}")
            
            if var_type == "NUM":
                # Continuous variable with bounds from -infinity to +infinity
                variables[var_name] = solver.NumVar(-solver.infinity(), solver.infinity(), var_name)
            elif var_type == "INT":
                # For GLOP, treat integer variables as continuous (GLOP is LP-only)
                print(f"[DEBUG] Warning: GLOP solver treats integer variable {var_name} as continuous")
                variables[var_name] = solver.NumVar(-solver.infinity(), solver.infinity(), var_name)
            elif var_type == "BIN":
                # For GLOP, treat binary variables as continuous [0,1]
                print(f"[DEBUG] Warning: GLOP solver treats binary variable {var_name} as continuous [0,1]")
                variables[var_name] = solver.NumVar(0, 1, var_name)
            else:
                print(f"[DEBUG] ERROR: Unknown variable type: {var_type}")
                raise ValueError(f"Unknown variable type: {var_type}")
            
        return variables
    
    def _add_constraints(self, solver, variables, constraints):
        """Add constraints to the solver."""
        print(f"[DEBUG] Adding {len(constraints.equations)} constraints")
        for i, constraint in enumerate(constraints.equations):
            print(f"[DEBUG] Processing constraint {i}: {constraint}")
            # Create the constraint
            if constraint.operator == "<=":
                ct = solver.Constraint(-solver.infinity(), constraint.rhs, f"constraint_{i}")
                print(f"[DEBUG] Created <= constraint with RHS = {constraint.rhs}")
            elif constraint.operator == ">=":
                ct = solver.Constraint(constraint.rhs, solver.infinity(), f"constraint_{i}")
                print(f"[DEBUG] Created >= constraint with RHS = {constraint.rhs}")
            elif constraint.operator == "=":
                ct = solver.Constraint(constraint.rhs, constraint.rhs, f"constraint_{i}")
                print(f"[DEBUG] Created = constraint with RHS = {constraint.rhs}")
            else:
                print(f"[DEBUG] ERROR: Unknown constraint operator: {constraint.operator}")
                raise ValueError(f"Unknown constraint operator: {constraint.operator}")
            
            # Add terms to the constraint
            for term in constraint.lhs:
                if term.variable not in variables:
                    print(f"[DEBUG] ERROR: Variable {term.variable} not found in decision variables")
                    raise ValueError(f"Variable {term.variable} not found in decision variables")
                ct.SetCoefficient(variables[term.variable], term.coefficient)
                print(f"[DEBUG] Added term: {term.coefficient} * {term.variable}")
    
    def _set_objective(self, solver, variables, objective):
        """Set the objective function."""
        print(f"[DEBUG] Setting {objective.type} objective function")
        objective_expr = solver.Objective()
        
        # Add terms to objective
        for term in objective.terms:
            if term.variable not in variables:
                print(f"[DEBUG] ERROR: Variable {term.variable} not found in decision variables")
                raise ValueError(f"Variable {term.variable} not found in decision variables")
            objective_expr.SetCoefficient(variables[term.variable], term.coefficient)
            print(f"[DEBUG] Added objective term: {term.coefficient} * {term.variable}")
        
        # Set optimization direction
        if objective.type == "maximize":
            objective_expr.SetMaximization()
            print("[DEBUG] Set objective to maximize")
        elif objective.type == "minimize":
            objective_expr.SetMinimization()
            print("[DEBUG] Set objective to minimize")
        else:
            print(f"[DEBUG] ERROR: Unknown objective type: {objective.type}")
            raise ValueError(f"Unknown objective type: {objective.type}")
    
    def _format_solution(self, solver, variables, status, components: LinearProgrammingComponents) -> Union[LpProblemSolution, str]:
        """Format the solver results as a Solution Pydantic model or error message."""
        
        print(f"[DEBUG] Formatting solution, solver status = {status}")
        
        if status == pywraplp.Solver.OPTIMAL:
            print("[DEBUG] Optimal solution found")
            # Extract variable values
            variable_values = {}
            for var_name, var_obj in variables.items():
                variable_values[var_name] = var_obj.solution_value()
                print(f"[DEBUG] Variable {var_name} = {var_obj.solution_value()}")
            
            # Create and return Solution object
            solution = LpProblemSolution(
                optimal_variable_values=variable_values,
                optimal_objective_value=solver.Objective().Value()
            )
            
            print(f"[DEBUG] Optimal objective value = {solver.Objective().Value()}")
            return solution
            
        elif status == pywraplp.Solver.FEASIBLE:
            print("[DEBUG] Feasible but not optimal solution found")
            return "Feasible solution found but may not be optimal. GLOP solver should typically find optimal solutions for LP problems."
            
        elif status == pywraplp.Solver.INFEASIBLE:
            print("[DEBUG] Problem is infeasible")
            return "The problem is infeasible - no solution exists that satisfies all constraints."
            
        elif status == pywraplp.Solver.UNBOUNDED:
            print("[DEBUG] Problem is unbounded")
            return "The problem is unbounded - the objective function can be improved infinitely."
            
        else:
            print(f"[DEBUG] Unexpected solver status: {status}")
            return f"Solver finished with unexpected status: {status}"