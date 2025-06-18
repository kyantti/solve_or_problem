#!/usr/bin/env python
from random import randint

from enum import Enum

from pydantic import BaseModel, Field

from crewai.flow import Flow, listen, start, router
from crewai.agent import Agent, Task
from solve_or_problem.schema import ProblemClassificationResult, SolutionResult, LinearProgrammingComponents,  ProblemModel, LpProblemSolution
from solve_or_problem.crews.outline_problem_crew.outline_crew import OutlineCrew
from solve_or_problem.crews.lp_problem_modeling_crew.lp_problem_modeling_crew import LpProblemModelingCrew
from solve_or_problem.crews.lp_problem_solving_crew.lp_problem_solving_crew import LpProblemSolvingCrew
class OrProblemState(BaseModel):
    """State for the OR Problem Crew"""

    problem_statement: str = (
        """
        A tailor has 230 meters of a certain fabric and has orders for up to 20 suits, up to 30 jackets, and up to 40 pairs of trousers to be made from this fabric.
        Each suit requires 6 meters of fabric, each jacket 3 meters, and each pair of trousers 2 meters.
        If the tailor's profit is 20 euros per suit, 14 euros per jacket, and 12 euros per pair of trousers, how many of each should he make to obtain the maximum profit with the fabric available?
        """
    )
    problem_outline: ProblemClassificationResult = ProblemClassificationResult(
        is_operations_research=False,
        category="",
        subcategory="",
        explanation=""
    )

    problem_model: ProblemModel = ProblemModel() 

    problem_result: SolutionResult = SolutionResult(
        solution_found=False,
        solution_summary=""
    )


class OrProblemFlow(Flow[OrProblemState]):
    """Crew for solving operations research problems."""
    
    @start()
    def generate_problem_outline(self):
        print("Kickoff the Problem Outline Crew...")

        output = (
            OutlineCrew()
            .crew()
            .kickoff(inputs={"problem_statement": self.state.problem_statement})
        )

        is_operations_research = output["is_operations_research"]
        category = output["category"]
        subcategory = output["subcategory"]
        explanation = output["explanation"]

        self.state.problem_outline = ProblemClassificationResult(
            is_operations_research=is_operations_research,
            category=category,
            subcategory=subcategory,
            explanation=explanation
        )

        print(f"Problem Outline: {self.state.problem_outline}")

    @router(generate_problem_outline)
    def choose_data_extractor(self):
        """Route to choose the data extractor based on the problem outline."""

        # Create a Pydantic model specifically for the response format
        class AbbreviationTypes(str, Enum):
            """Enum for different types of operations research problems."""
            LP = "LP"
            NF = "NF"
            NONE = "None"
        
        class ExtractorSelection(BaseModel):
            """Model for selecting the appropriate data extractor."""
            abbreviation: AbbreviationTypes = Field(..., description="Selected abbreviation for the problem type")
    
        selector = Agent(
            role="Data Extractor Selector",
            goal=(
                "Select the appropriate data extractor based on the problem outline {self.state.problem_outline}."
            ),
            backstory=(
                "You are an expert in operations research problem classification and data extraction. "
                "You can understand the different types of operations research problems and select the appropriate data extractor based on the problem outline."
            ),
            verbose=True,
        )

        query = (
            f"Select the appropriate data extractor abbreviation based on the problem outline: {self.state.problem_outline} from a set of predefined abbreviations."
            "If the problem is a Linear Programming problem or any subcategory of it, as Integer Programming, return 'LP'."
            "If it's a Network Flow problem, return 'NF'."
            "Return 'None' if the problem is not an operations research problem."
            "Return only the abbreviation that best matches."
        )

        result = selector.kickoff(query, response_format=ExtractorSelection)
        #if result.pydantic:
        #    print("result pydantic", result.pydantic)
        #    return result.pydantic.model_dump()["abbreviation"]
        #else:
        #    print("result", result)
        #    return "None"

        if result.pydantic is not None and result.pydantic.model_dump()["abbreviation"] == AbbreviationTypes.LP:
            return "LP"
        elif result.pydantic is not None and result.pydantic.model_dump()["abbreviation"] == AbbreviationTypes.NF:
            return "NF"

    @listen("LP")
    def lp_problem_modeling(self):
        """Handle the case where the problem is a Linear Programming problem."""
        print("Linear Programming Data Extractor selected.")

        output = (
            LpProblemModelingCrew()
            .crew()
            .kickoff(inputs={"problem_statement": self.state.problem_statement})
        )

        decision_variables = output["decision_variables"]
        constraints = output["constraints"]
        objective_function = output["objective_function"]

        lp_model = LinearProgrammingComponents(
            decision_variables=decision_variables,
            constraints=constraints,
            objective_function=objective_function
        )

        self.state.problem_model = ProblemModel(
            components=lp_model 
        )
        print(f"Linear Programming Model: {self.state.problem_model}")

    @listen(lp_problem_modeling)
    def lp_problem_solver(self):
        """Handle the case where the problem is a Linear Programming problem."""
        print("Linear Programming Problem Solver selected.")

        result = (
            LpProblemSolvingCrew()
            .crew()
            .kickoff(inputs={"problem_model": self.state.problem_model.model_dump_json()})
        )
        
        optimal_variable_values = result["optimal_variable_values"]
        optimal_objective_value = result["optimal_objective_value"]

        if isinstance(self.state.problem_model.components, LinearProgrammingComponents):
            self.state.problem_model.components.solution = LpProblemSolution(
                optimal_variable_values=optimal_variable_values,
                optimal_objective_value=optimal_objective_value
            )
        
        print(f"Linear Programming Solution: {self.state.problem_model}")
        

    @listen("NF")
    def network_flow_problem_modeling(self):
        """Handle the case where the problem is a Network Flow problem."""
        print("Network Flow Data Extractor selected.")



def kickoff():
    or_problem_flow = OrProblemFlow()
    or_problem_flow.kickoff()


def plot():
    or_problem_flow = OrProblemFlow()
    or_problem_flow.plot()

if __name__ == "__main__":
    kickoff()