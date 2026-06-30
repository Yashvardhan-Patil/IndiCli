import axios from "axios";

const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 30000);
const ML_TIMEOUT_MS = Number(import.meta.env.VITE_ML_API_TIMEOUT_MS || 120000);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: DEFAULT_TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    let msg = err.response?.data?.detail || err.message || "API error";
    if (typeof msg === "object" && msg !== null) {
      if (Array.isArray(msg)) {
        msg = msg
          .map((item) => {
            if (typeof item === "object" && item !== null) {
              const loc = item.loc ? `${item.loc.join(".")}: ` : "";
              return `${loc}${item.msg}`;
            }
            return String(item);
          })
          .join("; ");
      } else {
        msg = JSON.stringify(msg);
      }
    }
    console.error("[API]", msg);
    return Promise.reject(new Error(msg));
  }
);

// ── Datasets ──────────────────────────────────────────────────────────────────
export const datasetsApi = {
  getMeta:    () => api.get("/datasets/meta"),
  getQuality: () => api.get("/datasets/quality"),
  getSummary: () => api.get("/datasets/summary"),
};

// ── Climate State ─────────────────────────────────────────────────────────────
export const climateApi = {
  getCurrent:   (date, variable, bbox) =>
    api.get("/climate-state/current", { params: { date, variable, bbox } }),
  getLatest:    (variable) =>
    api.get("/climate-state/latest", { params: { variable } }),
  getTimeseries:(lat, lon, start, end) =>
    api.get("/climate-state/timeseries", { params: { lat, lon, start, end } }),
  getNationalSummary: (date) =>
    api.get("/climate-state/national-summary", { params: { date } }),
};

// ── Forecasting ───────────────────────────────────────────────────────────────
export const forecastApi = {
  pointForecast: (payload) => api.post("/forecast/point", payload, { timeout: ML_TIMEOUT_MS }),
  trainModels:   () => api.post("/forecast/train", null, { timeout: ML_TIMEOUT_MS }),
};

// ── Scenarios ─────────────────────────────────────────────────────────────────
export const scenarioApi = {
  runScenario:  (payload) => api.post("/scenario/run", payload, { timeout: ML_TIMEOUT_MS }),
  getTypes:     () => api.get("/scenario/types"),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  trend:      (payload) => api.post("/analytics/trend", payload, { timeout: ML_TIMEOUT_MS }),
  anomaly:    (payload) => api.post("/analytics/anomaly", payload, { timeout: ML_TIMEOUT_MS }),
  risk:       (payload) => api.post("/analytics/risk", payload, { timeout: ML_TIMEOUT_MS }),
  indicators: (start, end) => api.get("/analytics/indicators", { params: { start, end }, timeout: ML_TIMEOUT_MS }),
};

export default api;
