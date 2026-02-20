"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "@/lib/types";

interface PriceChartProps {
  data: PricePoint[];
  title?: string;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

export default function PriceChart({ data, title }: PriceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-gray-400 text-sm">
        No price data available
      </div>
    );
  }

  return (
    <div>
      {title && <h3 className="text-sm font-semibold text-gray-600 mb-3">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ca8a04" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#ca8a04" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="rangeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#fbbf24" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis
            dataKey="report_date"
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
            formatter={(val: number, name: string) => [
              `$${Number(val).toFixed(0)}/ton`,
              name === "price_wtavg" ? "Wtd Avg" : name === "price_high" ? "High" : "Low",
            ]}
            labelFormatter={(l) =>
              new Date(l).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })
            }
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
          />
          {data[0]?.price_high && (
            <Area
              type="monotone"
              dataKey="price_high"
              stroke="#fbbf24"
              strokeWidth={0}
              fill="url(#rangeGrad)"
              name="price_high"
            />
          )}
          <Area
            type="monotone"
            dataKey="price_wtavg"
            stroke="#ca8a04"
            strokeWidth={2}
            fill="url(#priceGrad)"
            dot={false}
            activeDot={{ r: 4 }}
            name="price_wtavg"
          />
          {data[0]?.price_low && (
            <Area
              type="monotone"
              dataKey="price_low"
              stroke="#fbbf24"
              strokeWidth={0}
              fill="transparent"
              name="price_low"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
