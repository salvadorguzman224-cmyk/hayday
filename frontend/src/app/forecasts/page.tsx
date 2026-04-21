"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import RegionFilter from "@/components/RegionFilter";
import ForecastChart from "@/components/ForecastChart";
import type { Forecast, Meta } from "@/lib/types";

const HORIZON_LABELS: Record<number, string> = {
  1: "1 Week",
  2: "2 Weeks",
  4: "4 Weeks",
  12: "12 Weeks",
};

export default function ForecastsPage() {
  const [filter, setFilter] = useState({
    region: "central_san_joaquin_valley",
    hayType: "alfalfa",
    grade: "premium",
  });

  const { data: meta } = useSWR<Meta>("meta", () => api.getMeta() as Promise<Meta>);

  const key = `forecasts-${filter.region}-${filter.hayType}-${filter.grade}`;
  const { data: forecasts, mutate, isLoading } = useSWR<Forecast[]>(key, () =>
    api.getForecasts(filter.region, filter.hayType, filter.grade) as Promise<Forecast[]>
  );

  const seriesKey = `series-${filter.region}-${filter.hayType}-${filter.grade}`;
  const { data: series } = useSWR(seriesKey, () =>
    api.getPriceSeries(filter.region, filter.hayType, filter.grade, 52)
  );

  const handleRefresh = async () => {
    await api.refreshForecasts(filter.region, filter.hayType, filter.grade);
    mutate();
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Price Forecasts</h1>
          <p className="mt-1 text-gray-500 text-sm">
            XGBoost ensemble predictions with 80% and 95% confidence intervals
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-hay-700 hover:bg-hay-800 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Refresh Forecasts
        </button>
      </div>

      {meta && (
        <RegionFilter
          regions={meta.regions}
          hayTypes={meta.hay_types}
          grades={meta.grades}
          selected={filter}
          onChange={(k, v) => setFilter((f) => ({ ...f, [k]: v }))}
        />
      )}

      {/* Combined chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-4">Historical + Multi-Horizon Forecast</h2>
        {isLoading ? (
          <div className="h-80 flex items-center justify-center text-gray-400 text-sm animate-pulse">
            Loading forecasts…
          </div>
        ) : (
          <ForecastChart history={series || []} forecasts={forecasts || []} />
        )}
      </div>

      {/* Forecast table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Forecast Detail</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                <th className="px-6 py-3">Horizon</th>
                <th className="px-6 py-3">Target Date</th>
                <th className="px-6 py-3">Forecast ($/ton)</th>
                <th className="px-6 py-3">80% CI</th>
                <th className="px-6 py-3">95% CI</th>
                <th className="px-6 py-3">MAPE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(forecasts || [])
                .sort((a, b) => a.horizon_weeks - b.horizon_weeks)
                .map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {HORIZON_LABELS[f.horizon_weeks] || `${f.horizon_weeks}w`}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {new Date(f.target_date).toLocaleDateString("en-US", {
                        month: "short", day: "numeric", year: "numeric",
                      })}
                    </td>
                    <td className="px-6 py-4 font-bold text-hay-700">
                      ${Number(f.price_predicted).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {f.price_low_80 && f.price_high_80
                        ? `$${Number(f.price_low_80).toFixed(0)} – $${Number(f.price_high_80).toFixed(0)}`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {f.price_low_95 && f.price_high_95
                        ? `$${Number(f.price_low_95).toFixed(0)} – $${Number(f.price_high_95).toFixed(0)}`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {f.mape_estimate
                        ? `${(Number(f.mape_estimate) * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                  </tr>
                ))}
              {(!forecasts || forecasts.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-gray-400 text-sm">
                    No forecasts available yet. Click Refresh Forecasts to generate.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature importance */}
      {forecasts?.[0]?.feature_importance && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">Feature Importance (4-week model)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {Object.entries(
              forecasts.find((f) => f.horizon_weeks === 4)?.feature_importance || {}
            )
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([feat, score]) => {
                const pct = Math.min(100, Math.round((score as number) * 100));
                const label = feat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                return (
                  <div key={feat}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{label}</span>
                      <span className="font-medium">{pct}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full">
                      <div className="h-2 bg-hay-500 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
