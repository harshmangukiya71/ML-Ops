"use client";

import { formatINR, formatPercent, tickerColor } from "@/lib/utils";
import type { StockAllocation } from "@/lib/api";
import { Trash2, TrendingUp } from "lucide-react";

interface AllocationTableProps {
  allocations: StockAllocation[];
  capital:     number;
  onRemove?:   (ticker: string) => void;
  loading?:    boolean;
}

export default function AllocationTable({
  allocations,
  capital,
  onRemove,
  loading,
}: AllocationTableProps) {
  if (!allocations.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <TrendingUp className="w-10 h-10 text-text-muted mb-3" />
        <p className="text-text-secondary font-medium">No stocks in portfolio</p>
        <p className="text-text-muted text-sm mt-1">Add stocks to get started</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Stock</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Weight</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Allocation (₹)</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Distribution</th>
            {onRemove && <th className="py-3 px-4" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {allocations.map((a) => {
            const color = tickerColor(a.ticker);
            const pct   = a.weight * 100;
            return (
              <tr
                key={a.ticker}
                className="group hover:bg-bg-tertiary/50 transition-colors duration-150"
              >
                {/* Ticker */}
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-bg-primary flex-shrink-0"
                      style={{ background: color }}
                    >
                      {a.ticker.slice(0, 2)}
                    </div>
                    <div>
                      <p className="font-semibold text-text-primary font-mono">
                        {a.ticker.replace(".NS", "")}
                      </p>
                      <p className="text-xs text-text-muted">{a.ticker}</p>
                    </div>
                  </div>
                </td>

                {/* Weight */}
                <td className="py-3 px-4 text-right">
                  <span className="font-mono font-semibold text-text-primary">
                    {formatPercent(a.weight)}
                  </span>
                </td>

                {/* Allocation */}
                <td className="py-3 px-4 text-right">
                  <span className="font-mono text-accent-cyan font-semibold">
                    {formatINR(a.allocation_inr)}
                  </span>
                </td>

                {/* Bar */}
                <td className="py-3 px-4 min-w-[120px]">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-bg-tertiary rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: color }}
                      />
                    </div>
                    <span className="text-xs text-text-muted w-10 text-right">
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                </td>

                {/* Remove */}
                {onRemove && (
                  <td className="py-3 px-4">
                    <button
                      onClick={() => onRemove(a.ticker)}
                      disabled={loading}
                      className="btn-danger opacity-0 group-hover:opacity-100 transition-opacity duration-150"
                      title={`Remove ${a.ticker}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>

        {/* Footer */}
        <tfoot>
          <tr className="border-t border-border">
            <td className="py-3 px-4 text-sm font-semibold text-text-secondary">Total</td>
            <td className="py-3 px-4 text-right font-mono font-bold text-text-primary">
              {formatPercent(allocations.reduce((s, a) => s + a.weight, 0))}
            </td>
            <td className="py-3 px-4 text-right font-mono font-bold text-accent-cyan">
              {formatINR(capital)}
            </td>
            <td colSpan={onRemove ? 2 : 1} />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
