#!/usr/bin/env python
from random import randint

from enum import Enum

from pydantic import BaseModel, Field

from crewai.flow import Flow, listen, start, router
from crewai.agent import Agent, Task
from solve_or_problem.schema import ProblemClassificationResult, SolutionResult, LinearProgrammingComponents,  ProblemModel, LpProblemSolution, NetworkFlowProblem, NetworkFlowSolution, ProblemType
from solve_or_problem.crews.outline_problem_crew.outline_crew import OutlineCrew
from solve_or_problem.crews.lp_problem_modeling_crew.lp_problem_modeling_crew import LpProblemModelingCrew
from solve_or_problem.crews.nf_problem_modeling_crew.nf_problem_modeling_crew import NfProblemModelingCrew
from solve_or_problem.crews.lp_problem_solving_crew.lp_problem_solving_crew import LpProblemSolvingCrew
from solve_or_problem.crews.nf_problem_solving_crew.nf_problem_solving_crew import NfProblemSolvingCrew

tailor_problem_statement = (
    """
        A tailor has 230 meters of a certain fabric and has orders for up to 20 suits, up to 30 jackets, and up to 40 pairs of trousers to be made from this fabric.
        Each suit requires 6 meters of fabric, each jacket 3 meters, and each pair of trousers 2 meters.
        If the tailor's profit is 20 euros per suit, 14 euros per jacket, and 12 euros per pair of trousers, how many of each should he make to obtain the maximum profit with the fabric available?
    """
)

mf_problem_statement = (
    """
    The problem is defined by the following graph, which represents a transportation network: https://developers.google.com/static/optimization/images/flow/max_flow.svg
    You want to transport material from node 0 (the source) to node 4 (the sink). The numbers next to the arcs are their capacities — the capacity of an arc is the maximum amount that can be transported across it in a fixed period of time. The capacities are the constraints for the problem.
    A flow is an assignment of a non-negative number to each arc (the flow amount) that satisfies the following flow conservation rule:
    The max flow problem is to find a flow for which the sum of the flow amounts for the entire network is as large as possible.
    The following sections present a programs to find the maximum flow from the source (0) to the sink (4).
    """
)

mf_problem_text = (
    """
    Network Graph:

    Nodes: 0, 1, 2, 3, 4
    Source: Node 0
    Sink: Node 4

    Edges and Capacities:

    Edge (0,1): capacity 20
    Edge (0,2): capacity 30
    Edge (0,3): capacity 10
    Edge (1,2): capacity 40
    Edge (1,4): capacity 30
    Edge (2,3): capacity 10
    Edge (2,4): capacity 20
    Edge (3,4): capacity 20
    Edge (3,2): capacity 5

    Problem Objective:
    Transport material from node 0 (source) to node 4 (sink) while respecting the capacity constraints on each arc.

    Flow Conservation Rule:
    A flow is an assignment of non-negative numbers to each arc (the flow amount) such that for every node except the source and sink, the total flow entering the node equals the total flow leaving the node.

    This is a maximum flow problem where you need to find the maximum amount of material that can be transported from the source to the sink given the capacity constraints.
    """
)

class OrProblemState(BaseModel):
    """State for the OR Problem Crew"""

    problem_statement: str = (
        mf_problem_text  # or mf_problem_statement
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
        solution_summary="",
        flow_solution=None,
        lp_solution=None
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
    def model_lp_problem(self):
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

    @listen("NF")
    def model_nf_problem(self):
        """Handle the case where the problem is a Network Flow problem."""
        print("Network Flow Data Extractor selected.")

        graph_image_path = None
    
        output = (
            NfProblemModelingCrew()
            .crew()
            .kickoff(inputs={"problem_statement": self.state.problem_statement, "graph_image": graph_image_path})  
            #.kickoff(inputs={"problem_statement": self.state.problem_statement})
        )

        problem_type_str = output["problem_type"]
        nodes = output["nodes"]
        arcs = output["arcs"]
        
        # Convert string problem type to enum
        if problem_type_str == "maxflow":
            problem_type = ProblemType.MAX_FLOW
            source_node = output["source_node"]
            sink_node = output["sink_node"]
        else:
            # Handle other problem types if needed
            raise ValueError(f"Unsupported problem type: {problem_type_str}")
        
        self.state.problem_model = ProblemModel(
            components=NetworkFlowProblem(
                problem_type=problem_type,
                nodes=nodes,
                arcs=arcs,
                source_node=source_node if problem_type_str == "maxflow" else None,
                sink_node=sink_node if problem_type_str == "maxflow" else None
            )
        )

        print(f"Network Flow Model: {self.state.problem_model}")

    @listen(model_lp_problem)
    def solve_lp_problem(self):
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


    @listen(model_nf_problem)
    def solve_network_flow_problem(self):
        """Handle the case where the problem is a Network Flow problem."""
        print("Network Flow Problem Solver selected.")
        
        # Call the Network Flow Problem Solving Crew
        result = (
            NfProblemSolvingCrew()
            .crew()
            .kickoff(inputs={"problem_model": self.state.problem_model.model_dump_json()})
        )

        problem_type = result["problem_type"]
        max_flow_solution = result["max_flow_solution"]
        min_cost_flow_solution = result["min_cost_flow_solution"]
        solution_summary = result["solution_summary"]

        if isinstance(self.state.problem_model.components, SolutionResult):
            self.state.problem_model.components.flow_solution = NetworkFlowSolution(
                problem_type=problem_type,
                max_flow_solution=max_flow_solution,
                min_cost_flow_solution=min_cost_flow_solution,
                solution_summary=solution_summary
            )
        else:
            print("Error: The problem model does not contain a valid NetworkFlowProblem component.")
            return

        print(f"Network Flow Model: {self.state.problem_model}")
        

def kickoff():
    or_problem_flow = OrProblemFlow()
    or_problem_flow.kickoff()


def plot():
    or_problem_flow = OrProblemFlow()
    or_problem_flow.plot()

if __name__ == "__main__":
    kickoff()