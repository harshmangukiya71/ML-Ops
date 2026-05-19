import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/** Format a number as Indian Rupee string. */
export function formatINR(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

/** Format a decimal as percentage string. */
export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/** Format a decimal ratio (e.g. Sharpe) to fixed decimals. */
export function formatRatio(value: number, decimals = 3): string {
  return value.toFixed(decimals);
}

/** Color class for a metric value (positive = green, negative = red). */
export function metricColor(value: number): string {
  if (value > 0) return "text-success";
  if (value < 0) return "text-danger";
  return "text-text-secondary";
}

/** Truncate a string to maxLen with ellipsis. */
export function truncate(str: string, maxLen = 20): string {
  return str.length > maxLen ? str.slice(0, maxLen) + "…" : str;
}

/** Generate a consistent color for a ticker symbol. */
export function tickerColor(ticker: string): string {
  const colors = [
    "#00d4ff", "#7c3aed", "#10b981", "#f59e0b",
    "#ef4444", "#06b6d4", "#8b5cf6", "#84cc16",
    "#f97316", "#ec4899", "#3b82f6", "#a3e635",
  ];
  let hash = 0;
  for (let i = 0; i < ticker.length; i++) {
    hash = (hash << 5) - hash + ticker.charCodeAt(i);
    hash |= 0;
  }
  return colors[Math.abs(hash) % colors.length];
}
