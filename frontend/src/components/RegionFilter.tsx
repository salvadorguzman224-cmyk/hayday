"use client";

interface FilterProps {
  regions: { value: string; label: string }[];
  hayTypes: string[];
  grades: string[];
  selected: { region: string; hayType: string; grade: string };
  onChange: (key: "region" | "hayType" | "grade", value: string) => void;
}

export default function RegionFilter({ regions, hayTypes, grades, selected, onChange }: FilterProps) {
  const labelClass = "block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1";
  const selectClass =
    "block w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-hay-500 focus:border-transparent";

  return (
    <div className="flex flex-wrap gap-4 items-end">
      <div>
        <label className={labelClass}>Region</label>
        <select
          className={selectClass}
          value={selected.region}
          onChange={(e) => onChange("region", e.target.value)}
        >
          {regions.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={labelClass}>Hay Type</label>
        <select
          className={selectClass}
          value={selected.hayType}
          onChange={(e) => onChange("hayType", e.target.value)}
        >
          {hayTypes.map((t) => (
            <option key={t} value={t}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={labelClass}>Grade</label>
        <select
          className={selectClass}
          value={selected.grade}
          onChange={(e) => onChange("grade", e.target.value)}
        >
          {grades.map((g) => (
            <option key={g} value={g}>
              {g.charAt(0).toUpperCase() + g.slice(1)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
