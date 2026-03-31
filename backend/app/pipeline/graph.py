from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph

from app.agents.copywriter import copywriter_node
from app.agents.funnel_builder import funnel_builder_node
from app.agents.state import AgentState
from app.config import settings


async def build_graph():
    """
    Build the MVP LangGraph pipeline topology.

    Topology:
      copywriter -> funnel_builder -> END
    """
    graph = StateGraph(AgentState)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("funnel_builder", funnel_builder_node)
    graph.set_entry_point("copywriter")
    graph.add_edge("copywriter", "funnel_builder")
    graph.add_edge("funnel_builder", END)

    return graph


async def run_pipeline(state: AgentState, thread_id: str):
    """
    Run the compiled graph with the provided initial state.
    """
    graph = await build_graph()
    config = {"configurable": {"thread_id": thread_id}}

    async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL_DIRECT) as checkpointer:
        await checkpointer.setup()
        compiled = graph.compile(checkpointer=checkpointer)
        return await compiled.ainvoke(state, config)
