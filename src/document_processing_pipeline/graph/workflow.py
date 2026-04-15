from __future__ import annotations

from document_processing_pipeline.graph.nodes.aggregator import aggregator_node
from document_processing_pipeline.graph.nodes.discharge_agent import discharge_summary_agent_node
from document_processing_pipeline.graph.nodes.id_agent import id_agent_node
from document_processing_pipeline.graph.nodes.itemized_bill_agent import itemized_bill_agent_node
from document_processing_pipeline.graph.nodes.segregator import segregator_node
from document_processing_pipeline.graph.state import ClaimGraphState
from langgraph.graph import END, START, StateGraph


def build_claim_graph():
    graph = StateGraph(ClaimGraphState)
    graph.add_node("segregator", segregator_node)
    graph.add_node("id_agent", id_agent_node)
    graph.add_node("discharge_summary_agent", discharge_summary_agent_node)
    graph.add_node("itemized_bill_agent", itemized_bill_agent_node)
    graph.add_node("aggregator", aggregator_node)

    graph.add_edge(START, "segregator")
    graph.add_edge("segregator", "id_agent")
    graph.add_edge("segregator", "discharge_summary_agent")
    graph.add_edge("segregator", "itemized_bill_agent")
    graph.add_edge("id_agent", "aggregator")
    graph.add_edge("discharge_summary_agent", "aggregator")
    graph.add_edge("itemized_bill_agent", "aggregator")
    graph.add_edge("aggregator", END)
    return graph.compile()
