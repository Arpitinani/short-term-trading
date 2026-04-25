"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { BacktestResponse } from "@/lib/types";

const strategies = [
  {
    id: "connors_rsi2",
    name: "Connors RSI(2)",
    description: "Mean reversion — buy oversold pullbacks in uptrends",
    defaultParams: { rsi_period: 2, sma_period: 200, entry_threshold: 5, exit_threshold: 65 },
  },
  {
    id: "turtle_system2",
    name: "Turtle System 2",
    description: "Trend following — 55-day breakout with ATR stops",
    defaultParams: { entry_period: 55, exit_period: 20, atr_period: 20, atr_stop_mult: 2.0, long_only: true },
  },
];

function MetricRow({ label, value, good }: { label: string; value: string; good?: boolean | null }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className={`font-mono text-sm ${good === true ? "text-green-400" : good === false ? "text-red-400" : "text-gray-200"}`}>
        {value}
      </span>
    </div>
  );
}

export default function BacktestPage() {
  const [selectedStrategy, setSelectedStrategy] = useState(strategies[0]);
  const [ticker, setTicker] = useState("SPY");
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runBacktest() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runBacktest(selectedStrategy.id, ticker, selectedStrategy.defaultParams);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run backtest");
    } finally {
      setLoading(false);
    }
  }

  const m = result?.metrics;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Backtest</h1>

      {/* Strategy selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {strategies.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelectedStrategy(s)}
            className={`text-left p-4 rounded-lg border transition-colors ${
              selectedStrategy.id === s.id
                ? "border-blue-500 bg-blue-500/10"
                : "border-gray-800 bg-gray-900 hover:border-gray-700"
            }`}
          >
            <div className="font-semibold">{s.name}</div>
            <div className="text-xs text-gray-500 mt-1">{s.description}</div>
          </button>
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Ticker:</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="w-20 px-2 py-1 text-sm bg-gray-900 border border-gray-700 rounded text-gray-300 focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={runBacktest}
          disabled={loading}
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-md transition-colors"
        >
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {m && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Trade Metrics */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h2 className="font-semibold mb-3">Trade Metrics</h2>
            <MetricRow label="Total Trades" value={String(m.total_trades)} />
            <MetricRow label="Win Rate" value={`${(m.win_rate * 100).toFixed(1)}%`} good={m.win_rate > 0.5} />
            <MetricRow label="Avg Win" value={`${(m.avg_win_pct * 100).toFixed(2)}%`} good={true} />
            <MetricRow label="Avg Loss" value={`${(m.avg_loss_pct * 100).toFixed(2)}%`} good={false} />
            <MetricRow label="Avg Trade" value={`${(m.avg_trade_pct * 100).toFixed(2)}%`} good={m.avg_trade_pct > 0} />
            <MetricRow label="Profit Factor" value={m.profit_factor.toFixed(2)} good={m.profit_factor > 1.5} />
            <MetricRow label="Expectancy" value={`$${m.expectancy.toFixed(0)}`} good={m.expectancy > 0} />
            <MetricRow label="Avg Bars Held" value={m.avg_bars_held.toFixed(1)} />
          </div>

          {/* Portfolio Metrics */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h2 className="font-semibold mb-3">Portfolio Metrics</h2>
            <MetricRow label="Total Return" value={`${(m.total_return * 100).toFixed(1)}%`} good={m.total_return > 0} />
            <MetricRow label="Annual Return" value={`${(m.annual_return * 100).toFixed(1)}%`} good={m.annual_return > 0} />
            <MetricRow label="Sharpe Ratio" value={m.sharpe_ratio.toFixed(2)} good={m.sharpe_ratio > 1} />
            <MetricRow label="Sortino Ratio" value={m.sortino_ratio.toFixed(2)} good={m.sortino_ratio > 1} />
            <MetricRow label="Max Drawdown" value={`${(m.max_drawdown * 100).toFixed(1)}%`} good={m.max_drawdown > -0.2} />
            <MetricRow label="Max DD Duration" value={`${m.max_drawdown_duration} days`} />
            <MetricRow label="Total Costs" value={`$${m.total_costs.toFixed(0)}`} />
          </div>
        </div>
      )}

      {/* Strategy Parameters */}
      {result && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Parameters Used</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(selectedStrategy.defaultParams).map(([key, value]) => (
              <span key={key} className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-300">
                {key}: {String(value)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
