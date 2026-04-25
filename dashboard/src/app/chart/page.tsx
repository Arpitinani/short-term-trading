"use client";

import { useState } from "react";

const defaultTickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"];

export default function ChartPage() {
  const [ticker, setTicker] = useState("SPY");
  const [customTicker, setCustomTicker] = useState("");

  const widgetUrl = `https://s.tradingview.com/widgetembed/?symbol=${ticker}&interval=D&theme=light&style=1&locale=en&toolbar_bg=%23fafaf9&enable_publishing=false&hide_side_toolbar=false&allow_symbol_change=true&studies=%5B%5D&show_popup_button=true&popup_width=1000&popup_height=650`;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-800">{ticker}</h1>
      </div>

      {/* Ticker selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {defaultTickers.map((t) => (
          <button
            key={t}
            onClick={() => setTicker(t)}
            className={`px-3 py-1 text-sm rounded-md border transition-colors ${
              ticker === t
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-stone-300 text-stone-500 hover:border-stone-400 hover:text-stone-700"
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
            className="w-24 px-2 py-1 text-sm bg-white border border-stone-300 rounded-md text-stone-600 placeholder-stone-400 focus:outline-none focus:border-blue-500"
          />
        </form>
      </div>

      {/* TradingView Advanced Chart Widget */}
      <div className="rounded-xl overflow-hidden border border-stone-200 shadow-sm" style={{ height: 600 }}>
        <iframe
          key={ticker}
          src={widgetUrl}
          width="100%"
          height="100%"
          frameBorder="0"
          allowTransparency
          allow="encrypted-media"
          style={{ border: "none" }}
        />
      </div>

      <p className="text-xs text-stone-400 text-center">
        Full TradingView charting — add indicators, draw trendlines, change timeframes directly on the chart
      </p>
    </div>
  );
}
