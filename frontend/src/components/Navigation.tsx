"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/forecasts", label: "Forecasts" },
  { href: "/explorer", label: "Explorer" },
  { href: "/alerts", label: "Alerts" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-hay-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌾</span>
            <span className="font-bold text-lg tracking-tight">Hay Price Predictor</span>
            <span className="ml-2 text-hay-400 text-xs font-medium bg-hay-900 px-2 py-0.5 rounded-full">
              California
            </span>
          </div>
          <div className="flex gap-1">
            {links.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                  pathname === href
                    ? "bg-hay-600 text-white"
                    : "text-hay-200 hover:bg-hay-700 hover:text-white"
                )}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
