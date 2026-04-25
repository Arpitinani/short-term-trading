import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trading Dashboard",
  description: "Short-term trading system — regime detection, screening, backtesting, execution",
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/chart", label: "Chart" },
  { href: "/screener", label: "Screener" },
  { href: "/backtest", label: "Backtest" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-stone-50 text-stone-900">
        <nav className="border-b border-stone-200 bg-white/90 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-14 items-center justify-between">
              <div className="flex items-center gap-1">
                <span className="text-lg font-semibold text-stone-800 mr-6">
                  Trading System
                </span>
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-1.5 text-sm rounded-md text-stone-500 hover:text-stone-900 hover:bg-stone-100 transition-colors"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                  PAPER
                </span>
              </div>
            </div>
          </div>
        </nav>
        <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}
