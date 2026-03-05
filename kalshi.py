#!/usr/bin/env python3
"""
kalshi-claw-skill — main CLI dispatcher.
"""

import typer
from typing import Optional

app = typer.Typer(
    name="kalshi",
    help="Trading-enabled Kalshi skill for OpenClaw",
    no_args_is_help=True,
)

markets_app = typer.Typer(help="Market browsing commands")
hedge_app = typer.Typer(help="Hedge discovery commands")
wallet_app = typer.Typer(help="Wallet / portfolio commands")

app.add_typer(markets_app, name="markets")
app.add_typer(hedge_app, name="hedge")
app.add_typer(wallet_app, name="wallet")


# ── Markets ────────────────────────────────────────────────────────────────────

@markets_app.command("trending")
def markets_trending(limit: int = typer.Option(20, help="Number of markets to show")):
    """Top open markets by volume."""
    from scripts.markets import cmd_trending
    cmd_trending(limit)


@markets_app.command("search")
def markets_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, help="Max results"),
):
    """Search markets by keyword."""
    from scripts.markets import cmd_search
    cmd_search(query, limit)


@app.command("market")
def market_detail(ticker: str = typer.Argument(..., help="Market ticker")):
    """Show market details with yes/no prices."""
    from scripts.markets import cmd_detail
    cmd_detail(ticker)


# ── Trading ────────────────────────────────────────────────────────────────────

@app.command("buy")
def buy(
    ticker: str = typer.Argument(..., help="Market ticker"),
    side: str = typer.Argument(..., help="YES or NO"),
    amount: float = typer.Argument(..., help="Amount in USD"),
):
    """Buy YES or NO contracts on a market."""
    from scripts.trade import cmd_buy
    cmd_buy(ticker, side.lower(), amount)


@app.command("sell")
def sell(
    ticker: str = typer.Argument(..., help="Market ticker"),
    side: str = typer.Argument(..., help="YES or NO"),
    amount: float = typer.Argument(..., help="Amount in USD"),
):
    """Sell YES or NO contracts on a market."""
    from scripts.trade import cmd_sell
    cmd_sell(ticker, side.lower(), amount)


# ── Positions ──────────────────────────────────────────────────────────────────

@app.command("positions")
def positions():
    """List open positions with live P&L."""
    from scripts.positions import cmd_positions
    cmd_positions()


@app.command("position")
def position(ticker: str = typer.Argument(..., help="Market ticker")):
    """Show detailed position for a market."""
    from scripts.positions import cmd_position
    cmd_position(ticker)


# ── Wallet ─────────────────────────────────────────────────────────────────────

@wallet_app.command("status")
def wallet_status():
    """Show balance and open orders."""
    from scripts.wallet import cmd_status
    cmd_status()


# ── Hedge ──────────────────────────────────────────────────────────────────────

@hedge_app.command("scan")
def hedge_scan(
    query: Optional[str] = typer.Option(None, help="Filter markets by topic"),
    limit: int = typer.Option(20, help="Number of markets to consider"),
    model: str = typer.Option("nvidia/nemotron-nano-9b-v2:free", help="LLM model"),
    min_tier: int = typer.Option(3, help="Minimum tier (1-3) to display"),
):
    """Scan markets for hedging opportunities using LLM analysis."""
    from scripts.hedge import cmd_scan
    cmd_scan(query, limit, model, min_tier)


@hedge_app.command("analyze")
def hedge_analyze(
    ticker_a: str = typer.Argument(..., help="First market ticker"),
    ticker_b: str = typer.Argument(..., help="Second market ticker"),
    model: str = typer.Option("nvidia/nemotron-nano-9b-v2:free", help="LLM model"),
):
    """Analyze a specific pair of markets for hedge potential."""
    from scripts.hedge import cmd_analyze
    cmd_analyze(ticker_a, ticker_b, model)


if __name__ == "__main__":
    app()
