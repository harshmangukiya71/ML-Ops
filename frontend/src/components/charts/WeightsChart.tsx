"use client";

import dynamic from "next/dynamic";
import type { StockAllocation } from "@/lib/api";
import { tickerColor } from "@/lib/utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface WeightsChartProps {
  allocations: StockAllocation[];
}

export default function WeightsChart({ allocations }: WeightsChartProps) {
  if (!allocations.length) {
    return (
      <div className="flex items-center justify-center h-64 text-text-muted text-sm">
        No holdings
      </div>
    );
  }

  const labels = allocations.map((a) => a.ticker.replace(".NS", ""));
  const values = allocations.map((a) => a.weight);
  const colors = allocations.map((a) => tickerColor(a.ticker));

  return (
    <Plot
      data={[
        {
          type:        "pie",
          labels,
          values,
          marker:      { colors, line: { color: "#0d1b2e", width: 2 } },
          textinfo:    "label+percent",
          textfont:    { color: "#f0f4ff", size: 11 },
          hovertemplate: "<b>%{label}</b><br>Weight: %{percent}<extra></extra>",
          hole:         0.5,
        } as any,
      ]}
      layout={{
        paper_bgcolor: "transparent",
        plot_bgcolor:  "transparent",
        showlegend:    false,
        margin:        { l: 10, r: 10, t: 10, b: 10 },
        annotations: [{
          font:  { size: 13, color: "#94a3b8", family: "Inter" },
          showarrow: false,
          text:  `${allocations.length} stocks`,
          x: 0.5, y: 0.5,
          xref: "paper", yref: "paper",
        }],
      } as any}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "260px" }}
    />
  );
}
