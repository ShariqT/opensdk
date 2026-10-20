from .utils import uv_tool, read_file, write_file, create_file, read_directory
from .agent import CoderAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class ModelProviderBase():
    def __init__(self, model, api_key):
        self.model = model
        self.api_key = api_key
        
    def generate(self, prompt: str):
        raise NotImplementedError

class WavespeedProvider(ModelProviderBase):
    def __init__(self, model, api_key, system_prompt=None):
        super().__init__(model, api_key)
        self.base_url = "https://llm.wavespeed.ai/v1"
        model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=self.base_url,
            max_retries=2
        )

        self.agent = CoderAgent(model, [uv_tool, read_file, write_file, create_file, read_directory], system_prompt)

    def generate(self, prompt: str, trace: bool = False):
        result = self.agent.graph.invoke({"messages": [HumanMessage(content=prompt)]})
        print(f"agent call {result}")
        return result