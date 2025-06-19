from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from solve_or_problem.schema import DecisionVariables, ObjectiveFunction, Constraints, LinearProgrammingComponents
from dotenv import load_dotenv


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


load_dotenv()

@CrewBase
class LpProblemModelingCrew:
    """Lp Problem Modeling Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # If you would lik to add tools to your crew, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def lp_data_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["lp_data_extractor"],  # type: ignore[index]
            verbose = True,
        )
    
    @agent
    def lp_problem_model_assembler(self) -> Agent:
        return Agent(
            config=self.agents_config["lp_problem_model_assembler"], #type: ignore
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task

    @task
    def analyze_problem(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_problem"], # type: ignore[index]
        )
    
    @task
    def extract_variables(self) -> Task:
        return Task(
            config=self.tasks_config["extract_variables"], #type: ignore[index]
            output_pydantic=DecisionVariables,
            context=[self.analyze_problem()],  # type: ignore[index]
        )
    
    @task
    def extract_objective_function(self) -> Task:
        return Task(
            config=self.tasks_config["extract_objective_function"], # type: ignore[index]
            output_pydantic=ObjectiveFunction,
            context=[self.analyze_problem()],  # type: ignore[index]
        )
    
    @task
    def extract_constraints(self) -> Task:
        return Task(
            config=self.tasks_config["extract_constraints"], # type: ignore[index]
            output_pydantic=Constraints,
            context=[self.analyze_problem()],  # type: ignore[index]
        )
    
    @task
    def assemble_lp_problem(self) -> Task:
        return Task(
            config=self.tasks_config["assemble_lp_problem"], # type: ignore[index]
            output_pydantic=LinearProgrammingComponents ,
            context=[self.extract_variables(), self.extract_objective_function(), self.extract_constraints()],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
