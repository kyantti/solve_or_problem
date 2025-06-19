from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional, Dict, Any
from crewai_tools import VisionTool
from solve_or_problem.schema import NetworkFlowProblem, NodeList, ArcList, ProblemType
from dotenv import load_dotenv

load_dotenv()

def is_graph_missing(inputs: Dict[str, Any]) -> bool:
    """Check if the graph image is missing in the inputs."""
    return inputs.get("graph_image") is None

@CrewBase
class NfProblemModelingCrew:
    """Network Flow Problem Modeling Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def nf_data_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["nf_data_extractor"],  # type: ignore[index]
            tools=[VisionTool()],
            verbose = True,
        )
    
    @agent
    def nf_problem_model_assembler(self) -> Agent:
        return Agent(
            config=self.agents_config["nf_problem_model_assembler"], #type: ignore
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task

    @task
    def analyze_network_problem(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_network_problem"], # type: ignore[index]
            #context=[self.interpret_graph_image()],  # Will only be included if condition is met
        )
    
    @task
    def identify_problem_type(self) -> Task:
        return Task(
            config=self.tasks_config["identify_problem_type"], # type: ignore[index]
            context=[self.analyze_network_problem()],  # type: ignore[index]
        )
    
    @task
    def extract_nodes(self) -> Task:
        return Task(
            config=self.tasks_config["extract_nodes"], # type: ignore[index]
            output_pydantic=NodeList,
            context=[self.analyze_network_problem(), self.identify_problem_type()],  # type: ignore[index]
        )
    
    @task
    def extract_arcs(self) -> Task:
        return Task(
            config=self.tasks_config["extract_arcs"], # type: ignore[index]
            output_pydantic=ArcList,
            context=[self.analyze_network_problem(), self.extract_nodes()],  # type: ignore[index]
        )
    
    @task
    def assemble_network_model(self) -> Task:
        return Task(
            config=self.tasks_config["assemble_network_model"], # type: ignore[index]
            output_pydantic=NetworkFlowProblem,
            context=[
                self.identify_problem_type(), 
                self.extract_nodes(), 
                self.extract_arcs()
            ],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Network Flow Problem Modeling Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
