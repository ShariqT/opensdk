from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain.messages import AnyMessage, SystemMessage, ToolMessage
import operator
from typing_extensions import Annotated

class CoderState(TypedDict):
    error: str
    messages: Annotated[list[AnyMessage], operator.add]

class CoderAgent:
    def __init__(self, model, tools, system=""):
        self.tools = {t.name: t for t in tools }
        self.model = model.bind_tools(tools)
        self.system = system
        graph = StateGraph(CoderState)
        graph.add_node("model", self.call_model_provider)
        graph.add_node("call_tool", self.call_tool)
        graph.add_conditional_edges("model", self.exists_tool, {True: "call_tool", False: END })
        graph.add_edge("call_tool", "model")
        graph.set_entry_point("model")
        self.graph = graph.compile()
        

    def call_model_provider(self, state: CoderState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        print(f"from agent: {message.content}")
        return {"messages": [message], "error": ""}

    def exists_tool(self, state: CoderState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_tool(self, state: CoderState):
        tools_called = state['messages'][-1].tool_calls
        results = []
        final_state = {"messages": state['messages'], "error": state['error']}
        for t in tools_called:
            print(f"agent calling {t['name']} with {t['args']}")
            if not t['name'] in self.tools:
                result = "this tool does not exist. try another way."
                final_state['error'] = f"There is no tool called {t['name']}"
            else:
                result = self.tools[t['name']].invoke(t['args'])
            newm = ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result))
            results.append(newm)
            final_state['messages'] = results
        return final_state


    