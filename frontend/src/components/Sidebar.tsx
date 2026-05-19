"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  BarChart3,
  RefreshCw,
  Brain,
  LogOut,
  TrendingUp,
  ChevronRight,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard",  icon: LayoutDashboard, label: "Dashboard"  },
  { href: "/portfolio",  icon: Briefcase,        label: "Portfolio"  },
  { href: "/analytics",  icon: BarChart3,         label: "Analytics"  },
];

interface SidebarProps {
  modelStatus?: string;   // "idle" | "training" | "done" | "error"
  nextRebalance?: string;
}

export default function Sidebar({ modelStatus = "idle", nextRebalance }: SidebarProps) {
  const pathname = usePathname();
  const router   = useRouter();

  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  const statusColor: Record<string, string> = {
    idle:     "bg-text-muted",
    training: "bg-warning animate-pulse",
    done:     "bg-success",
    error:    "bg-danger",
  };

  const statusLabel: Record<string, string> = {
    idle:     "Ready",
    training: "Training…",
    done:     "Trained",
    error:    "Error",
  };

  return (
    <aside className="w-64 flex-shrink-0 bg-bg-secondary border-r border-border flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-accent flex items-center justify-center shadow-glow-cyan flex-shrink-0">
            <TrendingUp className="w-5 h-5 text-bg-primary" />
          </div>
          <div>
            <p className="text-sm font-bold text-text-primary leading-tight">AI Portfolio</p>
            <p className="text-xs text-text-muted leading-tight">Manager</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group",
                active
                  ? "bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
              )}
            >
              <Icon className={cn("w-4 h-4 flex-shrink-0", active ? "text-accent-cyan" : "text-text-muted group-hover:text-text-secondary")} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="w-3 h-3 text-accent-cyan" />}
            </Link>
          );
        })}

        {/* Divider */}
        <div className="glow-line my-3" />

        {/* Model status */}
        <div className="px-3 py-3 rounded-xl bg-bg-tertiary border border-border">
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-xs text-text-muted font-medium uppercase tracking-wide">Model Status</span>
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <div className={cn("w-2 h-2 rounded-full flex-shrink-0", statusColor[modelStatus] || "bg-text-muted")} />
            <span className="text-sm font-medium text-text-primary">{statusLabel[modelStatus] || "Unknown"}</span>
          </div>
          {nextRebalance && (
            <div className="flex items-center gap-1.5 mt-2">
              <RefreshCw className="w-3 h-3 text-text-muted" />
              <span className="text-xs text-text-muted">Next: {nextRebalance}</span>
            </div>
          )}
        </div>

        {/* Brain indicator */}
        <div className="px-3 py-2.5 rounded-xl flex items-center gap-2 text-xs text-text-muted">
          <Brain className="w-3.5 h-3.5 text-accent-purple" />
          <span>Functional SPT · GARCH</span>
        </div>
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-border">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
                     text-text-secondary hover:text-danger hover:bg-danger/10
                     transition-all duration-200 group"
        >
          <LogOut className="w-4 h-4 text-text-muted group-hover:text-danger" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
