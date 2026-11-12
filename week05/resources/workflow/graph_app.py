"""Assemble the actual LangGraph state machine."""

from .graph_state import AgentState
from .nodes import Nodes
from .routing import route_approval, route_planner, route_retry, route_verify


def connect_conditional_edges(builder):
    """Connect Verify and HumanApproval to their named possible successors."""
    # TODO W5.2: Add the two conditional edges with their allowed destination lists.
    raise NotImplementedError("Complete W5.2 in workflow/graph_app.py.")


def build_graph(checkpointer, effects, *, crash_at=None):
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    nodes = Nodes(effects, suspend=interrupt, crash_at=crash_at)
    builder = StateGraph(AgentState)
    for name, action in (
        ("Planner", nodes.planner),
        ("Execute", nodes.execute),
        ("Verify", nodes.verify),
        ("Retry", nodes.retry),
        ("PrepareApproval", nodes.prepare_approval),
        ("HumanApproval", nodes.human_approval),
        ("ApplyAction", nodes.apply_action),
        ("Finish", nodes.finish),
    ):
        builder.add_node(name, action)
    builder.add_edge(START, "Planner")
    builder.add_conditional_edges("Planner", route_planner, ["Finish", "Execute"])
    builder.add_edge("Execute", "Verify")
    builder.add_conditional_edges("Retry", route_retry, ["Finish", "Execute"])
    builder.add_edge("PrepareApproval", "HumanApproval")
    builder.add_edge("ApplyAction", "Finish")
    builder.add_edge("Finish", END)
    connect_conditional_edges(builder)
    return builder.compile(checkpointer=checkpointer)
