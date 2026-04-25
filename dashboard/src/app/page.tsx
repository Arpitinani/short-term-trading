"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RegimeData, AccountData, PositionData } from "@/lib/types";

const regimeStyles: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  risk_on: { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-800", badge: "bg-emerald-600" },
  bullish: { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-800", badge: "bg-blue-600" },
  cautious: { bg: "bg-amber-50", border: "border-amber-300", text: "text-amber-800", badge: "bg-amber-600" },
  risk_off: { bg: "bg-red-50", border: "border-red-300", text: "text-red-800", badge: "bg-red-600" },
};

const regimeLabels: Record<string, string> = {
  risk_on: "RISK-ON",
  bullish: "BULLISH",
  cautious: "CAUTIOUS",
  risk_off: "RISK-OFF",
};

function SignalBar({ value, label }: { value: number; label: string }) {
  const pct = ((value + 1) / 2) * 100;
  const color = value > 0.2 ? "bg-emerald-500" : value < -0.2 ? "bg-red-500" : "bg-stone-300";

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-40 text-stone-500 truncate">{label}</span>
      <div className="flex-1 h-2.5 bg-stone-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${Math.max(3, pct)}%` }}
        />
      </div>
      <span className={`w-14 text-right font-mono text-sm font-medium ${value > 0 ? "text-emerald-700" : value < 0 ? "text-red-600" : "text-stone-400"}`}>
        {value > 0 ? "+" : ""}{value.toFixed(2)}
      </span>
    </div>
  );
}

function MetricCard({ label, value, subtext }: { label: string; value: string; subtext?: string }) {
  return (
    <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
      <div className="text-xs text-stone-400 uppercase tracking-wider font-medium">{label}</div>
      <div className="text-2xl font-bold text-stone-800 mt-1">{value}</div>
      {subtext && <div className="text-xs text-stone-400 mt-1">{subtext}</div>}
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
        <div className="text-stone-400">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
        <p className="font-semibold">Connection Error</p>
        <p className="text-sm mt-1">{error}</p>
        <p className="text-xs text-red-400 mt-2">
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

  const rs = regime ? regimeStyles[regime.regime] : regimeStyles.bullish;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-800">Dashboard</h1>
        <span className="text-xs text-stone-400">
          {regime ? new Date(regime.timestamp).toLocaleString() : ""}
        </span>
      </div>

      {/* Regime Banner */}
      {regime && (
        <div className={`border-2 rounded-xl p-5 ${rs.bg} ${rs.border}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-xs uppercase tracking-wider font-medium ${rs.text} opacity-70`}>Market Regime</div>
              <div className="flex items-center gap-3 mt-1">
                <span className={`text-3xl font-bold ${rs.text}`}>{regimeLabels[regime.regime]}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${rs.badge}`}>
                  {regime.score > 0 ? "+" : ""}{regime.score.toFixed(3)}
                </span>
              </div>
            </div>
            <div className={`text-right text-sm ${rs.text}`}>
              <div>Max Position: <span className="font-semibold">{(regime.max_position_pct * 100).toFixed(1)}%</span></div>
              <div>Max Heat: <span className="font-semibold">{(regime.max_heat_pct * 100).toFixed(0)}%</span></div>
              <div className="mt-1 text-xs opacity-60">
                {regime.allowed_strategies.length > 0
                  ? regime.allowed_strategies.join(", ")
                  : "No strategies (cash)"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Account Metrics */}
      {account && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Equity" value={`$${account.equity.toLocaleString()}`} />
          <MetricCard label="Cash" value={`$${account.cash.toLocaleString()}`} />
          <MetricCard label="Buying Power" value={`$${account.buying_power.toLocaleString()}`} />
          <MetricCard label="Open Positions" value={String(positions.length)} subtext={account.is_paper ? "Paper Account" : "LIVE"} />
        </div>
      )}

      {/* Positions Table */}
      {positions.length > 0 && (
        <div className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-stone-100 bg-stone-50">
            <h2 className="font-semibold text-stone-700">Open Positions</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="text-xs text-stone-400 uppercase bg-stone-50/50">
              <tr>
                <th className="px-4 py-2.5 text-left">Ticker</th>
                <th className="px-4 py-2.5 text-right">Qty</th>
                <th className="px-4 py-2.5 text-right">Entry</th>
                <th className="px-4 py-2.5 text-right">Current</th>
                <th className="px-4 py-2.5 text-right">P&L</th>
                <th className="px-4 py-2.5 text-right">P&L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.ticker} className="border-t border-stone-100 hover:bg-stone-50">
                  <td className="px-4 py-3 font-semibold text-stone-800">{p.ticker}</td>
                  <td className="px-4 py-3 text-right text-stone-600">{p.qty}</td>
                  <td className="px-4 py-3 text-right text-stone-600">${p.entry_price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-stone-800 font-medium">${p.current_price.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right font-medium ${p.unrealized_pnl >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                    ${p.unrealized_pnl.toFixed(0)}
                  </td>
                  <td className={`px-4 py-3 text-right font-medium ${p.unrealized_pnl_pct >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                    {(p.unrealized_pnl_pct * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Signal Breakdown */}
      {regime && (
        <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold text-stone-700 mb-4">Regime Signals</h2>
          <div className="space-y-2.5">
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
