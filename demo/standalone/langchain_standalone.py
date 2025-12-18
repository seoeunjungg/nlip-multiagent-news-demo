"""
LangChain Standalone Agent with NLIP Integration

This demonstrates direct NLIP integration with LangChain using local weather tools.
No delegation - all tools are implemented locally within this agent.
"""

import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.callbacks import BaseCallbackHandler
w
# Import NLIP components
from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server import server

# Import shared utilities
from ..shared.weather_tools import get_weather_alerts, get_weather_forecast

# Load environment variables
load_dotenv()


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        print(token, end="", flush=True)


# Local Weather Tools (NOT delegating - implementing directly)
@tool
async def get_weather_alerts_local(state: str) -> str:
    """Get weather alerts for a US state using local implementation.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
    """
    print(f"🌦️ [LangChain Standalone] Fetching weather alerts for {state.upper()}...")
    result = await get_weather_alerts(state)
    print(f"✅ [LangChain Standalone] Weather alerts retrieved")
    return result


@tool
async def get_weather_forecast_local(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location using local implementation.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    print(f"🌤️ [LangChain Standalone] Fetching weather forecast for ({latitude}, {longitude})...")
    result = await get_weather_forecast(latitude, longitude)
    print(f"✅ [LangChain Standalone] Weather forecast retrieved")
    return result


class LangChainStandaloneApplication(server.NLIP_Application):
    """LangChain standalone application with local weather tools."""
    
    async def startup(self):
        print("🚀 Starting LangChain Standalone Agent...")
        print("This agent uses local weather tools (no delegation)")

    async def shutdown(self):
        print("🛑 Shutting down LangChain Standalone Agent")
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LangChainStandaloneSession()


class LangChainStandaloneSession(server.NLIP_Session):
    """Standalone chat session using LangChain with local tools."""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent_executor = None
        self.tools = []

    async def start(self):
        """Initialize LangChain components with local tools."""
        try:
            print("🔧 Initializing LangChain standalone components...")
            
            # Check for API key
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required. Get your key from https://openrouter.ai/")
            
            print(f"🔑 Using OpenRouter API key: {api_key[:10]}...")
            
            # Initialize model via OpenRouter API
            self.llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4", 
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7,
                callbacks=[StreamingCallbackHandler()],
                # Add headers for OpenRouter
                model_kwargs={
                    "extra_headers": {
                        "HTTP-Referer": "https://github.com/nlip-org/agent-frameworks-demo", 
                        "X-Title": "NLIP Agent Frameworks Demo"
                    }
                }
            )
            
            # Define available tools (local implementations)
            self.tools = [
                get_weather_alerts_local,
                get_weather_forecast_local
            ]
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", 
                 "You are a helpful weather assistant with direct access to weather tools. "
                 "You can get weather alerts for any US state and weather forecasts for any location "
                 "with latitude and longitude coordinates. "
                 "Provide clear, helpful responses based on the tool results."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            # Create agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            print("✅ LangChain standalone components initialized successfully.")
            print(f"🛠️ Available local tools: {[tool.name for tool in self.tools]}")
            
        except Exception as e:
            print(f"❌ Error initializing LangChain standalone components: {e}")
            raise

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        """Execute user query using LangChain agent with local tools."""
        logger = self.get_logger()
        text = msg.extract_text()
        
        try:
            print(f"\n📨 [LangChain Standalone] Processing query: {text}")
            print("=" * 70)
            
            # Use the agent executor to process the query
            result = await self.agent_executor.ainvoke({"input": text})
            response = result["output"]
            
            print("=" * 70)
            print(f"📤 [LangChain Standalone] Sending response to client\n")
            logger.info(f"LangChain Standalone Response: {response}")
            return NLIP_Factory.create_text(response)
            
        except Exception as e:
            logger.error(f"Exception in LangChain standalone execution: {e}")
            return NLIP_Factory.create_text(f"❌ Error processing request: {str(e)}")

    async def stop(self):
        """Clean up resources."""
        print("🛑 Stopping LangChain standalone session")
        self.llm = None
        self.agent_executor = None
        self.tools = []


# Standalone demo function
async def standalone_demo():
    """Run a standalone demo without NLIP server integration."""
    print("=== LangChain Standalone Weather Demo ===")
    print("This demo showcases LangChain with local weather tools (no delegation).")
    print("Available commands:")
    print("- Weather alerts: 'Get weather alerts for Indiana'")
    print("- Weather forecast: 'What's the weather forecast for Bloomington, Indiana?'")
    print("- Weather forecast: 'What's the weather forecast for coordinates 34.0522, -118.2437?'")
    print("- Combined queries: 'Are there any alerts for California? What's the forecast for LA?'")
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
    
    tools = [get_weather_alerts_local, get_weather_forecast_local]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a helpful weather assistant with direct access to weather tools. "
         "You can get weather alerts for any US state and weather forecasts for any location "
         "with latitude and longitude coordinates. "
         "Provide clear, helpful responses based on the tool results."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    print("🤖 LangChain standalone agent initialized with local tools:")
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
                
            print("\nAssistant: ", end="")
            result = await agent_executor.ainvoke({"input": user_input})
            print(f"\n{result['output']}\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


# Create the FastAPI app
app = server.setup_server(LangChainStandaloneApplication())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Run standalone demo
        asyncio.run(standalone_demo())
    else:
        print("🌟 LangChain Standalone NLIP Server Ready!")
        print("This server uses LangChain with local weather tools (no delegation).")
        print("🚀 Start with: poetry run uvicorn demo.standalone.langchain_standalone:app --host 0.0.0.0 --port 8014 --reload")
