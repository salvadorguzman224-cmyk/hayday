"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Forecast, PricePoint } from "@/lib/types";

interface ForecastChartProps {
  history: PricePoint[];
  forecasts: Forecast[];
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function ForecastChart({ history, forecasts }: ForecastChartProps) {
  if (!history.length && !forecasts.length) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 text-sm">
        No data available
      </div>
    );
  }

  // Combine last 26 weeks of history + forecast points
  const last26 = history.slice(-26).map((h) => ({
    date: h.report_date,
    actual: h.price_wtavg,
    low80: null as number | null,
    high80: null as number | null,
    forecast: null as number | null,
  }));

  const forecastPoints = forecasts
    .sort((a, b) => a.horizon_weeks - b.horizon_weeks)
    .map((f) => ({
      date: f.target_date,
      actual: null as number | null,
      low80: f.price_low_80 ?? null,
      high80: f.price_high_80 ?? null,
      forecast: Number(f.price_predicted),
    }));

  const data = [...last26, ...forecastPoints];
  const dividerDate = last26[last26.length - 1]?.date;

  return (
    <ResponsiveContainer width="100%" height={350}>
      <AreaChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ca8a04" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#ca8a04" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#93c5fd" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#93c5fd" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          tickFormatter={(v) => `$${v}`}
          width={55}
        />
        <Tooltip
          formatter={(val: number | null, name: string) =>
            val !== null ? [`$${Number(val).toFixed(0)}/ton`, name] : [null, name]
          }
          labelFormatter={(l) =>
            new Date(l).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })
          }
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
        />
        {dividerDate && (
          <ReferenceLine
            x={dividerDate}
            stroke="#6b7280"
            strokeDasharray="4 2"
            label={{ value: "Today", fontSize: 10, fill: "#6b7280" }}
          />
        )}
        {/* 80% confidence band */}
        <Area
          type="monotone"
          dataKey="high80"
          stroke="#93c5fd"
          strokeWidth={0}
          fill="url(#ciGrad)"
          name="80% CI High"
        />
        <Area
          type="monotone"
          dataKey="low80"
          stroke="#93c5fd"
          strokeWidth={0}
          fill="transparent"
          name="80% CI Low"
        />
        {/* Historical prices */}
        <Area
          type="monotone"
          dataKey="actual"
          stroke="#ca8a04"
          strokeWidth={2}
          fill="url(#histGrad)"
          dot={false}
          activeDot={{ r: 4 }}
          name="Historical"
          connectNulls={false}
        />
        {/* Forecast */}
        <Area
          type="monotone"
          dataKey="forecast"
          stroke="#3b82f6"
          strokeWidth={2.5}
          strokeDasharray="5 3"
          fill="url(#forecastGrad)"
          dot={{ r: 5, fill: "#3b82f6" }}
          activeDot={{ r: 6 }}
          name="Forecast"
          connectNulls={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
