"""
Shared stock quote tools for NLIP agent frameworks demo.
This version uses Stooq (CSV) as a no-key demo data source.
"""

import re
import httpx


def _normalize_ticker(query: str) -> str:
    t = query.strip().upper()
    t = re.sub(r"[^A-Z0-9\.]", "", t)
    return t


async def get_stock_quote(query: str) -> str:
    """
    Fetch a current-ish stock quote using Stooq CSV.
    Input: ticker or company name (best with ticker for now).
    Output: formatted text with OHLCV.
    """
    ticker = _normalize_ticker(query)

    sym = ticker.lower()
    if "." not in sym:
        sym = f"{sym}.us"

    url = f"https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=20.0)
        r.raise_for_status()
        text = r.text.strip()

    lines = text.splitlines()
    if len(lines) < 2:
        return f"❌ No quote found for '{query}'. Try a ticker like NVDA/AAPL/TSLA."

    header = lines[0].split(",")
    vals = lines[1].split(",")
    row = dict(zip(header, vals))

    if row.get("Close") in (None, "", "N/A"):
        return f"❌ Quote unavailable for '{query}' (symbol used: {sym})."

    return (
        f"📈 **{row.get('Symbol', ticker)}**\n"
        f"- Date: {row.get('Date')} {row.get('Time')}\n"
        f"- Open: {row.get('Open')}\n"
        f"- High: {row.get('High')}\n"
        f"- Low: {row.get('Low')}\n"
        f"- Close: {row.get('Close')}\n"
        f"- Volume: {row.get('Volume')}\n"
        f"- Source: Stooq (CSV)\n"
    )
