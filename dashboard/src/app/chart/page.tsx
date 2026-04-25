"use client";

import { useEffect, useState } from "react";
import CandlestickChart from "@/components/CandlestickChart";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const defaultTickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"];
const periods = [
  { value: "6mo", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "2y", label: "2Y" },
  { value: "5y", label: "5Y" },
  { value: "max", label: "Max" },
];

export default function ChartPage() {
  const [ticker, setTicker] = useState("SPY");
  const [period, setPeriod] = useState("1y");
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [customTicker, setCustomTicker] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/ohlcv?ticker=${ticker}&period=${period}`);
        if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
        const json = await res.json();
        setData(json.data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load chart data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [ticker, period]);

  const lastBar = data.length > 0 ? data[data.length - 1] : null;
  const prevBar = data.length > 1 ? data[data.length - 2] : null;
  const dayChange = lastBar && prevBar ? lastBar.close - prevBar.close : 0;
  const dayChangePct = prevBar ? (dayChange / prevBar.close) * 100 : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">{ticker}</h1>
          {lastBar && (
            <div className="flex items-center gap-2">
              <span className="text-2xl">${lastBar.close.toFixed(2)}</span>
              <span className={`text-sm ${dayChange >= 0 ? "text-green-400" : "text-red-400"}`}>
                {dayChange >= 0 ? "+" : ""}{dayChange.toFixed(2)} ({dayChangePct.toFixed(1)}%)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Ticker selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {defaultTickers.map((t) => (
          <button
            key={t}
            onClick={() => setTicker(t)}
            className={`px-3 py-1 text-sm rounded-md border transition-colors ${
              ticker === t
                ? "border-blue-500 bg-blue-500/20 text-blue-400"
                : "border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300"
            }`}
          >
            {t}
          </button>
        ))}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (customTicker.trim()) {
              setTicker(customTicker.trim().toUpperCase());
              setCustomTicker("");
            }
          }}
          className="flex gap-1"
        >
          <input
            type="text"
            value={customTicker}
            onChange={(e) => setCustomTicker(e.target.value)}
            placeholder="Custom..."
            className="w-24 px-2 py-1 text-sm bg-gray-900 border border-gray-700 rounded-md text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500"
          />
        </form>

        <div className="ml-auto flex gap-1">
          {periods.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                period === p.value
                  ? "bg-gray-700 text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="flex items-center justify-center h-[500px] bg-gray-900 border border-gray-800 rounded-lg">
          <div className="text-gray-500">Loading chart...</div>
        </div>
      ) : error ? (
        <div className="bg-red-950 border border-red-800 rounded-lg p-4 text-red-400">
          {error}
        </div>
      ) : (
        <CandlestickChart data={data} ticker={ticker} height={500} />
      )}

      {/* Price info */}
      {lastBar && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
          {[
            { label: "Open", value: `$${lastBar.open.toFixed(2)}` },
            { label: "High", value: `$${lastBar.high.toFixed(2)}` },
            { label: "Low", value: `$${lastBar.low.toFixed(2)}` },
            { label: "Close", value: `$${lastBar.close.toFixed(2)}` },
            { label: "Volume", value: lastBar.volume.toLocaleString() },
          ].map((item) => (
            <div key={item.label} className="bg-gray-900 border border-gray-800 rounded p-2">
              <div className="text-xs text-gray-500">{item.label}</div>
              <div className="font-medium">{item.value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
