import { create } from "zustand";
import { devtools } from "zustand/middleware";

const useStore = create(
  devtools(
    (set, get) => ({
      // ── Active selections ──────────────────────────────────────────────────
      selectedDate:     "2025-07-15",
      selectedVariable: "rainfall",
      selectedLayer:    "current",   // current | forecast | scenario
      selectedLat:      20.5937,
      selectedLon:      78.9629,

      // ── Dataset meta ───────────────────────────────────────────────────────
      datasetMeta: null,
      dataQuality: null,

      // ── Climate data ───────────────────────────────────────────────────────
      currentState:     null,
      timeseries:       null,
      nationalSummary:  null,

      // ── Forecast ───────────────────────────────────────────────────────────
      forecastData:     null,
      forecastLoading:  false,

      // ── Scenario ───────────────────────────────────────────────────────────
      activeScenario:   null,
      scenarioResult:   null,
      scenarioLoading:  false,

      // ── Analytics ─────────────────────────────────────────────────────────
      trendResult:      null,
      anomalyResult:    null,
      riskResult:       null,
      indicators:       null,

      // ── UI state ──────────────────────────────────────────────────────────
      sidebarOpen:      true,
      mapMode:          "globe",   // globe | flat
      loading:          false,
      error:            null,

      // ── Setters ───────────────────────────────────────────────────────────
      setSelectedDate:     (d) => set({ selectedDate: d }),
      setSelectedVariable: (v) => set({ selectedVariable: v }),
      setSelectedLayer:    (l) => set({ selectedLayer: l }),
      setSelectedLocation: (lat, lon) => set({ selectedLat: lat, selectedLon: lon }),
      setDatasetMeta:      (m) => set({ datasetMeta: m }),
      setDataQuality:      (q) => set({ dataQuality: q }),
      setCurrentState:     (s) => set({ currentState: s }),
      setTimeseries:       (t) => set({ timeseries: t }),
      setNationalSummary:  (s) => set({ nationalSummary: s }),
      setForecastData:     (f) => set({ forecastData: f }),
      setForecastLoading:  (b) => set({ forecastLoading: b }),
      setActiveScenario:   (s) => set({ activeScenario: s }),
      setScenarioResult:   (r) => set({ scenarioResult: r }),
      setScenarioLoading:  (b) => set({ scenarioLoading: b }),
      setTrendResult:      (r) => set({ trendResult: r }),
      setAnomalyResult:    (r) => set({ anomalyResult: r }),
      setRiskResult:       (r) => set({ riskResult: r }),
      setIndicators:       (i) => set({ indicators: i }),
      toggleSidebar:       () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setError:            (e) => set({ error: e }),
      clearError:          () => set({ error: null }),
    }),
    { name: "IndiCliStore" }
  )
);

export default useStore;
