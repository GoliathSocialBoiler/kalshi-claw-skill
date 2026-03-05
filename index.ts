#!/usr/bin/env node
/**
 * kalshi-claw-skill MCP server
 * Bridges OpenClaw / Claude Desktop to the Python Kalshi skill via subprocess.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(__dirname, "..");
const PYTHON_CLI = path.join(SKILL_ROOT, "scripts", "kalshi.py");

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS: Tool[] = [
  {
    name: "kalshi_markets_trending",
    description: "List top open Kalshi prediction markets by volume.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Number of markets (default 20)" },
      },
    },
  },
  {
    name: "kalshi_markets_search",
    description: "Search Kalshi markets by keyword.",
    inputSchema: {
      type: "object",
      required: ["query"],
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results (default 20)" },
      },
    },
  },
  {
    name: "kalshi_market_detail",
    description: "Get detailed info for a specific Kalshi market.",
    inputSchema: {
      type: "object",
      required: ["ticker"],
      properties: {
        ticker: { type: "string", description: "Market ticker (e.g. INXD-23DEC31-B4000)" },
      },
    },
  },
  {
    name: "kalshi_buy",
    description: "Buy YES or NO contracts on a Kalshi market.",
    inputSchema: {
      type: "object",
      required: ["ticker", "side", "amount"],
      properties: {
        ticker: { type: "string", description: "Market ticker" },
        side: { type: "string", enum: ["YES", "NO"], description: "Contract side" },
        amount: { type: "number", description: "Amount in USD" },
      },
    },
  },
  {
    name: "kalshi_sell",
    description: "Sell YES or NO contracts on a Kalshi market.",
    inputSchema: {
      type: "object",
      required: ["ticker", "side", "amount"],
      properties: {
        ticker: { type: "string" },
        side: { type: "string", enum: ["YES", "NO"] },
        amount: { type: "number" },
      },
    },
  },
  {
    name: "kalshi_positions",
    description: "List all open positions with live P&L.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "kalshi_position_detail",
    description: "Get detailed P&L for a single position.",
    inputSchema: {
      type: "object",
      required: ["ticker"],
      properties: {
        ticker: { type: "string" },
      },
    },
  },
  {
    name: "kalshi_wallet_status",
    description: "Show Kalshi portfolio balance and open orders.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "kalshi_hedge_scan",
    description:
      "Scan open Kalshi markets for hedging opportunities using LLM analysis.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Optional topic filter" },
        limit: { type: "number", description: "Markets to consider (default 20)" },
        model: { type: "string", description: "OpenRouter model (default: nvidia/nemotron-nano-9b-v2:free)" },
        min_tier: { type: "number", description: "Min tier 1-3 (default 3)" },
      },
    },
  },
  {
    name: "kalshi_hedge_analyze",
    description: "Analyze a specific pair of Kalshi markets for hedge potential.",
    inputSchema: {
      type: "object",
      required: ["ticker_a", "ticker_b"],
      properties: {
        ticker_a: { type: "string" },
        ticker_b: { type: "string" },
        model: { type: "string" },
      },
    },
  },
];

// ── CLI runner ────────────────────────────────────────────────────────────────

async function runCLI(args: string[]): Promise<string> {
  const uvArgs = ["run", "python", PYTHON_CLI, ...args];
  try {
    const { stdout, stderr } = await execFileAsync("uv", uvArgs, {
      cwd: SKILL_ROOT,
      env: { ...process.env },
      timeout: 120_000,
    });
    return stdout + (stderr ? `\n[stderr]\n${stderr}` : "");
  } catch (err: any) {
    return `Error: ${err.message}\n${err.stderr ?? ""}`;
  }
}

// ── Tool handler ──────────────────────────────────────────────────────────────

async function callTool(name: string, args: Record<string, unknown>): Promise<string> {
  switch (name) {
    case "kalshi_markets_trending":
      return runCLI(["markets", "trending", "--limit", String(args.limit ?? 20)]);

    case "kalshi_markets_search":
      return runCLI([
        "markets", "search", String(args.query),
        "--limit", String(args.limit ?? 20),
      ]);

    case "kalshi_market_detail":
      return runCLI(["market", String(args.ticker)]);

    case "kalshi_buy":
      return runCLI(["buy", String(args.ticker), String(args.side), String(args.amount)]);

    case "kalshi_sell":
      return runCLI(["sell", String(args.ticker), String(args.side), String(args.amount)]);

    case "kalshi_positions":
      return runCLI(["positions"]);

    case "kalshi_position_detail":
      return runCLI(["position", String(args.ticker)]);

    case "kalshi_wallet_status":
      return runCLI(["wallet", "status"]);

    case "kalshi_hedge_scan": {
      const cliArgs = ["hedge", "scan"];
      if (args.query) cliArgs.push("--query", String(args.query));
      if (args.limit) cliArgs.push("--limit", String(args.limit));
      if (args.model) cliArgs.push("--model", String(args.model));
      if (args.min_tier) cliArgs.push("--min-tier", String(args.min_tier));
      return runCLI(cliArgs);
    }

    case "kalshi_hedge_analyze": {
      const cliArgs = ["hedge", "analyze", String(args.ticker_a), String(args.ticker_b)];
      if (args.model) cliArgs.push("--model", String(args.model));
      return runCLI(cliArgs);
    }

    default:
      return `Unknown tool: ${name}`;
  }
}

// ── Server ────────────────────────────────────────────────────────────────────

const server = new Server(
  { name: "kalshi-claw-skill", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const result = await callTool(
    req.params.name,
    (req.params.arguments ?? {}) as Record<string, unknown>
  );
  return {
    content: [{ type: "text", text: result }],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
