"use client";

import dynamic from "next/dynamic";
import type { TimeSeriesPoint } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface TurnoverChartProps {
  turnover:       TimeSeriesPoint[];
  relativeWealth: TimeSeriesPoint[];
}

export default function TurnoverChart({ turnover, relativeWealth }: TurnoverChartProps) {
  const baseLayout = {
    paper_bgcolor: "transparent",
    plot_bgcolor:  "transparent",
    font: { family: "Inter, sans-serif", color: "#94a3b8", size: 11 },
    margin: { l: 50, r: 20, t: 10, b: 40 },
    hovermode: "x unified" as const,
    hoverlabel: {
      bgcolor: "#112240", bordercolor: "#1e3a5f",
      font:    { color: "#f0f4ff", size: 12 },
    },
    xaxis: {
      gridcolor: "#1e3a5f", linecolor: "#1e3a5f",
      tickfont:  { color: "#475569", size: 10 },
      zeroline:  false,
    },
  };

  if (!turnover.length && !relativeWealth.length) {
    return (
      <div className="flex items-center justify-center h-48 text-text-muted text-sm">
        No data — train the model first
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Relative Wealth */}
      {relativeWealth.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-3">
            Relative Wealth — SPT / Market
          </p>
          <Plot
            data={[
              {
                x: relativeWealth.map((d) => d.date),
                y: relativeWealth.map((d) => d.value),
                name: "Relative Wealth",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
                fill: "tozeroy",
                fillcolor: "rgba(16,185,129,0.05)",
              } as any,
              {
                x: relativeWealth.map((d) => d.date),
                y: relativeWealth.map(() => 1.0),
                name: "Market baseline",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 1, dash: "dash" },
              } as any,
            ]}
            layout={{
              ...baseLayout,
              yaxis: {
                gridcolor: "#1e3a5f", linecolor: "#1e3a5f",
                tickfont:  { color: "#475569", size: 10 },
                zeroline:  false,
              },
              legend: {
                bgcolor: "rgba(13,27,46,0.8)", bordercolor: "#1e3a5f",
                borderwidth: 1, font: { size: 11, color: "#94a3b8" },
                x: 0.01, y: 0.99,
              },
            } as any}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: "220px" }}
          />
        </div>
      )}

      {/* Turnover */}
      {turnover.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-3">
            Portfolio Turnover (rebalance days)
          </p>
          <Plot
            data={[
              {
                x: turnover.map((d) => d.date),
                y: turnover.map((d) => d.value),
                name: "Turnover",
                type: "bar",
                marker: { color: "#f59e0b", opacity: 0.8 },
              } as any,
            ]}
            layout={{
              ...baseLayout,
              yaxis: {
                gridcolor: "#1e3a5f", linecolor: "#1e3a5f",
                tickfont:  { color: "#475569", size: 10 },
                zeroline:  false,
              },
              bargap: 0.3,
            } as any}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: "200px" }}
          />
        </div>
      )}
    </div>
  );
}
