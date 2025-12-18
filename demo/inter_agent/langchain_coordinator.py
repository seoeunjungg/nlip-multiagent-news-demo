"""
LangChain Coordinator Agent for Inter-Agent Communication Demo

This agent receives client requests and delegates tool execution to the LlamaIndex worker
agent via NLIP protocol. It demonstrates how different AI frameworks can collaborate.
"""

import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.callbacks import BaseCallbackHandler

# Import NLIP components
from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server import server

# Import shared utilities
from ..shared.nlip_client import NLIPClient

# Load environment variables
load_dotenv()

# Configuration
LLAMAINDEX_SERVER_URL = os.getenv("LLAMAINDEX_SERVER_URL", "http://localhost:8013")


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        print(token, end="", flush=True)

@tool
async def get_tech_news(topic: str, days: int = 1) -> str:
    """Get recent tech news about a topic by delegating to the LlamaIndex worker via NLIP."""
    print(f"\n🔄 [LangChain] Delegating tech news query for '{topic}' (days={days}) to LlamaIndex worker...")
    
    client = NLIPClient(LLAMAINDEX_SERVER_URL)
    query = f"Get recent tech news about '{topic}' in the last {days} days."
    
    response = await client.send_message(query)
    print(f"✅ [LangChain] Tech news response received from LlamaIndex worker\n")
    return response

class LangChainApplication(server.NLIP_Application):
    """LangChain application for inter-agent communication."""
    
    async def startup(self):
        print("🚀 Starting LangChain Agent...")
        print("This agent delegates tool execution to LlamaIndex worker via NLIP protocol")

    async def shutdown(self):
        print("🛑 Shutting down LangChain Agent")
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LangChainSession()


class LangChainSession(server.NLIP_Session):
    """Chat session using LangChain with tool delegation."""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent_executor = None
        self.tools = []

    async def start(self):
        """Initialize LangChain components for coordination."""
        try:
            print("🔧 Initializing LangChain components...")
            
            print("🔑 Using local Ollama model 'llama3.1' ...")

            self.llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            # Check for API key
            # api_key = os.getenv("OPENROUTER_API_KEY")
            # if not api_key:
            #     raise ValueError("OPENROUTER_API_KEY environment variable is required. Get your key from https://openrouter.ai/")
            
            # print(f"🔑 Using OpenRouter API key: {api_key[:10]}...")
            
            # Initialize model via OpenRouter API
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",         
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.3,
                max_tokens=512,
                callbacks=[StreamingCallbackHandler()],
            )

            # Define available tools (all delegating to LlamaIndex server)
            self.tools = [
                get_tech_news,
            ]
            
            # Create prompt template for coordination
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                "You are a helpful tech news agent. You answer questions about recent AI, computer science, "
                "and cybersecurity news. You delegate fetching of raw news articles to a specialized worker agent "
                "via tools, then you synthesize concise, factual summaries. When users ask about a single topic, "
                "produce a TL;DR and key events. When they ask for a comparison (e.g., OpenAI vs Anthropic), "
                "call the tool separately for each entity and produce a point-by-point comparison. "
                "Avoid speculation; clearly distinguish between known facts and uncertainty."),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Create agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            print("✅ LangChain components initialized successfully.")
            print(f"🛠️ Available delegating tools: {[tool.name for tool in self.tools]}")
            print(f"🌐 LlamaIndex worker server URL: {LLAMAINDEX_SERVER_URL}")
            
        except Exception as e:
            print(f"❌ Error initializing LangChain components: {e}")
            raise

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        """Execute user query using LangChain with delegation."""
        logger = self.get_logger()
        text = msg.extract_text()
        
        try:
            print(f"\n📨 [LangChain] Processing client query: {text}")
            print("=" * 80)
            
            # Use the agent executor to process the query
            result = await self.agent_executor.ainvoke({"input": text})
            response = result["output"]
            
            print("=" * 80)
            print(f"📤 [LangChain] Sending final response to client\n")
            logger.info(f"LangChain Response: {response}")
            return NLIP_Factory.create_text(response)
            
        except Exception as e:
            logger.error(f"Exception in LangChain execution: {e}")
            return NLIP_Factory.create_text(f"❌ Error processing request: {str(e)}")

    async def stop(self):
        """Clean up resources."""
        print("🛑 Stopping LangChain session")
        self.llm = None
        self.agent_executor = None
        self.tools = []


# Standalone demo function for testing
async def standalone_demo():
    """Run a standalone demo to test the functionality."""
    print("=== LangChain Standalone Demo ===")
    print("This demo tests the agent with delegation to LlamaIndex worker.")
    print("Make sure the LlamaIndex worker is running on port 8013!")
    print()
    print("Available commands:")
    print("- Weather alerts: 'Get weather alerts for Indiana'")
    print("- Weather forecast: 'What's the weather forecast for Bloomington, Indiana?'")
    print("- Combined queries: 'Are there any alerts for California? What's the LA forecast?'")
    print("- Quit: 'quit' or 'exit'")
    print()
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY environment variable is required!")
        print("Get your API key from: https://openrouter.ai/")
        print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
        return
    
    # Initialize LangChain components
    llm = ChatOpenAI(
        model="anthropic/claude-sonnet-4", 
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        model_kwargs={
            "extra_headers": {
                "HTTP-Referer": "https://github.com/nlip-org/agent-frameworks-demo", 
                "X-Title": "NLIP Agent Frameworks Demo"
            }
        }
    )
    
    tools = [get_weather_alerts, get_weather_forecast]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a helpful weather agent. You have access to weather tools, "
         "but you delegate the actual execution to a specialized weather worker agent. "
         "When users ask about weather, use the appropriate tools to get the information. "
         "Present the results in a clear, helpful manner."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    print("🤖 LangChain initialized with delegating tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input:
                continue
                
            print("\nAgent: ", end="")
            result = await agent_executor.ainvoke({"input": user_input})
            print(f"\n{result['output']}\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


# Create the FastAPI app
app = server.setup_server(LangChainApplication())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Run standalone demo
        asyncio.run(standalone_demo())
    else:
        print("🌟 LangChain NLIP Server Ready!")
        print("This server coordinates requests and delegates tool execution to LlamaIndex worker.")
        print("🚀 Start with: poetry run uvicorn demo.inter_agent.langchain_coordinator:app --host 0.0.0.0 --port 8012 --reload")
        print("Make sure the LlamaIndex worker is running on port 8013 first!")
