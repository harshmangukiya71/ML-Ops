"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { authAPI } from "@/lib/api";
import { TrendingUp, Lock, Mail, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode]         = useState<"login" | "register">("login");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res =
        mode === "login"
          ? await authAPI.login(email, password)
          : await authAPI.register(email, password);

      localStorage.setItem("token", res.data.access_token);
      toast.success(mode === "login" ? "Welcome back!" : "Account created!");
      router.push("/dashboard");
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        (mode === "login" ? "Invalid credentials" : "Registration failed");
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 bg-gradient-glow opacity-40 pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-accent-purple/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-md mx-4">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8 animate-fade-in">
          <div className="w-14 h-14 rounded-2xl bg-gradient-accent flex items-center justify-center mb-4 shadow-glow-cyan">
            <TrendingUp className="w-7 h-7 text-bg-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">AI Portfolio Manager</h1>
          <p className="text-text-secondary text-sm mt-1">
            Functional SPT · GARCH · Deep Learning
          </p>
        </div>

        {/* Card */}
        <div className="card p-8 animate-slide-up">
          {/* Tab switcher */}
          <div className="flex rounded-xl bg-bg-tertiary p-1 mb-6">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200 capitalize ${
                  mode === m
                    ? "bg-bg-secondary text-text-primary shadow-card"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {m === "login" ? "Sign In" : "Sign Up"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="input pl-10"
                />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  className="input pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-bg-primary border-t-transparent rounded-full animate-spin" />
                  {mode === "login" ? "Signing in…" : "Creating account…"}
                </span>
              ) : mode === "login" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-text-muted text-xs mt-6">
          Powered by Functional Stochastic Portfolio Theory
        </p>
      </div>
    </div>
  );
}
