"""
NLIP client for inter-agent communication.
"""

import httpx
from typing import Optional

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip


class NLIPClient:
    """Client for sending NLIP messages to other agents using proper NLIP SDK."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def send_message(self, content: str, format_type: str = "text", subformat: str = "english") -> str:
        """Send a NLIP message to another agent and return the response."""
        url = f"{self.base_url}/nlip/"
        
        # Create NLIP message using the SDK
        nlip_message = NLIP_Factory.create_text(content)
        
        # Serialize the NLIP message to JSON
        if hasattr(nlip_message, 'model_dump'):
            message_data = nlip_message.model_dump()
        else:
            message_data = nlip_message
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=message_data,
                    headers={"Content-Type": "application/json"},
                    timeout=60.0
                )
                response.raise_for_status()
                result_data = response.json()
                
                # Parse the response back into a NLIP message and extract text
                response_message = nlip.NLIP_Message.model_validate(result_data)
                return response_message.extract_text()
                
            except Exception as e:
                return f"Error communicating with agent at {self.base_url}: {str(e)}"
