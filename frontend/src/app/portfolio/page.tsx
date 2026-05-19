"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import toast from "react-hot-toast";
import { Plus, RefreshCw, Briefcase, Calendar, TrendingUp } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import AllocationTable from "@/components/AllocationTable";
import StockModal from "@/components/StockModal";
import { portfolioAPI, modelAPI } from "@/lib/api";
import { formatINR } from "@/lib/utils";

export default function PortfolioPage() {
  const router = useRouter();

  useEffect(() => {
    if (!localStorage.getItem("token")) router.push("/login");
  }, [router]);

  const [addModal, setAddModal]   = useState(false);
  const [removing, setRemoving]   = useState<string | null>(null);

  const { data: portfolios, mutate: mutatePortfolios } = useSWR(
    "portfolios",
    () => portfolioAPI.list().then((r) => r.data),
    { refreshInterval: 30_000 }
  );

  const { data: modelStatus } = useSWR(
    "model-status",
    () => modelAPI.status().then((r) => r.data),
    { refreshInterval: 10_000 }
  );

  const portfolio = portfolios?.[0];

  const { data: weightsData, mutate: mutateWeights } = useSWR(
    portfolio ? `weights-${portfolio.id}` : null,
    () => portfolioAPI.getWeights(portfolio!.id).then((r) => r.data),
    { refreshInterval: 60_000 }
  );

  async function handleRemove(ticker: string) {
    if (!portfolio) return;
    if (!confirm(`Remove ${ticker}?\n\nIts capital will be redistributed proportionally among remaining stocks.`)) return;
    setRemoving(ticker);
    try {
      await portfolioAPI.removeStock(portfolio.id, ticker);
      toast.success(`${ticker} removed. Model retraining…`);
      mutatePortfolios();
      mutateWeights();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to remove");
    } finally {
      setRemoving(null);
    }
  }

  async function handleRetrain() {
    if (!portfolio) return;
    try {
      await modelAPI.retrain(portfolio.id);
      toast.success("Retraining started");
    } catch {
      toast.error("Failed to start retraining");
    }
  }

  return (
    <div className="flex h-screen bg-bg-primary overflow-hidden">
      <Sidebar modelStatus={modelStatus?.status} />

      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-bg-primary/80 backdrop-blur-md border-b border-border px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Briefcase className="w-5 h-5 text-accent-cyan" />
            <h1 className="text-xl font-bold text-text-primary">Portfolio Management</h1>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleRetrain} className="btn-ghost flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Retrain Model
            </button>
            <button onClick={() => setAddModal(true)} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Stock
            </button>
          </div>
        </div>

        <div className="p-8 space-y-6 animate-fade-in">
          {/* Portfolio info cards */}
          {portfolio && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="card p-5">
                <p className="label mb-2">Total Capital</p>
                <p className="text-2xl font-bold font-mono text-accent-cyan">
                  {formatINR(portfolio.capital)}
                </p>
              </div>
              <div className="card p-5">
                <p className="label mb-2">Holdings</p>
                <p className="text-2xl font-bold font-mono text-text-primary">
                  {portfolio.stocks.length} <span className="text-sm font-normal text-text-muted">stocks</span>
                </p>
              </div>
              <div className="card p-5">
                <p className="label mb-2">Last Rebalanced</p>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-text-muted" />
                  <p className="text-sm font-medium text-text-primary">
                    {portfolio.last_rebalanced
                      ? new Date(portfolio.last_rebalanced).toLocaleDateString("en-IN", {
                          day: "2-digit", month: "short", year: "numeric",
                        })
                      : "Never"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Holdings table */}
          <div className="card">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent-cyan" />
                <h2 className="text-sm font-semibold text-text-secondary">Current Holdings</h2>
              </div>
              <div className="flex items-center gap-3">
                {weightsData?.model_trained ? (
                  <span className="badge-success">AI Weights</span>
                ) : (
                  <span className="badge-warning">Equal Weights (Training…)</span>
                )}
                <span className="badge-info">
                  {(weightsData?.allocations?.length ?? 0)} positions
                </span>
              </div>
            </div>

            <AllocationTable
              allocations={weightsData?.allocations ?? []}
              capital={weightsData?.capital ?? portfolio?.capital ?? 0}
              onRemove={handleRemove}
              loading={!!removing}
            />
          </div>

          {/* Stock universe chips */}
          {portfolio && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4">Stock Universe</h3>
              <div className="flex flex-wrap gap-2">
                {portfolio.stocks.map((s) => (
                  <div
                    key={s}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-tertiary border border-border text-xs font-mono text-text-secondary"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan" />
                    {s}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {portfolio && (
        <StockModal
          isOpen={addModal}
          onClose={() => setAddModal(false)}
          portfolioId={portfolio.id}
          existingStocks={portfolio.stocks}
          onSuccess={() => { mutatePortfolios(); mutateWeights(); }}
        />
      )}
    </div>
  );
}
