"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  type IChartApi,
  ColorType,
} from "lightweight-charts";

interface OHLCVBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema9: number | null;
  ema21: number | null;
  sma200: number | null;
}

interface CandlestickChartProps {
  data: OHLCVBar[];
  ticker: string;
  height?: number;
}

export default function CandlestickChart({ data, ticker, height = 500 }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0a0a0a" },
        textColor: "#9ca3af",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: "#374151",
      },
      timeScale: {
        borderColor: "#374151",
        timeVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height,
    });

    chartRef.current = chart;

    // Candlestick series (v5 API: chart.addSeries(Type, options))
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    candleSeries.setData(
      data.map((d) => ({
        time: d.time as unknown as import("lightweight-charts").Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }))
    );

    // EMA 9 (yellow)
    const ema9Series = chart.addSeries(LineSeries, {
      color: "#eab308",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema9Series.setData(
      data
        .filter((d) => d.ema9 !== null)
        .map((d) => ({ time: d.time as unknown as import("lightweight-charts").Time, value: d.ema9! }))
    );

    // EMA 21 (cyan)
    const ema21Series = chart.addSeries(LineSeries, {
      color: "#06b6d4",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    ema21Series.setData(
      data
        .filter((d) => d.ema21 !== null)
        .map((d) => ({ time: d.time as unknown as import("lightweight-charts").Time, value: d.ema21! }))
    );

    // SMA 200 (purple, dashed)
    const sma200Series = chart.addSeries(LineSeries, {
      color: "#a855f7",
      lineWidth: 1,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    sma200Series.setData(
      data
        .filter((d) => d.sma200 !== null)
        .map((d) => ({ time: d.time as unknown as import("lightweight-charts").Time, value: d.sma200! }))
    );

    // Volume histogram
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#374151",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(
      data.map((d) => ({
        time: d.time as unknown as import("lightweight-charts").Time,
        value: d.volume,
        color: d.close >= d.open ? "#22c55e33" : "#ef444433",
      }))
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, height]);

  return (
    <div>
      <div className="flex items-center gap-4 mb-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-yellow-500 inline-block" /> EMA 9
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-cyan-500 inline-block" /> EMA 21
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-purple-500 inline-block" /> SMA 200
        </span>
      </div>
      <div ref={chartContainerRef} className="rounded-lg overflow-hidden border border-gray-800" />
    </div>
  );
}
