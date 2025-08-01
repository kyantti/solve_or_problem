# Operations Research Problem Solver

An intelligent multi-agent system powered by [crewAI](https://crewai.com) that automatically classifies, models, and solves operations research problems using natural language descriptions. The system leverages AI agents to analyze problem statements, determine the appropriate optimization technique, and provide complete solutions.

## Features

🤖 **Intelligent Problem Classification**: Automatically identifies if a problem belongs to operations research and categorizes it
📊 **Multi-Problem Support**: Handles Linear Programming (LP) and Network Flow (NF) problems
🔄 **Automated Workflow**: Complete end-to-end pipeline from problem statement to solution
⚡ **Google OR-Tools Integration**: Uses industry-standard optimization solvers
🎯 **Structured Output**: Provides detailed solutions with optimal values and explanations

## Supported Problem Types

### Linear Programming (LP)
- Resource allocation problems
- Production planning
- Diet problems
- Transportation problems
- Integer Programming variants

### Network Flow (NF)
- Maximum flow problems
- Minimum cost flow problems
- Transportation networks
- Supply chain optimization

## Installation

### Install from Source

Ensure you have Python >=3.10 <3.14 installed on your system.

#### Using pip:
```bash
git clone https://github.com/kyantti/solve_or_problem.git
cd solve_or_problem
pip install -e .
```

#### Using UV (recommended for development):
This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

First, install uv if you haven't already:

```bash
pip install uv
```

Then install the project:
```bash
git clone https://github.com/kyantti/solve_or_problem.git
cd solve_or_problem
uv sync
```

#### Using crewAI CLI:
```bash
crewai install
```

### Development Installation

For development with optional dependencies:

```bash
pip install -e ".[dev]"
```

Or with UV:
```bash
uv sync --group dev
```

### Environment Setup

**Add your `OPENAI_API_KEY` to the `.env` file:**

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Project

### Command Line Interface

After installation, you can use the package from anywhere:

```bash
solve-or-problem
```

Or alternatively:
```bash
or-solver
```

### From Source

To solve an operations research problem, run:

```bash
crewai run
```

Or directly:
```bash
python -m solve_or_problem.main
```

### Programmatic Usage

You can also use the package in your Python code:

```python
from solve_or_problem.main import OrProblemFlow

# Create and run the flow
flow = OrProblemFlow()
flow.kickoff()
```

### Example Problems

The system comes with two example problems:

#### 1. Tailor Production Problem (Linear Programming)
A resource allocation problem where a tailor needs to optimize fabric usage for suits, jackets, and trousers to maximize profit.

#### 2. Network Flow Problem
A maximum flow problem in a transportation network with capacity constraints.

## System Architecture

The system uses a multi-agent flow with the following crews:

### 1. Outline Problem Crew
- **Research Agent**: Gathers information about operations research
- **Problem Classifier**: Determines if the problem is OR-related and categorizes it

### 2. Problem Modeling Crews
- **LP Problem Modeling Crew**: Extracts decision variables, constraints, and objective functions for linear programming problems
- **NF Problem Modeling Crew**: Identifies nodes, arcs, and network structure for flow problems

### 3. Problem Solving Crews
- **LP Problem Solving Crew**: Solves linear programming problems using OR-Tools GLOP solver
- **NF Problem Solving Crew**: Solves network flow problems using OR-Tools network flow algorithms

## Project Structure

```
src/solve_or_problem/
├── main.py                     # Main flow orchestration
├── schema.py                   # Data models and schemas
├── crews/                      # AI agent crews
│   ├── outline_problem_crew/   # Problem classification
│   ├── lp_problem_modeling_crew/  # LP problem modeling
│   ├── nf_problem_modeling_crew/  # Network flow modeling
│   ├── lp_problem_solving_crew/   # LP solving
│   └── nf_problem_solving_crew/   # Network flow solving
└── tools/                      # OR-Tools integration
    ├── lp_problem_solver_tool.py   # Linear programming solver
    └── nf_problem_solver_tool.py   # Network flow solver
```

## Customization

To solve your own problems:

1. **Modify Problem Statement**: Edit the `problem_statement` variable in `src/solve_or_problem/main.py`
2. **Customize Agents**: Update configuration files in `crews/*/config/agents.yaml`
3. **Adjust Tasks**: Modify task definitions in `crews/*/config/tasks.yaml`
4. **Extend Problem Types**: Add new crews for additional OR problem categories

## Dependencies

- **crewAI**: Multi-agent orchestration framework
- **Google OR-Tools**: Optimization solver library
- **Pydantic**: Data validation and settings management
- **Matplotlib/Plotly**: Visualization capabilities

## Flow Visualization

Generate a visual representation of the agent workflow:

```bash
or-plot
```

Or from Python:
```bash
python -c "from solve_or_problem.main import plot; plot()"
```
