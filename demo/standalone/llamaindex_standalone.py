"""
LlamaIndex Standalone Agent with NLIP Integration

This demonstrates direct NLIP integration with LlamaIndex using local weather tools.
No delegation - all tools are implemented locally within this agent.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from llama_index.llms.openai_like import OpenAILike

# Import NLIP components
from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server import server

# Import shared utilities
from ..shared.weather_tools import get_weather_alerts, get_weather_forecast

# Load environment variables
load_dotenv()


# Local weather tool wrappers for LlamaIndex
async def get_weather_alerts_local(state: str) -> str:
    """Get weather alerts for a US state using local implementation.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
    """
    print(f"🌦️ [LlamaIndex Standalone] Fetching weather alerts for {state.upper()}...")
    result = await get_weather_alerts(state)
    print(f"✅ [LlamaIndex Standalone] Weather alerts retrieved")
    return result


async def get_weather_forecast_local(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location using local implementation.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    print(f"🌤️ [LlamaIndex Standalone] Fetching weather forecast for ({latitude}, {longitude})...")
    result = await get_weather_forecast(latitude, longitude)
    print(f"✅ [LlamaIndex Standalone] Weather forecast retrieved")
    return result


class LlamaIndexStandaloneApplication(server.NLIP_Application):
    """LlamaIndex standalone application with local weather tools."""
    
    async def startup(self):
        print("🚀 Starting LlamaIndex Standalone Agent...")
        print("This agent uses local weather tools (no delegation)")

    async def shutdown(self):
        print("🛑 Shutting down LlamaIndex Standalone Agent")
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LlamaIndexStandaloneSession()


class LlamaIndexStandaloneSession(server.NLIP_Session):
    """Standalone chat session using LlamaIndex with local tools."""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None

    async def start(self):
        """Initialize LlamaIndex components with local tools."""
        try:
            print("🔧 Initializing LlamaIndex standalone components...")
            
            # Check for API key
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required. Get your key from https://openrouter.ai/")
            
            print(f"🔑 Using OpenRouter API key: {api_key[:10]}...")
            
            # Initialize Claude model via OpenRouter
            self.llm = OpenAILike(
                model="anthropic/claude-3.5-sonnet",
                api_key=api_key,
                api_base="https://openrouter.ai/api/v1",
                temperature=0.7,
                context_window=200000,
                is_chat_model=True,
                is_function_calling_model=True,
            )
            
            # Create FunctionTool objects from our local functions
            self.tools = [
                FunctionTool.from_defaults(
                    fn=get_weather_alerts_local,
                    name="get_weather_alerts_local",
                    description="Get weather alerts for a US state. Takes a state code like 'CA', 'NY', 'IN'."
                ),
                FunctionTool.from_defaults(
                    fn=get_weather_forecast_local,
                    name="get_weather_forecast_local", 
                    description="Get weather forecast for coordinates. Takes latitude and longitude as numbers."
                ),
            ]
            
            # Create LlamaIndex FunctionAgent
            self.agent = FunctionAgent(
                tools=self.tools,
                llm=self.llm,
                verbose=True,
                system_prompt=(
                    "You are a helpful weather assistant with direct access to weather tools. "
                    "You can get weather alerts for any US state and weather forecasts for any location "
                    "with latitude and longitude coordinates. "
                    "Always provide complete, accurate information based on the tool results."
                )
            )
            
            # Initialize context for maintaining conversation state
            self.context = Context(self.agent)
            
            print("✅ LlamaIndex standalone components initialized successfully.")
            print(f"🛠️ Available local tools: {[tool.metadata.name for tool in self.tools]}")
            
        except Exception as e:
            print(f"❌ Error initializing LlamaIndex standalone components: {e}")
            raise

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        """Execute user query using LlamaIndex agent with local tools."""
        logger = self.get_logger()
        text = msg.extract_text()
        
        try:
            print(f"\n📨 [LlamaIndex Standalone] Processing query: {text}")
            print("=" * 70)
            
            # Use the LlamaIndex agent to process the query
            response = await self.agent.run(text, ctx=self.context)
            response_text = str(response)
            
            print("=" * 70)
            print(f"📤 [LlamaIndex Standalone] Sending response to client\n")
            logger.info(f"LlamaIndex Standalone Response: {response_text}")
            return NLIP_Factory.create_text(response_text)
            
        except Exception as e:
            logger.error(f"Exception in LlamaIndex standalone execution: {e}")
            return NLIP_Factory.create_text(f"❌ Error processing request: {str(e)}")

    async def stop(self):
        """Clean up resources."""
        print("🛑 Stopping LlamaIndex standalone session")
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None


# Standalone demo function
async def standalone_demo():
    """Run a standalone demo without NLIP server integration."""
    print("=== LlamaIndex Standalone Weather Demo ===")
    print("This demo showcases LlamaIndex with local weather tools (no delegation).")
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
    
    # Initialize LlamaIndex components
    llm = OpenAILike(
        model="anthropic/claude-3.5-sonnet",
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        context_window=200000,
        is_chat_model=True,
        is_function_calling_model=True,
    )
    
    tools = [
        FunctionTool.from_defaults(
            fn=get_weather_alerts_local,
            name="get_weather_alerts_local",
            description="Get weather alerts for a US state. Takes a state code like 'CA', 'NY', 'IN'."
        ),
        FunctionTool.from_defaults(
            fn=get_weather_forecast_local,
            name="get_weather_forecast_local", 
            description="Get weather forecast for coordinates. Takes latitude and longitude as numbers."
        ),
    ]
    
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        verbose=True,
        system_prompt=(
            "You are a helpful weather assistant with direct access to weather tools. "
            "You can get weather alerts for any US state and weather forecasts for any location "
            "with latitude and longitude coordinates. "
            "Always provide complete, accurate information based on the tool results."
        )
    )
    
    context = Context(agent)
    
    print("🤖 LlamaIndex standalone agent initialized with local tools:")
    for tool in tools:
        print(f"  - {tool.metadata.name}: {tool.metadata.description}")
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
            response = await agent.run(user_input, ctx=context)
            print(f"{str(response)}\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


# Create the FastAPI app
app = server.setup_server(LlamaIndexStandaloneApplication())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Run standalone demo
        asyncio.run(standalone_demo())
    else:
        print("🌟 LlamaIndex Standalone NLIP Server Ready!")
        print("This server uses LlamaIndex with local weather tools (no delegation).")
        print("🚀 Start with: poetry run uvicorn demo.standalone.llamaindex_standalone:app --host 0.0.0.0 --port 8015 --reload")
