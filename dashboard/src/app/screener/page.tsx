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
        <span className="text-xs text-gray-500">Minervini 8-Criteria</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Universe:</label>
          <select
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300"
          >
            <option value="top20">Top 20 Stocks</option>
            <option value="sp500">S&P 500 (slow)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Min Criteria:</label>
          <select
            value={minCriteria}
            onChange={(e) => setMinCriteria(Number(e.target.value))}
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300"
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
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded-md transition-colors"
        >
          {loading ? "Scanning..." : "Run Scan"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {hasRun && !loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
            <h2 className="font-semibold">
              {results.length} stock{results.length !== 1 ? "s" : ""} found
            </h2>
            <span className="text-xs text-gray-500">
              {results.filter((r) => r.passes).length} pass all 8 criteria
            </span>
          </div>

          {results.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              No stocks passed {minCriteria}/8 criteria
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-gray-500 uppercase bg-gray-900/50">
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
                    <tr key={stock.ticker} className="border-t border-gray-800 hover:bg-gray-800/50">
                      <td className="px-4 py-3 font-medium">{stock.ticker}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                          stock.passes
                            ? "bg-green-500/20 text-green-400 border border-green-800"
                            : stock.criteria_met >= 7
                            ? "bg-amber-500/20 text-amber-400 border border-amber-800"
                            : "bg-gray-500/20 text-gray-400 border border-gray-700"
                        }`}>
                          {stock.criteria_met}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">${stock.price.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right">
                        {stock.rs_rank !== null ? (
                          <span className={stock.rs_rank >= 80 ? "text-green-400" : stock.rs_rank >= 60 ? "text-gray-300" : "text-gray-500"}>
                            {stock.rs_rank.toFixed(0)}
                          </span>
                        ) : (
                          <span className="text-gray-600">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-green-400">
                        +{stock.pct_above_52w_low.toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-right text-gray-400">
                        -{stock.pct_below_52w_high.toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-center">
                        {stock.passes ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">
                            PASS
                          </span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-500/20 text-gray-500">
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
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center text-gray-500">
          <p>Click &quot;Run Scan&quot; to screen stocks against Minervini&apos;s Trend Template</p>
          <p className="text-xs mt-2">8 criteria: MA alignment, trend direction, relative strength, proximity to highs</p>
        </div>
      )}
    </div>
  );
}
