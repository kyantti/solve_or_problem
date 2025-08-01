"""Test module initialization and basic imports."""

def test_import_main():
    """Test that the main module can be imported."""
    from solve_or_problem.main import OrProblemFlow, kickoff, plot
    assert OrProblemFlow is not None
    assert kickoff is not None
    assert plot is not None


def test_import_schema():
    """Test that schema module can be imported."""
    from solve_or_problem.schema import (
        ProblemClassificationResult,
        LinearProgrammingComponents,
        NetworkFlowProblem,
    )
    assert ProblemClassificationResult is not None
    assert LinearProgrammingComponents is not None
    assert NetworkFlowProblem is not None


def test_import_crews():
    """Test that crew modules can be imported."""
    from solve_or_problem.crews.outline_problem_crew.outline_crew import OutlineCrew
    from solve_or_problem.crews.lp_problem_modeling_crew.lp_problem_modeling_crew import LpProblemModelingCrew
    
    assert OutlineCrew is not None
    assert LpProblemModelingCrew is not None


def test_import_tools():
    """Test that tool modules can be imported."""
    from solve_or_problem.tools.lp_problem_solver_tool import LpProblemSolverTool
    from solve_or_problem.tools.nf_problem_solver_tool import NfProblemSolverTool
    
    assert LpProblemSolverTool is not None
    assert NfProblemSolverTool is not None
