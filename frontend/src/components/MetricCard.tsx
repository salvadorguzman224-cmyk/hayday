import { clsx } from "clsx";

interface MetricCardProps {
  title: string;
  value: string | number | null;
  subtitle?: string;
  delta?: { absolute: number; pct: number } | null;
  highlight?: boolean;
}

export default function MetricCard({ title, value, subtitle, delta, highlight }: MetricCardProps) {
  const positive = delta && delta.absolute > 0;
  const negative = delta && delta.absolute < 0;

  return (
    <div
      className={clsx(
        "rounded-xl border p-5 bg-white shadow-sm",
        highlight && "border-hay-400 ring-1 ring-hay-300"
      )}
    >
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900">
        {value !== null && value !== undefined ? value : "—"}
      </p>
      {subtitle && <p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>}
      {delta && (
        <p
          className={clsx(
            "mt-2 text-sm font-medium",
            positive ? "text-green-600" : negative ? "text-red-600" : "text-gray-500"
          )}
        >
          {positive ? "▲" : negative ? "▼" : "–"}{" "}
          ${Math.abs(delta.absolute).toFixed(0)}/ton ({Math.abs(delta.pct).toFixed(1)}%)
        </p>
      )}
    </div>
  );
}
