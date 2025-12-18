"""
Shared weather tools for NLIP agent frameworks demo.
These tools integrate with the National Weather Service API.
"""

import httpx
from typing import Optional


async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state using National Weather Service API.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
        
    Returns:
        Formatted string with weather alerts or no alerts message
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "nlip-agent-frameworks-demo/1.0"
    
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if not data or "features" not in data:
                return "Unable to fetch alerts or no alerts found."

            if not data["features"]:
                return f"✅ No active weather alerts for {state.upper()}."

            alerts = []
            for feature in data["features"]:
                props = feature["properties"]
                alert = f"""
⚠️ **{props.get('event', 'Unknown Event')}**
📍 Area: {props.get('areaDesc', 'Unknown')}
🚨 Severity: {props.get('severity', 'Unknown')}
📝 Description: {props.get('description', 'No description available')}
📋 Instructions: {props.get('instruction', 'No specific instructions provided')}
"""
                alerts.append(alert)
            
            return "\n---\n".join(alerts)
            
        except Exception as e:
            return f"❌ Error fetching weather alerts: {str(e)}"


async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location using National Weather Service API.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        
    Returns:
        Formatted string with weather forecast
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "nlip-agent-frameworks-demo/1.0"
    
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    
    async with httpx.AsyncClient() as client:
        try:
            # First get the forecast grid endpoint
            points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
            points_response = await client.get(points_url, headers=headers, timeout=30.0)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Get the forecast URL from the points response
            forecast_url = points_data["properties"]["forecast"]
            forecast_response = await client.get(forecast_url, headers=headers, timeout=30.0)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Format the periods into a readable forecast
            periods = forecast_data["properties"]["periods"]
            forecasts = []
            for period in periods[:5]:  # Only show next 5 periods
                forecast = f"""
🗓️ **{period['name']}:**
🌡️ Temperature: {period['temperature']}°{period['temperatureUnit']}
💨 Wind: {period['windSpeed']} {period['windDirection']}
📖 Forecast: {period['detailedForecast']}
"""
                forecasts.append(forecast)

            return "\n---\n".join(forecasts)
            
        except Exception as e:
            return f"❌ Error fetching weather forecast: {str(e)}"
