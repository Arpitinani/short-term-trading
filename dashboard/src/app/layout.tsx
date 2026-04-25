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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-14 items-center justify-between">
              <div className="flex items-center gap-1">
                <span className="text-lg font-semibold text-white mr-6">
                  Trading System
                </span>
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-1.5 text-sm rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="px-2 py-1 rounded bg-gray-800 text-amber-400">
                  DRY RUN
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
