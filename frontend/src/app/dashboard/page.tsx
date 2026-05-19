"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import toast from "react-hot-toast";
import {
  RefreshCw, Plus, TrendingUp, Activity,
  DollarSign, BarChart2, AlertTriangle, Brain,
} from "lucide-react";

import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";
import AllocationTable from "@/components/AllocationTable";
import WeightsChart from "@/components/charts/WeightsChart";
import WealthChart from "@/components/charts/WealthChart";
import StockModal from "@/components/StockModal";
import { portfolioAPI, modelAPI, type Portfolio } from "@/lib/api";
import { formatINR } from "@/lib/utils";

export default function DashboardPage() {
  const router = useRouter();

  // ── Auth guard ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!localStorage.getItem("token")) router.push("/login");
  }, [router]);

  // ── State ───────────────────────────────────────────────────────────────
  const [portfolioId,  setPortfolioId]  = useState<string | null>(null);
  const [addModal,     setAddModal]     = useState(false);
  const [rebalancing,  setRebalancing]  = useState(false);
  const [capitalInput, setCapitalInput] = useState("");
  const [savingCapital, setSavingCapital] = useState(false);

  // ── SWR data fetching ───────────────────────────────────────────────────
  const { data: portfolios, mutate: mutatePortfolios } = useSWR(
    "portfolios",
    () => portfolioAPI.list().then((r) => r.data),
    { refreshInterval: 30_000 }
  );

  const activePortfolio: Portfolio | undefined = portfolios?.[0];

  useEffect(() => {
    if (activePortfolio) {
      setPortfolioId(activePortfolio.id);
      if (!capitalInput) setCapitalInput(String(activePortfolio.capital));
    }
  }, [activePortfolio]);

  const { data: weightsData, mutate: mutateWeights } = useSWR(
    portfolioId ? `weights-${portfolioId}` : null,
    () => portfolioAPI.getWeights(portfolioId!).then((r) => r.data),
    { refreshInterval: 60_000 }
  );

  const { data: perfData, mutate: mutatePerf } = useSWR(
    portfolioId ? `perf-${portfolioId}` : null,
    () => portfolioAPI.getPerformance(portfolioId!).then((r) => r.data),
    { refreshInterval: 120_000 }
  );

  const { data: modelStatus } = useSWR(
    "model-status",
    () => modelAPI.status().then((r) => r.data),
    { refreshInterval: 10_000 }
  );

  // ── Handlers ────────────────────────────────────────────────────────────
  const handleRebalance = useCallback(async () => {
    if (!portfolioId) return;
    setRebalancing(true);
    try {
      const res = await portfolioAPI.rebalance(portfolioId);
      toast.success(`Rebalanced! Turnover: ${(res.data.turnover * 100).toFixed(2)}%`);
      mutateWeights();
      mutatePerf();
    } catch {
      toast.error("Rebalance failed");
    } finally {
      setRebalancing(false);
    }
  }, [portfolioId, mutateWeights, mutatePerf]);

  const handleRemoveStock = useCallback(async (ticker: string) => {
    if (!portfolioId) return;
    if (!confirm(`Remove ${ticker}? Capital redistributed to remaining stocks.`)) return;
    try {
      await portfolioAPI.removeStock(portfolioId, ticker);
      toast.success(`${ticker} removed. Model retraining…`);
      mutatePortfolios();
      mutateWeights();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to remove stock");
    }
  }, [portfolioId, mutatePortfolios, mutateWeights]);

  const handleSaveCapital = useCallback(async () => {
    if (!portfolioId || !capitalInput) return;
    setSavingCapital(true);
    try {
      await portfolioAPI.updateCapital(portfolioId, Number(capitalInput));
      toast.success("Capital updated");
      mutatePortfolios();
      mutateWeights();
    } catch {
      toast.error("Failed to update capital");
    } finally {
      setSavingCapital(false);
    }
  }, [portfolioId, capitalInput, mutatePortfolios, mutateWeights]);

  // ── No portfolio — create one ───────────────────────────────────────────
  if (portfolios && portfolios.length === 0) {
    return (
      <div className="flex h-screen bg-bg-primary">
        <Sidebar modelStatus={modelStatus?.status} />
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="card p-10 max-w-md w-full text-center animate-slide-up">
            <Brain className="w-12 h-12 text-accent-cyan mx-auto mb-4" />
            <h2 className="text-xl font-bold text-text-primary mb-2">Create Your Portfolio</h2>
            <p className="text-text-secondary text-sm mb-6">
              Start by creating an AI-managed portfolio. The model will learn optimal weights using Functional SPT and GARCH.
            </p>
            <button
              className="btn-primary w-full py-3"
              onClick={async () => {
                try {
                  await portfolioAPI.create("My Portfolio", [
                    "HDFCBANK.NS", "ICICIBANK.NS", "RELIANCE.NS",
                    "TCS.NS", "INFY.NS",
                  ], 100000);
                  toast.success("Portfolio created! Model training started…");
                  mutatePortfolios();
                } catch {
                  toast.error("Failed to create portfolio");
                }
              }}
            >
              Create Portfolio
            </button>
          </div>
        </main>
      </div>
    );
  }

  const metrics    = perfData?.metrics;
  const allocations = weightsData?.allocations ?? [];
  const capital    = weightsData?.capital ?? activePortfolio?.capital ?? 0;

  return (
    <div className="flex h-screen bg-bg-primary overflow-hidden">
      <Sidebar modelStatus={modelStatus?.status} />

      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-bg-primary/80 backdrop-blur-md border-b border-border px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              {activePortfolio?.name ?? "Dashboard"}
            </h1>
            <div className="flex items-center gap-2 mt-0.5">
              {weightsData?.model_trained ? (
                <span className="badge-success">Model Trained</span>
              ) : (
                <span className="badge-warning">Training…</span>
              )}
              {activePortfolio?.last_rebalanced && (
                <span className="text-xs text-text-muted">
                  Last rebalanced:{" "}
                  {new Date(activePortfolio.last_rebalanced).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Capital input */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">₹</span>
                <input
                  type="number"
                  value={capitalInput}
                  onChange={(e) => setCapitalInput(e.target.value)}
                  className="input pl-7 w-36 text-sm"
                  placeholder="Capital"
                />
              </div>
              <button
                onClick={handleSaveCapital}
                disabled={savingCapital}
                className="btn-ghost text-xs py-2"
              >
                {savingCapital ? "Saving…" : "Update"}
              </button>
            </div>

            <button
              onClick={() => setAddModal(true)}
              className="btn-ghost flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Stock
            </button>

            <button
              onClick={handleRebalance}
              disabled={rebalancing}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${rebalancing ? "animate-spin" : ""}`} />
              {rebalancing ? "Rebalancing…" : "Rebalance"}
            </button>
          </div>
        </div>

        <div className="p-8 space-y-8 animate-fade-in">
          {/* Model training banner */}
          {modelStatus?.status === "training" && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-warning/10 border border-warning/20 text-warning text-sm">
              <Activity className="w-4 h-4 animate-pulse flex-shrink-0" />
              <span>Model is retraining — weights will update automatically when complete.</span>
            </div>
          )}
          {modelStatus?.status === "error" && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>Training error: {modelStatus.error}</span>
            </div>
          )}

          {/* KPI Metrics */}
          <section>
            <h2 className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-4">Performance Metrics</h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                label="Sharpe Ratio"
                value={metrics?.sharpe ?? 0}
                format="ratio"
                trend={metrics && metrics.sharpe > 1 ? "up" : metrics && metrics.sharpe > 0 ? "neutral" : "down"}
                highlight={!!(metrics && metrics.sharpe > 1)}
                icon={<TrendingUp className="w-4 h-4" />}
                subtitle="Risk-adjusted return"
              />
              <MetricCard
                label="Annual Return"
                value={metrics?.arithmetic_return ?? 0}
                format="percent"
                trend={metrics && metrics.arithmetic_return > 0 ? "up" : "down"}
                icon={<BarChart2 className="w-4 h-4" />}
                subtitle="Arithmetic (annualized)"
              />
              <MetricCard
                label="Volatility"
                value={metrics?.volatility ?? 0}
                format="percent"
                trend="neutral"
                icon={<Activity className="w-4 h-4" />}
                subtitle="Annualized std dev"
              />
              <MetricCard
                label="Max Drawdown"
                value={metrics?.max_drawdown ?? 0}
                format="percent"
                trend="down"
                icon={<AlertTriangle className="w-4 h-4" />}
                subtitle="Peak-to-trough loss"
              />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <MetricCard
                label="Total Capital"
                value={formatINR(capital)}
                subtitle="Under management"
                icon={<DollarSign className="w-4 h-4" />}
              />
              <MetricCard
                label="Avg Turnover"
                value={metrics?.avg_turnover ?? 0}
                format="percent"
                trend="neutral"
                subtitle="Per rebalance day"
              />
              <MetricCard
                label="Cost Drag"
                value={metrics?.cost_drag ?? 0}
                format="ratio"
                trend="down"
                subtitle="Transaction cost impact"
              />
              <MetricCard
                label="Holdings"
                value={allocations.length}
                subtitle={`of ${activePortfolio?.stocks.length ?? 0} stocks`}
              />
            </div>
          </section>

          {/* Charts row */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Cumulative wealth */}
            <div className="card p-6 lg:col-span-2">
              <h3 className="text-sm font-semibold text-text-secondary mb-4">Cumulative Wealth</h3>
              <WealthChart
                spt={perfData?.wealth_spt ?? []}
                market={perfData?.wealth_market ?? []}
                net={perfData?.wealth_net ?? []}
              />
            </div>

            {/* Weights donut */}
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4">Weight Distribution</h3>
              <WeightsChart allocations={allocations} />
            </div>
          </section>

          {/* Allocation table */}
          <section className="card">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-secondary">Current Allocations</h3>
              <span className="badge-info">{allocations.length} positions</span>
            </div>
            <AllocationTable
              allocations={allocations}
              capital={capital}
              onRemove={handleRemoveStock}
            />
          </section>
        </div>
      </main>

      {/* Add Stock Modal */}
      {portfolioId && (
        <StockModal
          isOpen={addModal}
          onClose={() => setAddModal(false)}
          portfolioId={portfolioId}
          existingStocks={activePortfolio?.stocks ?? []}
          onSuccess={() => { mutatePortfolios(); mutateWeights(); }}
        />
      )}
    </div>
  );
}
