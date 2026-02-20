const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const url = `${API}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  getMeta: () => get("/api/v1/meta"),

  getPriceSeries: (region: string, hayType: string, grade: string, weeks = 104) =>
    get("/api/v1/prices/series", { region, hay_type: hayType, grade, weeks: String(weeks) }),

  getLatestPrices: (region?: string, hayType?: string) =>
    get("/api/v1/prices/latest", {
      ...(region ? { region } : {}),
      ...(hayType ? { hay_type: hayType } : {}),
    }),

  getPriceSummary: (region: string, hayType: string, grade: string) =>
    get("/api/v1/prices/summary", { region, hay_type: hayType, grade }),

  getForecasts: (region: string, hayType: string, grade: string) =>
    get("/api/v1/forecasts/", { region, hay_type: hayType, grade }),

  getDashboardForecast: (region: string, hayType = "alfalfa", grade = "premium") =>
    get("/api/v1/forecasts/dashboard", { region, hay_type: hayType, grade }),

  refreshForecasts: (region: string, hayType: string, grade: string) =>
    post(`/api/v1/forecasts/refresh?region=${region}&hay_type=${hayType}&grade=${grade}`),

  getAlerts: (email: string) => get("/api/v1/alerts/", { email }),

  createAlert: (payload: {
    user_email: string;
    region: string;
    hay_type: string;
    grade: string;
    threshold_price: number;
    direction: string;
  }) => post("/api/v1/alerts/", payload),

  toggleAlert: (id: number) => post(`/api/v1/alerts/${id}/toggle`),

  deleteAlert: async (id: number) => {
    const res = await fetch(`${API}/api/v1/alerts/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`API error ${res.status}`);
  },

  getIngestionLogs: () => get("/api/v1/ingestion/logs"),

  triggerIngestion: (source: string) =>
    post(`/api/v1/ingestion/trigger/${source}`),
};
