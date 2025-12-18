"""
Shared tech news tools for NLIP agent frameworks demo.
These tools integrate with an external news API to fetch recent articles.
"""

import os
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"


async def get_tech_news_brief(topic: str, days: int = 1) -> str:
    """
    Fetch real news articles about a tech topic using NewsAPI.org.
    """

    if not NEWS_API_KEY:
        return "❌ NEWS_API_KEY is missing. Add it to your .env file."

    # Date range
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    q = f'({topic}) AND (technology OR tech OR software OR AI OR "artificial intelligence" OR cybersecurity OR "information security" OR cloud OR "data center" OR semiconductors OR GPU OR chip OR "export controls")'

    params = {
        "q": q,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "searchIn": "title,description",
        "apiKey": NEWS_API_KEY,
        "domains": "arstechnica.com,techcrunch.com,theverge.com,wired.com,theregister.com,zdnet.com,venturebeat.com,engadget.com,bleepingcomputer.com,securityweek.com,krebsonsecurity.com",
        "pageSize": 20,  
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NEWS_API_URL, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()

        except Exception as e:
            return f"❌ Error fetching news: {str(e)}"

    if "articles" not in data or len(data["articles"]) == 0:
        return f"❌ No news found about '{topic}' in the last {days} days."

    articles = data["articles"]

    summaries = []
    for a in articles:
        title = a["title"]
        source = a["source"]["name"]
        date = a["publishedAt"]
        url = a["url"]
        desc = a.get("description", "(No description)")

        summaries.append(
            f"📰 **{title}**\n"
            f"   - Source: {source}\n"
            f"   - Date: {date}\n"
            f"   - Summary: {desc}\n"
            f"   - URL: {url}\n"
        )

    return "\n---\n".join(summaries)
