"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import AlertForm from "@/components/AlertForm";
import type { Alert, Meta } from "@/lib/types";

export default function AlertsPage() {
  const [email, setEmail] = useState("");
  const [lookupEmail, setLookupEmail] = useState("");

  const { data: meta } = useSWR<Meta>("meta", () => api.getMeta() as Promise<Meta>);

  const alertsKey = lookupEmail ? `alerts-${lookupEmail}` : null;
  const { data: alerts, mutate } = useSWR<Alert[]>(alertsKey, () =>
    api.getAlerts(lookupEmail) as Promise<Alert[]>
  );

  const handleToggle = async (id: number) => {
    await api.toggleAlert(id);
    mutate();
  };

  const handleDelete = async (id: number) => {
    await api.deleteAlert(id);
    mutate();
  };

  const directionBadge = (dir: string) =>
    dir === "below"
      ? "bg-blue-100 text-blue-700"
      : "bg-orange-100 text-orange-700";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Price Alerts</h1>
        <p className="mt-1 text-gray-500 text-sm">
          Get notified by email when hay prices cross your thresholds
        </p>
      </div>

      {/* Create alert form */}
      {meta && (
        <AlertForm
          regions={meta.regions}
          hayTypes={meta.hay_types}
          grades={meta.grades}
          onCreated={() => mutate()}
        />
      )}

      {/* Lookup alerts by email */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-4">View My Alerts</h3>
        <div className="flex gap-3">
          <input
            type="email"
            placeholder="your@email.com"
            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-hay-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setLookupEmail(email)}
          />
          <button
            onClick={() => setLookupEmail(email)}
            className="px-4 py-2 bg-hay-700 hover:bg-hay-800 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Lookup
          </button>
        </div>

        {/* Alert list */}
        {lookupEmail && (
          <div className="mt-6">
            {!alerts || alerts.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-8">
                No alerts found for <strong>{lookupEmail}</strong>
              </p>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex items-center justify-between border rounded-lg px-4 py-3 transition-opacity ${
                      alert.is_active ? "border-gray-200 bg-white" : "border-gray-100 bg-gray-50 opacity-60"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-2.5 h-2.5 rounded-full ${
                          alert.is_active ? "bg-green-400" : "bg-gray-300"
                        }`}
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {alert.region.replace(/_/g, " ")} ·{" "}
                          {alert.hay_type} · {alert.grade}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          Notify when price is{" "}
                          <span className={`font-semibold px-1.5 py-0.5 rounded ${directionBadge(alert.direction)}`}>
                            {alert.direction}
                          </span>{" "}
                          <strong>${Number(alert.threshold_price).toFixed(0)}/ton</strong>
                        </p>
                        {alert.last_triggered_at && (
                          <p className="text-xs text-gray-400 mt-0.5">
                            Last triggered:{" "}
                            {new Date(alert.last_triggered_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggle(alert.id)}
                        className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                          alert.is_active
                            ? "bg-gray-100 hover:bg-gray-200 text-gray-600"
                            : "bg-green-100 hover:bg-green-200 text-green-700"
                        }`}
                      >
                        {alert.is_active ? "Pause" : "Activate"}
                      </button>
                      <button
                        onClick={() => handleDelete(alert.id)}
                        className="text-xs px-3 py-1.5 rounded-md font-medium bg-red-50 hover:bg-red-100 text-red-600 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* How alerts work */}
      <div className="bg-hay-50 border border-hay-200 rounded-xl p-6">
        <h3 className="font-semibold text-hay-800 mb-2">How Alerts Work</h3>
        <ul className="text-sm text-hay-700 space-y-1.5">
          <li>• Alerts are checked every time new price data is ingested (weekly)</li>
          <li>• You receive an email when the latest price crosses your threshold</li>
          <li>• Set direction to <strong>below</strong> to catch buying opportunities</li>
          <li>• Set direction to <strong>above</strong> to know when to lock in sales</li>
        </ul>
      </div>
    </div>
  );
}
