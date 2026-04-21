"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import RegionFilter from "@/components/RegionFilter";
import PriceChart from "@/components/PriceChart";
import ForecastChart from "@/components/ForecastChart";
import MetricCard from "@/components/MetricCard";
import type { Meta, PriceSummary } from "@/lib/types";

export default function DashboardPage() {
  const [filter, setFilter] = useState({
    region: "central_san_joaquin_valley",
    hayType: "alfalfa",
    grade: "premium",
  });

  const { data: meta } = useSWR<Meta>("meta", () => api.getMeta() as Promise<Meta>);

  const seriesKey = `series-${filter.region}-${filter.hayType}-${filter.grade}`;
  const { data: series, isLoading: seriesLoading } = useSWR(seriesKey, () =>
    api.getPriceSeries(filter.region, filter.hayType, filter.grade, 104)
  );

  const summaryKey = `summary-${filter.region}-${filter.hayType}-${filter.grade}`;
  const { data: summary } = useSWR<PriceSummary>(summaryKey, () =>
    api.getPriceSummary(filter.region, filter.hayType, filter.grade) as Promise<PriceSummary>
  );

  const forecastKey = `forecast-${filter.region}-${filter.hayType}-${filter.grade}`;
  const { data: forecasts } = useSWR(forecastKey, () =>
    api.getForecasts(filter.region, filter.hayType, filter.grade)
  );

  const handleFilterChange = (key: "region" | "hayType" | "grade", value: string) => {
    setFilter((f) => ({ ...f, [key]: value }));
  };

  const grade1Week = forecasts?.find((f: any) => f.horizon_weeks === 1);
  const grade4Week = forecasts?.find((f: any) => f.horizon_weeks === 4);
  const topFeatures = grade4Week?.feature_importance
    ? Object.entries(grade4Week.feature_importance)
        .sort(([, a]: any, [, b]: any) => b - a)
        .slice(0, 5)
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Market Dashboard</h1>
        <p className="mt-1 text-gray-500 text-sm">
          California hay market prices and AI-powered forecasts
        </p>
      </div>

      {/* Filters */}
      {meta && (
        <RegionFilter
          regions={meta.regions}
          hayTypes={meta.hay_types}
          grades={meta.grades}
          selected={filter}
          onChange={handleFilterChange}
        />
      )}

      {/* Summary metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard
          title="Current Price"
          value={summary?.current_price ? `$${summary.current_price.toFixed(0)}` : "—"}
          subtitle="per ton (wtd avg)"
          highlight
        />
        <MetricCard
          title="vs 4 Weeks Ago"
          value={summary?.vs_4_weeks ? `$${Math.abs(summary.vs_4_weeks.absolute).toFixed(0)}` : "—"}
          subtitle="absolute change"
          delta={summary?.vs_4_weeks ?? null}
        />
        <MetricCard
          title="1-Week Forecast"
          value={grade1Week ? `$${Number(grade1Week.price_predicted).toFixed(0)}` : "—"}
          subtitle={
            grade1Week?.price_low_80 && grade1Week?.price_high_80
              ? `$${Number(grade1Week.price_low_80).toFixed(0)} – $${Number(grade1Week.price_high_80).toFixed(0)}`
              : "80% CI"
          }
        />
        <MetricCard
          title="4-Week Forecast"
          value={grade4Week ? `$${Number(grade4Week.price_predicted).toFixed(0)}` : "—"}
          subtitle={
            grade4Week?.mape_estimate
              ? `MAPE: ${(Number(grade4Week.mape_estimate) * 100).toFixed(1)}%`
              : "per ton"
          }
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Historical chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-4">
            Price History + Forecast
          </h2>
          {seriesLoading ? (
            <div className="h-72 flex items-center justify-center text-gray-400 text-sm animate-pulse">
              Loading…
            </div>
          ) : (
            <ForecastChart history={series || []} forecasts={forecasts || []} />
          )}
        </div>

        {/* Feature importance panel */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-1">Forecast Drivers</h2>
          <p className="text-xs text-gray-400 mb-4">
            Top factors for the 4-week prediction
          </p>
          {topFeatures.length === 0 ? (
            <p className="text-gray-400 text-sm">No forecast available yet</p>
          ) : (
            <ul className="space-y-3">
              {topFeatures.map(([feat, score]: any) => {
                const label = feat
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c: string) => c.toUpperCase());
                const pct = Math.min(100, Math.round(score * 100));
                return (
                  <li key={feat}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{label}</span>
                      <span className="font-medium">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full">
                      <div
                        className="h-1.5 bg-hay-500 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {grade4Week && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500">Model version</p>
              <p className="text-xs font-mono text-gray-700 mt-0.5">{grade4Week.model_version}</p>
            </div>
          )}
        </div>
      </div>

      {/* Historical price chart (standalone) */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-4">2-Year Price History</h2>
        <PriceChart data={series || []} />
      </div>
    </div>
  );
}
