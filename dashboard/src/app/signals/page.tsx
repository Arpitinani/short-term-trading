"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Signal {
  ticker: string;
  strategy: string;
  action: string;
  entry_price: number;
  stop_price: number;
  target_price: number | null;
  risk_pct: number;
  reward_risk: number | null;
  reason: string;
}

const strategyLabels: Record<string, string> = {
  connors_rsi2: "RSI(2)",
  turtle_system2: "Turtle",
};

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);
  const [scanTime, setScanTime] = useState("");

  async function runScan() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/signals`);
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setSignals(data);
      setHasRun(true);
      setScanTime(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to scan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-800">Signals</h1>
          <p className="text-sm text-stone-400 mt-0.5">Scan 34 stocks for RSI(2) and Turtle breakout signals</p>
        </div>
        <div className="flex items-center gap-3">
          {scanTime && <span className="text-xs text-stone-400">Last scan: {scanTime}</span>}
          <button
            onClick={runScan}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-stone-300 disabled:text-stone-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? "Scanning..." : "Scan Now"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-600 text-sm">{error}</div>
      )}

      {loading && (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center">
          <div className="text-stone-400">Scanning universe... this may take a minute</div>
        </div>
      )}

      {hasRun && !loading && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-stone-400 uppercase tracking-wider">Total Signals</div>
              <div className="text-3xl font-bold text-stone-800 mt-1">{signals.length}</div>
            </div>
            <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-stone-400 uppercase tracking-wider">RSI(2) Signals</div>
              <div className="text-3xl font-bold text-blue-600 mt-1">
                {signals.filter((s) => s.strategy === "connors_rsi2").length}
              </div>
            </div>
            <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs text-stone-400 uppercase tracking-wider">Turtle Signals</div>
              <div className="text-3xl font-bold text-emerald-600 mt-1">
                {signals.filter((s) => s.strategy === "turtle_system2").length}
              </div>
            </div>
          </div>

          {/* Signals Table */}
          {signals.length === 0 ? (
            <div className="bg-white border border-stone-200 rounded-xl p-8 text-center text-stone-500">
              No signals found. Market may be quiet or regime is filtering strategies.
            </div>
          ) : (
            <div className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-xs text-stone-400 uppercase bg-stone-50 border-b border-stone-200">
                    <tr>
                      <th className="px-4 py-3 text-left">Ticker</th>
                      <th className="px-4 py-3 text-left">Strategy</th>
                      <th className="px-4 py-3 text-left">Action</th>
                      <th className="px-4 py-3 text-right">Entry</th>
                      <th className="px-4 py-3 text-right">Stop</th>
                      <th className="px-4 py-3 text-right">Target</th>
                      <th className="px-4 py-3 text-right">Risk %</th>
                      <th className="px-4 py-3 text-right">R:R</th>
                      <th className="px-4 py-3 text-left">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {signals.map((s, i) => (
                      <tr key={`${s.ticker}-${s.strategy}-${i}`} className="border-t border-stone-100 hover:bg-stone-50">
                        <td className="px-4 py-3 font-semibold text-stone-800">{s.ticker}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            s.strategy === "connors_rsi2"
                              ? "bg-blue-100 text-blue-700"
                              : "bg-emerald-100 text-emerald-700"
                          }`}>
                            {strategyLabels[s.strategy] || s.strategy}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 uppercase">
                            {s.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-stone-700">${s.entry_price.toFixed(2)}</td>
                        <td className="px-4 py-3 text-right font-mono text-red-600">${s.stop_price.toFixed(2)}</td>
                        <td className="px-4 py-3 text-right font-mono text-emerald-600">
                          {s.target_price ? `$${s.target_price.toFixed(2)}` : "-"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`font-medium ${s.risk_pct > 5 ? "text-red-600" : s.risk_pct > 3 ? "text-amber-600" : "text-stone-600"}`}>
                            {s.risk_pct.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {s.reward_risk ? (
                            <span className={`font-medium ${s.reward_risk >= 2 ? "text-emerald-600" : "text-stone-500"}`}>
                              {s.reward_risk.toFixed(1)}:1
                            </span>
                          ) : "-"}
                        </td>
                        <td className="px-4 py-3 text-xs text-stone-500 max-w-xs truncate">{s.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!hasRun && !loading && (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center">
          <p className="text-stone-500">Click &quot;Scan Now&quot; to find trading signals across your portfolio and key stocks</p>
          <p className="text-xs text-stone-400 mt-2">Scans RSI(2) mean reversion + Turtle 55-day breakout</p>
        </div>
      )}
    </div>
  );
}
