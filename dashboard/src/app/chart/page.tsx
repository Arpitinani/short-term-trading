"use client";

import { useState } from "react";

// Portfolio holdings (top by value) + key indices
const topHoldings = [
  "AMZN", "TSLA", "META", "VOO", "AMD", "GOOG", "DELL", "XLE",
  "SCHD", "NOW", "MSFT", "GLD", "SNAP", "ZS", "TSM", "ORCL", "VST",
  "AXON", "OKLO", "CRM", "DVN", "CEG", "BA", "RKLB", "MSTR",
];
const moreHoldings = [
  "SLV", "MBLY", "S", "IGV", "NEM", "B", "SLB", "OIH", "MP", "MOS",
  "NLR", "ALB", "CCJ", "GDXJ", "GDX", "SLVP", "ACHR", "KTOS", "BWXT",
  "SLI", "NOC", "ANGX", "UBER", "LAC", "SOXX", "LIT", "CIBR", "SKYY",
  "GBTC", "ASM", "HL", "KGC",
];
const indexTickers = ["SPY", "QQQ", "DIA", "IWM"];

const ranges = [
  { label: "1M", value: "1M" },
  { label: "3M", value: "3M" },
  { label: "6M", value: "6M" },
  { label: "YTD", value: "YTD" },
  { label: "1Y", value: "12M" },
  { label: "5Y", value: "60M" },
  { label: "All", value: "ALL" },
];

export default function ChartPage() {
  const [ticker, setTicker] = useState("SPY");
  const [range, setRange] = useState("12M");
  const [customTicker, setCustomTicker] = useState("");
  const [fullscreen, setFullscreen] = useState(false);

  const widgetUrl = `https://s.tradingview.com/widgetembed/?symbol=${ticker}&interval=D&theme=light&style=1&locale=en&toolbar_bg=%23fafaf9&enable_publishing=false&hide_side_toolbar=false&allow_symbol_change=true&show_popup_button=true&popup_width=1400&popup_height=800&range=${range}`;

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-[100] bg-white flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b border-stone-200 bg-stone-50">
          <div className="flex items-center gap-3">
            <span className="font-bold text-lg text-stone-800">{ticker}</span>
            <div className="flex gap-1">
              {ranges.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setRange(r.value)}
                  className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                    range === r.value
                      ? "bg-stone-800 text-white"
                      : "text-stone-500 hover:text-stone-700"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
          <button
            onClick={() => setFullscreen(false)}
            className="px-3 py-1 text-sm rounded-md border border-stone-300 text-stone-600 hover:bg-stone-100 transition-colors"
          >
            Exit Fullscreen
          </button>
        </div>
        <div className="flex-1">
          <iframe
            key={`${ticker}-${range}-fs`}
            src={widgetUrl}
            width="100%"
            height="100%"
            style={{ border: "none" }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-800">{ticker}</h1>
        <button
          onClick={() => setFullscreen(true)}
          className="px-3 py-1 text-sm rounded-md border border-stone-300 text-stone-600 hover:bg-stone-100 transition-colors"
        >
          Fullscreen
        </button>
      </div>

      {/* Ticker + Range selectors */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Indices */}
          <span className="text-xs text-stone-400 font-medium">Indices:</span>
          {indexTickers.map((t) => (
            <button key={t} onClick={() => setTicker(t)}
              className={`px-2.5 py-0.5 text-xs rounded-md border transition-colors ${
                ticker === t ? "border-blue-500 bg-blue-50 text-blue-700 font-medium" : "border-stone-200 text-stone-500 hover:border-stone-400"
              }`}>{t}</button>
          ))}

          <span className="text-stone-200">|</span>
          <span className="text-xs text-stone-400 font-medium">Portfolio:</span>
          {topHoldings.map((t) => (
            <button key={t} onClick={() => setTicker(t)}
              className={`px-2.5 py-0.5 text-xs rounded-md border transition-colors ${
                ticker === t ? "border-blue-500 bg-blue-50 text-blue-700 font-medium" : "border-stone-200 text-stone-500 hover:border-stone-400"
              }`}>{t}</button>
          ))}

          {/* More holdings dropdown */}
          <select
            value={moreHoldings.includes(ticker) ? ticker : ""}
            onChange={(e) => { if (e.target.value) setTicker(e.target.value); }}
            className={`px-2 py-0.5 text-xs rounded-md border bg-white focus:outline-none focus:border-blue-500 ${
              moreHoldings.includes(ticker) ? "border-blue-500 text-blue-700 font-medium" : "border-stone-200 text-stone-500"
            }`}
          >
            <option value="">More ({moreHoldings.length})</option>
            {moreHoldings.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          {/* Custom input */}
          <form onSubmit={(e) => { e.preventDefault(); if (customTicker.trim()) { setTicker(customTicker.trim().toUpperCase()); setCustomTicker(""); } }} className="flex gap-1">
            <input type="text" value={customTicker} onChange={(e) => setCustomTicker(e.target.value)}
              placeholder="Other..."
              className="w-20 px-2 py-0.5 text-xs bg-white border border-stone-300 rounded-md text-stone-600 placeholder-stone-400 focus:outline-none focus:border-blue-500" />
          </form>
        </div>

        {/* Date range */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-stone-400 font-medium">Range:</span>
          <div className="flex gap-1 border border-stone-200 rounded-lg p-0.5 bg-white">
            {ranges.map((r) => (
              <button key={r.value} onClick={() => setRange(r.value)}
                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                  range === r.value ? "bg-stone-800 text-white" : "text-stone-500 hover:text-stone-700 hover:bg-stone-50"
                }`}>{r.label}</button>
            ))}
          </div>
        </div>
      </div>

      {/* TradingView Chart */}
      <div
        className="rounded-xl overflow-hidden border border-stone-200 shadow-sm"
        style={{ height: "calc(100vh - 180px)", minHeight: 500 }}
      >
        <iframe
          key={`${ticker}-${range}`}
          src={widgetUrl}
          width="100%"
          height="100%"
          style={{ border: "none" }}
        />
      </div>
    </div>
  );
}
