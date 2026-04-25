"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ScreenerStock } from "@/lib/types";

export default function ScreenerPage() {
  const [results, setResults] = useState<ScreenerStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [minCriteria, setMinCriteria] = useState(7);
  const [universe, setUniverse] = useState("top20");
  const [hasRun, setHasRun] = useState(false);

  async function runScan() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getScreener(minCriteria, universe);
      setResults(data);
      setHasRun(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run screener");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Trend Template Screener</h1>
        <span className="text-xs text-stone-400">Minervini 8-Criteria</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm text-stone-500">Universe:</label>
          <select
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            className="bg-white border border-stone-300 rounded px-2 py-1 text-sm text-stone-600"
          >
            <option value="top20">Top 20 Stocks</option>
            <option value="sp500">S&P 500 (slow)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-stone-500">Min Criteria:</label>
          <select
            value={minCriteria}
            onChange={(e) => setMinCriteria(Number(e.target.value))}
            className="bg-white border border-stone-300 rounded px-2 py-1 text-sm text-stone-600"
          >
            {[8, 7, 6, 5].map((n) => (
              <option key={n} value={n}>
                {n}/8 {n === 8 ? "(strict)" : n === 6 ? "(relaxed)" : ""}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={runScan}
          disabled={loading}
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-stone-200 disabled:text-stone-400 text-stone-800 text-sm rounded-md transition-colors"
        >
          {loading ? "Scanning..." : "Run Scan"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {hasRun && !loading && (
        <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-stone-200 flex items-center justify-between">
            <h2 className="font-semibold">
              {results.length} stock{results.length !== 1 ? "s" : ""} found
            </h2>
            <span className="text-xs text-stone-400">
              {results.filter((r) => r.passes).length} pass all 8 criteria
            </span>
          </div>

          {results.length === 0 ? (
            <div className="px-4 py-8 text-center text-stone-400">
              No stocks passed {minCriteria}/8 criteria
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-stone-400 uppercase bg-white/50">
                  <tr>
                    <th className="px-4 py-2 text-left">Ticker</th>
                    <th className="px-4 py-2 text-center">Score</th>
                    <th className="px-4 py-2 text-right">Price</th>
                    <th className="px-4 py-2 text-right">RS Rank</th>
                    <th className="px-4 py-2 text-right">Above 52w Low</th>
                    <th className="px-4 py-2 text-right">Below 52w High</th>
                    <th className="px-4 py-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((stock) => (
                    <tr key={stock.ticker} className="border-t border-stone-200 hover:bg-stone-100/50">
                      <td className="px-4 py-3 font-medium">{stock.ticker}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                          stock.passes
                            ? "bg-emerald-100 text-emerald-600 border border-emerald-300"
                            : stock.criteria_met >= 7
                            ? "bg-amber-100 text-amber-700 border border-amber-300"
                            : "bg-stone-100 text-stone-500 border border-stone-300"
                        }`}>
                          {stock.criteria_met}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">${stock.price.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right">
                        {stock.rs_rank !== null ? (
                          <span className={stock.rs_rank >= 80 ? "text-emerald-600" : stock.rs_rank >= 60 ? "text-stone-600" : "text-stone-400"}>
                            {stock.rs_rank.toFixed(0)}
                          </span>
                        ) : (
                          <span className="text-stone-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600">
                        +{stock.pct_above_52w_low.toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-right text-stone-500">
                        -{stock.pct_below_52w_high.toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-center">
                        {stock.passes ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-600">
                            PASS
                          </span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-stone-100 text-stone-400">
                            {stock.criteria_met}/8
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {!hasRun && !loading && (
        <div className="bg-white border border-stone-200 rounded-lg p-8 text-center text-stone-400">
          <p>Click &quot;Run Scan&quot; to screen stocks against Minervini&apos;s Trend Template</p>
          <p className="text-xs mt-2">8 criteria: MA alignment, trend direction, relative strength, proximity to highs</p>
        </div>
      )}
    </div>
  );
}
