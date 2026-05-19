import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "AI Portfolio Manager — Functional SPT",
  description:
    "Production-grade AI-driven portfolio management using Functional Stochastic Portfolio Theory, GARCH volatility modeling, and deep learning.",
  keywords: ["portfolio", "AI", "SPT", "GARCH", "investment", "stocks"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-bg-primary text-text-primary antialiased">
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#0d1b2e",
              color: "#f0f4ff",
              border: "1px solid #1e3a5f",
              borderRadius: "12px",
              fontSize: "14px",
            },
            success: {
              iconTheme: { primary: "#10b981", secondary: "#0d1b2e" },
            },
            error: {
              iconTheme: { primary: "#ef4444", secondary: "#0d1b2e" },
            },
          }}
        />
      </body>
    </html>
  );
}
