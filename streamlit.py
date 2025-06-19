import streamlit as st
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from solve_or_problem.main import OrProblemFlow
from solve_or_problem.schema import (
    ProblemType,
    NetworkFlowProblem,
    LinearProgrammingComponents,
    NetworkFlowSolution,
    LpProblemSolution,
    ProblemModel
)

# Configure page
st.set_page_config(
    page_title="Operations Research Problem Solver",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Operations Research Problem Solver")
st.write("""
This application uses AI to classify, model, and solve operations research problems.
Enter a problem description below to get started.
""")

# Example problems for user to choose from
example_problems = {
    "Tailor Production Problem": """
        A tailor has 230 meters of a certain fabric and has orders for up to 20 suits, up to 30 jackets, and up to 40 pairs of trousers to be made from this fabric.
        Each suit requires 6 meters of fabric, each jacket 3 meters, and each pair of trousers 2 meters.
        If the tailor's profit is 20 euros per suit, 14 euros per jacket, and 12 euros per pair of trousers, how many of each should he make to obtain the maximum profit with the fabric available?
    """,
    "Max Flow Network Problem": """
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
}

# Problem input area
with st.expander("Problem Description", expanded=True):
    select_example = st.selectbox(
        "Select an example problem or enter your own:",
        ["Custom Problem"] + list(example_problems.keys())
    )
    
    if select_example == "Custom Problem":
        problem_statement = st.text_area(
            "Enter your problem statement:", 
            height=200,
            placeholder="Describe an operations research problem..."
        )
    else:
        problem_statement = st.text_area(
            "Problem statement:",
            value=example_problems[select_example],
            height=200
        )

# Initialize session state
if 'problem_solved' not in st.session_state:
    st.session_state.problem_solved = False
if 'problem_flow' not in st.session_state:
    st.session_state.problem_flow = None
if 'problem_outline' not in st.session_state:
    st.session_state.problem_outline = None
if 'problem_model' not in st.session_state:
    st.session_state.problem_model = None
if 'problem_result' not in st.session_state:
    st.session_state.problem_result = None

# Main processing
if st.button("Solve Problem", type="primary", disabled=not problem_statement.strip()):
    if problem_statement:
        with st.spinner("Processing your problem..."):
            # Initialize the flow with the problem statement
            flow = OrProblemFlow()
            flow.state.problem_statement = problem_statement
            
            # Run the flow
            flow.kickoff()
            
            # Store results in session state
            st.session_state.problem_flow = flow
            st.session_state.problem_outline = flow.state.problem_outline
            st.session_state.problem_model = flow.state.problem_model
            st.session_state.problem_solved = True
    else:
        st.error("Please enter a problem description.")

# Display results if problem solved
if st.session_state.problem_solved:
    st.success("Problem analysis completed!")
    
    # Create tabs for different sections of the results
    tab1, tab2, tab3 = st.tabs(["Problem Classification", "Problem Model", "Solution"])
    
    # Tab 1: Problem Classification
    with tab1:
        st.header("Problem Classification")
        outline = st.session_state.problem_outline
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Is Operations Research Problem?**")
            if outline.is_operations_research:
                st.success("Yes")
            else:
                st.error("No")
        
        with col2:
            st.write("**Problem Category:**")
            st.info(outline.category)
            if outline.subcategory:
                st.write("**Subcategory:**")
                st.info(outline.subcategory)
        
        st.write("**Explanation:**")
        st.write(outline.explanation)
    
    # Tab 2: Problem Model
    with tab2:
        st.header("Problem Model")
        problem_model = st.session_state.problem_model
        
        if isinstance(problem_model.components, LinearProgrammingComponents):
            st.subheader("Linear Programming Model")
            
            # Display decision variables
            st.write("**Decision Variables:**")
            variables_df = pd.DataFrame({
                "Variable": problem_model.components.decision_variables.variables,
                "Type": [problem_model.components.decision_variables.types.get(var, "NUM") 
                         for var in problem_model.components.decision_variables.variables]
            })
            st.table(variables_df)
            
            # Display objective function
            st.write("**Objective Function:**")
            objective_type = problem_model.components.objective_function.type
            st.write(f"Type: **{objective_type.upper()}**")
            
            obj_terms = []
            for term in problem_model.components.objective_function.terms:
                obj_terms.append(f"{term.coefficient} * {term.variable}")
            
            st.latex(f"{objective_type} \quad Z = {' + '.join(obj_terms)}")
            
            # Display constraints
            st.write("**Constraints:**")
            for i, constraint in enumerate(problem_model.components.constraints.equations):
                lhs_terms = []
                for term in constraint.lhs:
                    lhs_terms.append(f"{term.coefficient} * {term.variable}")
                
                lhs = " + ".join(lhs_terms)
                operator = constraint.operator
                rhs = constraint.rhs
                
                # Convert operator for LaTeX
                if operator == "<=":
                    latex_op = "\\leq"
                elif operator == ">=":
                    latex_op = "\\geq"
                else:
                    latex_op = "="
                
                st.latex(f"{lhs} {latex_op} {rhs}")
            
        elif isinstance(problem_model.components, NetworkFlowProblem):
            st.subheader("Network Flow Model")
            
            # Display problem type
            st.write(f"**Problem Type:** {problem_model.components.problem_type}")
            
            if problem_model.components.problem_type == ProblemType.MAX_FLOW:
                st.write(f"**Source Node:** {problem_model.components.source_node}")
                st.write(f"**Sink Node:** {problem_model.components.sink_node}")
            
            # Display nodes
            st.write("**Nodes:**")
            nodes_data = []
            for node in problem_model.components.nodes.nodes:
                node_info = {
                    "ID": node.id,
                    "Supply/Demand": node.supply if node.supply is not None else "N/A",
                }
                if node.label:
                    node_info["Label"] = node.label
                nodes_data.append(node_info)
            
            nodes_df = pd.DataFrame(nodes_data)
            st.table(nodes_df)
            
            # Display arcs
            st.write("**Arcs:**")
            arcs_data = []
            for arc in problem_model.components.arcs.arcs:
                arc_info = {
                    "Source": arc.source,
                    "Target": arc.target,
                    "Capacity": arc.capacity,
                }
                if arc.unit_cost is not None:
                    arc_info["Unit Cost"] = arc.unit_cost
                if arc.label:
                    arc_info["Label"] = arc.label
                arcs_data.append(arc_info)
            
            arcs_df = pd.DataFrame(arcs_data)
            st.table(arcs_df)
            
            # Create and display network graph visualization
            st.write("**Network Visualization:**")
            
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add nodes
            for node in problem_model.components.nodes.nodes:
                label = node.label if node.label else f"Node {node.id}"
                
                # Add node attributes based on problem type
                if problem_model.components.problem_type == ProblemType.MAX_FLOW:
                    if node.id == problem_model.components.source_node:
                        G.add_node(node.id, label=label, color='green', node_type='source')
                    elif node.id == problem_model.components.sink_node:
                        G.add_node(node.id, label=label, color='red', node_type='sink')
                    else:
                        G.add_node(node.id, label=label, color='skyblue', node_type='transshipment')
                else:  # Min Cost Flow
                    if node.supply and node.supply > 0:
                        G.add_node(node.id, label=label, color='green', node_type='supply')
                    elif node.supply and node.supply < 0:
                        G.add_node(node.id, label=label, color='red', node_type='demand')
                    else:
                        G.add_node(node.id, label=label, color='skyblue', node_type='transshipment')
            
            # Add edges
            for arc in problem_model.components.arcs.arcs:
                edge_label = f"{arc.capacity}"
                if arc.unit_cost is not None:
                    edge_label += f" / ${arc.unit_cost}"
                G.add_edge(arc.source, arc.target, capacity=arc.capacity, 
                         unit_cost=arc.unit_cost, label=edge_label)
            
            # Plot the graph
            plt.figure(figsize=(10, 7))
            pos = nx.spring_layout(G, seed=42)  # Layout with seed for reproducibility
            
            # Draw nodes
            node_colors = [G.nodes[n]['color'] for n in G.nodes()]
            nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, width=2, arrowsize=20)
            
            # Draw labels for nodes and edges
            nx.draw_networkx_labels(G, pos, font_weight='bold')
            edge_labels = {(u, v): G[u][v]['label'] for u, v in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            
            plt.title("Network Flow Graph")
            plt.axis("off")
            
            # Display the graph in Streamlit
            st.pyplot(plt)
        
        else:
            st.write("No problem model available.")
    
    # Tab 3: Solution
    with tab3:
        st.header("Solution")
        problem_model = st.session_state.problem_model
        
        if isinstance(problem_model.components, LinearProgrammingComponents) and problem_model.components.solution:
            st.subheader("Linear Programming Solution")
            
            # Display optimal objective value
            st.write(f"**Optimal Objective Value:** {problem_model.components.solution.optimal_objective_value:.4f}")
            
            # Display variable values
            st.write("**Optimal Variable Values:**")
            vars_df = pd.DataFrame({
                "Variable": list(problem_model.components.solution.optimal_variable_values.keys()),
                "Value": list(problem_model.components.solution.optimal_variable_values.values())
            })
            st.table(vars_df)
            
            # Simple chart for variable values
            st.bar_chart(vars_df.set_index("Variable"))
            
        elif isinstance(problem_model.components, NetworkFlowProblem):
            # Check if solution exists
            if hasattr(problem_model.components, 'solution') and problem_model.components.solution:
                solution = problem_model.components.solution
                
                # Debug information
                st.write(f"Debug - Solution type: {type(solution)}")
                
                if problem_model.components.problem_type == ProblemType.MAX_FLOW and solution.max_flow_solution:
                    st.subheader("Maximum Flow Solution")
                    
                    # Display max flow value
                    st.write(f"**Maximum Flow Value:** {solution.max_flow_solution.max_flow_value}")
                    
                    # Display min cut
                    st.write("**Min Cut:**")
                    st.write(f"Source side: {solution.max_flow_solution.source_side_mincut}")
                    st.write(f"Sink side: {solution.max_flow_solution.sink_side_mincut}")
                    
                    # Display arc flows
                    st.write("**Arc Flows:**")
                    flows_data = []
                    for flow in solution.max_flow_solution.arc_flows:
                        flow_info = {
                            "Source": flow.source,
                            "Target": flow.target,
                            "Flow": flow.flow,
                            "Capacity": flow.capacity,
                            "Utilization": f"{flow.flow/flow.capacity*100:.1f}%" if flow.capacity > 0 else "N/A"
                        }
                        if flow.arc_label:
                            flow_info["Label"] = flow.arc_label
                        flows_data.append(flow_info)
                    
                    flows_df = pd.DataFrame(flows_data)
                    st.table(flows_df)
                    
                    # Create visualization of the flow network with flows
                    st.write("**Flow Visualization:**")
                    
                    # Create a directed graph for the flow solution
                    G = nx.DiGraph()
                    
                    # Add nodes from the problem
                    for node in problem_model.components.nodes.nodes:
                        label = node.label if node.label else f"Node {node.id}"
                        
                        if node.id == problem_model.components.source_node:
                            G.add_node(node.id, label=label, color='green', node_type='source')
                        elif node.id == problem_model.components.sink_node:
                            G.add_node(node.id, label=label, color='red', node_type='sink')
                        else:
                            G.add_node(node.id, label=label, color='skyblue', node_type='transshipment')
                    
                    # Add edges with flow information
                    for flow in solution.max_flow_solution.arc_flows:
                        edge_label = f"{flow.flow}/{flow.capacity}"
                        # Color edges based on flow usage
                        if flow.capacity > 0:
                            saturation = flow.flow / flow.capacity
                            if saturation == 1:  # Full capacity
                                edge_color = 'red'
                                width = 3.0
                            elif saturation > 0:  # Partial flow
                                edge_color = 'blue'
                                width = 2.0 * saturation + 1.0
                            else:  # No flow
                                edge_color = 'lightgray'
                                width = 1.0
                        else:
                            edge_color = 'lightgray'
                            width = 1.0
                        
                        G.add_edge(flow.source, flow.target, flow=flow.flow, capacity=flow.capacity, 
                                 label=edge_label, color=edge_color, width=width)
                    
                    # Plot the graph
                    plt.figure(figsize=(10, 7))
                    pos = nx.spring_layout(G, seed=42)  # Layout with seed for reproducibility
                    
                    # Draw nodes
                    node_colors = [G.nodes[n]['color'] for n in G.nodes()]
                    nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, alpha=0.8)
                    
                    # Draw edges with varying colors and widths based on flow
                    for u, v, data in G.edges(data=True):
                        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=data['width'],
                                             edge_color=data['color'], arrows=True, arrowsize=20)
                    
                    # Draw labels for nodes and edges
                    nx.draw_networkx_labels(G, pos, font_weight='bold')
                    edge_labels = {(u, v): G[u][v]['label'] for u, v in G.edges()}
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
                    
                    plt.title("Network Flow Solution")
                    plt.axis("off")
                    
                    # Display the graph in Streamlit
                    st.pyplot(plt)
                    
                    # Show flow saturation with a gauge chart
                    if len(flows_data) > 0:
                        st.write("**Arc Flow Utilization:**")
                        for flow in flows_data:
                            if "Utilization" in flow and flow["Utilization"] != "N/A":
                                util_pct = float(flow["Utilization"].strip('%')) / 100
                                label = f"{flow['Source']} → {flow['Target']}"
                                if "Label" in flow:
                                    label += f" ({flow['Label']})"
                                
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.write(label)
                                with col2:
                                    st.progress(util_pct)
                                    st.write(f"{flow['Flow']} / {flow['Capacity']} ({flow['Utilization']})")
                
                elif problem_model.components.problem_type == ProblemType.MIN_COST_FLOW and solution.min_cost_flow_solution:
                    st.subheader("Minimum Cost Flow Solution")
                    
                    # Display min cost value
                    st.write(f"**Minimum Cost Value:** {solution.min_cost_flow_solution.min_cost_value}")
                    st.write(f"**Total Flow Satisfied:** {solution.min_cost_flow_solution.total_flow_satisfied}")
                    
                    # Similar visualizations as for max flow would go here
                    
                # Display solution summary
                if solution.solution_summary:
                    st.subheader("Solution Summary")
                    st.write(solution.solution_summary)
            else:
                # To debug, let's examine the problem model components
                st.write("**Solution Data Not Found**")
                st.write("Debugging information:")
                if hasattr(problem_model.components, 'solution'):
                    st.write("Solution attribute exists but appears to be empty or None")
                else:
                    st.write("Solution attribute doesn't exist on the model components")
                
                # Try to recover from the problem_result if available
                if st.session_state.problem_result and st.session_state.problem_result.flow_solution:
                    st.write("Recovered solution from problem_result:")
                    solution = st.session_state.problem_result.flow_solution
                    st.write(f"Max flow value: {solution.max_flow_solution.max_flow_value if solution.max_flow_solution else 'N/A'}")
                    st.write(solution.solution_summary)
        else:
            st.write("No solution available.")

st.sidebar.header("About")
st.sidebar.write("""
This application uses CrewAI to analyze and solve operations research problems:

1. **Problem Classification**: Determines the type of OR problem
2. **Problem Modeling**: Extracts mathematical components
3. **Problem Solving**: Uses OR-Tools to find optimal solutions
""")

st.sidebar.header("Supported Problem Types")
st.sidebar.write("""
- Linear Programming Problems
- Network Flow Problems (Max Flow)
""")
