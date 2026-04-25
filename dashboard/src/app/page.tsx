"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RegimeData, AccountData, PositionData } from "@/lib/types";

const regimeColors: Record<string, string> = {
  risk_on: "text-green-400 bg-green-950 border-green-800",
  bullish: "text-blue-400 bg-blue-950 border-blue-800",
  cautious: "text-amber-400 bg-amber-950 border-amber-800",
  risk_off: "text-red-400 bg-red-950 border-red-800",
};

const regimeLabels: Record<string, string> = {
  risk_on: "RISK-ON",
  bullish: "BULLISH",
  cautious: "CAUTIOUS",
  risk_off: "RISK-OFF",
};

function SignalBar({ value, label }: { value: number; label: string }) {
  const pct = ((value + 1) / 2) * 100;
  const color = value > 0.2 ? "bg-green-500" : value < -0.2 ? "bg-red-500" : "bg-gray-500";

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-36 text-gray-400 truncate">{label}</span>
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${Math.max(2, pct)}%` }}
        />
      </div>
      <span className={`w-12 text-right font-mono ${value > 0 ? "text-green-400" : value < 0 ? "text-red-400" : "text-gray-500"}`}>
        {value > 0 ? "+" : ""}{value.toFixed(2)}
      </span>
    </div>
  );
}

function MetricCard({ label, value, subtext }: { label: string; value: string; subtext?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [account, setAccount] = useState<AccountData | null>(null);
  const [positions, setPositions] = useState<PositionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [r, a, p] = await Promise.all([
          api.getRegime(),
          api.getAccount(),
          api.getPositions(),
        ]);
        setRegime(r);
        setAccount(a);
        setPositions(p);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-950 border border-red-800 rounded-lg p-4 text-red-400">
        <p className="font-semibold">Connection Error</p>
        <p className="text-sm mt-1">{error}</p>
        <p className="text-xs text-red-500 mt-2">
          Make sure the API server is running: uvicorn api.main:app --port 8000
        </p>
      </div>
    );
  }

  const signalNames: Record<string, string> = {
    spx_vs_200sma: "SPX vs 200 SMA",
    spx_vs_50sma: "SPX vs 50 SMA",
    sma_cross: "SMA Cross",
    vix: "VIX",
    vix_term: "VIX Term Structure",
    breadth: "Market Breadth",
    yield_curve: "Yield Curve",
    momentum_20d: "20-Day Momentum",
    fear_greed: "Fear & Greed",
    rate_expectations: "Rate Expectations",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <span className="text-xs text-gray-500">
          {regime ? new Date(regime.timestamp).toLocaleString() : ""}
        </span>
      </div>

      {regime && (
        <div className={`border rounded-lg p-5 ${regimeColors[regime.regime]}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wide opacity-70">Market Regime</div>
              <div className="text-3xl font-bold mt-1">{regimeLabels[regime.regime]}</div>
              <div className="text-sm opacity-80 mt-1">
                Score: {regime.score > 0 ? "+" : ""}{regime.score.toFixed(3)}
              </div>
            </div>
            <div className="text-right text-sm">
              <div>Max Position: {(regime.max_position_pct * 100).toFixed(1)}%</div>
              <div>Max Heat: {(regime.max_heat_pct * 100).toFixed(0)}%</div>
              <div className="mt-1 opacity-70">
                {regime.allowed_strategies.length > 0
                  ? regime.allowed_strategies.join(", ")
                  : "No strategies (cash)"}
              </div>
            </div>
          </div>
        </div>
      )}

      {account && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Equity" value={`$${account.equity.toLocaleString()}`} />
          <MetricCard label="Cash" value={`$${account.cash.toLocaleString()}`} />
          <MetricCard label="Buying Power" value={`$${account.buying_power.toLocaleString()}`} />
          <MetricCard label="Open Positions" value={String(positions.length)} subtext={account.is_paper ? "Paper Account" : "LIVE"} />
        </div>
      )}

      {positions.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h2 className="font-semibold">Open Positions</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 uppercase bg-gray-900/50">
              <tr>
                <th className="px-4 py-2 text-left">Ticker</th>
                <th className="px-4 py-2 text-right">Qty</th>
                <th className="px-4 py-2 text-right">Entry</th>
                <th className="px-4 py-2 text-right">Current</th>
                <th className="px-4 py-2 text-right">P&L</th>
                <th className="px-4 py-2 text-right">P&L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.ticker} className="border-t border-gray-800">
                  <td className="px-4 py-3 font-medium">{p.ticker}</td>
                  <td className="px-4 py-3 text-right">{p.qty}</td>
                  <td className="px-4 py-3 text-right">${p.entry_price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">${p.current_price.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right ${p.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    ${p.unrealized_pnl.toFixed(0)}
                  </td>
                  <td className={`px-4 py-3 text-right ${p.unrealized_pnl_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {(p.unrealized_pnl_pct * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {regime && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Regime Signals</h2>
          <div className="space-y-2">
            {Object.entries(regime.signals)
              .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
              .map(([key, value]) => (
                <SignalBar key={key} label={signalNames[key] || key} value={value} />
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
