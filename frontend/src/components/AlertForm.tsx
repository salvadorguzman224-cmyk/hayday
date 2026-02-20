"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface Props {
  regions: { value: string; label: string }[];
  hayTypes: string[];
  grades: string[];
  onCreated: () => void;
}

export default function AlertForm({ regions, hayTypes, grades, onCreated }: Props) {
  const [form, setForm] = useState({
    user_email: "",
    region: regions[0]?.value ?? "",
    hay_type: "alfalfa",
    grade: "premium",
    threshold_price: "",
    direction: "below",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.user_email || !form.threshold_price) {
      setError("Email and threshold price are required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.createAlert({
        ...form,
        threshold_price: parseFloat(form.threshold_price),
      });
      setForm((f) => ({ ...f, threshold_price: "", user_email: "" }));
      onCreated();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    "block w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-hay-500";

  return (
    <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">Create Price Alert</h3>
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Your Email</label>
          <input
            type="email"
            className={inputClass}
            placeholder="you@example.com"
            value={form.user_email}
            onChange={(e) => handle("user_email", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Region</label>
          <select className={inputClass} value={form.region} onChange={(e) => handle("region", e.target.value)}>
            {regions.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Hay Type</label>
          <select className={inputClass} value={form.hay_type} onChange={(e) => handle("hay_type", e.target.value)}>
            {hayTypes.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Grade</label>
          <select className={inputClass} value={form.grade} onChange={(e) => handle("grade", e.target.value)}>
            {grades.map((g) => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Trigger When Price Is</label>
          <select className={inputClass} value={form.direction} onChange={(e) => handle("direction", e.target.value)}>
            <option value="below">Below threshold</option>
            <option value="above">Above threshold</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Threshold Price ($/ton)</label>
          <input
            type="number"
            className={inputClass}
            placeholder="e.g. 280"
            value={form.threshold_price}
            onChange={(e) => handle("threshold_price", e.target.value)}
            min={0}
            step={0.01}
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={saving}
        className="mt-5 px-5 py-2 bg-hay-700 hover:bg-hay-800 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
      >
        {saving ? "Creating…" : "Create Alert"}
      </button>
    </form>
  );
}
