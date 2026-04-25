export interface RegimeData {
  regime: "risk_on" | "bullish" | "cautious" | "risk_off";
  score: number;
  max_position_pct: number;
  max_heat_pct: number;
  allowed_strategies: string[];
  signals: Record<string, number>;
  timestamp: string;
}

export interface ScanResult {
  timestamp: string;
  regime: string;
  regime_score: number;
  signals_count: number;
  orders_placed: number;
  orders_skipped: number;
  positions_closed: number;
  summary: string;
}

export interface ScreenerStock {
  ticker: string;
  passes: boolean;
  criteria_met: number;
  price: number;
  rs_rank: number | null;
  pct_above_52w_low: number;
  pct_below_52w_high: number;
}

export interface BacktestMetrics {
  total_trades: number;
  win_rate: number;
  avg_win_pct: number;
  avg_loss_pct: number;
  avg_trade_pct: number;
  avg_bars_held: number;
  profit_factor: number;
  expectancy: number;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  total_costs: number;
}

export interface BacktestResponse {
  strategy: string;
  ticker: string;
  metrics: BacktestMetrics;
  trade_count: number;
}

export interface PositionData {
  ticker: string;
  qty: number;
  side: string;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface AccountData {
  equity: number;
  cash: number;
  buying_power: number;
  portfolio_value: number;
  is_paper: boolean;
}
