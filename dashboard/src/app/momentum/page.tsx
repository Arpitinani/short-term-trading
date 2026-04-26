"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MomentumRank {
  ticker: string;
  return_12m: number;
  return_1m: number;
  momentum_score: number;
  rank: number;
  percentile: number;
}

export default function MomentumPage() {
  const [ranks, setRanks] = useState<MomentumRank[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  async function runRanking() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/momentum`);
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      setRanks(await res.json());
      setHasRun(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  const topMomentum = ranks.filter((r) => r.percentile >= 60);
  const weakMomentum = ranks.filter((r) => r.percentile < 40);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-800">Momentum Ranking</h1>
          <p className="text-sm text-stone-400 mt-0.5">12-1 month momentum factor (Jegadeesh & Titman 1993)</p>
        </div>
        <button
          onClick={runRanking}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-stone-300 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {loading ? "Ranking..." : "Run Ranking"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-600 text-sm">{error}</div>
      )}

      {loading && (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center text-stone-400">
          Downloading price data and computing momentum... this takes ~30 seconds
        </div>
      )}

      {hasRun && !loading && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
              <div className="text-xs text-emerald-600 uppercase tracking-wider font-medium">Strong Momentum</div>
              <div className="text-3xl font-bold text-emerald-700 mt-1">{topMomentum.length}</div>
              <div className="text-xs text-emerald-500 mt-1">Percentile 60+</div>
            </div>
            <div className="bg-white border border-stone-200 rounded-xl p-4">
              <div className="text-xs text-stone-400 uppercase tracking-wider font-medium">Total Ranked</div>
              <div className="text-3xl font-bold text-stone-800 mt-1">{ranks.length}</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="text-xs text-red-600 uppercase tracking-wider font-medium">Weak Momentum</div>
              <div className="text-3xl font-bold text-red-700 mt-1">{weakMomentum.length}</div>
              <div className="text-xs text-red-500 mt-1">Percentile &lt;40</div>
            </div>
          </div>

          {/* Rankings Table */}
          <div className="bg-white border border-stone-200 rounded-xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-stone-100 bg-stone-50">
              <h2 className="font-semibold text-stone-700">Rankings (12-month return minus last month)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-stone-400 uppercase bg-stone-50 border-b border-stone-200">
                  <tr>
                    <th className="px-4 py-3 text-center w-16">Rank</th>
                    <th className="px-4 py-3 text-left">Ticker</th>
                    <th className="px-4 py-3 text-right">12M Return</th>
                    <th className="px-4 py-3 text-right">1M Return</th>
                    <th className="px-4 py-3 text-right">Momentum Score</th>
                    <th className="px-4 py-3 text-center">Percentile</th>
                    <th className="px-4 py-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {ranks.map((r) => (
                    <tr key={r.ticker} className={`border-t border-stone-100 hover:bg-stone-50 ${
                      r.percentile >= 60 ? "" : r.percentile < 40 ? "opacity-50" : ""
                    }`}>
                      <td className="px-4 py-3 text-center font-mono text-stone-500">{r.rank}</td>
                      <td className="px-4 py-3 font-semibold text-stone-800">{r.ticker}</td>
                      <td className={`px-4 py-3 text-right font-mono ${r.return_12m >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        {r.return_12m > 0 ? "+" : ""}{r.return_12m.toFixed(1)}%
                      </td>
                      <td className={`px-4 py-3 text-right font-mono ${r.return_1m >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        {r.return_1m > 0 ? "+" : ""}{r.return_1m.toFixed(1)}%
                      </td>
                      <td className={`px-4 py-3 text-right font-mono font-medium ${r.momentum_score >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                        {r.momentum_score > 0 ? "+" : ""}{r.momentum_score.toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 h-2 bg-stone-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                r.percentile >= 60 ? "bg-emerald-500" : r.percentile >= 40 ? "bg-amber-400" : "bg-red-400"
                              }`}
                              style={{ width: `${r.percentile}%` }}
                            />
                          </div>
                          <span className="text-xs text-stone-500 w-8">{r.percentile.toFixed(0)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {r.percentile >= 60 ? (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                            Strong
                          </span>
                        ) : r.percentile >= 40 ? (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-stone-100 text-stone-600">
                            Neutral
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-600">
                            Weak
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="text-xs text-stone-400 text-center">
            Strong momentum stocks (top 60%) are prioritized for trading signals. Weak momentum stocks are avoided.
          </p>
        </>
      )}

      {!hasRun && !loading && (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center">
          <p className="text-stone-500">Click &quot;Run Ranking&quot; to rank stocks by 12-1 month momentum</p>
          <p className="text-xs text-stone-400 mt-2">Academically verified factor — stocks with strong trailing momentum tend to continue outperforming</p>
        </div>
      )}
    </div>
  );
}
