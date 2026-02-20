"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import type { Meta, PricePoint } from "@/lib/types";

export default function ExplorerPage() {
  const [filter, setFilter] = useState({
    region: "san_joaquin_valley",
    hayType: "alfalfa",
    grade: "premium",
    weeks: "104",
  });

  const { data: meta } = useSWR<Meta>("meta", () => api.getMeta() as Promise<Meta>);

  const key = `explore-${filter.region}-${filter.hayType}-${filter.grade}-${filter.weeks}`;
  const { data: series, isLoading } = useSWR<PricePoint[]>(key, () =>
    api.getPriceSeries(filter.region, filter.hayType, filter.grade, parseInt(filter.weeks))
  );

  const handleExport = () => {
    if (!series || series.length === 0) return;
    const headers = ["Date", "Wtd Avg ($/ton)", "Low ($/ton)", "High ($/ton)", "Volume (tons)"];
    const rows = series.map((p) => [
      p.report_date,
      p.price_wtavg.toFixed(2),
      p.price_low?.toFixed(2) ?? "",
      p.price_high?.toFixed(2) ?? "",
      p.volume_tons?.toString() ?? "",
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hay_prices_${filter.region}_${filter.hayType}_${filter.grade}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const selectClass =
    "border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-hay-500";

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Historical Explorer</h1>
          <p className="mt-1 text-gray-500 text-sm">
            Browse and export historical hay price data
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={!series || series.length === 0}
          className="px-4 py-2 bg-white border border-gray-200 hover:border-hay-400 text-gray-700 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-40"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-end">
        {meta && (
          <>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Region</label>
              <select className={selectClass} value={filter.region} onChange={(e) => setFilter((f) => ({ ...f, region: e.target.value }))}>
                {meta.regions.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Hay Type</label>
              <select className={selectClass} value={filter.hayType} onChange={(e) => setFilter((f) => ({ ...f, hayType: e.target.value }))}>
                {meta.hay_types.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Grade</label>
              <select className={selectClass} value={filter.grade} onChange={(e) => setFilter((f) => ({ ...f, grade: e.target.value }))}>
                {meta.grades.map((g) => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Time Range</label>
              <select className={selectClass} value={filter.weeks} onChange={(e) => setFilter((f) => ({ ...f, weeks: e.target.value }))}>
                <option value="52">1 Year</option>
                <option value="104">2 Years</option>
                <option value="156">3 Years</option>
                <option value="260">5 Years</option>
              </select>
            </div>
          </>
        )}
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-4">Price Trend</h2>
        {isLoading ? (
          <div className="h-72 flex items-center justify-center text-gray-400 text-sm animate-pulse">Loading…</div>
        ) : (
          <PriceChart data={series || []} />
        )}
      </div>

      {/* Data table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Price Records</h2>
          <span className="text-xs text-gray-400">{series?.length ?? 0} records</span>
        </div>
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-50">
              <tr className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Wtd Avg</th>
                <th className="px-6 py-3">Low</th>
                <th className="px-6 py-3">High</th>
                <th className="px-6 py-3">Spread</th>
                <th className="px-6 py-3">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(series || []).slice().reverse().map((p, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-3 text-gray-600">
                    {new Date(p.report_date).toLocaleDateString("en-US", {
                      month: "short", day: "numeric", year: "numeric",
                    })}
                  </td>
                  <td className="px-6 py-3 font-semibold text-gray-900">${p.price_wtavg.toFixed(2)}</td>
                  <td className="px-6 py-3 text-gray-500">{p.price_low ? `$${p.price_low.toFixed(2)}` : "—"}</td>
                  <td className="px-6 py-3 text-gray-500">{p.price_high ? `$${p.price_high.toFixed(2)}` : "—"}</td>
                  <td className="px-6 py-3 text-gray-400 text-xs">
                    {p.price_low && p.price_high
                      ? `$${(p.price_high - p.price_low).toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-6 py-3 text-gray-500">{p.volume_tons ? `${p.volume_tons.toLocaleString()} tons` : "—"}</td>
                </tr>
              ))}
              {(!series || series.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-gray-400 text-sm">
                    No data found for the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
