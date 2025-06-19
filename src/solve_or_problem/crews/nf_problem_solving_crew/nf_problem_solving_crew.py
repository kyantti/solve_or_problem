from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
from solve_or_problem.tools.nf_problem_solver_tool import NfProblemSolverTool
from solve_or_problem.schema import NetworkFlowSolution

load_dotenv()

@CrewBase
class NfProblemSolvingCrew():
    """Network Flow Problem Solving Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    @agent
    def solver(self) -> Agent:
        return Agent(
            config=self.agents_config['solver'], # type: ignore[index]
            tools=[NfProblemSolverTool()],
            verbose=True
        )
    
    @task
    def solve_nf_problem(self) -> Task:
        return Task(
            config=self.tasks_config['solve_nf_problem'], # type: ignore[index]
            output_pydantic=NetworkFlowSolution, # type: ignore[index]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Network Flow Problem Solving Crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
