"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Trade {
  id: number;
  timestamp: string;
  ticker: string;
  strategy: string;
  action: string;
  qty: number;
  entry_price: number;
  stop_price: number;
  target_price: number | null;
  order_id: string;
  order_status: string;
  status: string;
}

const strategyLabels: Record<string, string> = {
  connors_rsi2: "RSI(2)",
  turtle_system2: "Turtle",
};

export default function HistoryPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStrategy, setFilterStrategy] = useState<string>("all");

  useEffect(() => {
    loadTrades();
  }, []);

  async function loadTrades() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/trades`);
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      setTrades(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  const filtered = filterStrategy === "all"
    ? trades
    : trades.filter((t) => t.strategy === filterStrategy);

  const strategies = [...new Set(trades.map((t) => t.strategy))];
  const totalValue = filtered.reduce((sum, t) => sum + t.qty * t.entry_price, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-800">Trade History</h1>
          <p className="text-sm text-stone-400 mt-0.5">All executed trades from paper trading</p>
        </div>
        <button
          onClick={loadTrades}
          className="px-3 py-1.5 text-sm border border-stone-300 rounded-lg text-stone-600 hover:bg-stone-100 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-stone-400 uppercase tracking-wider">Total Trades</div>
          <div className="text-3xl font-bold text-stone-800 mt-1">{filtered.length}</div>
        </div>
        <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-stone-400 uppercase tracking-wider">Unique Tickers</div>
          <div className="text-3xl font-bold text-stone-800 mt-1">
            {new Set(filtered.map((t) => t.ticker)).size}
          </div>
        </div>
        <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-stone-400 uppercase tracking-wider">Total Deployed</div>
          <div className="text-2xl font-bold text-stone-800 mt-1">${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm">
          <div className="text-xs text-stone-400 uppercase tracking-wider">Strategies Used</div>
          <div className="text-3xl font-bold text-stone-800 mt-1">{strategies.length}</div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-stone-500">Filter:</span>
        <button
          onClick={() => setFilterStrategy("all")}
          className={`px-3 py-1 text-xs rounded-md border transition-colors ${
            filterStrategy === "all" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-stone-200 text-stone-500"
          }`}
        >
          All
        </button>
        {strategies.map((s) => (
          <button
            key={s}
            onClick={() => setFilterStrategy(s)}
            className={`px-3 py-1 text-xs rounded-md border transition-colors ${
              filterStrategy === s ? "border-blue-500 bg-blue-50 text-blue-700" : "border-stone-200 text-stone-500"
            }`}
          >
            {strategyLabels[s] || s}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-600 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center text-stone-400">
          Loading trades...
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center text-stone-500">
          <p>No trades yet.</p>
          <p className="text-xs text-stone-400 mt-2">Go to the Signals page, scan for signals, and click Execute to place your first trade.</p>
        </div>
      ) : (
        <div className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-stone-400 uppercase bg-stone-50 border-b border-stone-200">
                <tr>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Ticker</th>
                  <th className="px-4 py-3 text-left">Strategy</th>
                  <th className="px-4 py-3 text-left">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Entry</th>
                  <th className="px-4 py-3 text-right">Stop</th>
                  <th className="px-4 py-3 text-right">Target</th>
                  <th className="px-4 py-3 text-right">Value</th>
                  <th className="px-4 py-3 text-center">Order Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id} className="border-t border-stone-100 hover:bg-stone-50">
                    <td className="px-4 py-3 text-stone-500 text-xs">
                      {new Date(t.timestamp).toLocaleDateString()}{" "}
                      {new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="px-4 py-3 font-semibold text-stone-800">{t.ticker}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        t.strategy === "connors_rsi2" ? "bg-blue-100 text-blue-700" : "bg-emerald-100 text-emerald-700"
                      }`}>
                        {strategyLabels[t.strategy] || t.strategy}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 uppercase">
                        {t.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-stone-700">{t.qty}</td>
                    <td className="px-4 py-3 text-right font-mono text-stone-700">${t.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono text-red-600">${t.stop_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-600">
                      {t.target_price ? `$${t.target_price.toFixed(2)}` : "-"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-stone-700">
                      ${(t.qty * t.entry_price).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        t.order_status.includes("filled") || t.order_status.includes("FILLED")
                          ? "bg-emerald-100 text-emerald-700"
                          : t.order_status.includes("accepted") || t.order_status.includes("ACCEPTED")
                          ? "bg-amber-100 text-amber-700"
                          : "bg-stone-100 text-stone-600"
                      }`}>
                        {t.order_status.replace("OrderStatus.", "")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
