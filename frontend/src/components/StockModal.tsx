"use client";

import { useState } from "react";
import toast from "react-hot-toast";
import { X, Plus, Search } from "lucide-react";
import { portfolioAPI } from "@/lib/api";

// Popular NSE stocks for quick-add
const SUGGESTED_STOCKS = [
  "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "RELIANCE.NS", "TCS.NS",
  "INFY.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS", "AXISBANK.NS",
  "BHARTIARTL.NS", "ADANIENT.NS", "POWERGRID.NS", "NESTLEIND.NS",
  "BAJAJFINSV.NS", "HCLTECH.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
  "INDUSINDBK.NS", "DRREDDY.NS",
];

interface StockModalProps {
  isOpen:      boolean;
  onClose:     () => void;
  portfolioId: string;
  existingStocks: string[];
  onSuccess:   () => void;
}

export default function StockModal({
  isOpen,
  onClose,
  portfolioId,
  existingStocks,
  onSuccess,
}: StockModalProps) {
  const [ticker,  setTicker]  = useState("");
  const [search,  setSearch]  = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const filtered = SUGGESTED_STOCKS.filter(
    (s) =>
      !existingStocks.includes(s) &&
      (search === "" || s.toLowerCase().includes(search.toLowerCase()))
  );

  async function handleAdd(tickerToAdd: string) {
    const t = tickerToAdd.trim().toUpperCase();
    if (!t) { toast.error("Enter a ticker symbol"); return; }
    setLoading(true);
    try {
      await portfolioAPI.addStock(portfolioId, t);
      toast.success(`${t} added! Model retraining started.`);
      setTicker("");
      onSuccess();
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add stock");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="card w-full max-w-md animate-slide-up p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-lg font-bold text-text-primary">Add Stock</h2>
              <p className="text-xs text-text-muted mt-0.5">
                Model will retrain with the new stock universe
              </p>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Custom ticker input */}
          <div className="mb-5">
            <label className="label">Enter Ticker Symbol</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === "Enter" && handleAdd(ticker)}
                placeholder="e.g. AAPL, RELIANCE.NS"
                className="input flex-1"
                disabled={loading}
              />
              <button
                onClick={() => handleAdd(ticker)}
                disabled={loading || !ticker.trim()}
                className="btn-primary px-4"
              >
                {loading ? (
                  <span className="w-4 h-4 border-2 border-bg-primary border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          <div className="glow-line mb-4" />

          {/* Quick-add from suggestions */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="label mb-0">Quick Add (NSE)</label>
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Filter…"
                  className="input pl-6 py-1 text-xs w-32"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
              {filtered.map((s) => (
                <button
                  key={s}
                  onClick={() => handleAdd(s)}
                  disabled={loading}
                  className="px-2.5 py-1 rounded-lg text-xs font-mono font-medium
                             bg-bg-tertiary border border-border text-text-secondary
                             hover:border-accent-cyan hover:text-accent-cyan hover:bg-accent-cyan/5
                             transition-all duration-150 active:scale-95"
                >
                  {s.replace(".NS", "")}
                </button>
              ))}
              {filtered.length === 0 && (
                <p className="text-xs text-text-muted">No suggestions match your filter</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
