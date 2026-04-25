const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res.json();
}

export const api = {
  getRegime: () =>
    fetchApi<import("./types").RegimeData>("/regime"),

  runScan: () =>
    fetchApi<import("./types").ScanResult>("/scan"),

  getScreener: (minCriteria = 7, universe = "top20") =>
    fetchApi<import("./types").ScreenerStock[]>(
      `/screener?min_criteria=${minCriteria}&universe=${universe}`
    ),

  runBacktest: (strategy: string, ticker: string, params?: Record<string, unknown>) =>
    fetchApi<import("./types").BacktestResponse>("/backtest", {
      method: "POST",
      body: JSON.stringify({ strategy, ticker, period: "max", params }),
    }),

  getPositions: () =>
    fetchApi<import("./types").PositionData[]>("/positions"),

  getAccount: () =>
    fetchApi<import("./types").AccountData>("/account"),

  getStatus: () =>
    fetchApi<Record<string, unknown>>("/status"),
};
