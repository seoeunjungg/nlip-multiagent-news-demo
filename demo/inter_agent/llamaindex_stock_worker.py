import os
from dotenv import load_dotenv

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server import server

from ..shared.stock_tools import get_stock_quote

load_dotenv()


class LlamaIndexStockApplication(server.NLIP_Application):
    async def startup(self):
        print("📈 Starting LlamaIndex Stock Worker...")

    async def shutdown(self):
        print("🛑 Shutting down LlamaIndex Stock Worker")
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LlamaIndexStockSession()


class LlamaIndexStockSession(server.NLIP_Session):
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None

class LlamaIndexStockSession(server.NLIP_Session):
    async def start(self):
        print("✅ Stock worker initialized (no LLM).")

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        text = msg.extract_text()
        try:
            out = await get_stock_quote(text)
            return NLIP_Factory.create_text(out)
        except Exception as e:
            return NLIP_Factory.create_text(f"❌ Error: {str(e)}")

    async def stop(self):
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None


app = server.setup_server(LlamaIndexStockApplication())
