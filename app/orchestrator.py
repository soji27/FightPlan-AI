"""
LangGraph orchestrator for FightPlan AI.
Routes questions to the appropriate agent (RAG or Tools) and formats final answers.
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv
from typing_extensions import TypedDict

load_dotenv()

# ── Keywords for routing ─────────────────────────────────────────────────────

_RAG_KEYWORDS = [
    "stats", "historique", "palmarès", "combat", "record", "défaite",
    "victoire", "faille", "faiblesse", "a gagné", "a perdu", "csv",
    "données", "data", "fights", "wins", "losses", "history",
    "performance", "précision", "accuracy", "knockdown", "submission",
    "average", "moyenne",
]

_TOOLS_KEYWORDS = [
    "récent", "actualité", "news", "calcule", "compare", "analyse",
    "pattern", "tendance", "dernier combat", "prochain", "recent",
    "latest", "next", "upcoming", "calculate", "trend", "style",
    "web", "internet",
]


# ── State schema ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    question: str
    history: str
    route: str          # "rag" or "tools"
    route_reason: str
    agent_response: Dict[str, Any]
    final_answer: str


# ── Node functions ────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> AgentState:
    """Analyze question intent and decide which agent to use."""
    question = state["question"].lower()

    rag_score = sum(1 for kw in _RAG_KEYWORDS if kw in question)
    tools_score = sum(1 for kw in _TOOLS_KEYWORDS if kw in question)

    if tools_score > rag_score:
        route = "tools"
        reason = f"Question contains {tools_score} tools keywords (récent/actualité/pattern/calcul)"
    elif rag_score > 0:
        route = "rag"
        reason = f"Question contains {rag_score} RAG keywords (stats/historique/record)"
    else:
        # Default to RAG
        route = "rag"
        reason = "No specific routing signal — defaulting to RAG for historical/data lookup"

    print(f"[Routeur] → Agent: {route.upper()} | Raison: {reason}")

    return {
        **state,
        "route": route,
        "route_reason": reason,
    }


def rag_node(state: AgentState) -> AgentState:
    """Call the RAG agent."""
    from app.agents.rag_agent import RAGAgent

    agent = RAGAgent()
    response = agent.query(
        question=state["question"],
        history=state["history"],
    )
    return {
        **state,
        "agent_response": response,
    }


def tools_node(state: AgentState) -> AgentState:
    """Call the Tools agent."""
    from app.agents.tools_agent import ToolsAgent

    agent = ToolsAgent()
    response = agent.run(
        question=state["question"],
        history=state["history"],
    )
    return {
        **state,
        "agent_response": response,
    }


def response_node(state: AgentState) -> AgentState:
    """Format and finalize the answer."""
    response = state.get("agent_response", {})
    answer = response.get("answer", "No answer generated.")

    # Add routing metadata as a note
    route = state.get("route", "unknown").upper()
    reason = state.get("route_reason", "")

    final = answer  # The answer already contains citations from the agents

    print(f"[Final] → {final[:100]}...")

    return {
        **state,
        "final_answer": final,
    }


def _route_condition(state: AgentState) -> str:
    """LangGraph conditional edge: returns next node name based on route."""
    return state.get("route", "rag")


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph():
    """Build and compile the LangGraph StateGraph."""
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("tools_node", tools_node)
    graph.add_node("response", response_node)

    # Entry point
    graph.set_entry_point("router")

    # Conditional routing from router
    graph.add_conditional_edges(
        "router",
        _route_condition,
        {
            "rag": "rag_node",
            "tools": "tools_node",
        },
    )

    # Both agents flow to response
    graph.add_edge("rag_node", "response")
    graph.add_edge("tools_node", "response")

    # Response is terminal
    graph.add_edge("response", END)

    return graph.compile()


# Singleton compiled graph (lazy init)
_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ── Public API ────────────────────────────────────────────────────────────────

def run_query(question: str, history_obj) -> str:
    """Run a question through the orchestrator pipeline.

    Args:
        question: The user's question.
        history_obj: A ConversationHistory instance.

    Returns:
        The final answer string.
    """
    history_str = history_obj.get_formatted() if history_obj else ""

    initial_state: AgentState = {
        "question": question,
        "history": history_str,
        "route": "",
        "route_reason": "",
        "agent_response": {},
        "final_answer": "",
    }

    graph = _get_graph()
    final_state = graph.invoke(initial_state)
    return final_state.get("final_answer", "No answer generated.")
