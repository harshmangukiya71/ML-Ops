"use client";

import { cn, formatPercent, formatRatio } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  format?: "percent" | "ratio" | "raw";
  highlight?: boolean;
  className?: string;
  icon?: React.ReactNode;
}

export default function MetricCard({
  label,
  value,
  subtitle,
  trend,
  format,
  highlight = false,
  className,
  icon,
}: MetricCardProps) {
  // Format the value
  const displayValue = (() => {
    if (typeof value !== "number") return value;
    if (format === "percent") return formatPercent(value);
    if (format === "ratio")   return formatRatio(value);
    return value.toFixed(4);
  })();

  // Color based on trend or value
  const valueClass = (() => {
    if (trend === "up")      return "metric-positive";
    if (trend === "down")    return "metric-negative";
    if (trend === "neutral") return "metric-neutral";
    if (typeof value === "number") {
      if (value > 0) return "metric-positive";
      if (value < 0) return "metric-negative";
    }
    return "text-text-primary";
  })();

  const TrendIcon =
    trend === "up" ? TrendingUp :
    trend === "down" ? TrendingDown :
    Minus;

  return (
    <div
      className={cn(
        "card-hover p-5 relative overflow-hidden group",
        highlight && "border-accent-cyan/30",
        className
      )}
    >
      {/* Glow accent top bar */}
      {highlight && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-accent" />
      )}

      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-text-muted uppercase tracking-widest">{label}</p>
        <div className="flex items-center gap-1.5">
          {icon && <span className="text-text-muted">{icon}</span>}
          {trend && (
            <TrendIcon
              className={cn(
                "w-3.5 h-3.5",
                trend === "up"      ? "text-success" :
                trend === "down"    ? "text-danger"  :
                "text-text-muted"
              )}
            />
          )}
        </div>
      </div>

      <p className={cn("text-2xl font-bold font-mono tracking-tight leading-none", valueClass)}>
        {displayValue}
      </p>

      {subtitle && (
        <p className="text-xs text-text-muted mt-2">{subtitle}</p>
      )}

      {/* Subtle hover glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent-cyan/0 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl pointer-events-none" />
    </div>
  );
}
